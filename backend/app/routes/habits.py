from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_user_id
from app.database import get_db
from app.models import Habit, HabitSchedule
from app.schemas.habit import (
    HabitCreate,
    HabitResponse,
    HabitUpdate,
)

router = APIRouter(
    prefix="/api/habits",
    tags=["Habits"]
)


def get_schedule_days(
    habit: Habit
) -> list[int]:
    return sorted(
        schedule.day_of_week
        for schedule in habit.schedules
    )


def habit_to_response(
    habit: Habit
) -> HabitResponse:
    return HabitResponse(
        id=habit.id,
        name=habit.name,
        description=habit.description,
        frequency_type=habit.frequency_type,
        start_date=habit.start_date,
        end_date=habit.end_date,
        archived=habit.archived,
        days_of_week=get_schedule_days(habit),
    )


@router.post(
    "",
    response_model=HabitResponse,
    status_code=status.HTTP_201_CREATED
)
def create_habit(
    habit_data: HabitCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    if (
        habit_data.end_date is not None
        and habit_data.end_date < habit_data.start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="end_date cannot be before start_date"
        )

    if (
        habit_data.frequency_type == "custom"
        and habit_data.days_of_week is None
    ):
        raise HTTPException(
            status_code=400,
            detail="days_of_week is required for custom frequency"
        )

    habit = Habit(
        user_id=user_id,
        name=habit_data.name,
        description=habit_data.description,
        frequency_type=habit_data.frequency_type,
        start_date=habit_data.start_date,
        end_date=habit_data.end_date,
    )

    db.add(habit)
    db.flush()

    if habit_data.frequency_type == "daily":
        days = list(range(7))
    else:
        days = habit_data.days_of_week or []

    for day in days:
        schedule = HabitSchedule(
            habit_id=habit.id,
            day_of_week=day,
        )

        db.add(schedule)

    db.commit()
    db.refresh(habit)

    return habit_to_response(habit)


@router.get(
    "",
    response_model=list[HabitResponse]
)
def get_habits(
    archived: bool = False,
    q: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    query = db.query(Habit).filter(
        Habit.user_id == user_id,
        Habit.archived == archived,
    )
    if q:
        query = query.filter(Habit.name.ilike(f"%{q.strip()}%"))
    habits = query.order_by(Habit.created_at.desc()).all()

    return [
        habit_to_response(habit)
        for habit in habits
    ]


@router.get(
    "/{habit_id}",
    response_model=HabitResponse
)
def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == user_id)
        .first()
    )

    if habit is None:
        raise HTTPException(
            status_code=404,
            detail="Habit not found"
        )

    return habit_to_response(habit)


@router.put(
    "/{habit_id}",
    response_model=HabitResponse
)
def update_habit(
    habit_id: int,
    habit_data: HabitUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == user_id)
        .first()
    )

    if habit is None:
        raise HTTPException(
            status_code=404,
            detail="Habit not found"
        )

    update_data = habit_data.model_dump(
        exclude_unset=True
    )

    days_of_week = update_data.pop(
        "days_of_week",
        None
    )
    was_custom = habit.frequency_type == "custom"

    for field, value in update_data.items():
        setattr(habit, field, value)

    if (
        habit.end_date is not None
        and habit.end_date < habit.start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="end_date cannot be before start_date"
        )

    if (
        habit.frequency_type == "custom"
        and days_of_week is None
        and (not was_custom or len(habit.schedules) == 0)
    ):
        raise HTTPException(
            status_code=400,
            detail="days_of_week is required for custom frequency"
        )

    if habit.frequency_type == "daily":
        days = list(range(7))

    elif days_of_week is not None:
        days = days_of_week

    else:
        days = get_schedule_days(habit)

    if habit.frequency_type is not None or days_of_week is not None:
        habit.schedules.clear()

        for day in days:
            habit.schedules.append(
                HabitSchedule(
                    day_of_week=day
                )
            )

    db.commit()
    db.refresh(habit)

    return habit_to_response(habit)


@router.patch(
    "/{habit_id}/archive",
    response_model=HabitResponse
)
def archive_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == user_id)
        .first()
    )

    if habit is None:
        raise HTTPException(
            status_code=404,
            detail="Habit not found"
        )

    habit.archived = True

    db.commit()
    db.refresh(habit)

    return habit_to_response(habit)


@router.patch(
    "/{habit_id}/restore",
    response_model=HabitResponse
)
def restore_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == user_id)
        .first()
    )

    if habit is None:
        raise HTTPException(
            status_code=404,
            detail="Habit not found"
        )

    habit.archived = False

    db.commit()
    db.refresh(habit)

    return habit_to_response(habit)