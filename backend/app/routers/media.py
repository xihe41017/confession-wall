"""媒体上传：图片与 ≤15 秒短视频。文件存本地 data/uploads/ 下，返回相对 URL。"""
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.database import get_db
from app.deps import check_ip_allowed, get_ip, optional_user
from app.models import User
from app.ratelimit import dyn, limiter
from app.settings_service import service as settings_service

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTS = {".mp4", ".webm", ".mov"}
VIDEO_MAX_SECONDS = 15


def _limits(db: Session) -> tuple[int, int]:
    img_mb = settings_service.get_int(db, "image_max_mb", 2)
    vid_mb = settings_service.get_int(db, "video_max_mb", 15)
    return img_mb * 1024 * 1024, vid_mb * 1024 * 1024

router = APIRouter(prefix="/api", tags=["media"])


def _probe_duration(path: Path) -> float | None:
    """用 ffprobe / ffmpeg 探测视频时长（秒）。无法探测时返回 None。"""
    probe = shutil.which("ffprobe")
    if probe:
        try:
            r = subprocess.run(
                [probe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True, timeout=30,
            )
            return float(r.stdout.decode().strip())
        except (ValueError, subprocess.TimeoutExpired, OSError):
            pass
    # 回退：用 ffmpeg -i 解析 Duration
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        try:
            r = subprocess.run([ffmpeg, "-i", str(path), "-f", "null", "-"],
                               capture_output=True, timeout=30)
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr.decode("utf-8", "ignore"))
            if m:
                return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        except (subprocess.TimeoutExpired, OSError):
            pass
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        r = subprocess.run([get_ffmpeg_exe(), "-i", str(path), "-f", "null", "-"],
                           capture_output=True, timeout=30)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr.decode("utf-8", "ignore"))
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return None


@router.post("/upload")
@limiter.limit(dyn("rate_upload", "10/minute"))
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    ip = get_ip(request)
    check_ip_allowed(db, ip)

    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    is_image = ext in IMAGE_EXTS
    is_video = ext in VIDEO_EXTS
    if not is_image and not is_video:
        raise HTTPException(status_code=400, detail="仅支持图片（jpg/png/gif/webp）或视频（mp4/webm/mov）")

    # 鉴权：未登录不能上传视频（匿名只能发 1 张图片）
    if is_video and not user:
        raise HTTPException(status_code=403, detail="登录后才能上传视频")

    image_max, video_max = _limits(db)
    max_size = image_max if is_image else video_max
    content = await file.read()
    if len(content) > max_size:
        size_mb = max_size // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"文件过大，{ '图片' if is_image else '视频' }不能超过 {size_mb}MB")

    kind = "images" if is_image else "videos"
    folder = UPLOAD_DIR / kind
    folder.mkdir(parents=True, exist_ok=True)
    name = uuid.uuid4().hex + ext
    path = folder / name
    path.write_bytes(content)

    if is_video:
        duration = _probe_duration(path)
        if duration is not None and duration > VIDEO_MAX_SECONDS + 0.5:
            path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"视频时长 {duration:.1f} 秒，不能超过 {VIDEO_MAX_SECONDS} 秒",
            )

    return {"url": f"/uploads/{kind}/{name}"}
