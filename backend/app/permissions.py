"""权限体系：超管恒有全部权限；其余用户权限 = role 基础权限 ∪ 单独授予的权限。

权限键分两类：
- 功能权限（content.manage / content.pin / ...）
- 设置项权限（settings.<key>，可细到每个设置项）

部分设置项（站点名、限速、请求体上限、JWT密钥）由超管硬性独占，不在此授予。
"""
import json

from app.models import User

# 可授予的权限键定义：(key, 分组, 说明)
PERMISSIONS = [
    ("content.manage", "内容管理", "查看内容管理、审核上墙、删除内容与评论"),
    ("content.pin", "内容管理", "置顶 / 取消置顶"),
    ("content.edit", "内容管理", "修改内容的点赞数 / 对象 / 昵称"),
    ("content.ban_ip", "内容管理", "对内容一键拉黑发布 IP"),
    ("comment.edit", "评论管理", "修改评论的点赞数"),
    ("ban.manage", "IP 黑名单", "查看 / 解除 IP 黑名单"),
    ("settings.view", "服务器设置", "查看服务器设置"),
    ("settings.site_announcement", "服务器设置", "修改：站点公告"),
    ("settings.moderation_mode", "服务器设置", "修改：发布需审核开关"),
    ("settings.allow_register", "服务器设置", "修改：开放注册开关"),
    ("settings.register_approval", "服务器设置", "修改：注册需激活开关"),
    ("settings.anonymous_post_limit", "服务器设置", "修改：匿名限发条数"),
]
PERMISSION_KEYS = [k for k, _g, _d in PERMISSIONS]
PERMISSION_LABELS = {k: (g, d) for k, g, d in PERMISSIONS}

# 管理员默认权限（提升为管理员时写入）
ADMIN_DEFAULT_PERMS = [
    "content.manage", "content.pin", "content.edit", "content.ban_ip",
    "comment.edit", "ban.manage", "settings.view",
    "settings.site_announcement", "settings.moderation_mode",
    "settings.allow_register", "settings.register_approval",
    "settings.anonymous_post_limit",
]


def _perm_list(user: User) -> list:
    if not user.permissions:
        return []
    try:
        data = json.loads(user.permissions)
        return data if isinstance(data, list) else []
    except (TypeError, ValueError):
        return []


def effective_perms(user: User) -> set:
    """计算用户实际生效的权限。"""
    if user.role == "super_admin":
        return set(PERMISSION_KEYS)
    perms = set(_perm_list(user))
    if not perms and user.role == "admin":
        # 旧数据：老管理员未配置权限时，按默认管理员权限处理
        perms = set(ADMIN_DEFAULT_PERMS)
    return perms


def has_perm(user: User, key: str) -> bool:
    if user.role == "super_admin":
        return True  # 超管恒有全部权限（含隐式权限）
    return key in effective_perms(user)


def set_perms(user: User, keys: list):
    """写入用户权限（会过滤非法键）。"""
    user.permissions = json.dumps(sorted(set(k for k in keys if k in PERMISSION_KEYS)), ensure_ascii=False)
