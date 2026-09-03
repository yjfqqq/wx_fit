from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    APP_NAME: str = "Fit API"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # mysql（正式）或 sqlite（本机没装 MySQL 时用它先跑起来）
    DB_ENGINE: str = "mysql"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "fit_app"
    SQLITE_PATH: str = "./fit_app.db"

    JWT_SECRET: str = "please-change-this-to-a-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30

    WX_APPID: str = ""
    WX_SECRET: str = ""
    WX_MOCK_LOGIN: bool = True
    MOCK_OPENID: str = "mock_openid_0001"

    # 每日打卡提醒（订阅消息）：WX_TEMPLATE_ID 填入小程序后台申领的模板 ID 后启用，
    # 每天 WX_REMIND_HOUR 点给「已开启提醒且当天没记体重」的用户推送
    WX_TEMPLATE_ID: str = ""
    WX_REMIND_HOUR: int = 21

    CORS_ORIGINS: str = "*"

    # 头像等用户上传文件的本地存储
    UPLOAD_DIR: str = "./uploads"
    AVATAR_URL_PREFIX: str = "/uploads/avatars"

    @property
    def database_url(self) -> str:
        if self.DB_ENGINE.lower() == "sqlite":
            return f"sqlite:///{self.SQLITE_PATH}"
        pwd = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{self.DB_USER}:{pwd}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [i.strip() for i in self.CORS_ORIGINS.split(",") if i.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
