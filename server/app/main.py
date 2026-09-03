# 允许直接 python app/main.py 运行(把项目根加入 sys.path,解决 from app.xxx import)
# 也兼容 uvicorn app.main:app 模块方式启动(不影响)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 配置了订阅消息模板 ID 才启动打卡提醒定时任务
    if settings.WX_TEMPLATE_ID:
        from app.services.scheduler import start_scheduler

        start_scheduler()
    yield
    try:
        from app.services.scheduler import stop_scheduler

        stop_scheduler()
    except Exception:  # noqa: S110
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="减肥记录小程序后端 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    # 用户上传文件静态访问（头像等），目录不存在时自动创建
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    @app.get("/health", tags=["系统"])
    def health():
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "mock_login": settings.WX_MOCK_LOGIN,
            "remind_configured": bool(settings.WX_TEMPLATE_ID),
        }

    return app


app = create_app()


# 支持直接 python app/main.py 启动（或 IDE 直接 Run 本文件）
# 生产/日常推荐:uvicorn app.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
