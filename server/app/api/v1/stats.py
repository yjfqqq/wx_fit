"""趋势页数据与本地规则分析"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.record import DailySummary
from app.models.user import Goal, User, UserProfile
from app.schemas.record import CaloriePoint, OverviewOut, WeightPoint, WeightStatsOut
from app.services.calc import (
    calc_age,
    calc_bmi,
    calc_bmr,
    calc_daily_budget,
    calc_progress,
    calc_tdee,
    moving_average,
    predict_goal_date,
    weekly_change_rate,
)
from app.services.summary import get_weight_series
from app.schemas.auth import PlanOut

router = APIRouter(prefix="/stats", tags=["统计"])


def _profile_map(db: Session, user_id: int) -> tuple[UserProfile | None, Goal | None]:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    goal = db.scalar(select(Goal).where(Goal.user_id == user_id))
    return profile, goal


@router.get("/weight", response_model=WeightStatsOut, summary="体重趋势与移动平均")
def weight_stats(
    days: int = Query(default=30, ge=7, le=365),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    end = date.today()
    start = end - timedelta(days=days - 1)
    pairs = get_weight_series(db, user.id, start, end)
    by_date = dict(pairs)

    # 生成连续日期轴，没有记录的日期 weight 为 None
    axis = [start + timedelta(days=i) for i in range(days)]
    values = [by_date.get(d) for d in axis]
    avgs = moving_average(values, window=7)

    points = []
    for d, v, a in zip(axis, values, avgs):
        if v is None:
            continue
        points.append(WeightPoint(date=d, weight=v, avg7=a))

    total_change = None
    real = [w for _, w in pairs]
    if len(real) >= 2:
        total_change = round(real[-1] - real[0], 2)

    return WeightStatsOut(
        points=points,
        total_change=total_change,
        weekly_rate=weekly_change_rate(pairs),
    )


@router.get("/calories", response_model=list[CaloriePoint], summary="热量收支序列")
def calorie_stats(
    days: int = Query(default=30, ge=7, le=365),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    end = date.today()
    start = end - timedelta(days=days - 1)
    rows = db.scalars(
        select(DailySummary)
        .where(
            DailySummary.user_id == user.id,
            DailySummary.summary_date >= start,
            DailySummary.summary_date <= end,
        )
        .order_by(DailySummary.summary_date)
    ).all()
    by_date = {r.summary_date: r for r in rows}

    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        s = by_date.get(d)
        out.append(
            CaloriePoint(
                date=d,
                intake=float(s.intake_kcal) if s else 0.0,
                burn=float(s.burn_kcal) if s else 0.0,
            )
        )
    return out


@router.get("/overview", response_model=OverviewOut, summary="总体概览")
def overview(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    profile, goal = _profile_map(db, user.id)
    end = date.today()
    pairs = get_weight_series(db, user.id, end - timedelta(days=365), end)
    current = pairs[-1][1] if pairs else None

    start_weight = float(goal.start_weight) if goal and goal.start_weight else None
    if start_weight is None and pairs:
        start_weight = pairs[0][1]

    total_lost = None
    if start_weight is not None and current is not None:
        total_lost = round(start_weight - current, 2)

    streak = 0
    cur = end
    while True:
        s = db.scalar(
            select(DailySummary).where(
                DailySummary.user_id == user.id, DailySummary.summary_date == cur
            )
        )
        if s and (s.meal_count or s.exercise_count or s.weight_kg is not None):
            streak += 1
            cur -= timedelta(days=1)
        else:
            break

    recorded_days = (
        db.scalar(
            select(func.count())
            .select_from(DailySummary)
            .where(DailySummary.user_id == user.id)
        )
        or 0
    )

    return OverviewOut(
        start_weight=start_weight,
        current_weight=current,
        target_weight=float(goal.target_weight) if goal and goal.target_weight else None,
        total_lost=total_lost,
        weekly_rate=weekly_change_rate(pairs),
        streak_days=streak,
        recorded_days=recorded_days,
    )


@router.get("/plan", response_model=PlanOut, summary="BMR / TDEE / 热量预算测算")
def plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile, goal = _profile_map(db, user.id)
    end = date.today()
    pairs = get_weight_series(db, user.id, end - timedelta(days=365), end)
    current = pairs[-1][1] if pairs else None

    bmr = tdee = budget = bmi = None
    bmi_level = None
    if profile and profile.height_cm and current and profile.birthday:
        age = calc_age(profile.birthday)
        bmr = calc_bmr(profile.gender, current, float(profile.height_cm), age)
        tdee = calc_tdee(bmr, profile.activity_level)
        deficit = goal.daily_deficit if goal else 500
        budget = calc_daily_budget(tdee, deficit, profile.gender, bmr)
        bmi, bmi_level = calc_bmi(current, float(profile.height_cm))

    rate = weekly_change_rate(pairs)
    progress = None
    if goal and goal.start_weight and current and goal.target_weight:
        progress = calc_progress(
            float(goal.start_weight), current, float(goal.target_weight)
        )

    predict = None
    if goal and goal.target_weight and current:
        predict = predict_goal_date(current, float(goal.target_weight), rate)

    return PlanOut(
        has_goal=bool(goal and goal.target_weight),
        bmr=round(bmr, 1) if bmr else None,
        tdee=round(tdee, 1) if tdee else None,
        daily_budget=budget,
        bmi=bmi,
        bmi_level=bmi_level,
        current_weight=current,
        progress=progress,
        weekly_rate=rate,
        predict_date=predict,
    )


@router.get("/analysis", summary="本地规则分析（不依赖 AI）")
def analysis(
    days: int = Query(default=30, ge=7, le=90),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """纯规则引擎输出洞察：评分、阶段判断、风险提醒、下一步建议"""
    end = date.today()
    start = end - timedelta(days=days - 1)
    pairs = get_weight_series(db, user.id, start, end)
    summaries = db.scalars(
        select(DailySummary).where(
            DailySummary.user_id == user.id,
            DailySummary.summary_date >= start,
            DailySummary.summary_date <= end,
        )
    ).all()

    profile, goal = _profile_map(db, user.id)
    current = pairs[-1][1] if pairs else None
    rate = weekly_change_rate(pairs)

    # 记录完整度：区间内有任意记录的天数占比
    active_days = sum(
        1 for s in summaries if (s.meal_count or s.exercise_count or s.weight_kg)
    )
    completeness = round(active_days / days, 2)

    # 热量达标率：摄入落在预算 ±10% 内的天数占比
    budget = None
    if profile and profile.height_cm and current and profile.birthday:
        age = calc_age(profile.birthday)
        bmr = calc_bmr(profile.gender, current, float(profile.height_cm), age)
        tdee = calc_tdee(bmr, profile.activity_level)
        budget = calc_daily_budget(
            tdee, goal.daily_deficit if goal else 500, profile.gender, bmr
        )

    hit_days = 0
    if budget:
        for s in summaries:
            intake = float(s.intake_kcal)
            if intake and abs(intake - budget) / budget <= 0.1:
                hit_days += 1
    hit_rate = round(hit_days / max(active_days, 1), 2)

    # 趋势方向
    if rate is None:
        stage, trend_score = "数据不足，再记几天看看", 50
    elif rate <= -0.8:
        stage, trend_score = "掉重偏快，注意别掉肌肉", 70
    elif rate <= -0.2:
        stage, trend_score = "稳步下降，节奏很健康", 95
    elif rate < 0.2:
        stage, trend_score = "进入平台期，属于正常波动", 65
    else:
        stage, trend_score = "体重在回升，该复盘一下饮食了", 40

    score = int(trend_score * 0.5 + completeness * 100 * 0.25 + hit_rate * 100 * 0.25)

    risks: list[str] = []
    if current and goal and goal.target_weight and budget:
        avg_intake = (
            sum(float(s.intake_kcal) for s in summaries) / active_days
            if active_days
            else 0
        )
        if avg_intake and avg_intake < 1200:
            risks.append(f"近 {days} 天日均摄入约 {avg_intake:.0f} 千卡，偏低，长期不利于代谢")
    if rate is not None and rate <= -1.0 and current:
        risks.append(f"每周约减 {abs(rate):.1f}kg，超过体重的 1%，建议放慢节奏")
    if active_days <= max(3, days // 4):
        risks.append(f"{days} 天里只记了 {active_days} 天，记录越完整，趋势越可信")
    if current and profile and profile.height_cm:
        bmi, level = calc_bmi(current, float(profile.height_cm))
        if bmi and bmi >= 24:
            risks.append(f"当前 BMI {bmi}，属于{level}区间，建议把目标拆成小台阶")

    tips: list[str] = []
    if goal and goal.target_weight and current:
        gap = current - float(goal.target_weight)
        if gap > 0:
            tips.append(f"距目标还差 {gap:.1f}kg，按每周 0.5kg 的节奏约需 {int(gap / 0.5)} 周")
        else:
            tips.append("已完成目标，接下来重点是维持，别急着放松")
    if budget:
        tips.append(f"建议每日摄入约 {budget:.0f} 千卡，先保证蛋白质再谈缺口")
    if completeness < 0.6:
        tips.append("先把「每天称一次体重」坚持下来，单点数据的价值很有限")
    else:
        tips.append("记录习惯已经养成了，接下来关注热量缺口是否稳定")

    return {
        "range_days": days,
        "score": score,
        "stage": stage,
        "risks": risks,
        "tips": tips,
        "metrics": {
            "record_days": active_days,
            "completeness": completeness,
            "budget_hit_rate": hit_rate,
            "weekly_rate": rate,
            "current_weight": current,
            "daily_budget": budget,
        },
        "source": "本地规则分析",
    }
