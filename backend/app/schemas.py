from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8)
    state: str = "CA"  # where the player lives; their default Dex

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
    state: str
    created_at: datetime


class UserUpdate(BaseModel):
    state: str


class StateOut(BaseModel):
    code: str
    name: str
    species_count: int
    # Map extent in degrees: {"west", "east", "south", "north"}
    bounds: dict


class SpeciesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slug: str
    common_name: str
    scientific_name: str
    category: str
    rarity: str


class DexOut(BaseModel):
    species: SpeciesOut
    size: str | None = None
    weight: str | None = None
    fun_fact: str | None = None
    where_to_find: str | None = None
    active_time: str | None = None
    spotting_tip: str | None = None
    # "none", "caution" or "danger"; safe_distance and safety_note are shown on the entry.
    safety: str = "none"
    safe_distance: str | None = None
    safety_note: str | None = None
    hotspots: list[str] = []
    # {"grid": {lon0, lat0, step, cols, rows}, "cells": [[col, row, count], ...]}
    range: dict | None = None


class HotspotSpecies(BaseModel):
    slug: str
    common_name: str
    rarity: str
    observations: int


class HotspotOut(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    blurb: str
    species: list[HotspotSpecies]


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
    state: str
    caught: int
    total: int
    entries: list[CollectionEntry]
