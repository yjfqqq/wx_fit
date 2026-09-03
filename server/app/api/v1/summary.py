"""首页与月历所需的每日汇总"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.record import DailySummary, MealRecord
from app.models.user import Goal, User, UserProfile
from app.schemas.record import CalendarDay, SummaryOut
from app.services.calc import calc_age, calc_bmr, calc_daily_budget, calc_tdee
from app.services.summary import recalc_daily_summary

router = APIRouter(prefix="/summary", tags=["汇总"])


def _daily_budget(db: Session, user_id: int, weight_kg: float | None) -> float | None:
    """按当前体重实时算预算，不落库，资料一改立刻生效"""
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    goal = db.scalar(select(Goal).where(Goal.user_id == user_id))
    if profile is None or profile.height_cm is None or weight_kg is None:
        return None
    age = calc_age(profile.birthday)
    if age is None:
        return None
    bmr = calc_bmr(profile.gender, weight_kg, float(profile.height_cm), age)
    tdee = calc_tdee(bmr, profile.activity_level)
    deficit = goal.daily_deficit if goal else 500
    return calc_daily_budget(tdee, deficit, profile.gender, bmr)


def _latest_weight(db: Session, user_id: int, before: date | None = None) -> float | None:
    from app.models.record import WeightRecord

    stmt = (
        select(WeightRecord.weight_kg)
        .where(WeightRecord.user_id == user_id)
    )
    if before:
        stmt = stmt.where(WeightRecord.record_date <= before)
    row = db.scalar(
        stmt.order_by(WeightRecord.record_date.desc(), WeightRecord.id.desc()).limit(1)
    )
    return float(row) if row is not None else None


@router.get("", response_model=SummaryOut, summary="某日总览")
def daily_summary(
    date_: date = Query(default=None, alias="date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    day = date_ or date.today()
    summary = db.scalar(
        select(DailySummary).where(
            DailySummary.user_id == user.id, DailySummary.summary_date == day
        )
    )
    if summary is None:
        # 汇总缺失（比如建号后没写过）时现场算一次
        summary = recalc_daily_summary(db, user.id, day)
        db.commit()

    weight = summary.weight_kg or _latest_weight(db, user.id, day)
    budget = _daily_budget(db, user.id, weight)

    unknown_count = (
        db.scalar(
            select(func.count())
            .select_from(MealRecord)
            .where(
                MealRecord.user_id == user.id,
                MealRecord.record_date == day,
                MealRecord.calories.is_(None),
            )
        )
        or 0
    )

    intake = float(summary.intake_kcal)
    burn = float(summary.burn_kcal)
    return SummaryOut(
        date=day,
        intake_kcal=intake,
        burn_kcal=burn,
        net_kcal=round(intake - burn, 1),
        budget_kcal=budget,
        remaining_kcal=round(budget - intake, 1) if budget else None,
        weight_kg=weight,
        protein=float(summary.protein),
        fat=float(summary.fat),
        carbs=float(summary.carbs),
        meal_count=summary.meal_count,
        exercise_count=summary.exercise_count,
        unknown_calorie_count=unknown_count,
    )


@router.get("/calendar", response_model=list[CalendarDay], summary="月历打卡情况")
def calendar(
    month: str = Query(default="", description="YYYY-MM，留空则取当月"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if month:
        year, mon = (int(x) for x in month.split("-"))
    else:
        today = date.today()
        year, mon = today.year, today.month

    start = date(year, mon, 1)
    end = date(year + (mon == 12), (mon % 12) + 1, 1)

    rows = db.scalars(
        select(DailySummary).where(
            DailySummary.user_id == user.id,
            DailySummary.summary_date >= start,
            DailySummary.summary_date < end,
        )
    ).all()
    by_date = {r.summary_date: r for r in rows}

    out = []
    cur = start
    while cur < end:
        s = by_date.get(cur)
        out.append(
            CalendarDay(
                date=cur,
                has_weight=bool(s and s.weight_kg is not None),
                has_meal=bool(s and s.meal_count > 0),
                has_exercise=bool(s and s.exercise_count > 0),
            )
        )
        cur += timedelta(days=1)
    return out
