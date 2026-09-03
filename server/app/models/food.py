from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, pk_type


class FoodItem(Base, TimestampMixin):
    """系统预置食物库，数值以每 100g 计"""

    __tablename__ = "food_items"
    __table_args__ = (
        Index("idx_food_name", "name"),
        Index("idx_food_initial", "initial"),
    )

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    pinyin: Mapped[str] = mapped_column(String(64), default="", server_default="")
    # 拼音首字母，如 鸡胸肉 -> jxr
    initial: Mapped[str] = mapped_column(String(32), default="", server_default="")
    category: Mapped[str] = mapped_column(String(32), default="其他", server_default="其他")
    calories_per_100g: Mapped[float] = mapped_column(Numeric(8, 1), default=0, server_default="0")
    protein: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    fat: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    carbs: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    fiber: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    # 常见份量单位与对应克重，如 1个 / 100
    common_unit: Mapped[str] = mapped_column(String(16), default="克", server_default="克")
    unit_weight_g: Mapped[float] = mapped_column(Numeric(8, 1), default=100, server_default="100")
    # 排序权重，越大越靠前
    sort_weight: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")


class CustomFood(Base, TimestampMixin):
    """用户自定义食物"""

    __tablename__ = "custom_foods"

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    pinyin: Mapped[str] = mapped_column(String(64), default="", server_default="")
    initial: Mapped[str] = mapped_column(String(32), default="", server_default="")
    calories_per_100g: Mapped[float] = mapped_column(Numeric(8, 1), default=0, server_default="0")
    protein: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    fat: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    carbs: Mapped[float] = mapped_column(Numeric(6, 1), default=0, server_default="0")
    common_unit: Mapped[str] = mapped_column(String(16), default="克", server_default="克")
    unit_weight_g: Mapped[float] = mapped_column(Numeric(8, 1), default=100, server_default="100")


class ExerciseItem(Base, TimestampMixin):
    """系统预置运动库，met_value 用于估算消耗"""

    __tablename__ = "exercise_items"

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    pinyin: Mapped[str] = mapped_column(String(64), default="", server_default="")
    initial: Mapped[str] = mapped_column(String(32), default="", server_default="")
    category: Mapped[str] = mapped_column(String(32), default="其他", server_default="其他")
    met_value: Mapped[float] = mapped_column(Numeric(4, 1), default=3.0, server_default="3.0")
    sort_weight: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
