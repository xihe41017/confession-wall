import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import check_ip_allowed, get_device_id, get_ip, optional_user
from app.models import Comment, Post, PostLike, User
from app.ratelimit import dyn, limiter
from app.schemas import AuthorInfo, PaginatedPosts, PostCreate, PostOut
from app.settings_service import service as settings_service

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _comment_count_subquery():
    return select(func.count(Comment.id)).where(Comment.post_id == Post.id).scalar_subquery()


def _author_info(user: User | None) -> AuthorInfo | None:
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


def _to_post_out(post: Post, comment_count: int, liked: bool = False) -> PostOut:
    anonymous = bool(post.is_anonymous)
    return PostOut(
        id=post.id,
        to_name=post.to_name,
        nickname=post.nickname,
        content=post.content,
        theme=post.theme,
        likes=post.likes,
        comment_count=comment_count,
        liked=liked,
        pinned=bool(post.pinned),
        is_anonymous=anonymous,
        images=_parse_images(post),
        video=post.video,
        # 匿名发布不显示作者信息与头衔（user_id 保留供管理员追溯）
        author=None if anonymous else _author_info(post.author),
        created_at=post.created_at,
    )


@router.get("", response_model=PaginatedPosts)
def list_posts(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    sort: str = Query("latest", pattern="^(latest|hot)$"),
    db: Session = Depends(get_db),
):
    stmt = select(Post, _comment_count_subquery().label("comment_count")).where(
        Post.status == "approved"
    )
    # 置顶内容永远排最前
    if sort == "hot":
        stmt = stmt.order_by(Post.pinned.desc(), Post.likes.desc(), Post.created_at.desc())
    else:
        stmt = stmt.order_by(Post.pinned.desc(), Post.created_at.desc())

    total = db.scalar(select(func.count(Post.id)).where(Post.status == "approved")) or 0
    pages = max(1, (total + page_size - 1) // page_size)
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()

    ip = get_ip(request)
    ids = [p.id for p, _ in rows]
    liked_ids = {
        r[0]
        for r in db.query(PostLike.post_id)
        .filter(PostLike.post_id.in_(ids), PostLike.ip == ip)
        .all()
    } if ids else set()

    items = [_to_post_out(p, cc, liked=(p.id in liked_ids)) for p, cc in rows]
    return PaginatedPosts(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.status != "approved":
        raise HTTPException(status_code=404, detail="内容不存在")
    ip = get_ip(request)
    liked = db.query(PostLike.post_id).filter_by(post_id=post_id, ip=ip).first() is not None
    count = db.scalar(select(func.count(Comment.id)).where(Comment.post_id == post_id)) or 0
    return _to_post_out(post, count, liked)


@router.post("", response_model=PostOut, status_code=201)
@limiter.limit(dyn("rate_post", "20/minute"))
def create_post(
    request: Request,
    payload: PostCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    ip = get_ip(request)
    check_ip_allowed(db, ip)
    device_id = get_device_id(request)

    # 匿名媒体限制：未登录只能发 1 张图片，不能发视频
    if not user:
        if len(payload.images) > 1:
            raise HTTPException(status_code=403, detail="未登录只能发 1 张图片，登录后可发 9 张")
        if payload.video:
            raise HTTPException(status_code=403, detail="登录后才能发布视频")

    # 匿名限发：未登录用户单个 IP / 设备 24 小时内限发
    if not user:
        limit = settings_service.get_int(db, "anonymous_post_limit", 3)
        if limit > 0:
            since = datetime.now() - timedelta(hours=24)
            ip_count = (
                db.query(func.count(Post.id))
                .filter(Post.user_id.is_(None), Post.ip == ip, Post.created_at >= since)
                .scalar()
                or 0
            )
            if ip_count >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"未登录用户每 IP 24 小时内限发 {limit} 条，登录后不限。",
                )
            if device_id:
                dev_count = (
                    db.query(func.count(Post.id))
                    .filter(Post.user_id.is_(None), Post.device_id == device_id, Post.created_at >= since)
                    .scalar()
                    or 0
                )
                if dev_count >= limit:
                    raise HTTPException(
                        status_code=429,
                        detail=f"未登录用户每设备 24 小时内限发 {limit} 条，登录后不限。",
                    )

    anonymous = bool(payload.anonymous)
    nickname = (payload.nickname or "").strip()
    if anonymous or not nickname:
        # 匿名发布 → 一律显示为匿名同学；未填昵称时取用户昵称或匿名
        nickname = "匿名同学" if anonymous else ((user.nickname if user else "") or "匿名同学")

    post = Post(
        user_id=user.id if user else None,   # 匿名时仍保留 user_id 供管理员追溯
        content=payload.content,
        to_name=payload.to_name or None,
        nickname=nickname,
        theme=payload.theme or "pink",
        is_anonymous=1 if anonymous else 0,
        images=json.dumps(payload.images or [], ensure_ascii=False) if payload.images else None,
        video=payload.video or None,
        ip=ip,
        device_id=device_id,
        status="pending" if settings_service.get_bool(db, "moderation_mode", False) else "approved",
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _to_post_out(post, 0)


@router.post("/{post_id}/like")
@limiter.limit(dyn("rate_like", "60/minute"))
def like_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.status != "approved":
        raise HTTPException(status_code=404, detail="内容不存在")
    ip = get_ip(request)
    if db.query(PostLike).filter_by(post_id=post_id, ip=ip).first():
        raise HTTPException(status_code=400, detail="你已经为这条内容点过赞啦 ❤")
    db.add(PostLike(post_id=post_id, ip=ip))
    post.likes += 1
    db.commit()
    return {"likes": post.likes}
