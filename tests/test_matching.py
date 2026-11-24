from app.services.matching import compute_match
from app.services.skills import extract_skills, normalize_skills, skill_overlap


def test_hybrid_score_is_sixty_forty():
    match = compute_match(
        cv_embedding=[1.0, 0.0],
        job_embedding=[1.0, 0.0],
        candidate_skills=["Python", "SQL"],
        required_skills=["Python", "SQL", "Docker"],
    )
    assert match["semantic_score"] == 100.0
    assert match["skill_score"] == 66.7
    assert match["score"] == 86.7
    assert match["matched_skills"] == ["Python", "SQL"]
    assert match["missing_skills"] == ["Docker"]


def test_semantic_only_when_no_required_skills():
    match = compute_match([1.0, 0.0], [0.0, 1.0], ["Python"], [])
    assert match["score"] == 0.0
    assert match["missing_skills"] == []


def test_skill_aliases_and_extraction():
    text = "Built APIs with postgres, js, react.js and FastAPI. Deployed with k8s."
    skills = extract_skills(text)
    assert "PostgreSQL" in skills
    assert "JavaScript" in skills
    assert "React" in skills
    assert "FastAPI" in skills
    assert "Kubernetes" in skills


def test_overlap_normalizes_inputs():
    matched, missing, overlap = skill_overlap(["postgres", "JS"], ["PostgreSQL", "JavaScript", "AWS"])
    assert matched == ["JavaScript", "PostgreSQL"]
    assert missing == ["AWS"]
    assert overlap == 0.6667


def test_normalize_preserves_custom_skills():
    assert normalize_skills(["python", "Custom Skill", "custom skill"]) == ["Custom Skill", "Python"]
