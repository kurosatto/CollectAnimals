from datetime import date, datetime

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
    show_in_feed: bool | None = True
    is_private: bool | None = False


class SettingsIn(BaseModel):
    show_in_feed: bool | None = None
    is_private: bool | None = None


class UserUpdate(BaseModel):
    state: str


class StateOut(BaseModel):
    code: str
    name: str
    species_count: int
    # Map extent in degrees: {"west", "east", "south", "north"}
    bounds: dict


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
    # {"months": [12 sighting counts], "hours": [24], "night_ratio": float | None}
    season: dict | None = None
    captured: bool = False


class HotspotSpecies(BaseModel):
    number: int
    slug: str | None
    common_name: str | None
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


class ChoiceOut(BaseModel):
    """One of the model's top guesses, named, for 'Not this animal? Pick the right one'."""
    slug: str
    common_name: str
    probability: float


class PickIn(BaseModel):
    # A slug from the capture's choices, or "none" for "none of these".
    label: str


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
    # The model's top 5 species guesses with names, for the player to correct it.
    choices: list[ChoiceOut] = []


class CollectionEntry(BaseModel):
    species: SpeciesOut
    caught: bool
    capture_count: int = 0
    earned_at: datetime | None = None
    friends_caught: int = 0
    photo_url: str | None = None


class CollectionOut(BaseModel):
    state: str
    caught: int
    total: int
    entries: list[CollectionEntry]


class PhotoOut(BaseModel):
    id: int
    # None in the feed for species the viewer hasn't unlocked (the photo would give it away).
    url: str | None
    username: str
    species: SpeciesOut
    taken_on: date
    caught_at: datetime
    # How precise depends on who's looking and how rare the animal is (see app/places.py).
    latitude: float | None = None
    longitude: float | None = None
    location_precise: bool = False
    place: str | None = None
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


class Tally(BaseModel):
    caught: int
    total: int


class AchievementOut(BaseModel):
    id: str
    title: str
    description: str
    earned: bool
    progress: int
    goal: int


class ProfileOut(BaseModel):
    username: str
    joined: datetime
    # self | friends | requested (you asked them) | incoming (they asked you) | none
    friendship: str
    is_bot: bool = False
    # Private players show their photos only to themselves and friends.
    is_private: bool = False
    caught: int
    total: int
    by_rarity: dict[str, Tally]
    by_category: dict[str, Tally]
    likes_received: int
    achievements: list[AchievementOut]
    # Their legendary catches; names follow the viewer's own reveal rules.
    legendaries: list[SpeciesOut]
    # Album photos the viewer may see: all of them for you and friends, only
    # species the viewer has unlocked for everyone else.
    photos: list[PhotoOut]
    hidden_photos: int = 0


class GalleryOut(BaseModel):
    species: SpeciesOut
    scope: str
    sort: str
    total: int
    photos: list[PhotoOut]


class FeedOut(BaseModel):
    scope: str  # near | all | friends
    photos: list[PhotoOut]
    # Pass as ?before= to get the next, older page; None when there are no more.
    next_before: int | None = None


class AlbumPick(BaseModel):
    capture_id: int


class FriendRequestIn(BaseModel):
    username: str


class FriendOut(BaseModel):
    username: str
    caught: int = 0
    since: datetime
    is_bot: bool = False


class SuggestionOut(BaseModel):
    username: str
    caught: int = 0
    is_bot: bool = False


class FriendsOut(BaseModel):
    friends: list[FriendOut]
    incoming: list[FriendOut]
    outgoing: list[FriendOut]
