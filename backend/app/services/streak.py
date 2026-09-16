from datetime import date, timedelta

from app.models import Habit


def scheduled_dates(habit: Habit, through: date) -> list[date]:
    """Return the habit's scheduled dates from its active range through a date."""
    last_date = min(through, habit.end_date) if habit.end_date else through
    if last_date < habit.start_date:
        return []

    schedule_days = {schedule.day_of_week for schedule in habit.schedules}
    current = habit.start_date
    dates: list[date] = []
    while current <= last_date:
        if current.weekday() in schedule_days:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def calculate_streaks(
    habit: Habit,
    completed_dates: set[date],
    as_of: date,
) -> tuple[int, int]:
    """Calculate current and best streaks across scheduled occurrences."""
    occurrences = scheduled_dates(habit, as_of)
    completed_occurrences = [day for day in occurrences if day in completed_dates]

    best = 0
    run = 0
    previous: date | None = None
    for occurrence in occurrences:
        if occurrence in completed_dates:
            run = run + 1 if previous and occurrence > previous else 1
            best = max(best, run)
            previous = occurrence
        else:
            run = 0
            previous = None

    if not completed_occurrences:
        return 0, best

    current = 0
    previous = completed_occurrences[-1]
    for occurrence in reversed(occurrences):
        if occurrence > previous:
            continue
        if occurrence not in completed_dates:
            break
        current += 1
        previous = occurrence

    return current, best