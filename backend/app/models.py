from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    # Whether new catches appear in everyone's news feed (None = default, yes).
    show_in_feed: Mapped[bool | None] = mapped_column(nullable=True, default=True)
    # Built-in "bot friends" new players can add; requests to them are accepted at once.
    # Private players' photos are shown only to themselves and their friends.
    is_private: Mapped[bool | None] = mapped_column(nullable=True, default=False)
    is_bot: Mapped[bool | None] = mapped_column(nullable=True, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    common_name: Mapped[str] = mapped_column(String(128))
    scientific_name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32))
    rarity: Mapped[str] = mapped_column(String(16))
    region: Mapped[str] = mapped_column(String(32), default="california")


class Capture(Base):
    """Every photo a user submits, whether or not it matched a species."""

    __tablename__ = "captures"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    species_id: Mapped[int | None] = mapped_column(ForeignKey("species.id"), nullable=True)
    image_path: Mapped[str] = mapped_column(String(255))
    predicted_label: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    # Where and when the photo was taken: from the phone (browser location) or
    # the photo's EXIF, read before EXIF is stripped from the saved file.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # The model's top guesses (comma-separated slugs, best first): the animals a
    # player may pick from when they say the model got it wrong.
    top_labels: Mapped[str | None] = mapped_column(String(400), nullable=True)
    # True when the species was picked by the player rather than the model.
    user_picked: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    species: Mapped["Species | None"] = relationship()


class Badge(Base):
    """One per (user, species): the user has 'caught' this animal."""

    __tablename__ = "badges"
    __table_args__ = (UniqueConstraint("user_id", "species_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"))
    first_capture_id: Mapped[int] = mapped_column(ForeignKey("captures.id"))
    capture_count: Mapped[int] = mapped_column(Integer, default=1)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    species: Mapped[Species] = relationship()


class AlbumPhoto(Base):
    """The one photo a user shows for a species: in their album, to friends,
    and in that species' global gallery. Points at one of their captures."""

    __tablename__ = "album_photos"
    __table_args__ = (UniqueConstraint("user_id", "species_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), index=True)
    capture_id: Mapped[int] = mapped_column(ForeignKey("captures.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship()
    species: Mapped[Species] = relationship()
    capture: Mapped[Capture] = relationship()


class PhotoLike(Base):
    __tablename__ = "photo_likes"
    __table_args__ = (UniqueConstraint("photo_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey("album_photos.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Friendship(Base):
    """A friend request from requester to addressee; friends once accepted."""

    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("requester_id", "addressee_id"),
                      CheckConstraint("requester_id <> addressee_id"))

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    addressee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    accepted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    requester: Mapped[User] = relationship(foreign_keys=[requester_id])
    addressee: Mapped[User] = relationship(foreign_keys=[addressee_id])
