from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def ensure_user_email_verification_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    dialect = engine.dialect.name
    with engine.begin() as connection:
        if "email_verified" not in existing_columns:
            default = "FALSE" if dialect == "postgresql" else "0"
            connection.execute(
                text(f"ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT {default}")
            )
        if "email_verified_at" not in existing_columns:
            timestamp_type = "TIMESTAMP WITH TIME ZONE" if dialect == "postgresql" else "DATETIME"
            connection.execute(
                text(f"ALTER TABLE users ADD COLUMN email_verified_at {timestamp_type}")
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
