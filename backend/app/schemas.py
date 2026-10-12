from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, v: str) -> str:
        if len(v.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    username: str
    created_at: datetime


class SpeciesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slug: str
    common_name: str
    scientific_name: str
    category: str
    rarity: str


class PredictionOut(BaseModel):
    label: str
    common_name: str | None
    probability: float


class CaptureOut(BaseModel):
    capture_id: int
    matched: bool
    species: SpeciesOut | None
    confidence: float
    new_badge: bool
    message: str
    top_predictions: list[PredictionOut]


class CollectionEntry(BaseModel):
    species: SpeciesOut
    caught: bool
    capture_count: int = 0
    earned_at: datetime | None = None


class CollectionOut(BaseModel):
    caught: int
    total: int
    entries: list[CollectionEntry]
