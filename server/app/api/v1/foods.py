"""食物库、自定义食物、运动库查询"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.food import CustomFood, ExerciseItem, FoodItem
from app.models.user import User
from app.schemas.common import Page
from app.schemas.food import CustomFoodIn, ExerciseItemOut, FoodOut

router = APIRouter(tags=["数据库"])


def _food_out(food: FoodItem | CustomFood, is_custom: bool = False) -> FoodOut:
    return FoodOut(
        id=food.id,
        name=food.name,
        category=getattr(food, "category", "自定义"),
        calories_per_100g=food.calories_per_100g,
        protein=food.protein,
        fat=food.fat,
        carbs=food.carbs,
        common_unit=food.common_unit,
        unit_weight_g=food.unit_weight_g,
        is_custom=is_custom,
    )


@router.get("/foods", response_model=Page, summary="搜索食物（含自定义）")
def search_foods(
    keyword: str = Query(default="", max_length=32),
    category: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kw = keyword.strip()

    # 自定义食物优先匹配，用户自己的东西应该排前面
    custom_stmt = select(CustomFood).where(CustomFood.user_id == user.id)
    if kw:
        custom_stmt = custom_stmt.where(
            or_(
                CustomFood.name.contains(kw),
                CustomFood.pinyin.contains(kw.lower()),
                CustomFood.initial.contains(kw.lower()),
            )
        )
    customs = db.scalars(
        custom_stmt.order_by(CustomFood.id.desc()).limit(10)
    ).all()

    stmt = select(FoodItem)
    if kw:
        stmt = stmt.where(
            or_(
                FoodItem.name.contains(kw),
                FoodItem.pinyin.contains(kw.lower()),
                FoodItem.initial.contains(kw.lower()),
            )
        )
    if category:
        stmt = stmt.where(FoodItem.category == category)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(FoodItem.sort_weight.desc(), FoodItem.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    merged = [_food_out(c, True) for c in customs] + [_food_out(i) for i in items]
    return Page(items=merged, total=total + len(customs), page=page, size=size)


@router.get("/foods/categories", response_model=list[str], summary="食物分类")
def food_categories(db: Session = Depends(get_db)):
    rows = db.scalars(select(FoodItem.category).distinct().order_by(FoodItem.category)).all()
    return list(rows)


@router.post("/foods/custom", response_model=FoodOut, summary="新增自定义食物")
def add_custom_food(
    body: CustomFoodIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food = CustomFood(user_id=user.id, **body.model_dump())
    db.add(food)
    db.commit()
    db.refresh(food)
    return _food_out(food, True)


@router.get("/foods/custom", response_model=list[FoodOut], summary="我的自定义食物")
def list_custom_food(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    rows = db.scalars(
        select(CustomFood)
        .where(CustomFood.user_id == user.id)
        .order_by(CustomFood.id.desc())
    ).all()
    return [_food_out(r, True) for r in rows]


@router.delete("/foods/custom/{food_id}", summary="删除自定义食物")
def delete_custom_food(
    food_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food = db.get(CustomFood, food_id)
    if food is None or food.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    db.delete(food)
    db.commit()
    return {"ok": True}


@router.get("/exercises", response_model=list[ExerciseItemOut], summary="搜索运动项")
def search_exercises(
    keyword: str = Query(default="", max_length=32),
    category: str = Query(default=""),
    db: Session = Depends(get_db),
):
    stmt = select(ExerciseItem)
    kw = keyword.strip()
    if kw:
        stmt = stmt.where(
            or_(
                ExerciseItem.name.contains(kw),
                ExerciseItem.pinyin.contains(kw.lower()),
                ExerciseItem.initial.contains(kw.lower()),
            )
        )
    if category:
        stmt = stmt.where(ExerciseItem.category == category)
    rows = db.scalars(
        stmt.order_by(ExerciseItem.sort_weight.desc(), ExerciseItem.id).limit(100)
    ).all()
    return [ExerciseItemOut.model_validate(r) for r in rows]
