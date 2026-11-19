import io
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEMP_ROOT = Path(tempfile.mkdtemp(prefix="talentmatch-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEMP_ROOT / 'test.db').as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["UPLOAD_DIR"] = str(TEMP_ROOT / "uploads")
os.environ["CHROMA_DIR"] = str(TEMP_ROOT / "chroma")
os.environ["EMBEDDING_BACKEND"] = "hashing"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def register_user(client):
    def _register(role="job_seeker", full_name="Test User", **overrides):
        email = f"{role}-{uuid.uuid4().hex[:10]}@test.dev"
        payload = {
            "full_name": full_name,
            "email": email,
            "password": "Password123!",
            "role": role,
        }
        payload.update(overrides)
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 201, response.text
        return {**response.json(), "email": email, "password": "Password123!"}

    return _register


@pytest.fixture()
def auth_headers():
    def _headers(account):
        return {"Authorization": f"Bearer {account['access_token']}"}

    return _headers


@pytest.fixture()
def make_docx():
    def _make_docx(text: str) -> bytes:
        from docx import Document

        document = Document()
        for line in text.split("\n"):
            document.add_paragraph(line)
        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    return _make_docx
