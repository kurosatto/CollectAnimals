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
    # Two-letter code from species/states.json; picks the Dex, Hotspots and maps.
    state: Mapped[str] = mapped_column(String(2), default="CA", server_default="CA")
    # Other states the player chose to unlock, comma-separated ("NC,CA"). Their
    # home state and any state they've captured in count as unlocked too.
    extra_states: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Whether new catches appear in everyone's news feed (None = default, yes).
    show_in_feed: Mapped[bool | None] = mapped_column(nullable=True, default=True)
    # Built-in "bot friends" new players can add; requests to them are accepted at once.
    # Private players' photos are shown only to themselves and their friends.
    is_private: Mapped[bool | None] = mapped_column(nullable=True, default=False)
    is_bot: Mapped[bool | None] = mapped_column(nullable=True, default=False)
    # Profile picture 1-10 (app/avatars.py); None on accounts from before pictures.
    avatar: Mapped[int | None] = mapped_column(nullable=True)
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


class StateSpecies(Base):
    """A species on one state's list. Rarity (and the display name) can differ by state."""

    __tablename__ = "state_species"
    __table_args__ = (UniqueConstraint("state", "species_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(2), index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"))
    position: Mapped[int] = mapped_column(Integer)  # order in the state's CSV = Dex number
    common_name: Mapped[str] = mapped_column(String(128))
    rarity: Mapped[str] = mapped_column(String(16))

    species: Mapped[Species] = relationship()


class Capture(Base):
    """Every photo a user submits, whether or not it matched a species."""

    __tablename__ = "captures"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    species_id: Mapped[int | None] = mapped_column(ForeignKey("species.id"), nullable=True)
    image_path: Mapped[str] = mapped_column(String(255))
    predicted_label: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    # Where and when the photo was taken: the photo's EXIF first (read before EXIF
    # is stripped from the saved file), else the phone's location and the upload
    # time. taken_at is the local wall time, with no zone, as cameras record it.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Where those came from: "photo" (EXIF), "device" (the phone's location when
    # uploading) or "edited" (the player fixed it). None on older captures.
    time_source: Mapped[str | None] = mapped_column(String(8), nullable=True)
    place_source: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # The state the player was playing in: a capture counts only in that state's
    # Field Guide (a coyote captured in California must be captured again in
    # North Carolina).
    state: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    # The model's top guesses (comma-separated slugs, best first): the animals a
    # player may pick from when they say the model got it wrong.
    top_labels: Mapped[str | None] = mapped_column(String(400), nullable=True)
    # True when the species was picked by the player rather than the model.
    user_picked: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Photo score (app/scoring.py) for the species it counts as: total points,
    # 1-5 stars and the breakdown as JSON [[label, points], ...].
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_parts: Mapped[str | None] = mapped_column(String(400), nullable=True)

    species: Mapped["Species | None"] = relationship()


class IdFeedback(Base):
    """The player said the model named the wrong animal: what it guessed, and what
    the player says it is (None = "none of these", not captured). One row per
    capture, updated if they change their mind. Kept as labels for retraining the
    model; the photo itself is used for training only under the photo terms the
    player agreed to."""

    __tablename__ = "id_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    capture_id: Mapped[int] = mapped_column(ForeignKey("captures.id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    state: Mapped[str] = mapped_column(String(2))
    # The model's best guess and every guess the player was shown (comma-separated slugs).
    predicted_label: Mapped[str] = mapped_column(String(64))
    rejected_labels: Mapped[str] = mapped_column(String(400))
    # The player's answer, and where it came from: "guesses" (one of the model's
    # other guesses) or "none" ("none of these", not captured).
    chosen_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


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
    # Hidden from everyone but its owner: reported by several players, or removed
    # by a moderator (app/safety.py).
    hidden: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

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


class PhotoComment(Base):
    """A comment on an album photo. Anyone who can see the photo can comment,
    friends or not; the commenter and the photo's owner can delete it."""

    __tablename__ = "photo_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey("album_photos.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Hidden from everyone but its writer after several players reported it.
    hidden: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    user: Mapped[User] = relationship()


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


class PushSubscription(Base):
    """A browser's Web Push address for a player (app/push.py). One per browser;
    dropped when the push service says it's gone or the player logs out there."""

    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    endpoint: Mapped[str] = mapped_column(String(1000), unique=True)
    p256dh: Mapped[str] = mapped_column(String(200))
    auth: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Block(Base):
    """blocker never sees blocked's photos or comments again, and the two can't
    friend, like or comment on each other (both ways)."""

    __tablename__ = "blocks"
    __table_args__ = (UniqueConstraint("blocker_id", "blocked_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    blocker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    blocked: Mapped[User] = relationship(foreign_keys=[blocked_id])


class Report(Base):
    """A player flagged a photo, a comment or a player for a moderator to look at.
    Exactly one of photo_id, comment_id is set for content; neither for a player."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reported_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    photo_id: Mapped[int | None] = mapped_column(ForeignKey("album_photos.id", ondelete="CASCADE"), nullable=True)
    comment_id: Mapped[int | None] = mapped_column(ForeignKey("photo_comments.id", ondelete="CASCADE"), nullable=True)
    reason: Mapped[str] = mapped_column(String(32))
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # "open" until a moderator removes the content ("removed") or keeps it ("kept").
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
