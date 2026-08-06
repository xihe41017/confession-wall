import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_perm
from app.models import Comment, Post, User
from app.schemas import (
    AdminStats,
    AuthorInfo,
    CommentAdminOut,
    CommentEditIn,
    PaginatedAdminPosts,
    PinUpdate,
    PostAdminOut,
    PostEditIn,
    StatusUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _comment_count_subquery():
    return select(func.count(Comment.id)).where(Comment.post_id == Post.id).scalar_subquery()


def _author_info(user) -> AuthorInfo | None:
    if not user:
        return None
    if user.role == "super_admin":
        title = "超级管理员"
    elif user.role == "admin":
        title = "管理员"
    else:
        title = user.title
    return AuthorInfo(role=user.role, title=title)


def _parse_images(post: Post) -> list:
    if not post.images:
        return []
    try:
        data = json.loads(post.images)
        return data if isinstance(data, list) else []
    except (TypeError, ValueError):
        return []


def _to_post_out(post: Post, comment_count: int) -> PostAdminOut:
    return PostAdminOut(
        id=post.id,
        to_name=post.to_name,
        nickname=post.nickname,
        content=post.content,
        theme=post.theme,
        likes=post.likes,
        comment_count=comment_count,
        status=post.status,
        pinned=bool(post.pinned),
        is_anonymous=bool(post.is_anonymous),
        images=_parse_images(post),
        video=post.video,
        # 管理后台始终展示真实作者（匿名内容也供管理员追溯）
        author=_author_info(post.author) if post.author else None,
        author_username=post.author.username if post.author else None,
        ip=post.ip,
        created_at=post.created_at,
    )


@router.get("/posts", response_model=PaginatedAdminPosts)
def admin_list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
    _: User = Depends(require_perm("content.manage")),
    db: Session = Depends(get_db),
):
    where = [True]
    if status:
        where = [Post.status == status]

    total = db.scalar(select(func.count(Post.id)).where(*where)) or 0
    pages = max(1, (total + page_size - 1) // page_size)

    stmt = (
        select(Post, _comment_count_subquery().label("comment_count"))
        .where(*where)
        .order_by(Post.pinned.desc(), Post.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(stmt).all()
    items = [_to_post_out(p, cc) for p, cc in rows]
    return PaginatedAdminPosts(
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )


@router.post("/posts/{post_id}/status", response_model=PostAdminOut)
def update_status(
    post_id: int,
    payload: StatusUpdate,
    _: User = Depends(require_perm("content.manage")),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="内容不存在")
    post.status = payload.status
    db.commit()
    db.refresh(post)
    count = db.scalar(select(func.count(Comment.id)).where(Comment.post_id == post.id)) or 0
    return _to_post_out(post, count)


@router.post("/posts/{post_id}/pin", response_model=PostAdminOut)
def pin_post(
    post_id: int,
    payload: PinUpdate,
    _: User = Depends(require_perm("content.pin")),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="内容不存在")
    post.pinned = 1 if payload.pinned else 0
    db.commit()
    db.refresh(post)
    count = db.scalar(select(func.count(Comment.id)).where(Comment.post_id == post.id)) or 0
    return _to_post_out(post, count)


@router.post("/posts/{post_id}/edit", response_model=PostAdminOut)
def edit_post(
    post_id: int,
    payload: PostEditIn,
    _: User = Depends(require_perm("content.edit")),
    db: Session = Depends(get_db),
):
    """修改内容的点赞数 / 对象 / 昵称。"""
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="内容不存在")
    if payload.likes is not None:
        post.likes = payload.likes
    if payload.to_name is not None:
        post.to_name = payload.to_name or None
    if payload.nickname is not None:
        post.nickname = payload.nickname or None
    db.commit()
    db.refresh(post)
    count = db.scalar(select(func.count(Comment.id)).where(Comment.post_id == post.id)) or 0
    return _to_post_out(post, count)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, _: User = Depends(require_perm("content.manage")), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="内容不存在")
    db.delete(post)
    db.commit()


@router.get("/comments", response_model=List[CommentAdminOut])
def admin_list_comments(
    post_id: int = Query(...),
    _: User = Depends(require_perm("content.manage")),
    db: Session = Depends(get_db),
):
    return (
        db.query(Comment)
        .filter_by(post_id=post_id)
        .order_by(Comment.created_at.desc())
        .limit(200)
        .all()
    )


@router.post("/comments/{comment_id}/edit", response_model=CommentAdminOut)
def edit_comment(
    comment_id: int,
    payload: CommentEditIn,
    _: User = Depends(require_perm("comment.edit")),
    db: Session = Depends(get_db),
):
    """修改评论的点赞数。"""
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    if payload.likes is not None:
        comment.likes = payload.likes
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, _: User = Depends(require_perm("content.manage")), db: Session = Depends(get_db)):
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    db.delete(comment)
    db.commit()


@router.get("/stats", response_model=AdminStats)
def admin_stats(_: User = Depends(require_perm("content.manage")), db: Session = Depends(get_db)):
    return AdminStats(
        total_posts=db.scalar(select(func.count(Post.id))) or 0,
        pending_posts=(
            db.scalar(select(func.count(Post.id)).where(Post.status == "pending")) or 0
        ),
        total_comments=db.scalar(select(func.count(Comment.id))) or 0,
        total_likes=db.scalar(select(func.coalesce(func.sum(Post.likes), 0))) or 0,
        total_users=db.scalar(select(func.count(User.id))) or 0,
        banned_users=(
            db.scalar(select(func.count(User.id)).where(User.status == "banned")) or 0
        ),
    )
