"""APScheduler 定时任务：每日打卡提醒。"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.services.remind import send_pending_reminds

logger = logging.getLogger("uvicorn.error")

scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        return
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        send_pending_reminds,
        trigger="cron",
        hour=settings.WX_REMIND_HOUR,
        minute=5,
        id="daily-weight-remind",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"打卡提醒定时任务已启动：每天 {settings.WX_REMIND_HOUR:02d}:05")


def stop_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
