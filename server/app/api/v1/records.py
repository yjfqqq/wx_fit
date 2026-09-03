"""三类记录的增删改查。所有写操作都会触发当日汇总重算。"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.food import ExerciseItem, FoodItem
from app.models.record import ExerciseRecord, MealRecord, WeightRecord
from app.models.user import User, UserProfile
from app.schemas.record import (
    ExerciseIn,
    ExerciseOut,
    MealIn,
    MealOut,
    WeightIn,
    WeightOut,
)
from app.services.calc import estimate_exercise_calories
from app.services.summary import recalc_daily_summary

router = APIRouter(prefix="/records", tags=["记录"])


def _weight_kg_for_calc(db: Session, user_id: int) -> float:
    """算运动消耗需要一个体重值：优先当天，其次最近一次，最后兜底 60kg"""
    row = db.scalar(
        select(WeightRecord.weight_kg)
        .where(WeightRecord.user_id == user_id)
        .order_by(WeightRecord.record_date.desc(), WeightRecord.id.desc())
        .limit(1)
    )
    return float(row) if row else 60.0


# ------------------------------ 体重 ------------------------------


@router.post("/weight", response_model=WeightOut, summary="记录体重")
def add_weight(
    body: WeightIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 同一天只保留一条，重复记录视为覆盖
    rec = db.scalar(
        select(WeightRecord).where(
            WeightRecord.user_id == user.id,
            WeightRecord.record_date == body.record_date,
        )
    )
    if rec is None:
        rec = WeightRecord(user_id=user.id, record_date=body.record_date)
        db.add(rec)
    rec.record_date = body.record_date
    rec.weight_kg = body.weight_kg
    rec.body_fat = body.body_fat
    rec.waist_cm = body.waist_cm
    rec.note = body.note
    db.commit()
    recalc_daily_summary(db, user.id, body.record_date)
    db.commit()
    db.refresh(rec)
    return WeightOut.model_validate(rec)


@router.get("/weight", response_model=list[WeightOut], summary="体重列表")
def list_weight(
    start: date = Query(default=None),
    end: date = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    end = end or date.today()
    start = start or (end - timedelta(days=89))
    rows = db.scalars(
        select(WeightRecord)
        .where(
            WeightRecord.user_id == user.id,
            WeightRecord.record_date >= start,
            WeightRecord.record_date <= end,
        )
        .order_by(WeightRecord.record_date)
    ).all()
    return [WeightOut.model_validate(r) for r in rows]


@router.delete("/weight/{record_id}", summary="删除体重记录")
def delete_weight(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = db.get(WeightRecord, record_id)
    if rec is None or rec.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    day = rec.record_date
    db.delete(rec)
    db.commit()
    recalc_daily_summary(db, user.id, day)
    db.commit()
    return {"ok": True}


# ------------------------------ 饮食 ------------------------------


@router.post("/meal", response_model=MealOut, summary="记录饮食")
def add_meal(
    body: MealIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = MealRecord(
        user_id=user.id,
        record_date=body.record_date,
        meal_type=body.meal_type,
        title=body.title,
        note=body.note,
    )

    if body.food_id and body.amount_g:
        food = db.get(FoodItem, body.food_id)
        if food is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "食物不存在")
        rec.food_id = food.id
        rec.amount_g = body.amount_g
        if not rec.title:
            rec.title = food.name
        ratio = body.amount_g / 100.0
        rec.calories = round(float(food.calories_per_100g) * ratio, 1)
        rec.protein = round(float(food.protein) * ratio, 1)
        rec.fat = round(float(food.fat) * ratio, 1)
        rec.carbs = round(float(food.carbs) * ratio, 1)

    db.add(rec)
    db.commit()
    recalc_daily_summary(db, user.id, body.record_date)
    db.commit()
    db.refresh(rec)
    return MealOut.model_validate(rec)


@router.get("/meal", response_model=list[MealOut], summary="某日饮食列表")
def list_meal(
    date_: date = Query(default=None, alias="date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    day = date_ or date.today()
    rows = db.scalars(
        select(MealRecord)
        .where(MealRecord.user_id == user.id, MealRecord.record_date == day)
        .order_by(MealRecord.meal_type, MealRecord.id)
    ).all()
    return [MealOut.model_validate(r) for r in rows]


@router.delete("/meal/{record_id}", summary="删除饮食记录")
def delete_meal(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = db.get(MealRecord, record_id)
    if rec is None or rec.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    day = rec.record_date
    db.delete(rec)
    db.commit()
    recalc_daily_summary(db, user.id, day)
    db.commit()
    return {"ok": True}


# ------------------------------ 运动 ------------------------------


@router.post("/exercise", response_model=ExerciseOut, summary="记录运动")
def add_exercise(
    body: ExerciseIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = ExerciseRecord(
        user_id=user.id,
        record_date=body.record_date,
        item_id=body.item_id,
        name=body.name,
        duration_min=body.duration_min,
        intensity=body.intensity,
        steps=body.steps,
        note=body.note,
    )

    met = None
    if body.item_id:
        item = db.get(ExerciseItem, body.item_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "运动项不存在")
        met = float(item.met_value)
        if not rec.name:
            rec.name = item.name

    if met and body.duration_min:
        weight = _weight_kg_for_calc(db, user.id)
        rec.calories = estimate_exercise_calories(met, weight, body.duration_min)

    db.add(rec)
    db.commit()
    recalc_daily_summary(db, user.id, body.record_date)
    db.commit()
    db.refresh(rec)
    return ExerciseOut.model_validate(rec)


@router.get("/exercise", response_model=list[ExerciseOut], summary="某日运动列表")
def list_exercise(
    date_: date = Query(default=None, alias="date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    day = date_ or date.today()
    rows = db.scalars(
        select(ExerciseRecord)
        .where(ExerciseRecord.user_id == user.id, ExerciseRecord.record_date == day)
        .order_by(ExerciseRecord.id)
    ).all()
    return [ExerciseOut.model_validate(r) for r in rows]


@router.delete("/exercise/{record_id}", summary="删除运动记录")
def delete_exercise(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = db.get(ExerciseRecord, record_id)
    if rec is None or rec.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    day = rec.record_date
    db.delete(rec)
    db.commit()
    recalc_daily_summary(db, user.id, day)
    db.commit()
    return {"ok": True}
