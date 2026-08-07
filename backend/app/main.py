from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import DEFAULT_SETTINGS, settings
from app.database import Base, SessionLocal, engine, run_migrations
from app.middleware import RequestBodyLimitMiddleware
from app.models import Setting, User  # noqa: F401  确保建表前已加载模型
from app.ratelimit import limiter
from app.routers import admin, auth, comments, media, nginx, posts, settings_admin, site, users
from app.routers.auto_update import router as auto_update_router

# 上传目录（图片/视频）
from app.routers.media import UPLOAD_DIR
from app.security import hash_password
from app.settings_service import service as settings_service

# 前端构建产物目录（生产部署时后端直接托管前端，只需一个进程）
DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
HAS_DIST = (DIST / "index.html").exists()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    db = SessionLocal()
    # 播种默认设置（已存在的保留；旧默认值自动升级）
    for key, default, desc, sensitive in DEFAULT_SETTINGS:
        if db.get(Setting, key) is None:
            db.add(Setting(key=key, value=str(default), description=desc, sensitive=sensitive))
        else:
            s = db.get(Setting, key)
            # 旧默认值升级（仅当仍是旧默认值时才升级，用户改过的保留）
            if key == "site_name" and s.value == "校园墙":
                s.value = str(default)
            elif key == "max_body_kb" and s.value == "512":
                s.value = str(default)  # 旧 512KB 请求体上限升级为 50MB
    # 播种超级管理员
    if not db.query(User).filter_by(role="super_admin").first():
        db.add(
            User(
                username=settings.ADMIN_USERNAME.lower(),
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                nickname="超级管理员",
                role="super_admin",
                status="active",
            )
        )
        print(f"[提示] 已创建超级管理员：{settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD}")
        print("[提示] 登录后请立即在 账号 → 管理后台 → 账号管理 中修改密码！")
    db.commit()
    settings_service.warm(db)  # 把设置载入缓存，供限流器等无 db 场景读取
    db.close()
    import app.auto_update as auto_update
    auto_update.start_scheduler()  # 自动更新后台调度
    yield


app = FastAPI(title="校园墙 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestBodyLimitMiddleware)

# 速率限制
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(site.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(media.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(settings_admin.router)
app.include_router(nginx.router)
app.include_router(auto_update_router)

# 上传文件静态托管
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 存在前端构建产物时，托管静态页面（生产模式）
if HAS_DIST:
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        target = DIST / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        return FileResponse(DIST / "index.html")

    print("[提示] 检测到前端构建产物，已启用静态托管模式")
