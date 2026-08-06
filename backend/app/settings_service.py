"""运行时设置服务：从数据库读取设置（带缓存），后台修改后立即生效。"""
from sqlalchemy.orm import Session

from app.models import Setting


class SettingsService:
    def __init__(self):
        self._cache = {}

    def invalidate(self, key: str = None):
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    def warm(self, db: Session):
        """启动时把全部设置载入缓存，供无 db 场景（限流器）读取。"""
        for s in db.query(Setting).all():
            self._cache[s.key] = s.value

    def get_cached(self, key: str, default: str = None) -> str:
        """仅读缓存（无 db）。限流器等调用点使用。"""
        value = self._cache.get(key)
        return default if value is None else str(value)

    def get_raw(self, db: Session, key: str, default: str = None) -> str:
        if key in self._cache:
            return self._cache[key]
        s = db.get(Setting, key)
        value = s.value if s else default
        self._cache[key] = value
        return value

    def get(self, db: Session, key: str, default: str = None) -> str:
        value = self.get_raw(db, key, default)
        return "" if value is None else str(value)

    def get_bool(self, db: Session, key: str, default: bool = False) -> bool:
        return self.get(db, key, "1" if default else "0") in ("1", "true", "True", "yes")

    def get_int(self, db: Session, key: str, default: int = 0) -> int:
        try:
            return int(float(self.get(db, key, str(default))))
        except (TypeError, ValueError):
            return default

    def set(self, db: Session, key: str, value: str) -> Setting:
        s = db.get(Setting, key)
        if s is None:
            s = Setting(key=key)
            db.add(s)
        s.value = str(value)
        db.commit()
        db.refresh(s)
        self._cache[key] = str(value)
        return s


service = SettingsService()
