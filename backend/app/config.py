"""全局配置。环境变量提供初始值，运行时可在管理后台动态修改（存数据库）。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings:
    # 数据库文件放在 backend/data/ 下
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'confession.db'}")

    # 管理员初始账号（首次启动自动创建，上线后请在后台修改或改环境变量）
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    # JWT 密钥（生产环境务必改成随机字符串）
    JWT_SECRET = os.getenv("JWT_SECRET", "confession-wall-dev-secret")
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))

    # 前端开发地址，部署后可改为前端域名
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")

    DEFAULT_PAGE_SIZE = 12

    # 生产托管静态资源模式
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", "8000"))

    # 自动更新（部署脚本会生成更新脚本；Windows 开发环境无此脚本则自动更新不可用）
    UPDATE_SCRIPT = os.getenv("UPDATE_SCRIPT", "/usr/local/bin/campus-confession-update.sh")
    UPDATE_STATE = os.getenv("UPDATE_STATE", "/var/log/campus-confession-update.state")


settings = Settings()


# ============ 运行时设置项（存入数据库，后台可改） ============
# (key, 默认值, 描述, 是否敏感[仅超管可改])
DEFAULT_SETTINGS = [
    ("site_name", "平和一中校园墙", "站点名称", 1),          # 仅超管
    ("site_announcement", "", "站点公告（显示在首页顶部）", 0),
    ("moderation_mode", "0", "发布是否需要管理员审核后才上墙（1=开启）", 0),
    ("allow_register", "1", "是否开放注册（1=开启）", 0),
    ("register_approval", "0", "注册是否需要管理员同意激活（1=需要）", 0),
    ("anonymous_post_limit", "3", "未登录用户单个IP/设备24小时内限发条数", 0),
    # 速率限制与请求体上限（防 DoS 相关，仅超管可改）
    ("rate_register", "20/minute", "注册接口限速", 1),
    ("rate_login", "30/minute", "登录接口限速", 1),
    ("rate_post", "20/minute", "发布接口限速", 1),
    ("rate_comment", "30/minute", "评论接口限速", 1),
    ("rate_like", "60/minute", "点赞接口限速", 1),
    ("rate_upload", "10/minute", "上传接口限速", 1),
    ("max_body_kb", "51200", "请求体大小上限(KB)，默认50MB", 1),
    ("image_max_mb", "2", "单张图片上传上限(MB，压缩后)", 1),
    ("video_max_mb", "15", "单个视频上传上限(MB)", 1),
    ("auto_update_enabled", "0", "自动更新开关（仅超管）", 1),
    ("auto_update_interval", "5", "自动更新检查间隔(分钟)（仅超管）", 1),
    ("jwt_secret", settings.JWT_SECRET, "JWT签名密钥（修改后所有人需重新登录）", 1),
]

# 需要隐藏真实值的设置项（像密码一样打码），目前仅 JWT 密钥
MASKED_SETTINGS = {"jwt_secret"}
