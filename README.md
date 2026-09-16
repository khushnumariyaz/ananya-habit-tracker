# Ananya's 75-Day Habit Tracker

A small, multi-user habit tracker for daily and weekday-based routines. The app provides a morning checklist, one-click completion logging, current and best streaks, pending reminders, history, search, and reversible archiving.

## Project structure

```text
backend/
	app/
		main.py              FastAPI application and static frontend serving
		models/              SQLAlchemy persistence models
		routes/              users, habits, completions, and today endpoints
		services/streak.py   Scheduled-day streak calculation
		schemas/             Pydantic request and response models
	tests/                 API acceptance tests
frontend/
	index.html             Landing, auth, dashboard, history, and manage views
	app.js                 Frontend state and API interactions
	styles.css             Responsive application styling
```

## Requirements

- Python 3.11 or newer
- SQLite (included with Python)
- A modern browser

## Setup and run

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the app at `http://127.0.0.1:8000`. The API explorer is available at `http://127.0.0.1:8000/docs`.

The local SQLite database is created at `backend/habit_tracker.db`. Existing local databases are migrated on startup to add habit ownership and the default user account.

## User flow

1. Create an account or log in from the landing page.
2. Open Today to see only habits scheduled for the selected date.
3. Tick habits as they are completed. The current and best streak values refresh automatically.
4. Use the reminder copy at the top of Today to see how many scheduled habits remain incomplete.
5. Use History for recent check-ins and Manage habits for search, updates, archive, and restore.

The current demo authentication uses a user name and the `X-User-ID` header internally. It is suitable for the local challenge app, but should be replaced with password or token authentication before production deployment.

## API reference

User ownership is selected with `X-User-ID`; the header defaults to user `1` for the local dashboard.

- `POST /api/users` creates a user.
- `GET /api/users` lists users for the local login screen.
- `POST /api/habits` creates a daily or custom weekday habit.
- `GET /api/habits?archived=false&q=read` lists or searches the current user's habits.
- `GET /api/habits/{id}` retrieves one habit owned by the current user.
- `PUT /api/habits/{id}` updates a habit and its schedule.
- `PATCH /api/habits/{id}/archive` and `/restore` hide or restore a habit without deleting it.
- `GET /api/today?date=YYYY-MM-DD` returns scheduled habits, completion state, streaks, and a pending reminder.
- `POST /api/completions` logs a scheduled habit for a date. Repeating the request is idempotent.
- `DELETE /api/completions/{habit_id}?date=YYYY-MM-DD` unchecks a logged habit.
- `GET /api/completions/{habit_id}` returns completion history with optional `from` and `to` filters.

Weekdays use Python's convention: Monday is `0` and Sunday is `6`.

## Tests

```bash
cd backend
python -m pytest -q
```

The acceptance suite covers daily and custom schedules, date validation, reminders, completion idempotency, unchecking, streak breaks and best streaks, end dates, archive/restore, search and updates, and cross-user isolation.

## Debugging

Check that the API is alive:

```bash
curl http://127.0.0.1:8000/health
```

Check the current user's Today payload:

```bash
curl -H 'X-User-ID: 1' \\
	'http://127.0.0.1:8000/api/today?date=2026-09-16'
```

If port `8000` is already in use, either use the existing healthy server or start another one:

```bash
uvicorn app.main:app --reload --port 8001
```

For frontend issues, open the browser developer console and verify that `/static/app.js`, `/static/styles.css`, and the relevant `/api/...` request return successfully. Clear `localStorage` key `day-by-day-user` to return to the login screen.
