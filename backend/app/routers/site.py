from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SiteInfo
from app.settings_service import service as settings_service

router = APIRouter(prefix="/api/site", tags=["site"])


@router.get("/info", response_model=SiteInfo)
def site_info(db: Session = Depends(get_db)):
    return SiteInfo(
        site_name=settings_service.get(db, "site_name", "校园墙"),
        site_announcement=settings_service.get(db, "site_announcement", ""),
        allow_register=settings_service.get_bool(db, "allow_register", True),
        register_approval=settings_service.get_bool(db, "register_approval", False),
        moderation_mode=settings_service.get_bool(db, "moderation_mode", False),
        anonymous_post_limit=settings_service.get_int(db, "anonymous_post_limit", 3),
        image_max_mb=settings_service.get_int(db, "image_max_mb", 2),
        video_max_mb=settings_service.get_int(db, "video_max_mb", 15),
    )
