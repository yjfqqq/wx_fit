from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, pk_type


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(64), default="", server_default="")
    avatar_url: Mapped[str] = mapped_column(String(512), default="", server_default="")
    # 1 正常 / 0 禁用
    status: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    goal: Mapped["Goal"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserProfile(Base, TimestampMixin):
    """身体资料，用于计算 BMR / TDEE"""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    # 0 未知 / 1 男 / 2 女
    gender: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    # 1 久坐 / 2 轻度 / 3 中度 / 4 高度 / 5 极高
    activity_level: Mapped[int] = mapped_column(
        SmallInteger, default=1, server_default="1"
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class Goal(Base, TimestampMixin):
    """减重目标"""

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    start_weight: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    target_weight: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # 每日热量缺口，默认 500 kcal ≈ 每周减 0.5kg
    daily_deficit: Mapped[int] = mapped_column(
        SmallInteger, default=500, server_default="500"
    )
    # 1 进行中 / 2 已完成 / 0 已放弃
    status: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")

    user: Mapped["User"] = relationship(back_populates="goal")
