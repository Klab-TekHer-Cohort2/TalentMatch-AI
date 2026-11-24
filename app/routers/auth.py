import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import (
    EmailOtp,
    EmailVerificationToken,
    EmployerProfile,
    JobSeekerProfile,
    PasswordResetToken,
    User,
    UserRole,
)
from ..schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageOut,
    RegisterRequest,
    RequestEmailOtpRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerificationRequiredOut,
    VerifyEmailOtpRequest,
    VerifyEmailRequest,
    UserPublic,
)
from ..security import create_access_token, hash_password, verify_password
from ..services.email import (
    send_email_otp,
    send_email_verification,
    send_password_reset_email,
    smtp_configured,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _token_response(user: User) -> TokenResponse:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post(
    "/register",
    response_model=TokenResponse | VerificationRequiredOut,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest, db: Session = Depends(get_db)
) -> TokenResponse | VerificationRequiredOut:
    email = payload.email.lower().strip()
    exists = db.scalar(select(User).where(func.lower(User.email) == email))
    if exists:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    if payload.role == UserRole.JOB_SEEKER:
        db.add(JobSeekerProfile(user_id=user.id))
    else:
        db.add(
            EmployerProfile(
                user_id=user.id,
                company_name=(payload.company_name or payload.full_name).strip(),
            )
        )

    db.commit()
    db.refresh(user)

    if smtp_configured():
        try:
            raw_token = _create_email_verification_token(db, user)
            otp_code = _create_email_otp(db, user)
            verification_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw_token}"
            send_email_verification(user.email, verification_url, otp_code)
        except Exception as exc:
            logger.exception("Failed to send registration verification email: %s", exc)
            _invalidate_active_otps(db, user)
        return VerificationRequiredOut(
            message="We sent a 6-digit verification code to your email. Enter it to activate your account.",
            email=user.email,
        )

    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled")
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Verify your email address with the code we sent you before logging in.",
            },
        )
    return _token_response(user)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/change-password", response_model=MessageOut)
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageOut:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the current password",
        )
    user.hashed_password = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return MessageOut(message="Password updated successfully")


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_otp(code: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _invalidate_active_otps(db: Session, user: User) -> None:
    now = datetime.now(timezone.utc)
    active = db.scalars(
        select(EmailOtp).where(
            EmailOtp.user_id == user.id,
            EmailOtp.used_at.is_(None),
            EmailOtp.expires_at > now,
        )
    ).all()
    for record in active:
        record.used_at = now
    db.commit()


def _create_email_otp(db: Session, user: User) -> str:
    _invalidate_active_otps(db, user)
    now = datetime.now(timezone.utc)
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        EmailOtp(
            user_id=user.id,
            code_hash=_hash_otp(code),
            expires_at=now + timedelta(minutes=settings.otp_expire_minutes),
        )
    )
    db.commit()
    return code


def _create_email_verification_token(db: Session, user: User) -> str:
    now = datetime.now(timezone.utc)
    active_tokens = db.scalars(
        select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
    ).all()
    for record in active_tokens:
        record.used_at = now

    raw_token = secrets.token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=_hash_reset_token(raw_token),
            expires_at=now + timedelta(minutes=settings.email_verification_expire_minutes),
        )
    )
    db.commit()
    return raw_token


