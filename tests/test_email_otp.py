import uuid

import app.routers.auth as auth_router
from app.config import settings
from fastapi.testclient import TestClient


def _register_unverified(client: TestClient) -> dict:
    email = f"unverified-{uuid.uuid4().hex[:10]}@test.dev"
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Unverified User",
            "email": email,
            "password": "Password123!",
            "role": "job_seeker",
        },
    )
    assert response.status_code == 201, response.text
    return {**response.json(), "email": email, "password": "Password123!"}


def test_login_and_apply_require_verified_email(client: TestClient):
    account = _register_unverified(client)

    login = client.post(
        "/auth/login",
        json={"email": account["email"], "password": account["password"]},
    )
    assert login.status_code == 403
    assert login.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"

    headers = {"Authorization": f"Bearer {account['access_token']}"}
    application = client.post("/seeker/jobs/999/apply", json={}, headers=headers)
    assert application.status_code == 403
    assert application.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"


def test_email_otp_flow(client: TestClient, monkeypatch):
    account = _register_unverified(client)
    sent = []
    monkeypatch.setattr(auth_router, "smtp_configured", lambda: True)
    monkeypatch.setattr(auth_router, "send_email_otp", lambda email, code: sent.append((email, code)))
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)

    email = account["email"]
    request = client.post("/auth/request-email-otp", json={"email": email})
    assert request.status_code == 200
    assert len(sent) == 1
    assert sent[0][0] == email

    code = sent[0][1]
    assert len(code) == 6 and code.isdigit()
    wrong_code = "000000" if code != "000000" else "111111"
    assert client.post(
        "/auth/verify-email-otp", json={"email": email, "code": wrong_code}
    ).status_code == 400

    verified = client.post("/auth/verify-email-otp", json={"email": email, "code": code})
    assert verified.status_code == 200

    login = client.post(
        "/auth/login",
        json={"email": email, "password": account["password"]},
    )
    assert login.status_code == 200
    assert login.json()["user"]["email_verified"] is True


def test_otp_can_only_be_used_once(client: TestClient, monkeypatch):
    account = _register_unverified(client)
    sent = []
    monkeypatch.setattr(auth_router, "smtp_configured", lambda: True)
    monkeypatch.setattr(auth_router, "send_email_otp", lambda email, code: sent.append((email, code)))
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)

    email = account["email"]
    assert client.post("/auth/request-email-otp", json={"email": email}).status_code == 200
    code = sent[0][1]

    assert client.post("/auth/verify-email-otp", json={"email": email, "code": code}).status_code == 200
    assert client.post("/auth/verify-email-otp", json={"email": email, "code": code}).status_code == 400


def test_registration_sends_code_and_blocks_login_until_verified(client: TestClient, monkeypatch):
    sent = []
    monkeypatch.setattr(auth_router, "smtp_configured", lambda: True)
    monkeypatch.setattr(
        auth_router,
        "send_email_verification",
        lambda email, url, code: sent.append((email, code)),
    )
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)

    email = f"signup-{uuid.uuid4().hex[:10]}@test.dev"
    password = "Password123!"
    response = client.post(
        "/auth/register",
        json={
            "full_name": "New Seeker",
            "email": email,
            "password": password,
            "role": "job_seeker",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["requires_verification"] is True
    assert body["email"] == email
    assert "access_token" not in body
    assert len(sent) == 1
    assert sent[0][0] == email
    code = sent[0][1]
    assert len(code) == 6 and code.isdigit()

    locked = client.post("/auth/login", json={"email": email, "password": password})
    assert locked.status_code == 403
    assert locked.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"

    assert client.post(
        "/auth/verify-email-otp", json={"email": email, "code": code}
    ).status_code == 200
    signed_in = client.post("/auth/login", json={"email": email, "password": password})
    assert signed_in.status_code == 200
    assert signed_in.json()["user"]["email_verified"] is True
