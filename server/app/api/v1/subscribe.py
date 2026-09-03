from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.notify import RemindSetting, SubscribeGrant
from app.models.user import User
from app.services.remind import send_pending_reminds

router = APIRouter(prefix="/subscribe", tags=["订阅提醒"])


def _status(db: Session, user: User) -> dict:
    unused = db.scalar(
        select(func.count())
        .select_from(SubscribeGrant)
        .where(SubscribeGrant.user_id == user.id, SubscribeGrant.used_at.is_(None))
    )
    setting = db.scalar(select(RemindSetting).where(RemindSetting.user_id == user.id))
    return {
        "enabled": bool(setting and setting.enabled == 1),
        "remind_time": f"{settings.WX_REMIND_HOUR:02d}:00",
        "template_configured": bool(settings.WX_TEMPLATE_ID),
        "unused_grants": int(unused or 0),
    }


@router.get("/config", summary="提醒功能配置（模板是否已配置、提醒时间）")
def get_config():
    # 模板 ID 会随小程序端发布（requestSubscribeMessage 需要用），本身不是敏感信息
    return {
        "template_configured": bool(settings.WX_TEMPLATE_ID),
        "template_id": settings.WX_TEMPLATE_ID,
        "remind_time": f"{settings.WX_REMIND_HOUR:02d}:00",
    }


@router.get("/status", summary="当前用户的提醒状态")
def get_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _status(db, user)


@router.post("/grant", summary="上报用户同意订阅弹窗（存一条一次性授权）")
def grant(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(SubscribeGrant(user_id=user.id, openid=user.openid))
    db.commit()
    return {"granted": True, **_status(db, user)}


class ToggleIn(BaseModel):
    enabled: bool


@router.post("/toggle", summary="开启/关闭每日打卡提醒")
def toggle(
    body: ToggleIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    setting = db.scalar(select(RemindSetting).where(RemindSetting.user_id == user.id))
    if setting is None:
        setting = RemindSetting(user_id=user.id)
        db.add(setting)
    setting.enabled = 1 if body.enabled else 0
    db.commit()
    return _status(db, user)


@router.post("/test-send", summary="[DEBUG] 手动给当前用户发一条提醒（联调用）")
def test_send(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not settings.DEBUG:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "仅 DEBUG 模式可用")
    result = send_pending_reminds(force=True, user_id=user.id)
    return result
