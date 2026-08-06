import re
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def _force_utc(v: datetime) -> datetime:
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v


# ---------- 墙内容 ----------
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    to_name: Optional[str] = Field(None, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, max_length=30)
    anonymous: bool = False   # 已登录用户选择匿名发布时置 true
    images: List[str] = Field(default_factory=list, max_length=9)  # 最多 9 张
    video: Optional[str] = None

    @field_validator("images")
    @classmethod
    def _check_images(cls, v):
        if not v:
            return []
        for url in v:
            if not url.startswith("/uploads/images/"):
                raise ValueError("图片地址不合法")
        return v[:9]

    @field_validator("video")
    @classmethod
    def _check_video(cls, v):
        if v and not v.startswith("/uploads/videos/"):
            raise ValueError("视频地址不合法")
        return v

    @field_validator("content")
    @classmethod
    def _strip_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("内容不能为空")
        return v


class AuthorInfo(BaseModel):
    role: str = "user"
    title: Optional[str] = None   # 头衔（管理员/超管自动头衔，或超管下发的自定义头衔）


class PostOut(BaseModel):
    id: int
    to_name: Optional[str] = None
    nickname: Optional[str] = None
    content: str
    theme: Optional[str] = "pink"
    likes: int
    comment_count: int = 0
    liked: bool = False
    pinned: bool = False
    is_anonymous: bool = False
    images: List[str] = []
    video: Optional[str] = None
    author: Optional[AuthorInfo] = None
    created_at: datetime
    _utc = field_validator("created_at")(classmethod(lambda cls, v: _force_utc(v)))


class PostAdminOut(PostOut):
    status: str
    ip: Optional[str] = None
    author_username: Optional[str] = None  # 真实发布者用户名（匿名内容供管理员追溯）


class PaginatedPosts(BaseModel):
    items: List[PostOut]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedAdminPosts(BaseModel):
    items: List[PostAdminOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------- 评论 ----------
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=200)
    nickname: Optional[str] = Field(None, max_length=50)

    @field_validator("content")
    @classmethod
    def _strip_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("评论不能为空")
        return v


class CommentOut(BaseModel):
    id: int
    post_id: int
    nickname: Optional[str]
    content: str
    likes: int = 0
    liked: bool = False
    created_at: datetime
    _utc = field_validator("created_at")(classmethod(lambda cls, v: _force_utc(v)))


class CommentAdminOut(CommentOut):
    ip: Optional[str] = None


# ---------- 账号 ----------
class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=64)
    nickname: str = Field(..., min_length=1, max_length=30)
    class_name: Optional[str] = Field(None, max_length=50)
    school: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)

    @field_validator("email")
    @classmethod
    def _check_email(cls, v):
        if v is not None and v.strip():
            v = v.strip()
            if not re.fullmatch(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", v):
                raise ValueError("邮箱格式不正确（应为 xxx@xx.xxx）")
            return v
        return None

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v):
        if v is not None and v.strip():
            v = v.strip()
            if not re.fullmatch(r"\d{11}", v):
                raise ValueError("电话号码应为 11 位数字")
            return v
        return None

    @model_validator(mode="after")
    def _contact_required(self):
        if not (self.email or self.phone):
            raise ValueError("邮箱和电话至少填写一项")
        return self


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    class_name: Optional[str]
    school: Optional[str]
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    title: Optional[str]
    status: str
    permissions: List[str] = []
    created_at: datetime
    _utc = field_validator("created_at")(classmethod(lambda cls, v: _force_utc(v)))


class UserAdminOut(UserOut):
    register_ip: Optional[str]
    register_device: Optional[str]
    register_browser: Optional[str]
    last_login_at: Optional[datetime]
    permissions: List[str] = []
    _utc2 = field_validator("last_login_at")(classmethod(lambda cls, v: _force_utc(v) if v else v))


class PaginatedUsers(BaseModel):
    items: List[UserAdminOut]
    total: int
    page: int
    page_size: int
    pages: int


class Token(BaseModel):
    token: str
    user: UserOut


# ---------- 管理 ----------
class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|approved|rejected)$")


class PinUpdate(BaseModel):
    pinned: bool


class PostEditIn(BaseModel):
    likes: Optional[int] = Field(None, ge=0)
    to_name: Optional[str] = Field(None, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)


class CommentEditIn(BaseModel):
    likes: Optional[int] = Field(None, ge=0)


class PermissionsUpdate(BaseModel):
    permissions: List[str] = []


class RoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(user|admin|super_admin)$")


class UserStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|pending|banned)$")


class TitleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=50)


class PasswordUpdate(BaseModel):
    password: str = Field(..., min_length=6, max_length=64)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=64)


class SettingOut(BaseModel):
    key: str
    value: str
    description: str = ""
    sensitive: bool = False   # 仅超管可改
    masked: bool = False      # 值需隐藏（如 JWT 密钥）


class SettingUpdate(BaseModel):
    value: str = Field(..., max_length=500)


class AutoUpdateIn(BaseModel):
    enabled: bool = False
    interval: int = Field(5, ge=1, le=1440)


class AutoUpdateOut(BaseModel):
    enabled: bool = False
    interval: int = 5
    script_exists: bool = False
    updating: bool = False
    last_result: str = ""
    last_run_at: Optional[float] = None


class BanIPIn(BaseModel):
    ip: str
    reason: Optional[str] = Field(None, max_length=200)


class AdminStats(BaseModel):
    total_posts: int
    pending_posts: int
    total_comments: int
    total_likes: int
    total_users: int
    banned_users: int


class SiteInfo(BaseModel):
    site_name: str
    site_announcement: str
    allow_register: bool
    register_approval: bool
    moderation_mode: bool
    anonymous_post_limit: int
    image_max_mb: int = 2
    video_max_mb: int = 15
