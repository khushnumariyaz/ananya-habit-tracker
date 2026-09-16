from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_user_id
from app.database import get_db
from app.models import Habit, HabitCompletion
from app.schemas.completion import CompletionCreate, CompletionResponse
from app.services.streak import scheduled_dates


router = APIRouter(prefix="/api/completions", tags=["Completions"])


def get_habit_or_404(habit_id: int, user_id: int, db: Session) -> Habit:
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user_id,
    ).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.post("", response_model=CompletionResponse, status_code=status.HTTP_201_CREATED)
def complete_habit(
    data: CompletionCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    habit = get_habit_or_404(data.habit_id, user_id, db)
    if habit.archived:
        raise HTTPException(status_code=400, detail="Archived habits cannot be logged")
    if data.date not in scheduled_dates(habit, data.date):
        raise HTTPException(status_code=400, detail="Habit is not scheduled for this date")

    completion = (
        db.query(HabitCompletion)
        .filter(
            HabitCompletion.habit_id == data.habit_id,
            HabitCompletion.date == data.date,
        )
        .first()
    )
    if completion is None:
        completion = HabitCompletion(habit_id=data.habit_id, date=data.date)
        db.add(completion)
        db.commit()
        db.refresh(completion)
    return completion


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def uncomplete_habit(
    habit_id: int,
    completion_date: date = Query(alias="date"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    get_habit_or_404(habit_id, user_id, db)
    completion = (
        db.query(HabitCompletion)
        .filter(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.date == completion_date,
        )
        .first()
    )
    if completion is None:
        raise HTTPException(status_code=404, detail="Completion not found")
    db.delete(completion)
    db.commit()


@router.get("/{habit_id}", response_model=list[CompletionResponse])
def get_completions(
    habit_id: int,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    get_habit_or_404(habit_id, user_id, db)
    query = db.query(HabitCompletion).filter(HabitCompletion.habit_id == habit_id)
    if from_date:
        query = query.filter(HabitCompletion.date >= from_date)
    if to_date:
        query = query.filter(HabitCompletion.date <= to_date)
    return query.order_by(HabitCompletion.date.desc()).all()