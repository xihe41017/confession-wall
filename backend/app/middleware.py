"""请求体大小限制：防止超大请求体攻击。上限可在管理后台配置。"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.settings_service import service as settings_service


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            length = request.headers.get("content-length")
            if length:
                try:
                    kb = int(settings_service.get_cached("max_body_kb", "512"))
                except (TypeError, ValueError):
                    kb = 512
                try:
                    if int(length) > kb * 1024:
                        return JSONResponse(
                            {"detail": "请求体过大，请精简内容"}, status_code=413
                        )
                except ValueError:
                    pass
        return await call_next(request)
