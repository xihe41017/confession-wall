"""公共依赖与请求工具：IP/设备识别、当前用户解析、角色权限校验。"""
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BannedIP, User
from app.permissions import has_perm
from app.security import decode_token


def get_ip(request: Request) -> str:
    """优先取 X-Forwarded-For（部署在 Nginx 等反向代理后）。"""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_device_id(request: Request) -> Optional[str]:
    """客户端设备标识（前端 localStorage 生成的 uuid）。"""
    did = request.headers.get("x-device-id")
    return did.strip() if did and did.strip() else None


def check_ip_allowed(db: Session, ip: str):
    if db.query(BannedIP).filter_by(ip=ip).first():
        raise HTTPException(status_code=403, detail="该 IP 已被拉黑")


def get_payload(db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    payload = decode_token(db, authorization.split(" ", 1)[1].strip())
    return payload


def optional_user(
    db: Session = Depends(get_db),
    payload: Optional[dict] = Depends(get_payload),
) -> Optional[User]:
    """解析当前登录用户（未登录返回 None，不报错）。"""
    if not payload:
        return None
    user = db.get(User, payload.get("uid"))
    if not user or user.status != "active":
        return None
    return user


def require_active_user(
    user: Optional[User] = Depends(optional_user),
) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def require_admin(
    user: Optional[User] = Depends(optional_user),
) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def require_super_admin(
    user: Optional[User] = Depends(optional_user),
) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return user


def require_perm(key: str):
    """按权限键校验（超管恒有全部权限）。"""
    def dep(user: Optional[User] = Depends(optional_user)) -> User:
        if not user:
            raise HTTPException(status_code=401, detail="请先登录")
        if not has_perm(user, key):
            raise HTTPException(status_code=403, detail="没有该操作权限")
        return user
    return dep
