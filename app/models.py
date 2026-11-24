import enum
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, enum.Enum):
    JOB_SEEKER = "job_seeker"
    EMPLOYER = "employer"


role_enum = SAEnum(
    UserRole,
    name="user_role",
    native_enum=False,
    validate_strings=True,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(role_enum, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    seeker_profile: Mapped["JobSeekerProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    employer_profile: Mapped["EmployerProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class JobSeekerProfile(Base):
    __tablename__ = "job_seeker_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    headline: Mapped[str | None] = mapped_column(String(160))
    location: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(40))
    links: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    manual_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="seeker_profile")
    cvs: Mapped[list["CV"]] = relationship(
        back_populates="seeker", cascade="all, delete-orphan", passive_deletes=True
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="seeker", cascade="all, delete-orphan", passive_deletes=True
    )


class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[int] = mapped_column(primary_key=True)
    seeker_id: Mapped[int] = mapped_column(
        ForeignKey("job_seeker_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    file_path: Mapped[str | None] = mapped_column(String(500))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    education: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    experience: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    job_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    seeker: Mapped[JobSeekerProfile] = relationship(back_populates="cvs")
    applications: Mapped[list["Application"]] = relationship(back_populates="cv")


class EmployerProfile(Base):
    __tablename__ = "employer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="employer_profile")
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="employer", cascade="all, delete-orphan", passive_deletes=True
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("employer_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    location: Mapped[str | None] = mapped_column(String(160))
    job_type: Mapped[str] = mapped_column(String(40), default="full_time")
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employer: Mapped[EmployerProfile] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", passive_deletes=True
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "seeker_id", name="uq_application_job_seeker"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    seeker_id: Mapped[int] = mapped_column(
        ForeignKey("job_seeker_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    cv_id: Mapped[int | None] = mapped_column(ForeignKey("cvs.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), default="submitted")
    cover_note: Mapped[str | None] = mapped_column(Text)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[Job] = relationship(back_populates="applications")
    seeker: Mapped[JobSeekerProfile] = relationship(back_populates="applications")
    cv: Mapped[CV | None] = relationship(back_populates="applications")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    level: Mapped[str] = mapped_column(String(30), default="beginner")
    duration: Mapped[str] = mapped_column(String(60), default="")
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    seeker_id: Mapped[int] = mapped_column(
        ForeignKey("job_seeker_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(30), default="job_match")
    score: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str | None] = mapped_column(Text)
    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    course_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    seeker: Mapped[JobSeekerProfile] = relationship()


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()


class EmailOtp(Base):
    __tablename__ = "email_otps"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()
