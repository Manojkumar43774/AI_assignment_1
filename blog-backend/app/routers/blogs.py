from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user, get_current_user_optional
from ..database import get_db
from ..models import Blog, Comment, Like, User
from ..moderation import contains_blocked_language
from ..schemas import (
    BlogCreate,
    BlogOut,
    BlogUpdate,
    CommentCreate,
    CommentOut,
    LikeOut,
)

router = APIRouter(prefix="/api/blogs", tags=["blogs"])

MAX_COMMENT_VIOLATIONS = 3


def _ban_user(db: Session, user: User) -> None:
    for blog in db.query(Blog).filter(Blog.author_id == user.id).all():
        db.delete(blog)
    db.query(Like).filter(Like.user_id == user.id).delete()
    db.query(Comment).filter(Comment.user_id == user.id).delete()
    db.delete(user)


def serialize_blog(blog: Blog, current_user: User | None = None) -> dict:
    liked_by_me = False
    if current_user is not None:
        liked_by_me = any(like.user_id == current_user.id for like in blog.likes)
    return {
        "id": blog.id,
        "title": blog.title,
        "content": blog.content,
        "author_id": blog.author_id,
        "author_username": blog.author.username,
        "author_avatar_url": blog.author.avatar_url,
        "created_at": blog.created_at,
        "updated_at": blog.updated_at,
        "like_count": len(blog.likes),
        "comment_count": len(blog.comments),
        "liked_by_me": liked_by_me,
        "is_draft": blog.is_draft,
    }


def serialize_comment(comment: Comment) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "user_id": comment.user_id,
        "username": comment.user.username,
        "avatar_url": comment.user.avatar_url,
        "blog_id": comment.blog_id,
        "created_at": comment.created_at,
    }


def _load_blog(db: Session, blog_id: int) -> Blog:
    blog = (
        db.query(Blog)
        .options(
            joinedload(Blog.author),
            joinedload(Blog.likes),
            joinedload(Blog.comments).joinedload(Comment.user),
        )
        .filter(Blog.id == blog_id)
        .first()
    )
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog


def _require_owner(blog: Blog, user: User) -> None:
    if blog.author_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own blogs")


def _require_visible(blog: Blog, current_user: User | None) -> None:
    if blog.is_draft and (current_user is None or current_user.id != blog.author_id):
        raise HTTPException(status_code=404, detail="Blog not found")


@router.get("", response_model=list[BlogOut])
def list_blogs(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    blogs = (
        db.query(Blog)
        .options(
            joinedload(Blog.author),
            joinedload(Blog.likes),
            joinedload(Blog.comments),
        )
        .filter(Blog.is_draft == False)
        .order_by(Blog.created_at.desc())
        .all()
    )
    return [serialize_blog(b, current_user) for b in blogs]


@router.get("/mine", response_model=list[BlogOut])
def list_my_blogs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blogs = (
        db.query(Blog)
        .options(
            joinedload(Blog.author),
            joinedload(Blog.likes),
            joinedload(Blog.comments),
        )
        .filter(Blog.author_id == current_user.id)
        .order_by(Blog.created_at.desc())
        .all()
    )
    return [serialize_blog(b, current_user) for b in blogs]


@router.get("/{blog_id}", response_model=BlogOut)
def get_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    blog = _load_blog(db, blog_id)
    _require_visible(blog, current_user)
    return serialize_blog(blog, current_user)


@router.post("", response_model=BlogOut, status_code=status.HTTP_201_CREATED)
def create_blog(
    payload: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = Blog(
        title=payload.title,
        content=payload.content,
        author_id=current_user.id,
        is_draft=payload.is_draft,
    )
    db.add(blog)
    db.commit()
    return serialize_blog(_load_blog(db, blog.id), current_user)


@router.put("/{blog_id}", response_model=BlogOut)
def update_blog(
    blog_id: int,
    payload: BlogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = _load_blog(db, blog_id)
    _require_owner(blog, current_user)
    blog.title = payload.title
    blog.content = payload.content
    if payload.is_draft is not None:
        blog.is_draft = payload.is_draft
    db.commit()
    return serialize_blog(_load_blog(db, blog_id), current_user)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = _load_blog(db, blog_id)
    _require_owner(blog, current_user)
    db.delete(blog)
    db.commit()
    return None


@router.post("/{blog_id}/like", response_model=LikeOut)
def toggle_like(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = _load_blog(db, blog_id)
    _require_visible(blog, current_user)
    existing = (
        db.query(Like)
        .filter(Like.blog_id == blog.id, Like.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        liked = False
    else:
        db.add(Like(user_id=current_user.id, blog_id=blog.id))
        db.commit()
        liked = True

    like_count = db.query(Like).filter(Like.blog_id == blog.id).count()
    return {"liked": liked, "like_count": like_count}


@router.get("/{blog_id}/comments", response_model=list[CommentOut])
def list_comments(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    blog = _load_blog(db, blog_id)
    _require_visible(blog, current_user)
    comments = (
        db.query(Comment)
        .options(joinedload(Comment.user))
        .filter(Comment.blog_id == blog_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return [serialize_comment(c) for c in comments]


@router.post(
    "/{blog_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    blog_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = _load_blog(db, blog_id)
    _require_visible(blog, current_user)

    if contains_blocked_language(payload.content):
        current_user.violation_count += 1
        if current_user.violation_count >= MAX_COMMENT_VIOLATIONS:
            _ban_user(db, current_user)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "account_banned",
                    "message": "Your account has been permanently banned for repeated abusive comments.",
                },
            )
        db.commit()
        remaining = MAX_COMMENT_VIOLATIONS - current_user.violation_count
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Comments can't contain abusive language. "
                f"{remaining} more attempt(s) and your account will be banned."
            ),
        )

    comment = Comment(
        content=payload.content.strip(),
        user_id=current_user.id,
        blog_id=blog_id,
    )
    db.add(comment)
    db.commit()
    comment = (
        db.query(Comment)
        .options(joinedload(Comment.user))
        .filter(Comment.id == comment.id)
        .first()
    )
    return serialize_comment(comment)


@router.delete("/{blog_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    blog_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = _load_blog(db, blog_id)
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.blog_id == blog_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and blog.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this comment")
    db.delete(comment)
    db.commit()
    return None
