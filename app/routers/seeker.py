from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..database import get_db
from ..deps import require_role
from ..models import Application, CV, Job, JobSeekerProfile, Recommendation, User, UserRole
from ..schemas import (
    ApplicationCreate,
    ApplicationOut,
    CourseAdviceOut,
    CVAnalysisOut,
    CVOut,
    JobOut,
    JobRecommendation,
    SeekerProfileOut,
    SeekerProfileUpdate,
)
from ..services.ai import ai_service
from ..services.course_advisor import recommend_for_job, recommend_for_skills
from ..services.cv_parser import CVValidationError, extract_text, remove_file, save_upload, validate_upload
from ..services.embeddings import cv_embedding_text, embedder
from ..services.matching import compute_match, explain_job_match
from ..services.skills import merge_skills, normalize_skills

router = APIRouter(prefix="/seeker", tags=["Job seeker"])
seeker_only = require_role(UserRole.JOB_SEEKER)


def _profile(user: User) -> JobSeekerProfile:
    if user.seeker_profile is None:
        raise HTTPException(status_code=400, detail="Job seeker profile is missing")
    return user.seeker_profile


def _active_cv(db: Session, seeker_id: int) -> CV | None:
    return db.scalar(
        select(CV)
        .where(CV.seeker_id == seeker_id, CV.is_active.is_(True))
        .order_by(CV.uploaded_at.desc(), CV.id.desc())
    )


def _effective_skills(profile: JobSeekerProfile, cv: CV | None) -> list[str]:
    return merge_skills(cv.skills if cv else [], profile.manual_skills)


def _open_jobs_query():
    return (
        select(Job)
        .options(selectinload(Job.employer), selectinload(Job.applications))
        .where(Job.status == "open")
        .where((Job.deadline.is_(None)) | (Job.deadline >= date.today()))
        .order_by(Job.created_at.desc())
    )


