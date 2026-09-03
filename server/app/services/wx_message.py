"""微信订阅消息发送：stable_token 获取 + subscribe/send 推送。"""

from __future__ import annotations

import logging
import threading
import time

import httpx

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/stable_token"
SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"

_token_lock = threading.Lock()
_token_cache: dict = {"token": "", "expires_at": 0.0}


def get_access_token() -> str:
    """获取 access_token（stable_token 接口，不挤掉旧 token，缓存到过期前 5 分钟）。"""
    with _token_lock:
        if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
            return _token_cache["token"]

        resp = httpx.post(
            TOKEN_URL,
            json={
                "grant_type": "client_credential",
                "appid": settings.WX_APPID,
                "secret": settings.WX_SECRET,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("access_token"):
            _token_cache["token"] = data["access_token"]
            _token_cache["expires_at"] = time.time() + int(data.get("expires_in", 7200)) - 300
            return _token_cache["token"]
        raise RuntimeError(f"获取 access_token 失败: {data}")


def build_remind_data() -> dict:
    """订阅消息模板字段。

    在小程序后台申领「打卡提醒」类模板后，按模板详情里的字段 ID（thing1/time2 等）
    调整这里的键名和内容。value 长度需符合字段类型限制（thing ≤20 字）。
    """
    return {
        "thing1": {"value": "该记录今天的体重啦"},
        "time2": {"value": f"{settings.WX_REMIND_HOUR:02d}:00"},
    }


def send_remind(openid: str) -> tuple[bool, str]:
    """发一条订阅消息。返回 (是否成功, 说明)。常见失败：43101 用户拒收。"""
    try:
        token = get_access_token()
        resp = httpx.post(
            SEND_URL,
            params={"access_token": token},
            json={
                "touser": openid,
                "template_id": settings.WX_TEMPLATE_ID,
                "page": "pages/index/index",
                "data": build_remind_data(),
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("errcode") == 0:
            return True, "ok"
        return False, f"{data.get('errmsg')} (errcode={data.get('errcode')})"
    except Exception as e:  # noqa: BLE001
        return False, str(e)
