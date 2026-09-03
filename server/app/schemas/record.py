from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class WeightIn(BaseModel):
    weight_kg: float = Field(gt=0, le=400)
    record_date: date
    body_fat: float | None = Field(default=None, ge=0, le=100)
    waist_cm: float | None = Field(default=None, gt=0, le=300)
    note: str = ""


class WeightOut(ORMModel):
    id: int
    record_date: date
    weight_kg: float
    body_fat: float | None
    waist_cm: float | None
    note: str


class MealIn(BaseModel):
    """快速记录：只传 meal_type + title
    查库记录：传 food_id + amount_g，后端自动算热量与营养素"""

    record_date: date
    meal_type: int = Field(default=1, ge=1, le=4)
    title: str = ""
    food_id: int | None = None
    amount_g: float | None = Field(default=None, gt=0, le=5000)
    note: str = ""


class MealOut(ORMModel):
    id: int
    record_date: date
    meal_type: int
    food_id: int | None
    title: str
    amount_g: float | None
    calories: float | None
    protein: float | None
    fat: float | None
    carbs: float | None
    note: str


class ExerciseIn(BaseModel):
    record_date: date
    item_id: int | None = None
    name: str = ""
    duration_min: int = Field(default=0, ge=0, le=1440)
    intensity: int = Field(default=2, ge=1, le=3)
    steps: int | None = Field(default=None, ge=0)
    note: str = ""


class ExerciseOut(ORMModel):
    id: int
    record_date: date
    item_id: int | None
    name: str
    duration_min: int
    intensity: int
    steps: int | None
    calories: float | None
    note: str


class SummaryOut(BaseModel):
    """某日总览"""

    date: date
    intake_kcal: float
    burn_kcal: float
    net_kcal: float
    budget_kcal: float | None
    remaining_kcal: float | None
    weight_kg: float | None
    protein: float
    fat: float
    carbs: float
    meal_count: int
    exercise_count: int
    # 有记录但没热量的条数，用于提示用户
    unknown_calorie_count: int


class CalendarDay(BaseModel):
    date: date
    has_weight: bool
    has_meal: bool
    has_exercise: bool


class WeightPoint(BaseModel):
    date: date
    weight: float
    avg7: float | None


class WeightStatsOut(BaseModel):
    points: list[WeightPoint]
    total_change: float | None
    weekly_rate: float | None


class CaloriePoint(BaseModel):
    date: date
    intake: float
    burn: float


class OverviewOut(BaseModel):
    start_weight: float | None
    current_weight: float | None
    target_weight: float | None
    total_lost: float | None
    weekly_rate: float | None
    streak_days: int
    recorded_days: int