@router.post("/verify-email", response_model=MessageOut)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageOut:
    token_hash = _hash_reset_token(payload.token.strip())
    record = db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)
    expires_at = record.expires_at if record else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if (
        record is None
        or record.used_at is not None
        or expires_at is None
        or expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Verification link is invalid or has expired")

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Verification link is invalid or has expired")

    user.email_verified = True
    user.email_verified_at = now
    record.used_at = now
    db.add(user)
    db.add(record)
    db.commit()
    return MessageOut(message="Email verified successfully")


@router.post("/request-email-otp", response_model=MessageOut)
def request_email_otp(
    payload: RequestEmailOtpRequest,
    db: Session = Depends(get_db),
) -> MessageOut:
    generic = MessageOut(message="If an unverified account exists, a verification code has been sent.")
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None or not user.is_active or user.email_verified:
        return generic
    if not smtp_configured():
        raise HTTPException(status_code=503, detail="Email delivery is not configured.")

    now = datetime.now(timezone.utc)
    last = db.scalar(
        select(EmailOtp)
        .where(
            EmailOtp.user_id == user.id,
            EmailOtp.used_at.is_(None),
            EmailOtp.expires_at > now,
        )
        .order_by(EmailOtp.created_at.desc())
    )
    last_created = _as_utc(last.created_at) if last else None
    if last_created is not None and (now - last_created) < timedelta(
        seconds=settings.otp_resend_cooldown_seconds
    ):
        raise HTTPException(status_code=429, detail="Please wait before requesting another code.")

    code = _create_email_otp(db, user)
    try:
        send_email_otp(user.email, code)
    except Exception as exc:
        logger.exception("Failed to send verification code: %s", exc)
        raise HTTPException(status_code=503, detail="Could not send the verification code. Please try again later.") from exc
    return generic


@router.post("/verify-email-otp", response_model=MessageOut)
def verify_email_otp(
    payload: VerifyEmailOtpRequest,
    db: Session = Depends(get_db),
) -> MessageOut:
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    code_hash = _hash_otp(payload.code.strip())
    record = None
    if user is not None:
        record = db.scalar(
            select(EmailOtp)
            .where(EmailOtp.user_id == user.id, EmailOtp.code_hash == code_hash)
            .order_by(EmailOtp.created_at.desc())
        )

    now = datetime.now(timezone.utc)
    expires_at = _as_utc(record.expires_at) if record else None
    if (
        record is None
        or record.used_at is not None
        or expires_at is None
        or expires_at <= now
        or record.attempts >= settings.otp_max_attempts
    ):
        if record is not None and record.used_at is None and expires_at is not None and expires_at > now:
            record.attempts += 1
            if record.attempts >= settings.otp_max_attempts:
                record.used_at = now
            db.add(record)
            db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    record.used_at = now
    active = db.scalars(
        select(EmailOtp).where(
            EmailOtp.user_id == user.id,
            EmailOtp.used_at.is_(None),
            EmailOtp.expires_at > now,
        )
    ).all()
    for other in active:
        other.used_at = now
    user.email_verified = True
    if user.email_verified_at is None:
        user.email_verified_at = now
    db.add(user)
    db.add(record)
    db.commit()
    return MessageOut(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageOut)
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> MessageOut:
    generic = MessageOut(message="If an unverified account exists, a verification email has been sent.")
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None or not user.is_active or user.email_verified:
        return generic
    if not smtp_configured():
        raise HTTPException(status_code=503, detail="Email delivery is not configured.")

    raw_token = _create_email_verification_token(db, user)
    verification_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw_token}"
    try:
        send_email_verification(user.email, verification_url)
    except Exception as exc:
        logger.exception("Failed to send verification email: %s", exc)
        raise HTTPException(status_code=503, detail="Could not send the verification email. Please try again later.")
    return generic


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageOut:
    generic = MessageOut(
        message="If an account exists for that email, a password reset link has been sent."
    )
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None or not user.is_active:
        return generic
    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Verify your email address before requesting a password reset.",
        )

    if not smtp_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Email delivery is not configured. Set SMTP_* and FRONTEND_URL in backend/.env, "
                "or ask an administrator to reset the password."
            ),
        )

    now = datetime.now(timezone.utc)
    active_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    ).all()
    for record in active_tokens:
        record.used_at = now

    raw_token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_reset_token(raw_token),
            expires_at=now + timedelta(minutes=settings.reset_token_expire_minutes),
        )
    )
    db.commit()

    reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"
    try:
        send_password_reset_email(user.email, reset_url)
    except Exception as exc:
        logger.exception("Failed to send password reset email: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Could not send the reset email. Please try again later or contact support.",
        )
    return generic


@router.post("/reset-password", response_model=MessageOut)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageOut:
    token_hash = _hash_reset_token(payload.token.strip())
    record = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)
    expires_at = record.expires_at if record else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if (
        record is None
        or record.used_at is not None
        or expires_at is None
        or expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired")

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired")

    user.hashed_password = hash_password(payload.new_password)
    record.used_at = now
    db.add(user)
    db.add(record)
    db.commit()
    return MessageOut(message="Password has been reset. You can now log in.")
