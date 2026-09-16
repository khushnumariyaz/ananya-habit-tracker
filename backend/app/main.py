from fastapi import FastAPI

from app.database import Base, engine
from app.models import Habit, HabitSchedule, HabitCompletion

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ananya's Habit Tracker",
    description="A habit tracking API with scheduling and streaks.",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Ananya's Habit Tracker API is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }