from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from .database import Base, engine
from .paths import AVATAR_DIR, UPLOAD_ROOT
from .routers import auth, blogs, users

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
AVATAR_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_schema() -> None:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "users" in tables:
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "oauth_provider" not in columns:
            Base.metadata.drop_all(bind=engine)
            tables = []

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "blogs" in inspector.get_table_names():
        blog_cols = {col["name"] for col in inspector.get_columns("blogs")}
        with engine.begin() as conn:
            if "updated_at" not in blog_cols:
                conn.execute(text("ALTER TABLE blogs ADD COLUMN updated_at DATETIME"))
            if "is_draft" not in blog_cols:
                conn.execute(text("ALTER TABLE blogs ADD COLUMN is_draft BOOLEAN DEFAULT 0"))

    if "users" in inspector.get_table_names():
        user_cols = {col["name"] for col in inspector.get_columns("users")}
        with engine.begin() as conn:
            if "bio" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
            if "avatar_url" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255)"))
            if "first_name" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(80)"))
            if "last_name" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(80)"))
            if "password_hash" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            if "violation_count" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN violation_count INTEGER DEFAULT 0"))

    if "pending_signups" in inspector.get_table_names():
        pending_cols = {col["name"] for col in inspector.get_columns("pending_signups")}
        with engine.begin() as conn:
            if "username" not in pending_cols:
                conn.execute(text("ALTER TABLE pending_signups ADD COLUMN username VARCHAR(40) DEFAULT ''"))


_ensure_schema()

app = FastAPI(title="Blog API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(blogs.router)
app.include_router(users.router)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
