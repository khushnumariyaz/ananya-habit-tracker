from datetime import date, datetime

from pydantic import BaseModel


class CompletionCreate(BaseModel):
    habit_id: int
    date: date


class CompletionResponse(BaseModel):
    id: int
    habit_id: int
    date: date
    completed_at: datetime

    model_config = {"from_attributes": True}


class StreakResponse(BaseModel):
    current_streak: int
    best_streak: int


class TodayHabitResponse(BaseModel):
    id: int
    name: str
    description: str | None
    frequency_type: str
    start_date: date
    end_date: date | None
    completed: bool
    completed_at: datetime | None
    current_streak: int
    best_streak: int


class TodayResponse(BaseModel):
    date: date
    habits: list[TodayHabitResponse]
    pending_count: int
    reminder: str | None