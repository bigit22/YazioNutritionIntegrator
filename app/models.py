from enum import StrEnum

from pydantic import BaseModel, Field


class MealType(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class NutritionResult(BaseModel):
    description: str = Field(min_length=2, max_length=120)
    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    fat: float = Field(ge=0)
    carbs: float = Field(ge=0)
    portion_grams: float | None = Field(default=None, ge=0)
    items: list[str] = Field(default_factory=list)
