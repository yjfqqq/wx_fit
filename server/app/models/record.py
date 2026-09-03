from datetime import date

from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, pk_type


class WeightRecord(Base, TimestampMixin):
    __tablename__ = "weight_records"
    __table_args__ = (Index("idx_weight_user_date", "user_id", "record_date"),)

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False)
    body_fat: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    note: Mapped[str] = mapped_column(String(255), default="", server_default="")


class MealRecord(Base, TimestampMixin):
    """饮食记录。快速记录只填 title；查库记录会带出热量与三大营养素"""

    __tablename__ = "meal_records"
    __table_args__ = (Index("idx_meal_user_date", "user_id", "record_date"),)

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    # 1 早餐 / 2 午餐 / 3 晚餐 / 4 加餐
    meal_type: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
    food_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(128), default="", server_default="")
    amount_g: Mapped[float | None] = mapped_column(Numeric(8, 1), nullable=True)
    calories: Mapped[float | None] = mapped_column(Numeric(8, 1), nullable=True)
    protein: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    fat: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    carbs: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    note: Mapped[str] = mapped_column(String(255), default="", server_default="")


class ExerciseRecord(Base, TimestampMixin):
    __tablename__ = "exercise_records"
    __table_args__ = (Index("idx_exercise_user_date", "user_id", "record_date"),)

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    item_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(String(64), default="", server_default="")
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    # 1 低 / 2 中 / 3 高
    intensity: Mapped[int] = mapped_column(SmallInteger, default=2, server_default="2")
    steps: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    calories: Mapped[float | None] = mapped_column(Numeric(8, 1), nullable=True)
    note: Mapped[str] = mapped_column(String(255), default="", server_default="")


class DailySummary(Base, TimestampMixin):
    """每日汇总。所有记录写操作都要触发重算，首页与趋势页直接读这里"""

    __tablename__ = "daily_summaries"
    __table_args__ = (
        UniqueConstraint("user_id", "summary_date", name="uk_summary_user_date"),
    )

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)
    intake_kcal: Mapped[float] = mapped_column(Numeric(8, 1), default=0, server_default="0")
    burn_kcal: Mapped[float] = mapped_column(Numeric(8, 1), default=0, server_default="0")
    protein: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    fat: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    carbs: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    # 当天记了几条（没有热量的也算，用于打卡统计）
    meal_count: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    exercise_count: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
