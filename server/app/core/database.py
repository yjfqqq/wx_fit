from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # 连接池参数只对 MySQL 有意义
    **({} if _is_sqlite else {"pool_pre_ping": True, "pool_recycle": 3600}),
    echo=settings.DEBUG,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, future=True)


class Base(DeclarativeBase):
    """所有模型的基类"""


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：每个请求一个 Session，结束后自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
