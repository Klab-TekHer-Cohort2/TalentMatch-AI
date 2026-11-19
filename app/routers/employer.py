from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..database import get_db
from ..deps import require_role
from ..models import Application, EmployerProfile, Job, JobSeekerProfile, User, UserRole
from ..schemas import (
    CandidateOut,
    EmployerProfileOut,
    EmployerProfileUpdate,
    JobCreate,
    JobOut,
    JobStatusUpdate,
)
from ..services.ai import ai_service
from ..services.embeddings import embedder, job_embedding_text
from ..services.matching import compute_match
from ..services.skills import merge_skills, normalize_skills

router = APIRouter(prefix="/employer", tags=["Employer"])
employer_only = require_role(UserRole.EMPLOYER)


def _profile(user: User) -> EmployerProfile:
    if user.employer_profile is None:
        raise HTTPException(status_code=400, detail="Employer profile is missing")
    return user.employer_profile


def _own_job(db: Session, employer_id: int, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None or job.employer_id != employer_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _job_payload(job: Job) -> JobOut:
    payload = JobOut.model_validate(job).model_dump()
    payload["application_count"] = len(job.applications)
    return JobOut(**payload)


@router.get("/profile", response_model=EmployerProfileOut)
def get_profile(user: User = Depends(employer_only)) -> EmployerProfile:
    return _profile(user)


@router.put("/profile", response_model=EmployerProfileOut)
def update_profile(
    payload: EmployerProfileUpdate,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
) -> EmployerProfile:
    profile = _profile(user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(profile, field, value)
    if not profile.company_name:
        raise HTTPException(status_code=400, detail="Company name is required")
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
) -> JobOut:
    profile = _profile(user)
    extracted = ai_service.extract_job_skills(payload.title, payload.description)
    skills = normalize_skills(merge_skills(payload.required_skills, extracted))
    embedding = embedder.embed(
        job_embedding_text(payload.title, payload.description, skills, payload.location)
    )

    job = Job(
        employer_id=profile.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        required_skills=skills,
        location=payload.location,
        job_type=payload.job_type,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        currency=payload.currency,
        deadline=payload.deadline,
        status="open",
        embedding=embedding,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_payload(job)


@router.get("/jobs", response_model=list[JobOut])
def my_jobs(
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
) -> list[JobOut]:
    profile = _profile(user)
    jobs = db.scalars(
        select(Job)
        .options(selectinload(Job.employer), selectinload(Job.applications))
        .where(Job.employer_id == profile.id)
        .order_by(Job.created_at.desc())
    ).all()
    return [_job_payload(job) for job in jobs]


@router.patch("/jobs/{job_id}", response_model=JobOut)
def update_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
) -> JobOut:
    profile = _profile(user)
    job = _own_job(db, profile.id, job_id)
    job.status = payload.status
    db.commit()
    db.refresh(job)
    return _job_payload(job)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
) -> Response:
    profile = _profile(user)
    job = _own_job(db, profile.id, job_id)
    db.delete(job)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateOut])
def job_candidates(
    job_id: int,
    candidate_status: str = Query(
        default="all", alias="status", pattern="^(all|applied|eligible)$"
    ),
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
) -> list[CandidateOut]:
    profile = _profile(user)
    job = _own_job(db, profile.id, job_id)
    applications = db.scalars(select(Application).where(Application.job_id == job.id)).all()
    applied_by_seeker = {application.seeker_id: application for application in applications}
    minimum = settings.min_apply_match_score

    seekers = db.scalars(
        select(JobSeekerProfile).options(
            selectinload(JobSeekerProfile.user), selectinload(JobSeekerProfile.cvs)
        )
    ).all()

    candidates: list[dict] = []
    for seeker in seekers:
        if seeker.user is None or not seeker.user.is_active:
            continue
        active = [cv for cv in seeker.cvs if cv.is_active]
        if not active:
            continue
        cv = max(active, key=lambda item: item.id)
        skills = merge_skills(cv.skills, seeker.manual_skills)
        match = compute_match(cv.embedding or [], job.embedding or [], skills, job.required_skills)
        applied = seeker.id in applied_by_seeker
        eligible = match["score"] >= minimum
        if candidate_status == "applied" and not applied:
            continue
        if candidate_status == "eligible" and not eligible:
            continue
        if candidate_status == "all" and not (applied or eligible):
            continue
        candidates.append(
            {
                "seeker": seeker,
                "cv": cv,
                "skills": skills,
                "match": match,
                "applied": applied,
                "eligible": eligible,
            }
        )

    candidates.sort(key=lambda item: item["match"]["score"], reverse=True)
    results: list[CandidateOut] = []
    for index, candidate in enumerate(candidates[:30]):
        seeker: JobSeekerProfile = candidate["seeker"]
        match = candidate["match"]
        if index < 5:
            explanation = ai_service.explain_match(
                job.title,
                match["score"],
                match["matched_skills"],
                match["missing_skills"],
                cv.job_titles if (cv := candidate["cv"]) else [],
                candidate["skills"],
            )
        else:
            explanation = ai_service.quick_explanation(
                job.title, match["score"], match["matched_skills"], match["missing_skills"]
            )
        application = applied_by_seeker.get(seeker.id)
        results.append(
            CandidateOut(
                seeker_id=seeker.id,
                full_name=seeker.user.full_name,
                email=seeker.user.email,
                headline=seeker.headline,
                location=seeker.location,
                skills=candidate["skills"],
                score=match["score"],
                semantic_score=match["semantic_score"],
                skill_score=match["skill_score"],
                matched_skills=match["matched_skills"],
                missing_skills=match["missing_skills"],
                explanation=explanation,
                applied=candidate["applied"],
                eligible=candidate["eligible"],
                application_id=application.id if application else None,
                cv_filename=candidate["cv"].filename,
            )
        )
    return results
