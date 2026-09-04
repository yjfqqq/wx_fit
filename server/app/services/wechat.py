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
    try:
        # 云托管环境可能注入 HTTPS 代理并替换证书；忽略代理变量，仍保留 HTTPS 证书校验。
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            resp = await client.get(CODE2SESSION_URL, params=params)
            data = resp.json()
    except httpx.HTTPError as e:
        # 连接不上微信服务器（DNS/超时/无公网出口等），转成业务错误避免 500
        raise WeChatLoginError(
            f"无法连接微信服务器（{e.__class__.__name__}），请检查部署环境的公网出口配置"
        )

    errcode = data.get("errcode")
    if errcode:
        raise WeChatLoginError(f"微信登录失败：{data.get('errmsg')} (errcode={errcode})")

    openid = data.get("openid")
    if not openid:
        raise WeChatLoginError("微信返回数据中没有 openid")
    return openid
