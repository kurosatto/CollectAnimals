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
    # Coins from finished minigame levels (app/games.py), and how many came in today.
    coins: Mapped[int | None] = mapped_column(nullable=True, default=0)
    coins_day: Mapped[str | None] = mapped_column(String(10), nullable=True)
    coins_today: Mapped[int | None] = mapped_column(nullable=True, default=0)
    # "Share photos to teach the game": photos the player names after "None of
    # these" are kept for training the identifier. Off unless they turn it on.
    share_training_photos: Mapped[bool | None] = mapped_column(nullable=True, default=False)
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


class NamedPhoto(Base):
    """After "None of these" the player told us what the animal really was, picked
    from the big name list (species/animal_names.json): a species' scientific name
    or a broad group ("group:beetle"). These are labels for retraining the model,
    never a badge. image_path is a small training copy of the photo, kept only
    while the player shares photos to teach the game. capture_id is None for
    answers the phone saved offline and sent later."""

    __tablename__ = "named_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    capture_id: Mapped[int | None] = mapped_column(ForeignKey("captures.id"), nullable=True, unique=True)
    label: Mapped[str] = mapped_column(String(96))
    # What the model said (a class slug), and the state the photo was played in.
    predicted_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


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


class GameScore(Base):
    """A player's best points on one minigame level with one animal (app/games.py)."""

    __tablename__ = "game_scores"
    __table_args__ = (UniqueConstraint("user_id", "level", "species_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # "<game>.<level number>", e.g. "sky.0".
    level: Mapped[str] = mapped_column(String(16), index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"))
    points: Mapped[int] = mapped_column(Integer)
    # The skin the animal wore for that best score ("frosty"), or None for its own colors.
    skin: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship()
    species: Mapped[Species] = relationship()


class GameItem(Base):
    """Something a player bought with coins: a skin for their animals, or a decoration
    for their habitat (on = shown there)."""

    __tablename__ = "game_items"
    __table_args__ = (UniqueConstraint("user_id", "item"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item: Mapped[str] = mapped_column(String(32))
    on: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnimalSkin(Base):
    """Which bought skin a player's animal wears, in the habitat and the games."""

    __tablename__ = "animal_skins"
    __table_args__ = (UniqueConstraint("user_id", "species_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"))
    skin: Mapped[str] = mapped_column(String(16))

    species: Mapped[Species] = relationship()
