"""每日打卡提醒：给已开启提醒且今天还没记体重的用户发一条订阅消息。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.notify import RemindSetting, SubscribeGrant
from app.models.record import WeightRecord
from app.services.wx_message import send_remind


def send_pending_reminds(
    force: bool = False,
    now: datetime | None = None,
    user_id: int | None = None,
) -> dict:
    """扫描已开启提醒的用户，当天还没记体重的发提醒。

    - 定时任务在 WX_REMIND_HOUR 点调用；force=True 手动触发时忽略小时检查
    - user_id 传入时只处理该用户（联调用）
    - 发送失败保留授权，下次再试（常见失败 43101 = 用户拒收）
    """
    if not settings.WX_TEMPLATE_ID:
        return {"skipped": "WX_TEMPLATE_ID 未配置，提醒功能未启用"}

    now = now or datetime.now()
    if not force and now.hour != settings.WX_REMIND_HOUR:
        return {"skipped": f"当前 {now.hour} 点 ≠ 设定 {settings.WX_REMIND_HOUR} 点"}

    today = now.date()
    sent = already_recorded = no_grant = failed = 0

    with SessionLocal() as db:
        q = select(RemindSetting).where(RemindSetting.enabled == 1)
        if user_id:
            q = q.where(RemindSetting.user_id == user_id)
        rows = db.scalars(q).all()

        for row in rows:
            has_weight = db.scalar(
                select(WeightRecord.id).where(
                    WeightRecord.user_id == row.user_id,
                    WeightRecord.record_date == today,
                )
            )
            if has_weight:
                already_recorded += 1
                continue

            grant = db.scalar(
                select(SubscribeGrant)
                .where(
                    SubscribeGrant.user_id == row.user_id,
                    SubscribeGrant.used_at.is_(None),
                )
                .order_by(SubscribeGrant.id)
            )
            if grant is None:
                no_grant += 1
                continue

            ok, msg = send_remind(grant.openid)
            if ok:
                grant.used_at = now
                db.commit()
                sent += 1
            else:
                failed += 1

    return {
        "checked": len(rows),
        "sent": sent,
        "already_recorded": already_recorded,
        "no_grant": no_grant,
        "failed": failed,
    }
