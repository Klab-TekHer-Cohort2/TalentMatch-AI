from datetime import date, timedelta

from sqlalchemy import select

from app.config import settings
from app.models import Course, Job
from app.services.course_advisor import index_courses
from app.services.matching import compute_match

CV_TEXT = """Jane Candidate
Senior Python Engineer

Summary: Engineer with five years of experience building APIs.

Experience:
2019 - Present Backend Engineer at DataWorks

Skills: Python, FastAPI, PostgreSQL, SQL, Git

Education:
Bachelor of Science in Computer Science, State University, 2019
"""


def _seed_courses(db):
    if db.scalar(select(Course).limit(1)) is None:
        db.add_all(
            [
                Course(
                    title="Docker and Kubernetes",
                    provider="Demo Academy",
                    description="Learn containers and orchestration for production deployments.",
                    skills=["Docker", "Kubernetes", "DevOps"],
                    level="intermediate",
                    duration="12 hours",
                    url="https://example.com/docker",
                ),
                Course(
                    title="AWS Cloud Practitioner",
                    provider="Demo Cloud",
                    description="Cloud fundamentals on Amazon Web Services, security and networking.",
                    skills=["AWS", "Cloud Security", "Networking"],
                    level="beginner",
                    duration="10 hours",
                    url="https://example.com/aws",
                ),
                Course(
                    title="Advanced FastAPI",
                    provider="Demo Academy",
                    description="Typed APIs, authentication and deployments with FastAPI.",
                    skills=["FastAPI", "Python", "REST APIs"],
                    level="advanced",
                    duration="8 hours",
                    url="https://example.com/fastapi",
                ),
            ]
        )
        db.commit()
    index_courses(db, reset=True)


