import logging
import smtplib
from email.message import EmailMessage

from ..config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


def send_email_verification(to_email: str, verification_url: str, otp_code: str | None = None) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    from_addr = settings.smtp_from_email.strip()
    message["From"] = f"{settings.smtp_from_name} <{from_addr}>" if settings.smtp_from_name else from_addr
    message["To"] = to_email
    message["Subject"] = "Verify your TalentMatch email"
    message.set_content(
        "Welcome to TalentMatch AI.\n\n"
        f"Verify your email address using this link:\n{verification_url}\n\n"
        + (
            f"Or enter this 6-digit code in the app:\n{otp_code}\n\n"
            if otp_code
            else ""
        )
        + f"This link expires in {settings.email_verification_expire_minutes} minutes."
        + (f" The code expires in {settings.otp_expire_minutes} minutes." if otp_code else "")
    )
    otp_html = (
        f'<p>Or enter this verification code in the app: <strong style="font-size:22px;letter-spacing:4px;">{otp_code}</strong></p>'
        if otp_code
        else ""
    )
    message.add_alternative(
        f"""\
<html>
  <body style="font-family:Arial,sans-serif;line-height:1.5;color:#171717;">
    <h2>Verify your TalentMatch email</h2>
    <p>Confirm that this is your email address so you can receive account notifications and reset your password.</p>
    <p><a href="{verification_url}" style="display:inline-block;padding:10px 16px;background:#000000;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">Verify email</a></p>
    {otp_html}
  </body>
</html>
""",
        subtype="html",
    )

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)

    logger.info("Email verification sent to %s", to_email)


def send_email_otp(to_email: str, code: str) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    from_addr = settings.smtp_from_email.strip()
    message["From"] = f"{settings.smtp_from_name} <{from_addr}>" if settings.smtp_from_name else from_addr
    message["To"] = to_email
    message["Subject"] = "Your TalentMatch verification code"
    message.set_content(
        f"Your TalentMatch email verification code is:\n\n{code}\n\n"
        f"This code expires in {settings.otp_expire_minutes} minutes. "
        "If you did not request it, you can ignore this email."
    )
    message.add_alternative(
        f"""\
<html>
  <body style="font-family:Arial,sans-serif;line-height:1.5;color:#171717;">
    <h2>Verify your TalentMatch email</h2>
    <p>Enter this 6-digit code in the app to verify your email address:</p>
    <p style="font-size:28px;font-weight:700;letter-spacing:6px;">{code}</p>
    <p style="font-size:13px;color:#525252;">This code expires in {settings.otp_expire_minutes} minutes. If you did not request it, you can ignore this email.</p>
  </body>
</html>
""",
        subtype="html",
    )

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)

    logger.info("Email verification code sent to %s", to_email)


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    from_addr = settings.smtp_from_email.strip()
    if settings.smtp_from_name:
        message["From"] = f"{settings.smtp_from_name} <{from_addr}>"
    else:
        message["From"] = from_addr
    message["To"] = to_email
    message["Subject"] = "Reset your TalentMatch password"
    message.set_content(
        "We received a request to reset your TalentMatch password.\n\n"
        f"Use this link to choose a new password:\n{reset_url}\n\n"
        f"This link expires in {settings.reset_token_expire_minutes} minutes. "
        "If you did not request a reset, you can ignore this email."
    )
    message.add_alternative(
        f"""\
<html>
  <body style="font-family:Arial,sans-serif;line-height:1.5;color:#171717;">
    <h2 style="margin-bottom:8px;">Reset your TalentMatch password</h2>
    <p>We received a request to reset your TalentMatch password.</p>
    <p>
      <a href="{reset_url}" style="display:inline-block;padding:10px 16px;background:#000000;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">
        Choose a new password
      </a>
    </p>
    <p style="font-size:13px;color:#525252;">Or copy this link:<br><a href="{reset_url}">{reset_url}</a></p>
    <p style="font-size:13px;color:#525252;">This link expires in {settings.reset_token_expire_minutes} minutes. If you did not request a reset, you can ignore this email.</p>
  </body>
</html>
""",
        subtype="html",
    )

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)

    logger.info("Password reset email sent to %s", to_email)
