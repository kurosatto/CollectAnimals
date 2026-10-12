from datetime import date, datetime

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
    """A species card. Names (and slug, which spells the name) are None until
    the viewer or one of their friends has caught it; category and rarity are
    always shown as hints."""
    model_config = ConfigDict(from_attributes=True)
    number: int
    slug: str | None
    common_name: str | None
    scientific_name: str | None
    category: str
    rarity: str
    revealed: bool = True


class DexOut(BaseModel):
    species: SpeciesOut
    size: str | None = None
    weight: str | None = None
    fun_fact: str | None = None
    # {"grid": {lon0, lat0, step, cols, rows}, "cells": [[col, row, count], ...]}
    range: dict | None = None


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
    # Set when this photo became the album photo for the species (first catch).
    album_photo_id: int | None = None


class CollectionEntry(BaseModel):
    species: SpeciesOut
    caught: bool
    capture_count: int = 0
    earned_at: datetime | None = None
    friends_caught: int = 0
    photo_url: str | None = None


class CollectionOut(BaseModel):
    caught: int
    total: int
    entries: list[CollectionEntry]


class PhotoOut(BaseModel):
    id: int
    url: str
    username: str
    species: SpeciesOut
    taken_on: date
    # Exact-ish (about 100 m) for you and your friends, about 10 km for everyone else.
    latitude: float | None = None
    longitude: float | None = None
    location_precise: bool = False
    like_count: int = 0
    liked_by_me: bool = False
    is_mine: bool = False
    by_friend: bool = False
    rank: int | None = None


class AlbumOut(BaseModel):
    username: str
    caught: int
    total: int
    photos: list[PhotoOut]


class GalleryOut(BaseModel):
    species: SpeciesOut
    scope: str
    sort: str
    total: int
    photos: list[PhotoOut]


class AlbumPick(BaseModel):
    capture_id: int


class FriendRequestIn(BaseModel):
    username: str


class FriendOut(BaseModel):
    username: str
    caught: int = 0
    since: datetime


class FriendsOut(BaseModel):
    friends: list[FriendOut]
    incoming: list[FriendOut]
    outgoing: list[FriendOut]
