import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Course, Job, JobSeekerProfile, Recommendation
from .ai import ai_service
from .embeddings import embedder
from .skills import normalize_skills
from .vector_store import course_store

logger = logging.getLogger(__name__)


def course_document(course: Course) -> str:
    return (
        f"Course: {course.title}. Provider: {course.provider}. Level: {course.level}. "
        f"Duration: {course.duration}. Skills taught: {', '.join(course.skills)}. "
        f"Description: {course.description}"
    )


def index_courses(db: Session, reset: bool = False) -> int:
    courses = db.scalars(select(Course).order_by(Course.id)).all()
    if not courses:
        return 0
    if reset:
        course_store.reset()
    documents = [course_document(course) for course in courses]
    embeddings = embedder.embed_many(documents)
    metadatas = [
        {
            "course_id": course.id,
            "title": course.title,
            "provider": course.provider,
            "level": course.level,
            "duration": course.duration,
            "url": course.url,
            "skills": json.dumps(normalize_skills(course.skills)),
        }
        for course in courses
    ]
    course_store.upsert(
        ids=[f"course-{course.id}" for course in courses],
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.info("Indexed %s courses into %s", len(courses), course_store.backend)
    return len(courses)


def ensure_course_index(db: Session) -> int:
    count = db.scalar(select(Course.id).limit(1))
    if count is None:
        return 0
    try:
        if course_store.count() >= len(db.scalars(select(Course.id)).all()):
            return course_store.count()
        return index_courses(db, reset=True)
    except Exception as exc:
        logger.warning("Course index unavailable: %s", exc)
        return 0


def _course_match_payload(course: Course, relevance: float, covers: list[str]) -> dict[str, Any]:
    return {
        "id": course.id,
        "title": course.title,
        "provider": course.provider,
        "description": course.description,
        "skills": normalize_skills(course.skills),
        "level": course.level,
        "duration": course.duration,
        "url": course.url,
        "relevance": round(relevance * 100, 1),
        "covers": covers,
    }


def retrieve_courses_for_gaps(db: Session, gaps: list[str], limit: int = 6) -> list[dict[str, Any]]:
    """For every gap, retrieve the most relevant catalog courses from the vector store."""
    if not gaps:
        return []

    collected: dict[int, dict[str, Any]] = {}
    semantic_only: dict[int, dict[str, Any]] = {}
    per_gap = max(3, settings.rag_top_k)

    for gap in gaps:
        query_vector = embedder.embed(
            f"Course that teaches {gap}. Training in {gap}, practical exercises, projects."
        )
        try:
            hits = course_store.query(query_vector, n_results=per_gap * 3)
        except Exception as exc:
            logger.warning("Vector query failed for gap %s: %s", gap, exc)
            hits = []

        exact_hit = False
        for hit in hits:
            metadata = hit.get("metadata") or {}
            try:
                course_id = int(metadata.get("course_id", 0))
            except (TypeError, ValueError):
                continue
            if not course_id:
                continue
            try:
                skills = normalize_skills(json.loads(metadata.get("skills") or "[]"))
            except json.JSONDecodeError:
                skills = []
            semantic_only.setdefault(
                course_id, {"score": hit["score"], "covers": set()}
            )
            if gap in skills:
                exact_hit = True
                entry = collected.setdefault(course_id, {"score": hit["score"], "covers": set()})
                entry["covers"].add(gap)
                entry["score"] = max(entry["score"], hit["score"])
        if not exact_hit and not collected:
            for hit in hits[:per_gap]:
                metadata = hit.get("metadata") or {}
                try:
                    course_id = int(metadata.get("course_id", 0))
                except (TypeError, ValueError):
                    continue
                if course_id:
                    semantic_only.setdefault(course_id, {"score": hit["score"], "covers": set()})

    chosen = collected or semantic_only
    if not chosen:
        return []

    rows = db.scalars(select(Course).where(Course.id.in_(chosen.keys()))).all()
    by_id = {row.id: row for row in rows}

    ranked = sorted(
        chosen.items(),
        key=lambda item: (len(item[1]["covers"]), item[1]["score"]),
        reverse=True,
    )[:limit]

    return [
        _course_match_payload(by_id[course_id], data["score"], sorted(data["covers"]))
        for course_id, data in ranked
        if course_id in by_id
    ]


def recommend_for_job(
    db: Session,
    seeker: JobSeekerProfile,
    job: Job,
    gaps: list[str],
    score: float,
    limit: int = 6,
) -> dict[str, Any]:
    if not gaps:
        advice = (
            "Your profile already covers all the required skills for this role. "
            "Keep the CV updated and tailor your application note to the employer's priorities."
        )
        db.add(
            Recommendation(
                seeker_id=seeker.id,
                job_id=job.id,
                kind="course_advice",
                score=score,
                explanation=advice,
                missing_skills=[],
                course_ids=[],
            )
        )
        db.commit()
        return {
            "job_id": job.id,
            "job_title": job.title,
            "skill_gaps": [],
            "courses": [],
            "advice": advice,
            "generated_by": "fallback",
        }

    courses = retrieve_courses_for_gaps(db, gaps, limit=limit)
    advice, source = ai_service.course_advice(job.title, gaps, courses)
    db.add(
        Recommendation(
            seeker_id=seeker.id,
            job_id=job.id,
            kind="course_advice",
            score=score,
            explanation=advice,
            missing_skills=gaps,
            course_ids=[course["id"] for course in courses],
        )
    )
    db.commit()
    return {
        "job_id": job.id,
        "job_title": job.title,
        "skill_gaps": gaps,
        "courses": courses,
        "advice": advice,
        "generated_by": source,
    }


def recommend_for_skills(
    db: Session,
    seeker: JobSeekerProfile,
    gaps: list[str],
    job_title: str | None = None,
    limit: int = 6,
    job_id: int | None = None,
    score: float | None = None,
) -> dict[str, Any]:
    gaps = list(dict.fromkeys(gaps))[:10]
    if not gaps:
        advice = (
            "No skill gaps were detected in your current recommendations. "
            "Upload an updated CV or browse jobs to refresh your gap analysis."
        )
        return {
            "job_id": job_id,
            "job_title": job_title,
            "skill_gaps": [],
            "courses": [],
            "advice": advice,
            "generated_by": "fallback",
        }

    courses = retrieve_courses_for_gaps(db, gaps, limit=limit)
    advice, source = ai_service.course_advice(job_title, gaps, courses)
    db.add(
        Recommendation(
            seeker_id=seeker.id,
            job_id=job_id,
            kind="course_advice",
            score=score,
            explanation=advice,
            missing_skills=gaps,
            course_ids=[course["id"] for course in courses],
        )
    )
    db.commit()
    return {
        "job_id": job_id,
        "job_title": job_title,
        "skill_gaps": gaps,
        "courses": courses,
        "advice": advice,
        "generated_by": source,
    }
