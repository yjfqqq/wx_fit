"""核心算法：BMR / TDEE / 热量预算 / MET 消耗 / BMI / 趋势

所有函数都是纯函数，不依赖数据库，方便单独测试。
"""

from __future__ import annotations

from datetime import date

# 活动系数：1 久坐 2 轻度 3 中度 4 高度 5 极高
ACTIVITY_FACTORS = {1: 1.2, 2: 1.375, 3: 1.55, 4: 1.725, 5: 1.9}

# 热量摄入安全下限（千卡），低于此值不建议继续制造缺口
MIN_CALORIE_FLOOR = {1: 1500, 2: 1200}  # 男 / 女


def calc_age(birthday: date | None, today: date | None = None) -> int | None:
    if birthday is None:
        return None
    today = today or date.today()
    age = today.year - birthday.year
    if (today.month, today.day) < (birthday.month, birthday.day):
        age -= 1
    return max(age, 0)


def calc_bmr(
    gender: int, weight_kg: float, height_cm: float, age: int
) -> float | None:
    """Mifflin-St Jeor 公式。gender: 1 男 / 2 女"""
    weight_kg, height_cm = float(weight_kg), float(height_cm)
    if not weight_kg or not height_cm or age is None:
        return None
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender == 1 else base - 161


def calc_tdee(bmr: float | None, activity_level: int) -> float | None:
    if bmr is None:
        return None
    return float(bmr) * ACTIVITY_FACTORS.get(activity_level, 1.2)


def calc_daily_budget(
    tdee: float | None, deficit: int, gender: int, bmr: float | None
) -> float | None:
    """每日热量预算 = TDEE - 缺口，并施加安全下限"""
    if tdee is None:
        return None
    tdee = float(tdee)
    budget = tdee - deficit
    floor = MIN_CALORIE_FLOOR.get(gender, 1200)
    # 三个上限约束：不低于安全下限、不低于 BMR、不超过 TDEE
    budget = max(budget, float(floor))
    if bmr:
        budget = max(budget, float(bmr))
    budget = min(budget, tdee)
    return round(budget)


def estimate_exercise_calories(
    met: float, weight_kg: float, duration_min: int
) -> float:
    """运动消耗 = MET × 体重(kg) × 时长(小时)"""
    met, weight_kg = float(met), float(weight_kg)
    if not met or not weight_kg or not duration_min:
        return 0.0
    return round(met * weight_kg * (duration_min / 60.0), 1)


def calc_bmi(weight_kg: float, height_cm: float) -> tuple[float, str] | tuple[None, None]:
    """返回 (BMI 值, 中国标准分级)"""
    weight_kg, height_cm = float(weight_kg), float(height_cm)
    if not weight_kg or not height_cm:
        return None, None
    h = height_cm / 100
    bmi = round(weight_kg / (h * h), 1)
    if bmi < 18.5:
        level = "偏瘦"
    elif bmi < 24:
        level = "正常"
    elif bmi < 28:
        level = "超重"
    else:
        level = "肥胖"
    return bmi, level


def calc_progress(
    start_weight: float | None, current_weight: float | None, target_weight: float | None
) -> float | None:
    """目标完成度 0~1"""
    if not all([start_weight, current_weight, target_weight]):
        return None
    start_weight = float(start_weight)
    current_weight = float(current_weight)
    target_weight = float(target_weight)
    total = start_weight - target_weight
    if abs(total) < 0.01:
        return 1.0
    done = (start_weight - current_weight) / total
    return round(min(max(done, 0.0), 1.0), 3)


def moving_average(values: list[float | None], window: int = 7) -> list[float | None]:
    """移动平均，用于抹平每日水分波动。前 window-1 个点返回 None"""
    out: list[float | None] = []
    for i in range(len(values)):
        seg = [float(v) for v in values[max(0, i - window + 1) : i + 1] if v is not None]
        out.append(round(sum(seg) / len(seg), 2) if seg else None)
    return out


def weekly_change_rate(pairs: list[tuple[date, float]], days: int = 14) -> float | None:
    """近 N 天体重的周均变化（kg/周），用最小二乘斜率 × 7。
    返回负数表示在减重。"""
    pts = [(i, float(w)) for i, (_, w) in enumerate(pairs[-days:])]
    if len(pts) < 3:
        return None
    n = len(pts)
    mean_x = sum(p[0] for p in pts) / n
    mean_y = sum(p[1] for p in pts) / n
    num = sum((p[0] - mean_x) * (p[1] - mean_y) for p in pts)
    den = sum((p[0] - mean_x) ** 2 for p in pts)
    if den == 0:
        return None
    return round(num / den * 7, 3)


def predict_goal_date(
    current_weight: float, target_weight: float, weekly_rate: float | None
) -> date | None:
    """按近期周均减重速度推算达成日期。速率 <= 0（没在减）时不给预测"""
    if weekly_rate is None or weekly_rate <= 0:
        return None
    gap = float(current_weight) - float(target_weight)
    if gap <= 0:
        return date.today()
    from datetime import timedelta

    return date.today() + timedelta(days=int(gap / weekly_rate * 7))
