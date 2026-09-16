from datetime import date
from pydantic import BaseModel, Field, field_validator


class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    frequency_type: str = "daily"
    start_date: date
    end_date: date | None = None
    days_of_week: list[int] | None = None

    @field_validator("frequency_type")
    @classmethod
    def validate_frequency_type(cls, value: str) -> str:
        allowed = {"daily", "custom"}

        if value not in allowed:
            raise ValueError(
                "frequency_type must be 'daily' or 'custom'"
            )

        return value

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(
        cls,
        value: list[int] | None
    ) -> list[int] | None:

        if value is None:
            return value

        if len(value) == 0:
            raise ValueError(
                "days_of_week cannot be empty"
            )

        if any(day < 0 or day > 6 for day in value):
            raise ValueError(
                "days_of_week must contain values from 0 to 6"
            )

        if len(set(value)) != len(value):
            raise ValueError(
                "days_of_week cannot contain duplicates"
            )

        return value


class HabitUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    description: str | None = None

    frequency_type: str | None = None

    start_date: date | None = None

    end_date: date | None = None

    days_of_week: list[int] | None = None

    @field_validator("frequency_type")
    @classmethod
    def validate_frequency_type(cls, value: str | None) -> str | None:
        if value is None:
            return value

        allowed = {"daily", "custom"}

        if value not in allowed:
            raise ValueError(
                "frequency_type must be 'daily' or 'custom'"
            )

        return value

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(
        cls,
        value: list[int] | None
    ) -> list[int] | None:

        if value is None:
            return value

        if len(value) == 0:
            raise ValueError(
                "days_of_week cannot be empty"
            )

        if any(day < 0 or day > 6 for day in value):
            raise ValueError(
                "days_of_week must contain values from 0 to 6"
            )

        if len(set(value)) != len(value):
            raise ValueError(
                "days_of_week cannot contain duplicates"
            )

        return value


class HabitResponse(BaseModel):
    id: int
    name: str
    description: str | None
    frequency_type: str
    start_date: date
    end_date: date | None
    archived: bool
    days_of_week: list[int]

    class Config:
        from_attributes = True