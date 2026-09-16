from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_user_id
from app.database import get_db
from app.models import Habit
from app.schemas.completion import TodayHabitResponse, TodayResponse
from app.services.streak import calculate_streaks


router = APIRouter(prefix="/api/today", tags=["Today"])


@router.get("", response_model=TodayResponse)
def get_today(
    today: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    target_date = today or date.today()
    habits = (
        db.query(Habit)
        .filter(
            Habit.user_id == user_id,
            Habit.archived.is_(False),
            Habit.start_date <= target_date,
        )
        .order_by(Habit.created_at.asc())
        .all()
    )
    result: list[TodayHabitResponse] = []
    for habit in habits:
        if habit.end_date and target_date > habit.end_date:
            continue
        if target_date.weekday() not in {item.day_of_week for item in habit.schedules}:
            continue
        completion = next(
            (item for item in habit.completions if item.date == target_date),
            None,
        )
        current, best = calculate_streaks(
            habit,
            {item.date for item in habit.completions},
            target_date,
        )
        result.append(
            TodayHabitResponse(
                id=habit.id,
                name=habit.name,
                description=habit.description,
                frequency_type=habit.frequency_type,
                start_date=habit.start_date,
                end_date=habit.end_date,
                completed=completion is not None,
                completed_at=completion.completed_at if completion else None,
                current_streak=current,
                best_streak=best,
            )
        )
    pending_count = sum(not habit.completed for habit in result)
    return TodayResponse(
        date=target_date,
        habits=result,
        pending_count=pending_count,
        reminder=(
            f"You have {pending_count} habit{'s' if pending_count != 1 else ''} left to log today."
            if pending_count
            else None
        ),
    )