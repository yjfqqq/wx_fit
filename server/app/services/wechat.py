"""微信小程序登录：code 换 openid。

没有 AppID/AppSecret 时由 config 里的 WX_MOCK_LOGIN 控制走 mock，
本地开发可以在不配置任何微信参数的情况下跑通全部业务逻辑。
"""

from __future__ import annotations

import httpx

from app.core.config import settings

CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


class WeChatLoginError(Exception):
    pass


async def code2session(code: str) -> str:
    """返回 openid。mock 模式下直接返回固定 openid。"""
    if settings.WX_MOCK_LOGIN or not (settings.WX_APPID and settings.WX_SECRET):
        return settings.MOCK_OPENID

    params = {
        "appid": settings.WX_APPID,
        "secret": settings.WX_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(CODE2SESSION_URL, params=params)
        data = resp.json()

    errcode = data.get("errcode")
    if errcode:
        raise WeChatLoginError(f"微信登录失败：{data.get('errmsg')} (errcode={errcode})")

    openid = data.get("openid")
    if not openid:
        raise WeChatLoginError("微信返回数据中没有 openid")
    return openid
