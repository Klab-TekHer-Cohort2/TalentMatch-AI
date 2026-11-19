from fastapi.testclient import TestClient


def test_register_login_and_me(client: TestClient, register_user, auth_headers):
    account = register_user(role="job_seeker", full_name="Ada Lovelace")
    headers = auth_headers(account)

    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == account["email"]
    assert me.json()["role"] == "job_seeker"

    login = client.post(
        "/auth/login",
        json={"email": account["email"], "password": account["password"]},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]

    wrong = client.post(
        "/auth/login",
        json={"email": account["email"], "password": "WrongPassword1!"},
    )
    assert wrong.status_code == 401


def test_duplicate_email_rejected(client: TestClient, register_user):
    account = register_user(role="job_seeker")
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Another Name",
            "email": account["email"],
            "password": "Password123!",
            "role": "job_seeker",
        },
    )
    assert response.status_code == 409


def test_role_protection(client: TestClient, register_user, auth_headers):
    seeker = register_user(role="job_seeker")
    employer = register_user(role="employer", company_name="Acme")

    assert client.get("/seeker/profile").status_code == 401
    assert client.get("/seeker/profile", headers=auth_headers(employer)).status_code == 403
    assert client.get("/employer/jobs", headers=auth_headers(seeker)).status_code == 403
    assert client.get("/seeker/profile", headers=auth_headers(seeker)).status_code == 200
    assert client.get("/employer/jobs", headers=auth_headers(employer)).status_code == 200
