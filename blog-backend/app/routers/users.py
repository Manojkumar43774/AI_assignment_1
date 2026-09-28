from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user, hash_secret, verify_secret
from ..database import get_db
from ..models import Blog, User
from ..paths import AVATAR_DIR, UPLOAD_ROOT
from ..schemas import ChangePasswordRequest, MessageOut, PublicUserOut, UserOut, UserProfileUpdate

router = APIRouter(prefix="/api/users", tags=["users"])

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


def serialize_public_user(user: User, blog_count: int) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "blog_count": blog_count,
        "created_at": user.created_at,
    }


@router.patch("/me", response_model=UserOut)
def update_my_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.bio is not None:
        current_user.bio = payload.bio.strip() or None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password", response_model=MessageOut)
def change_my_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    had_password = bool(current_user.password_hash)
    if had_password:
        if not payload.old_password or not verify_secret(payload.old_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect current password")

    current_user.password_hash = hash_secret(payload.new_password)
    db.commit()
    return {"message": "Password changed" if had_password else "Password set"}


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, detail="Avatar must be a JPEG, PNG, or WebP image"
        )

    data = await file.read()
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="Avatar must be under 2MB")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"

    if current_user.avatar_url and current_user.avatar_url.startswith("/uploads/avatars/"):
        old = UPLOAD_ROOT.parent / current_user.avatar_url.lstrip("/")
        if old.exists() and old.is_file():
            old.unlink(missing_ok=True)

    (AVATAR_DIR / filename).write_bytes(data)
    current_user.avatar_url = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{username}", response_model=PublicUserOut)
def get_public_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    blog_count = (
        db.query(Blog)
        .filter(Blog.author_id == user.id, Blog.is_draft == False)
        .count()
    )
    return serialize_public_user(user, blog_count)


@router.get("/{username}/blogs")
def get_user_blogs(username: str, db: Session = Depends(get_db)):
    from ..routers.blogs import serialize_blog

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    blogs = (
        db.query(Blog)
        .options(
            joinedload(Blog.author),
            joinedload(Blog.likes),
            joinedload(Blog.comments),
        )
        .filter(Blog.author_id == user.id, Blog.is_draft == False)
        .order_by(Blog.created_at.desc())
        .all()
    )
    return [serialize_blog(b) for b in blogs]
