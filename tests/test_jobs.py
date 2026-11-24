from datetime import date, timedelta

from sqlalchemy import select

from app.models import Application, CV, EmployerProfile, Job, JobSeekerProfile


def _job_payload(title="Backend Engineer"):
    return {
        "title": title,
        "description": (
            "We are looking for an engineer with strong Python, FastAPI, PostgreSQL, Docker "
            "and AWS experience to build reliable APIs."
        ),
        "required_skills": [],
        "location": "Remote",
        "job_type": "full_time",
        "salary_min": 60000,
        "salary_max": 80000,
        "currency": "EUR",
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
    }


def test_job_creation_extracts_skills(client, register_user, auth_headers):
    employer = register_user(role="employer", company_name="Skill Co")
    response = client.post("/employer/jobs", json=_job_payload(), headers=auth_headers(employer))
    assert response.status_code == 201, response.text
    job = response.json()
    for skill in ("Python", "FastAPI", "PostgreSQL", "Docker", "AWS"):
        assert skill in job["required_skills"]
    assert job["status"] == "open"
    assert job["employer"]["company_name"] == "Skill Co"


def test_employer_can_only_delete_own_jobs(client, register_user, auth_headers):
    owner = register_user(role="employer", company_name="Owner Co")
    stranger = register_user(role="employer", company_name="Stranger Co")

    created = client.post(
        "/employer/jobs", json=_job_payload("Owner Role"), headers=auth_headers(owner)
    )
    assert created.status_code == 201
    job_id = created.json()["id"]

    forbidden = client.delete(f"/employer/jobs/{job_id}", headers=auth_headers(stranger))
    assert forbidden.status_code == 404

    own_list = client.get("/employer/jobs", headers=auth_headers(owner)).json()
    assert [job["id"] for job in own_list] == [job_id]

    deleted = client.delete(f"/employer/jobs/{job_id}", headers=auth_headers(owner))
    assert deleted.status_code == 204
    assert client.get("/employer/jobs", headers=auth_headers(owner)).json() == []


def test_close_job_blocks_applications(client, register_user, auth_headers, make_docx):
    employer = register_user(role="employer", company_name="Closed Co")
    seeker = register_user(role="job_seeker")

    cv = make_docx("Skills: Python, FastAPI, PostgreSQL, Docker, AWS")
    upload = client.post(
        "/seeker/cv",
        headers=auth_headers(seeker),
        files={
            "file": (
                "cv.docx",
                cv,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload.status_code == 201, upload.text

    created = client.post(
        "/employer/jobs", json=_job_payload("Closing Role"), headers=auth_headers(employer)
    )
    job_id = created.json()["id"]

    closed = client.patch(
        f"/employer/jobs/{job_id}", json={"status": "closed"}, headers=auth_headers(employer)
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    application = client.post(
        f"/seeker/jobs/{job_id}/apply", json={}, headers=auth_headers(seeker)
    )
    assert application.status_code == 409


def test_employer_sees_applied_and_eligible_candidates(client, register_user, auth_headers, db):
    employer = register_user(role="employer", company_name="Pipeline Co")
    applied = register_user(role="job_seeker", full_name="Applied Seeker")
    eligible = register_user(role="job_seeker", full_name="Eligible Seeker")
    low_match = register_user(role="job_seeker", full_name="Low Match Seeker")

    employer_profile = db.scalar(
        select(EmployerProfile).where(EmployerProfile.user_id == employer["user"]["id"])
    )
    job = Job(
        employer_id=employer_profile.id,
        title="Backend Engineer",
        description="Build Python APIs.",
        required_skills=[],
        status="open",
        embedding=[1.0, 0.0],
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    cvs = {}
    for account, embedding in (
        (applied, [1.0, 0.0]),
        (eligible, [1.0, 0.0]),
        (low_match, [0.0, 1.0]),
    ):
        seeker_profile = db.scalar(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == account["user"]["id"])
        )
        cv = CV(
            seeker_id=seeker_profile.id,
            filename="cv.docx",
            raw_text="Skills: Python",
            skills=["Python"],
            embedding=embedding,
            is_active=True,
        )
        db.add(cv)
        db.commit()
        cvs[account["user"]["id"]] = (seeker_profile.id, cv)

    db.add(
        Application(
            job_id=job.id,
            seeker_id=cvs[applied["user"]["id"]][0],
            cv_id=cvs[applied["user"]["id"]][1].id,
            match_score=100.0,
            matched_skills=["Python"],
            missing_skills=[],
        )
    )
    db.commit()

    headers = auth_headers(employer)
    url = f"/employer/jobs/{job.id}/candidates"

    all_candidates = client.get(url, headers=headers).json()
    assert {item["full_name"] for item in all_candidates} == {
        "Applied Seeker",
        "Eligible Seeker",
    }
    assert all(item["eligible"] for item in all_candidates)
    assert sum(item["applied"] for item in all_candidates) == 1

    applied_only = client.get(url, params={"status": "applied"}, headers=headers).json()
    assert [item["full_name"] for item in applied_only] == ["Applied Seeker"]
    assert all(item["applied"] for item in applied_only)

    eligible_only = client.get(url, params={"status": "eligible"}, headers=headers).json()
    assert {item["full_name"] for item in eligible_only} == {
        "Applied Seeker",
        "Eligible Seeker",
    }
