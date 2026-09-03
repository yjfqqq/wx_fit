from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FoodOut(ORMModel):
    id: int
    name: str
    category: str
    calories_per_100g: float
    protein: float
    fat: float
    carbs: float
    common_unit: str
    unit_weight_g: float
    is_custom: bool = False


class CustomFoodIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    calories_per_100g: float = Field(ge=0, le=1000)
    protein: float = Field(default=0, ge=0, le=100)
    fat: float = Field(default=0, ge=0, le=100)
    carbs: float = Field(default=0, ge=0, le=100)
    common_unit: str = "克"
    unit_weight_g: float = Field(default=100, gt=0, le=5000)


class ExerciseItemOut(ORMModel):
    id: int
    name: str
    category: str
    met_value: float
