from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class LoginIn(BaseModel):
    """code: wx.login 拿到的临时凭证；mock 模式下可传任意值
    nickname / avatar_url 仅首次登录时用于初始化资料"""

    code: str
    nickname: str = ""
    avatar_url: str = ""


class LoginOut(BaseModel):
    token: str
    is_new: bool
    user_id: int


class ProfileOut(ORMModel):
    id: int
    openid: str
    nickname: str
    avatar_url: str
    gender: int
    birthday: date | None
    height_cm: float | None
    activity_level: int


class ProfileIn(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    gender: int | None = Field(default=None, ge=0, le=2)
    birthday: date | None = None
    height_cm: float | None = Field(default=None, gt=0, le=250)
    activity_level: int | None = Field(default=None, ge=1, le=5)


class GoalIn(BaseModel):
    start_weight: float | None = Field(default=None, gt=0, le=400)
    target_weight: float | None = Field(default=None, gt=0, le=400)
    target_date: date | None = None
    daily_deficit: int | None = Field(default=None, ge=0, le=1500)


class GoalOut(ORMModel):
    start_weight: float | None
    target_weight: float | None
    target_date: date | None
    daily_deficit: int
    status: int


class PlanOut(BaseModel):
    """目标计划与热量预算测算"""

    has_goal: bool
    bmr: float | None
    tdee: float | None
    daily_budget: float | None
    bmi: float | None
    bmi_level: str | None
    current_weight: float | None
    progress: float | None
    weekly_rate: float | None
    predict_date: date | None
