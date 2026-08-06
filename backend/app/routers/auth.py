from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import check_ip_allowed, get_device_id, get_ip, require_active_user
from app.models import User
from app.permissions import effective_perms
from app.ratelimit import dyn, limiter
from app.schemas import ChangePasswordIn, LoginIn, RegisterIn, Token, UserOut
from app.security import create_token, hash_password, verify_password
from app.settings_service import service as settings_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id, username=u.username, nickname=u.nickname, class_name=u.class_name,
        school=u.school, email=u.email, phone=u.phone, role=u.role,
        title=u.title, status=u.status,
        permissions=sorted(effective_perms(u)), created_at=u.created_at,
    )


@router.post("/register", response_model=Token, status_code=201)
@limiter.limit(dyn("rate_register", "20/minute"))
def register(request: Request, payload: RegisterIn, db: Session = Depends(get_db)):
    if not settings_service.get_bool(db, "allow_register", True):
        raise HTTPException(status_code=403, detail="注册通道已关闭")
    ip = get_ip(request)
    check_ip_allowed(db, ip)

    username = payload.username.strip().lower()
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="该用户名已被占用")

    ua = request.headers.get("user-agent", "") or ""
    status = "pending" if settings_service.get_bool(db, "register_approval", False) else "active"
    user = User(
        username=username,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname.strip(),
        class_name=(payload.class_name or "").strip() or None,
        school=(payload.school or "").strip() or None,
        email=payload.email,
        phone=payload.phone,
        status=status,
        register_ip=ip,
        register_device=get_device_id(request),
        register_browser=ua[:200],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(db, user.id, user.role, user.username)
    return Token(token=token, user=_user_out(user))


@router.post("/login", response_model=Token)
@limiter.limit(dyn("rate_login", "30/minute"))
def login(request: Request, payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=payload.username.strip().lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if user.status == "banned":
        raise HTTPException(status_code=403, detail="该账号已被拉黑")
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="账号待管理员激活，请稍后再试")
    user.last_login_at = datetime.now()
    db.commit()
    token = create_token(db, user.id, user.role, user.username)
    return Token(token=token, user=_user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(require_active_user)):
    return _user_out(user)


@router.post("/password")
@limiter.limit(dyn("rate_login", "30/minute"))
def change_own_password(
    request: Request,
    payload: ChangePasswordIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_active_user),
):
    """登录用户修改自己的密码。"""
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}
