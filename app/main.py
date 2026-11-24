import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, SessionLocal, engine, ensure_user_email_verification_columns
from .routers import auth, courses, employer, seeker
from .services.course_advisor import ensure_course_index
from .services.embeddings import embedder
from .services.vector_store import course_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_user_email_verification_columns()
    db = SessionLocal()
    try:
        ensure_course_index(db)
    except Exception as exc:
        logger.warning("Course index warm-up skipped: %s", exc)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered recruitment matching with CV analysis, hybrid job matching "
        "and retrieval-augmented course advice."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(seeker.router)
app.include_router(employer.router)
app.include_router(courses.router)


@app.get("/", tags=["System"])
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "status": "ok"}


@app.get("/health", tags=["System"])
def health() -> dict:
    return {
        "status": "ok",
        "environment": settings.environment,
        "ai_configured": bool(settings.anthropic_api_key.strip()),
        "embedding_model": settings.embedding_model,
        "embedding_backend": embedder.backend,
        "vector_store": course_store.backend,
    }
