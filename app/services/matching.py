import math
from typing import Any

from .ai import ai_service
from .skills import normalize_skills, skill_overlap


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def compute_match(
    cv_embedding: list[float],
    job_embedding: list[float],
    candidate_skills: list[str],
    required_skills: list[str],
) -> dict[str, Any]:
    """Hybrid score: 60% semantic cosine similarity + 40% required-skill overlap."""
    semantic = max(0.0, min(1.0, cosine_similarity(cv_embedding, job_embedding)))
    matched, missing, overlap = skill_overlap(candidate_skills, required_skills)
    required = normalize_skills(required_skills)

    if required:
        score = 0.6 * semantic + 0.4 * overlap
    else:
        score = semantic
        overlap = 0.0

    return {
        "score": round(score * 100, 1),
        "semantic_score": round(semantic * 100, 1),
        "skill_score": round(overlap * 100, 1),
        "matched_skills": matched,
        "missing_skills": missing,
    }


def explain_job_match(
    job_title: str,
    match: dict[str, Any],
    candidate_titles: list[str],
    candidate_skills: list[str],
) -> str:
    return ai_service.explain_match(
        job_title=job_title,
        score=match["score"],
        matched=match["matched_skills"],
        missing=match["missing_skills"],
        candidate_titles=candidate_titles,
        candidate_skills=candidate_skills,
    )


def sort_by_score(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: item["match"]["score"], reverse=True)