def test_cv_upload_match_apply_and_rag(
    client, db, register_user, auth_headers, make_docx, monkeypatch
):
    # This test covers the pipeline mechanics; the 50% apply gate has its own test.
    monkeypatch.setattr(settings, "min_apply_match_score", 0.0)
    _seed_courses(db)

    employer = register_user(role="employer", company_name="Flow Co")
    seeker = register_user(role="job_seeker", full_name="Jane Candidate")

    job_response = client.post(
        "/employer/jobs",
        headers=auth_headers(employer),
        json={
            "title": "Python API Engineer",
            "description": (
                "Build Python APIs with FastAPI and PostgreSQL. You will deploy services with "
                "Docker on AWS and collaborate with product."
            ),
            "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
            "location": "Remote",
            "job_type": "full_time",
            "salary_min": 60000,
            "salary_max": 85000,
            "currency": "EUR",
            "deadline": (date.today() + timedelta(days=20)).isoformat(),
        },
    )
    assert job_response.status_code == 201, job_response.text
    job = job_response.json()

    upload = client.post(
        "/seeker/cv",
        headers=auth_headers(seeker),
        files={
            "file": (
                "jane_cv.docx",
                make_docx(CV_TEXT),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    analysis = upload.json()
    assert "Python" in analysis["cv"]["skills"]
    assert "FastAPI" in analysis["cv"]["skills"]
    assert analysis["cv"]["is_active"] is True

    recommended = client.get("/seeker/jobs/recommended", headers=auth_headers(seeker))
    assert recommended.status_code == 200, recommended.text
    jobs = recommended.json()
    target = next(item for item in jobs if item["id"] == job["id"])
    assert target["score"] > 0
    assert "Python" in target["matched_skills"]
    assert "Docker" in target["missing_skills"]
    assert target["explanation"]

    advice = client.get(
        f"/seeker/courses/recommended?job_id={job['id']}", headers=auth_headers(seeker)
    )
    assert advice.status_code == 200, advice.text
    advice_data = advice.json()
    assert advice_data["skill_gaps"]
    assert advice_data["courses"], "RAG should retrieve catalog courses for the gaps"
    returned_ids = {course["id"] for course in advice_data["courses"]}
    catalog_ids = {course.id for course in db.scalars(select(Course)).all()}
    assert returned_ids <= catalog_ids, "The advisor must never invent courses"
    assert advice_data["advice"]

    application = client.post(
        f"/seeker/jobs/{job['id']}/apply",
        headers=auth_headers(seeker),
        json={"cover_note": "I build Python APIs and want to grow on AWS."},
    )
    assert application.status_code == 201, application.text
    assert application.json()["match_score"] > 0

    duplicate = client.post(
        f"/seeker/jobs/{job['id']}/apply", headers=auth_headers(seeker), json={}
    )
    assert duplicate.status_code == 409

    applications = client.get("/seeker/applications", headers=auth_headers(seeker)).json()
    assert len(applications) == 1
    assert applications[0]["job"]["title"] == "Python API Engineer"

    candidates = client.get(
        f"/employer/jobs/{job['id']}/candidates", headers=auth_headers(employer)
    )
    assert candidates.status_code == 200
    candidate = next(item for item in candidates.json() if item["email"] == seeker["email"])
    assert candidate["applied"] is True
    assert candidate["score"] > 0


def test_apply_rejected_below_minimum_match(client, db, register_user, auth_headers, make_docx):
    employer = register_user(role="employer", company_name="Gate Co")
    seeker = register_user(role="job_seeker", full_name="Jane Candidate")

    upload = client.post(
        "/seeker/cv",
        headers=auth_headers(seeker),
        files={
            "file": (
                "jane_cv.docx",
                make_docx(CV_TEXT),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload.status_code == 201, upload.text

    created = client.post(
        "/employer/jobs",
        headers=auth_headers(employer),
        json={
            "title": "Kubernetes Operator",
            "description": "Operate and scale Kubernetes clusters across regions.",
            "required_skills": ["Kubernetes"],
            "location": "Remote",
            "job_type": "full_time",
            "deadline": (date.today() + timedelta(days=20)).isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    job_id = created.json()["id"]

    job = db.get(Job, job_id)
    job.embedding = [0.0] * 384
    db.commit()

    application = client.post(
        f"/seeker/jobs/{job_id}/apply",
        headers=auth_headers(seeker),
        json={"cover_note": "Trying to apply below the threshold."},
    )
    assert application.status_code == 403, application.text
    assert "minimum" in application.json()["detail"].lower()

    applications = client.get("/seeker/applications", headers=auth_headers(seeker)).json()
    assert applications == []


def test_upload_validation(client, register_user, auth_headers, make_docx):
    seeker = register_user(role="job_seeker")
    headers = auth_headers(seeker)

    text_file = client.post(
        "/seeker/cv",
        headers=headers,
        files={"file": ("cv.txt", b"just text", "text/plain")},
    )
    assert text_file.status_code == 400

    fake_pdf = client.post(
        "/seeker/cv",
        headers=headers,
        files={"file": ("cv.pdf", b"not a real pdf", "application/pdf")},
    )
    assert fake_pdf.status_code == 400

    oversized = client.post(
        "/seeker/cv",
        headers=headers,
        files={"file": ("cv.pdf", b"%PDF" + b"0" * (5 * 1024 * 1024 + 10), "application/pdf")},
    )
    assert oversized.status_code == 400

    valid = client.post(
        "/seeker/cv",
        headers=headers,
        files={
            "file": (
                "cv.docx",
                make_docx(CV_TEXT),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert valid.status_code == 201


def test_profile_update_and_manual_skills(client, register_user, auth_headers):
    seeker = register_user(role="job_seeker", full_name="Old Name")
    headers = auth_headers(seeker)

    response = client.put(
        "/seeker/profile",
        headers=headers,
        json={
            "full_name": "New Name",
            "headline": "Data Engineer",
            "location": "Berlin",
            "manual_skills": ["python", "Airflow"],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["headline"] == "Data Engineer"
    assert "Airflow" in body["manual_skills"]
    assert "Python" in body["manual_skills"]
    assert "Python" in body["skills"]

    me = client.get("/auth/me", headers=headers).json()
    assert me["full_name"] == "New Name"


def test_matching_is_deterministic_for_same_inputs(db):
    _seed_courses(db)
    job = db.scalar(select(Job).limit(1))
    if job is None:
        return
    first = compute_match(job.embedding, job.embedding, job.required_skills, job.required_skills)
    assert first["score"] > 0
    assert first["missing_skills"] == []
