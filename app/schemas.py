from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from .models import UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth / users ----------
class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = UserRole.JOB_SEEKER
    company_name: str | None = Field(default=None, max_length=160)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=8, max_length=72)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserPublic(ORMModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    email_verified: bool = False
    created_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# ---------- Seeker profile ----------
class SeekerProfileOut(ORMModel):
    id: int
    headline: str | None = None
    location: str | None = None
    bio: str | None = None
    phone: str | None = None
    links: dict[str, Any] = {}
    manual_skills: list[str] = []
    skills: list[str] = []
    updated_at: datetime | None = None


class SeekerProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=4000)
    phone: str | None = Field(default=None, max_length=40)
    links: dict[str, str] | None = None
    manual_skills: list[str] | None = None


class CVOut(ORMModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    summary: str | None = None
    skills: list[str] = []
    education: list[dict[str, Any]] = []
    experience: list[dict[str, Any]] = []
    job_titles: list[str] = []
    is_active: bool
    uploaded_at: datetime | None = None


class CVAnalysisOut(BaseModel):
    cv: CVOut
    effective_skills: list[str]
    key_points: list[str] = []
    message: str


# ---------- Employer ----------
class EmployerProfileOut(ORMModel):
    id: int
    company_name: str
    website: str | None = None
    location: str | None = None
    description: str | None = None


class EmployerProfileUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=2, max_length=160)
    website: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=4000)


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=30, max_length=20000)
    required_skills: list[str] = []
    location: str | None = Field(default=None, max_length=160)
    job_type: str = Field(default="full_time", max_length=40)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=10)
    deadline: date | None = None

    @field_validator("required_skills")
    @classmethod
    def clean_skills(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(skill.strip() for skill in value if skill and skill.strip()))

    @field_validator("deadline")
    @classmethod
    def deadline_not_in_past(cls, value: date | None) -> date | None:
        if value is not None and value < date.today():
            raise ValueError("Deadline cannot be in the past")
        return value

    @model_validator(mode="after")
    def salary_range(self) -> "JobCreate":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max")
        return self


class JobStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|closed)$")


class EmployerPublic(ORMModel):
    id: int
    company_name: str
    website: str | None = None
    location: str | None = None


class JobOut(ORMModel):
    id: int
    title: str
    description: str
    required_skills: list[str] = []
    location: str | None = None
    job_type: str
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str
    deadline: date | None = None
    status: str
    created_at: datetime | None = None
    employer: EmployerPublic | None = None
    application_count: int = 0


class JobRecommendation(JobOut):
    score: float
    semantic_score: float
    skill_score: float
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    explanation: str = ""


# ---------- Applications / candidates ----------
class ApplicationCreate(BaseModel):
    cover_note: str | None = Field(default=None, max_length=2000)


class ApplicationOut(ORMModel):
    id: int
    job_id: int
    status: str
    cover_note: str | None = None
    match_score: float
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    created_at: datetime | None = None
    job: JobOut | None = None


class CandidateOut(BaseModel):
    seeker_id: int
    full_name: str
    email: EmailStr
    headline: str | None = None
    location: str | None = None
    skills: list[str] = []
    score: float
    semantic_score: float
    skill_score: float
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    explanation: str = ""
    applied: bool = False
    eligible: bool = False
    application_id: int | None = None
    cv_filename: str | None = None


# ---------- Courses / RAG ----------
class CourseOut(ORMModel):
    id: int
    title: str
    provider: str
    description: str
    skills: list[str] = []
    level: str
    duration: str
    url: str


class CourseMatch(CourseOut):
    relevance: float = 0.0
    covers: list[str] = []


class CourseAdviceRequest(BaseModel):
    job_id: int | None = None
    gap_skills: list[str] | None = None
    limit: int = Field(default=6, ge=1, le=12)

    @field_validator("gap_skills")
    @classmethod
    def clean_gaps(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return list(dict.fromkeys(skill.strip() for skill in value if skill and skill.strip()))


class CourseAdviceOut(BaseModel):
    job_id: int | None = None
    job_title: str | None = None
    skill_gaps: list[str] = []
    courses: list[CourseMatch] = []
    advice: str
    generated_by: str = "fallback"


class MessageOut(BaseModel):
    message: str