@router.get("/profile", response_model=SeekerProfileOut)
def get_profile(
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> SeekerProfileOut:
    profile = _profile(user)
    cv = _active_cv(db, profile.id)
    output = SeekerProfileOut.model_validate(profile)
    output.skills = _effective_skills(profile, cv)
    return output


@router.put("/profile", response_model=SeekerProfileOut)
def update_profile(
    payload: SeekerProfileUpdate,
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> SeekerProfileOut:
    profile = _profile(user)
    data = payload.model_dump(exclude_unset=True)

    if "full_name" in data and data["full_name"]:
        user.full_name = data.pop("full_name").strip()
    else:
        data.pop("full_name", None)

    if "manual_skills" in data and data["manual_skills"] is not None:
        data["manual_skills"] = normalize_skills(data["manual_skills"])
    for field in ("headline", "location", "bio", "phone"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip() or None

    for field, value in data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    cv = _active_cv(db, profile.id)
    output = SeekerProfileOut.model_validate(profile)
    output.skills = _effective_skills(profile, cv)
    return output


@router.post("/cv", response_model=CVAnalysisOut, status_code=status.HTTP_201_CREATED)
def upload_cv(
    file: UploadFile = File(...),
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> CVAnalysisOut:
    profile = _profile(user)
    try:
        contents, extension = validate_upload(file)
        raw_text = extract_text(contents, extension)
    except CVValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    structured = ai_service.extract_cv(raw_text)
    skills = normalize_skills(structured.get("skills") or [])
    embedding = embedder.embed(
        cv_embedding_text(
            skills=skills,
            job_titles=structured.get("job_titles") or [],
            summary=structured.get("summary") or "",
            raw_text=raw_text,
        )
    )

    stored_path = save_upload(contents, extension)
    previous = db.scalars(
        select(CV).where(CV.seeker_id == profile.id, CV.is_active.is_(True))
    ).all()
    for old in previous:
        old.is_active = False

    cv = CV(
        seeker_id=profile.id,
        filename=(file.filename or "cv")[:255],
        content_type=file.content_type or "application/octet-stream",
        file_path=stored_path,
        size_bytes=len(contents),
        raw_text=raw_text,
        summary=structured.get("summary"),
        skills=skills,
        education=structured.get("education") or [],
        experience=structured.get("experience") or [],
        job_titles=structured.get("job_titles") or [],
        embedding=embedding,
        is_active=True,
    )
    db.add(cv)
    try:
        db.commit()
    except Exception:
        db.rollback()
        remove_file(stored_path)
        raise
    db.refresh(cv)

    for old in previous:
        remove_file(old.file_path)

    key_points = structured.get("key_points") or []
    if not key_points:
        from ..services.ai import derive_key_points

        key_points = derive_key_points(
            {
                "summary": cv.summary,
                "skills": cv.skills,
                "education": cv.education,
                "experience": cv.experience,
                "job_titles": cv.job_titles,
            }
        )

    return CVAnalysisOut(
        cv=CVOut.model_validate(cv),
        effective_skills=_effective_skills(profile, cv),
        key_points=key_points,
        message=(
            f"CV analysed successfully. Extracted {len(cv.skills)} skills"
            + (f" and {len(cv.job_titles)} job titles." if cv.job_titles else ".")
            + " View recommended jobs and courses below."
        ),
    )


@router.get("/cv", response_model=CVOut)
def get_latest_cv(
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> CVOut:
    profile = _profile(user)
    cv = _active_cv(db, profile.id)
    if cv is None:
        raise HTTPException(status_code=404, detail="No CV uploaded yet")
    return CVOut.model_validate(cv)


@router.get("/jobs/recommended", response_model=list[JobRecommendation])
def recommended_jobs(
    limit: int = Query(default=10, ge=1, le=30),
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> list[JobRecommendation]:
    profile = _profile(user)
    cv = _active_cv(db, profile.id)
    if cv is None:
        raise HTTPException(status_code=400, detail="Upload a CV to get job recommendations")

    candidate_skills = _effective_skills(profile, cv)
    jobs = db.scalars(_open_jobs_query()).all()

    scored: list[tuple[Job, dict]] = []
    for job in jobs:
        match = compute_match(cv.embedding or [], job.embedding or [], candidate_skills, job.required_skills)
        scored.append((job, match))
    scored.sort(key=lambda item: item[1]["score"], reverse=True)
    top = scored[:limit]

    db.execute(
        delete(Recommendation).where(
            Recommendation.seeker_id == profile.id, Recommendation.kind == "job_match"
        )
    )
    results: list[JobRecommendation] = []
    for index, (job, match) in enumerate(top):
        if index < 3:
            explanation = explain_job_match(
                job.title, match, cv.job_titles or [], candidate_skills
            )
        else:
            explanation = ai_service.quick_explanation(
                job.title, match["score"], match["matched_skills"], match["missing_skills"]
            )
        job_payload = JobOut.model_validate(job).model_dump()
        job_payload["application_count"] = len(job.applications)
        results.append(JobRecommendation(**job_payload, **match, explanation=explanation))
        db.add(
            Recommendation(
                seeker_id=profile.id,
                job_id=job.id,
                kind="job_match",
                score=match["score"],
                explanation=explanation,
                matched_skills=match["matched_skills"],
                missing_skills=match["missing_skills"],
            )
        )
    db.commit()
    return results


@router.post("/jobs/{job_id}/apply", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    job_id: int,
    payload: ApplicationCreate,
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> ApplicationOut:
    profile = _profile(user)
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Verify your email address before applying to a job.",
            },
        )
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=409, detail="This job is closed")
    if job.deadline and job.deadline < date.today():
        raise HTTPException(status_code=409, detail="The application deadline has passed")

    cv = _active_cv(db, profile.id)
    if cv is None:
        raise HTTPException(status_code=400, detail="Upload a CV before applying")

    existing = db.scalar(
        select(Application).where(
            Application.job_id == job.id, Application.seeker_id == profile.id
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied to this job")

    match = compute_match(
        cv.embedding or [], job.embedding or [], _effective_skills(profile, cv), job.required_skills
    )
    minimum = settings.min_apply_match_score
    if match["score"] < minimum:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Your CV matches this job at {match['score']}%, below the minimum "
                f"{minimum:g}% required to apply. Improve the missing skills and try again."
            ),
        )
    application = Application(
        job_id=job.id,
        seeker_id=profile.id,
        cv_id=cv.id,
        cover_note=(payload.cover_note or "").strip() or None,
        match_score=match["score"],
        matched_skills=match["matched_skills"],
        missing_skills=match["missing_skills"],
    )
    db.add(application)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="You have already applied to this job") from exc
    db.refresh(application)
    return ApplicationOut.model_validate(application)


@router.get("/applications", response_model=list[ApplicationOut])
def my_applications(
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> list[ApplicationOut]:
    profile = _profile(user)
    applications = db.scalars(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.employer))
        .where(Application.seeker_id == profile.id)
        .order_by(Application.created_at.desc())
    ).all()
    return [ApplicationOut.model_validate(application) for application in applications]


@router.get("/courses/recommended", response_model=CourseAdviceOut)
def recommended_courses(
    job_id: int | None = Query(default=None),
    limit: int = Query(default=6, ge=1, le=12),
    user: User = Depends(seeker_only),
    db: Session = Depends(get_db),
) -> CourseAdviceOut:
    profile = _profile(user)
    cv = _active_cv(db, profile.id)
    if cv is None:
        raise HTTPException(status_code=400, detail="Upload a CV to get course recommendations")

    candidate_skills = _effective_skills(profile, cv)

    if job_id is not None:
        job = db.get(Job, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        match = compute_match(cv.embedding or [], job.embedding or [], candidate_skills, job.required_skills)
        result = recommend_for_job(
            db, profile, job, match["missing_skills"], match["score"], limit=limit
        )
        return CourseAdviceOut(**result)

    jobs = db.scalars(_open_jobs_query()).all()
    scored = []
    for job in jobs:
        match = compute_match(cv.embedding or [], job.embedding or [], candidate_skills, job.required_skills)
        if match["missing_skills"]:
            scored.append((job, match))
    scored.sort(key=lambda item: item[1]["score"], reverse=True)

    gaps: list[str] = []
    for _, match in scored[:5]:
        for skill in match["missing_skills"]:
            if skill not in gaps:
                gaps.append(skill)
    result = recommend_for_skills(
        db,
        profile,
        gaps[:8],
        job_title="your recommended roles",
        limit=limit,
    )
    return CourseAdviceOut(**result)
