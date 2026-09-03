"""初始化数据库：建库 → 建表 → 导入食物库与运动库种子数据。

用法：
    cd server
    python scripts/init_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pymysql  # noqa: E402
from sqlalchemy import inspect  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.db.seed_data import (  # noqa: E402
    COMMON_UNITS,
    EXERCISES,
    FOODS,
    POPULAR_EXERCISES,
    POPULAR_FOODS,
)
from app.models import ExerciseItem, FoodItem  # noqa: E402


def create_database_if_missing() -> None:
    if settings.DB_ENGINE.lower() != "mysql":
        print(f"[skip] DB_ENGINE={settings.DB_ENGINE}，跳过建库（SQLite 会自动建文件）")
        return

    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        print(f"[ok] 数据库 `{settings.DB_NAME}` 已就绪")
    finally:
        conn.close()


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    names = sorted(inspect(engine).get_table_names())
    print(f"[ok] 已建 {len(names)} 张表：{', '.join(names)}")


def seed_foods(db) -> int:
    exist = db.query(FoodItem).count()
    if exist:
        print(f"[skip] 食物库已有 {exist} 条，跳过导入")
        return 0

    rows = []
    for name, pinyin, initial, category, cal, protein, fat, carbs in FOODS:
        unit, weight = COMMON_UNITS.get(name, ("份", 100))
        rows.append(
            FoodItem(
                name=name,
                pinyin=pinyin,
                initial=initial,
                category=category,
                calories_per_100g=cal,
                protein=protein,
                fat=fat,
                carbs=carbs,
                common_unit=unit,
                unit_weight_g=weight,
                sort_weight=90 if name in POPULAR_FOODS else 20,
            )
        )
    db.add_all(rows)
    db.commit()
    print(f"[ok] 导入 {len(rows)} 条食物")
    return len(rows)


def seed_exercises(db) -> int:
    exist = db.query(ExerciseItem).count()
    if exist:
        print(f"[skip] 运动库已有 {exist} 条，跳过导入")
        return 0

    rows = []
    for name, pinyin, initial, category, met in EXERCISES:
        rows.append(
            ExerciseItem(
                name=name,
                pinyin=pinyin,
                initial=initial,
                category=category,
                met_value=met,
                sort_weight=90 if name in POPULAR_EXERCISES else 20,
            )
        )
    db.add_all(rows)
    db.commit()
    print(f"[ok] 导入 {len(rows)} 条运动")
    return len(rows)


def main() -> None:
    print(f"目标数据库：{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    create_database_if_missing()
    create_tables()
    db = SessionLocal()
    try:
        seed_foods(db)
        seed_exercises(db)
    finally:
        db.close()
    print("\n初始化完成。接下来运行：uvicorn app.main:app --reload --port 8000")


if __name__ == "__main__":
    main()
