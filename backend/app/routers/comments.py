from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import check_ip_allowed, get_ip, optional_user
from app.models import Comment, CommentLike, Post, User
from app.ratelimit import dyn, limiter
from app.schemas import CommentCreate, CommentOut

router = APIRouter(prefix="/api/posts/{post_id}/comments", tags=["comments"])


def _get_approved_post(post_id: int, db: Session) -> Post:
    post = db.get(Post, post_id)
    if not post or post.status != "approved":
        raise HTTPException(status_code=404, detail="内容不存在")
    return post


def _to_out(c: Comment, liked: bool = False) -> CommentOut:
    return CommentOut(
        id=c.id, post_id=c.post_id, nickname=c.nickname, content=c.content,
        likes=c.likes, liked=liked, created_at=c.created_at,
    )


@router.get("", response_model=List[CommentOut])
def list_comments(post_id: int, request: Request, db: Session = Depends(get_db)):
    _get_approved_post(post_id, db)
    comments = (
        db.query(Comment)
        .filter_by(post_id=post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    ip = get_ip(request)
    liked_ids = {
        r[0]
        for r in db.query(CommentLike.comment_id)
        .filter(CommentLike.comment_id.in_([c.id for c in comments] or [0]), CommentLike.ip == ip)
        .all()
    }
    return [_to_out(c, liked=(c.id in liked_ids)) for c in comments]


@router.post("", response_model=CommentOut, status_code=201)
@limiter.limit(dyn("rate_comment", "30/minute"))
def add_comment(
    request: Request,
    post_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    _get_approved_post(post_id, db)
    ip = get_ip(request)
    check_ip_allowed(db, ip)
    nickname = (payload.nickname or "").strip()
    if not nickname:
        nickname = (user.nickname if user else "") or "匿名同学"
    comment = Comment(
        post_id=post_id,
        user_id=user.id if user else None,
        content=payload.content,
        nickname=nickname,
        ip=ip,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _to_out(comment)


@router.post("/{comment_id}/like")
@limiter.limit(dyn("rate_like", "60/minute"))
def like_comment(request: Request, post_id: int, comment_id: int, db: Session = Depends(get_db)):
    _get_approved_post(post_id, db)
    comment = db.get(Comment, comment_id)
    if not comment or comment.post_id != post_id:
        raise HTTPException(status_code=404, detail="评论不存在")
    ip = get_ip(request)
    if db.query(CommentLike).filter_by(comment_id=comment_id, ip=ip).first():
        raise HTTPException(status_code=400, detail="你已经为这条评论点过赞啦 ❤")
    db.add(CommentLike(comment_id=comment_id, ip=ip))
    comment.likes += 1
    db.commit()
    return {"likes": comment.likes}
