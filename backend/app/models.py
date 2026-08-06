from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """用户账号。role: super_admin(超级管理员) / admin(管理员) / user(普通用户)
    status: active(正常) / pending(待激活) / banned(已拉黑)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(128))
    nickname = Column(String(50), nullable=True)
    class_name = Column(String(50), nullable=True)   # 班级
    school = Column(String(100), nullable=True)       # 学校
    email = Column(String(100), nullable=True)        # 邮箱（注册时邮箱/电话至少填一项）
    phone = Column(String(30), nullable=True)         # 电话号码
    role = Column(String(20), default="user", index=True)
    title = Column(String(50), nullable=True)         # 超管下发的自定义头衔
    status = Column(String(20), default="active", index=True)
    permissions = Column(String(500), nullable=True)  # JSON 数组，额外授予的权限键（超管恒有全部权限）

    # 注册溯源信息
    register_ip = Column(String(45), nullable=True)
    register_device = Column(String(200), nullable=True)
    register_browser = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    last_login_at = Column(DateTime, nullable=True)


class Setting(Base):
    """运行时设置项（后台可修改）。sensitive=1 表示仅超级管理员可改。"""
    __tablename__ = "settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(500), default="")
    description = Column(String(200), default="")
    sensitive = Column(Integer, default=0)


class BannedIP(Base):
    """拉黑的 IP。被拉黑后无法发布/评论/注册。"""
    __tablename__ = "banned_ips"

    id = Column(Integer, primary_key=True)
    ip = Column(String(45), unique=True, index=True)
    reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Post(Base):
    """一条墙上的内容。status: pending(待审核) / approved(已上墙) / rejected(已驳回)"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    to_name = Column(String(50), nullable=True)          # 发布对象
    nickname = Column(String(50), nullable=True)          # 展示昵称
    content = Column(Text, nullable=False)                # 内容
    theme = Column(String(30), default="pink")            # 卡片配色
    likes = Column(Integer, default=0)
    status = Column(String(10), default="approved", index=True)
    pinned = Column(Integer, default=0, index=True)        # 1=管理员/超管置顶
    is_anonymous = Column(Integer, default=0)              # 1=匿名发布（不显示昵称与头衔，user_id 仍保留供管理员追溯）
    images = Column(String(1000), nullable=True)           # JSON 数组：/uploads/images/xxx.jpg
    video = Column(String(500), nullable=True)             # /uploads/videos/xxx.mp4（≤15秒）
    ip = Column(String(45), nullable=True, index=True)    # 发布 IP（匿名追踪/拉黑用）
    device_id = Column(String(100), nullable=True)        # 客户端设备标识（匿名限发用）
    created_at = Column(DateTime, default=datetime.now, index=True)

    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    author = relationship("User", foreign_keys=[user_id], lazy="joined")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    nickname = Column(String(50), default="匿名同学")
    content = Column(Text, nullable=False)
    ip = Column(String(45), nullable=True)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    post = relationship("Post", back_populates="comments")


class PostLike(Base):
    """记录每个 IP 对某条内容点过赞，防止重复刷赞。"""
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    ip = Column(String(45), index=True)

    __table_args__ = (UniqueConstraint("post_id", "ip", name="uq_post_ip"),)


class CommentLike(Base):
    """评论点赞（IP 去重）。"""
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), index=True)
    ip = Column(String(45), index=True)

    __table_args__ = (UniqueConstraint("comment_id", "ip", name="uq_comment_ip"),)
