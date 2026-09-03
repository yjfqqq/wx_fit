"""数据导出：按天导出 CSV，带 BOM 保证 Excel 打开中文不乱码"""

import csv
import io
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.record import DailySummary
from app.models.user import User

router = APIRouter(prefix="/export", tags=["导出"])


@router.get("/records.csv", summary="导出每日记录 CSV")
def export_records(
    days: int = Query(default=90, ge=7, le=365),
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

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "日期",
            "体重kg",
            "摄入千卡",
            "消耗千卡",
            "净千卡",
            "蛋白质g",
            "脂肪g",
            "碳水g",
            "饮食条数",
            "运动条数",
        ]
    )
    for r in rows:
        intake = float(r.intake_kcal)
        burn = float(r.burn_kcal)
        writer.writerow(
            [
                r.summary_date.isoformat(),
                r.weight_kg if r.weight_kg is not None else "",
                intake,
                burn,
                round(intake - burn, 1),
                float(r.protein),
                float(r.fat),
                float(r.carbs),
                r.meal_count,
                r.exercise_count,
            ]
        )

    buf.seek(0)
    content = "\ufeff" + buf.getvalue()
    filename = f"fit_records_{end.isoformat()}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
