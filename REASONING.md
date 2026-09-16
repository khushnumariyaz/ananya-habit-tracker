## Solution rationale

### Start from the daily workflow

The most important action is logging a habit in the morning. The backend therefore exposes a date-specific `GET /api/today` response instead of making the frontend reconstruct schedules from raw database records. That response includes only active habits scheduled for the requested date, whether each is completed, the current and best streak, and the number of pending habits for the reminder.

### Model schedules explicitly

Daily habits are stored with all seven weekday values. Custom habits store only their selected weekday values. This keeps weekday filtering deterministic and makes future schedule types possible without encoding schedule rules in habit names or frontend code.

### Calculate streaks from scheduled occurrences

Streaks count completed scheduled occurrences rather than calendar dates. A Monday/Wednesday/Friday habit can therefore maintain a three-occurrence streak across the intervening unscheduled days. A missed scheduled occurrence breaks the current streak, while the best-ever streak remains unchanged.

### Make completion safe to repeat

The completion table has a unique constraint on `(habit_id, date)`. The API also checks for an existing record before inserting, so double-clicks and repeated network requests do not create duplicate check-ins. A delete endpoint supports correcting a mistaken check-off.

### Preserve habits through archiving

Archiving is a boolean state rather than deletion. Archived habits disappear from Today and active lists, but their schedules and completion history remain available and can be restored.

### Add ownership before expanding features

The original single-user implementation would have allowed every user to see every habit. Habits now belong to a user, and all habit, completion, search, archive, and Today queries filter by the active user. The local UI uses `X-User-ID` as a deliberately small authentication seam; a production application should replace it with a real session or token system.

### Keep the frontend deployable with the backend

The frontend is plain HTML, CSS, and JavaScript served by FastAPI. This avoids a second build server and CORS configuration while keeping the interaction model easy to inspect. The UI follows the product flow: landing page, sign up/log in, Today, completion and streak feedback, History/Progress, and Manage habits.

### Validate behavior with acceptance tests

The tests use an isolated in-memory SQLite database per test. They cover the user-visible requirements rather than only individual functions: schedules, pending reminders, idempotent logging, streak records, end dates, archive/restore, search/update, invalid data, and cross-user isolation. A final live smoke check verifies the server root, health endpoint, user initialization, and Today payload against the local database.

### Known production follow-ups

- Replace name-based login and `X-User-ID` with password or OAuth/session authentication.
- Add a real notification worker and delivery provider if reminders must arrive outside the open dashboard. The current implementation provides the morning reminder in the Today response and UI.
- Move startup schema migration to Alembic for a larger deployment.
- Store timezone preferences so “morning” and date boundaries match each user's location.
