"""速率限制：基于 slowapi。默认全局宽松兜底，关键接口限速可在管理后台配置。"""
from slowapi import Limiter
from starlette.requests import Request

from app.settings_service import service as settings_service


def _rate_key(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def dyn(key: str, default: str):
    """返回一个动态限流值（每次请求从设置缓存读取，后台改后即时生效）。"""
    return lambda: settings_service.get_cached(key, default) or default


limiter = Limiter(key_func=_rate_key, default_limits=["1000/minute"])
