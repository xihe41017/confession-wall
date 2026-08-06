from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
)

# SQLite 优化：WAL 模式提升并发读写能力
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA foreign_keys=ON"))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _ensure_column(conn, table, column, ddl):
    cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    if column not in {c[1] for c in cols}:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
        print(f"[迁移] 已为 {table} 表添加 {column} 列")


def run_migrations(engine):
    """轻量迁移：给已有表补新增字段（create_all 不会修改已存在的表）。"""
    with engine.connect() as conn:
        _ensure_column(conn, "posts", "pinned", "pinned INTEGER DEFAULT 0")
        _ensure_column(conn, "posts", "is_anonymous", "is_anonymous INTEGER DEFAULT 0")
        _ensure_column(conn, "posts", "images", "images VARCHAR(1000)")
        _ensure_column(conn, "posts", "video", "video VARCHAR(500)")
        _ensure_column(conn, "comments", "likes", "likes INTEGER DEFAULT 0")
        _ensure_column(conn, "users", "permissions", "permissions VARCHAR(500)")
        _ensure_column(conn, "users", "email", "email VARCHAR(100)")
        _ensure_column(conn, "users", "phone", "phone VARCHAR(30)")
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
