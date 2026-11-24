from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import CV, Course, Job, JobSeekerProfile, User, UserRole
from ..schemas import CourseAdviceOut, CourseAdviceRequest, CourseOut
from ..services.ai import ai_service
from ..services.course_advisor import recommend_for_job, recommend_for_skills, retrieve_courses_for_gaps
from ..services.matching import compute_match
from ..services.skills import merge_skills, normalize_skills

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(
    q: str | None = Query(default=None, max_length=120),
    level: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Course]:
    query = select(Course)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                Course.title.ilike(pattern),
                Course.description.ilike(pattern),
                Course.provider.ilike(pattern),
            )
        )
    if level:
        query = query.where(Course.level == level)
    query = query.order_by(Course.title).offset(offset).limit(limit)
    return list(db.scalars(query).all())


def _active_cv(db: Session, seeker_id: int) -> CV | None:
    return db.scalar(
        select(CV)
        .where(CV.seeker_id == seeker_id, CV.is_active.is_(True))
        .order_by(CV.uploaded_at.desc(), CV.id.desc())
    )


def _derive_gaps(db: Session, profile: JobSeekerProfile, cv: CV, max_gaps: int = 8) -> list[str]:
    jobs = db.scalars(
        select(Job)
        .where(Job.status == "open")
        .where((Job.deadline.is_(None)) | (Job.deadline >= date.today()))
    ).all()
    skills = merge_skills(cv.skills, profile.manual_skills)
    scored = []
    for job in jobs:
        match = compute_match(cv.embedding or [], job.embedding or [], skills, job.required_skills)
        if match["missing_skills"]:
            scored.append(match)
    scored.sort(key=lambda item: item["score"], reverse=True)
    gaps: list[str] = []
    for match in scored[:5]:
        for skill in match["missing_skills"]:
            if skill not in gaps:
                gaps.append(skill)
    return gaps[:max_gaps]


@router.post("/recommend", response_model=CourseAdviceOut)
def recommend_courses(
    payload: CourseAdviceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseAdviceOut:
    if user.role == UserRole.JOB_SEEKER:
        profile = user.seeker_profile
        if profile is None:
            raise HTTPException(status_code=400, detail="Job seeker profile is missing")
        cv = _active_cv(db, profile.id)
        if cv is None:
            raise HTTPException(status_code=400, detail="Upload a CV to get course recommendations")

        if payload.job_id is not None:
            job = db.get(Job, payload.job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            skills = merge_skills(cv.skills, profile.manual_skills)
            match = compute_match(cv.embedding or [], job.embedding or [], skills, job.required_skills)
            gaps = normalize_skills(payload.gap_skills) if payload.gap_skills else match["missing_skills"]
            result = recommend_for_job(
                db, profile, job, gaps, match["score"], limit=payload.limit
            )
            return CourseAdviceOut(**result)

        gaps = normalize_skills(payload.gap_skills) if payload.gap_skills else _derive_gaps(db, profile, cv)
        result = recommend_for_skills(
            db,
            profile,
            gaps,
            job_title="your target roles",
            limit=payload.limit,
        )
        return CourseAdviceOut(**result)

    profile = user.employer_profile
    if profile is None:
        raise HTTPException(status_code=400, detail="Employer profile is missing")

    job = None
    if payload.job_id is not None:
        job = db.get(Job, payload.job_id)
        if job is None or job.employer_id != profile.id:
            raise HTTPException(status_code=404, detail="Job not found")

    gaps = normalize_skills(payload.gap_skills) if payload.gap_skills else []
    if not gaps and job is not None:
        gaps = normalize_skills(job.required_skills)
    if not gaps:
        raise HTTPException(
            status_code=400, detail="Provide gap_skills or one of your jobs with required skills"
        )

    courses = retrieve_courses_for_gaps(db, gaps, limit=payload.limit)
    advice, source = ai_service.course_advice(job.title if job else None, gaps, courses)
    return CourseAdviceOut(
        job_id=job.id if job else None,
        job_title=job.title if job else None,
        skill_gaps=gaps,
        courses=courses,
        advice=advice,
        generated_by=source,
    )
