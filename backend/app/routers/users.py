from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_perm
from app.models import BannedIP, User
from app.permissions import ADMIN_DEFAULT_PERMS, effective_perms, set_perms
from app.schemas import (
    BanIPIn,
    PaginatedUsers,
    PasswordUpdate,
    PermissionsUpdate,
    RoleUpdate,
    TitleUpdate,
    UserAdminOut,
    UserStatusUpdate,
)
from app.security import hash_password

router = APIRouter(prefix="/api/admin/users", tags=["users"])


def _out(u: User) -> UserAdminOut:
    return UserAdminOut(
        id=u.id, username=u.username, nickname=u.nickname, class_name=u.class_name,
        school=u.school, email=u.email, phone=u.phone, role=u.role,
        title=u.title, status=u.status,
        created_at=u.created_at, register_ip=u.register_ip,
        register_device=u.register_device, register_browser=u.register_browser,
        last_login_at=u.last_login_at,
        permissions=sorted(effective_perms(u)),
    )


def _get_user(db: Session, user_id: int) -> User:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    return u


@router.get("", response_model=PaginatedUsers)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = Query(None, pattern="^(active|pending|banned)$"),
    _: User = Depends(require_perm("users.manage")),
    db: Session = Depends(get_db),
):
    where = [True]
    if status:
        where.append(User.status == status)
    if search:
        kw = f"%{search.strip()}%"
        where.append(or_(User.username.like(kw), User.nickname.like(kw), User.school.like(kw)))

    total = db.scalar(select(func.count(User.id)).where(*where)) or 0
    pages = max(1, (total + page_size - 1) // page_size)
    users = (
        db.query(User)
        .where(*where)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedUsers(
        items=[_out(u) for u in users], total=total,
        page=page, page_size=page_size, pages=pages,
    )


@router.post("/{user_id}/role", response_model=UserAdminOut)
def set_role(
    user_id: int, payload: RoleUpdate,
    admin: User = Depends(require_perm("users.manage")), db: Session = Depends(get_db),
):
    u = _get_user(db, user_id)
    if u.id == admin.id and payload.role != "super_admin":
        raise HTTPException(status_code=400, detail="不能降低自己的权限")
    u.role = payload.role
    if payload.role == "admin":
        # 提升为管理员时授予默认权限（超管可再单独调整）
        set_perms(u, ADMIN_DEFAULT_PERMS)
    elif payload.role == "user":
        set_perms(u, [])
    db.commit()
    db.refresh(u)
    return _out(u)


@router.post("/{user_id}/permissions", response_model=UserAdminOut)
def set_user_permissions(
    user_id: int, payload: PermissionsUpdate,
    admin: User = Depends(require_perm("users.manage")), db: Session = Depends(get_db),
):
    """单独修改某个用户的权限（详细到每个设置项）。"""
    u = _get_user(db, user_id)
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的权限")
    set_perms(u, payload.permissions)
    db.commit()
    db.refresh(u)
    return _out(u)


@router.post("/{user_id}/title", response_model=UserAdminOut)
def set_title(
    user_id: int, payload: TitleUpdate,
    _: User = Depends(require_perm("users.manage")), db: Session = Depends(get_db),
):
    u = _get_user(db, user_id)
    u.title = payload.title or None
    db.commit()
    db.refresh(u)
    return _out(u)


@router.post("/{user_id}/status", response_model=UserAdminOut)
def set_status(
    user_id: int, payload: UserStatusUpdate,
    admin: User = Depends(require_perm("users.manage")), db: Session = Depends(get_db),
):
    u = _get_user(db, user_id)
    if u.id == admin.id and payload.status != "active":
        raise HTTPException(status_code=400, detail="不能拉黑或冻结自己")
    u.status = payload.status
    db.commit()
    db.refresh(u)
    return _out(u)


@router.post("/{user_id}/password", response_model=UserAdminOut)
def reset_password(
    user_id: int, payload: PasswordUpdate,
    _: User = Depends(require_perm("users.manage")), db: Session = Depends(get_db),
):
    u = _get_user(db, user_id)
    u.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(u)
    return _out(u)


# ---------- IP 黑名单（IP黑名单标签页，ban.manage 权限） ----------
@router.get("/banned-ips", response_model=list)
def list_banned_ips(_: User = Depends(require_perm("ban.manage")), db: Session = Depends(get_db)):
    return [
        {"ip": b.ip, "reason": b.reason, "created_at": b.created_at}
        for b in db.query(BannedIP).order_by(BannedIP.created_at.desc()).all()
    ]


@router.post("/banned-ips", status_code=201)
def ban_ip(
    payload: BanIPIn, _: User = Depends(require_perm("content.ban_ip")), db: Session = Depends(get_db),
):
    ip = payload.ip.strip()
    if not ip:
        raise HTTPException(status_code=400, detail="IP 不能为空")
    if db.query(BannedIP).filter_by(ip=ip).first():
        raise HTTPException(status_code=400, detail="该 IP 已在黑名单")
    db.add(BannedIP(ip=ip, reason=payload.reason))
    db.commit()
    return {"ok": True, "ip": ip}


@router.delete("/banned-ips/{ip}", status_code=204)
def unban_ip(ip: str, _: User = Depends(require_perm("ban.manage")), db: Session = Depends(get_db)):
    b = db.query(BannedIP).filter_by(ip=ip).first()
    if not b:
        raise HTTPException(status_code=404, detail="该 IP 不在黑名单")
    db.delete(b)
    db.commit()
