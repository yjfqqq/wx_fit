"""每日汇总重算。

所有记录的增/删/改都必须调用 recalc_daily_summary，
否则首页和趋势页读到的汇总数据会和明细对不上。
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.record import DailySummary, ExerciseRecord, MealRecord, WeightRecord


def _f(v) -> float:
    return float(v) if v is not None else 0.0


def recalc_daily_summary(db: Session, user_id: int, day: date) -> DailySummary:
    meals = db.scalars(
        select(MealRecord).where(
            MealRecord.user_id == user_id, MealRecord.record_date == day
        )
    ).all()
    exercises = db.scalars(
        select(ExerciseRecord).where(
            ExerciseRecord.user_id == user_id, ExerciseRecord.record_date == day
        )
    ).all()

    # 同一天可能记多次体重，取最新一条（id 最大）
    latest_weight = db.scalar(
        select(WeightRecord.weight_kg)
        .where(WeightRecord.user_id == user_id, WeightRecord.record_date == day)
        .order_by(WeightRecord.id.desc())
        .limit(1)
    )

    summary = db.scalar(
        select(DailySummary).where(
            DailySummary.user_id == user_id, DailySummary.summary_date == day
        )
    )
    if summary is None:
        summary = DailySummary(user_id=user_id, summary_date=day)
        db.add(summary)

    summary.intake_kcal = round(sum(_f(m.calories) for m in meals), 1)
    summary.protein = round(sum(_f(m.protein) for m in meals), 1)
    summary.fat = round(sum(_f(m.fat) for m in meals), 1)
    summary.carbs = round(sum(_f(m.carbs) for m in meals), 1)
    summary.meal_count = len(meals)
    summary.burn_kcal = round(sum(_f(e.calories) for e in exercises), 1)
    summary.exercise_count = len(exercises)
    summary.weight_kg = float(latest_weight) if latest_weight is not None else None

    db.flush()
    return summary


def get_summary(db: Session, user_id: int, day: date) -> DailySummary | None:
    return db.scalar(
        select(DailySummary).where(
            DailySummary.user_id == user_id, DailySummary.summary_date == day
        )
    )


def get_weight_series(
    db: Session, user_id: int, start: date, end: date
) -> list[tuple[date, float]]:
    """返回 (日期, 当日最后一条体重) 序列，按日期升序"""
    rows = db.execute(
        select(WeightRecord.record_date, func.max(WeightRecord.id))
        .where(
            WeightRecord.user_id == user_id,
            WeightRecord.record_date >= start,
            WeightRecord.record_date <= end,
        )
        .group_by(WeightRecord.record_date)
        .order_by(WeightRecord.record_date)
    ).all()
    out = []
    for record_date, max_id in rows:
        w = db.scalar(select(WeightRecord.weight_kg).where(WeightRecord.id == max_id))
        if w is not None:
            out.append((record_date, float(w)))
    return out
