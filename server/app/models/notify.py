from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, pk_type


class RemindSetting(Base, TimestampMixin):
    """每日打卡提醒开关（每用户一行）"""

    __tablename__ = "remind_settings"

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    # 1 开启 / 0 关闭
    enabled: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")


class SubscribeGrant(Base, TimestampMixin):
    """一次性订阅消息授权记录。

    用户每次在小程序里同意订阅弹窗，就产生一条授权；推送成功消耗一条（used_at 置值）。
    想持续收到提醒，需要定期再次弹窗收集授权。
    """

    __tablename__ = "subscribe_grants"

    id: Mapped[int] = mapped_column(pk_type(), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    openid: Mapped[str] = mapped_column(String(64), index=True)
    # NULL = 未使用；发送成功后记录时间
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
