from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.database import Base, engine
from app.models import Habit, HabitSchedule, HabitCompletion
from app.routes.habits import router as habits_router
from app.routes.completions import router as completions_router
from app.routes.today import router as today_router
from app.routes.users import router as users_router


Base.metadata.create_all(bind=engine)

# Keep the existing local SQLite database usable after adding user ownership.
if "habits" in inspect(engine).get_table_names():
    habit_columns = {
        column["name"] for column in inspect(engine).get_columns("habits")
    }
    if "user_id" not in habit_columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE habits ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
            )

with engine.begin() as connection:
    connection.execute(
        text(
            "INSERT INTO users (id, name, created_at) "
            "SELECT 1, 'Ananya', CURRENT_TIMESTAMP "
            "WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = 1)"
        )
    )


app = FastAPI(
    title="Ananya's Habit Tracker",
    description="A habit tracking API with scheduling and streaks.",
    version="1.0.0"
)


app.include_router(habits_router)
app.include_router(completions_router)
app.include_router(today_router)
app.include_router(users_router)

frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def root():
    return FileResponse(frontend_dir / "index.html")


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }