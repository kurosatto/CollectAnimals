import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _secret_key() -> str:
    """SECRET_KEY from the environment, else a random key kept in backend/.secret_key.

    Generated once and reused, so logins survive restarts without anyone having
    to invent a key, and no shared default key exists to forge tokens with.
    """
    if os.getenv("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    path = ROOT / "backend" / ".secret_key"
    if not path.exists():
        path.write_text(secrets.token_hex(32), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", f"sqlite:///{ROOT / 'backend' / 'collectanimals.db'}"))
    secret_key: str = field(default_factory=_secret_key)
    # PUBLIC=1 when the site is reachable from the internet: hides the API docs
    # and internal error details.
    public: bool = field(default_factory=lambda: os.getenv("PUBLIC", "") not in ("", "0", "false"))
    token_ttl_minutes: int = field(default_factory=lambda: int(os.getenv("TOKEN_TTL_MINUTES", "10080")))
    # Lists each state's species CSV and map files (all in the same folder).
    states_json: Path = field(default_factory=lambda: Path(os.getenv(
        "STATES_JSON", ROOT / "species" / "states.json")))
    details_csv: Path = field(default_factory=lambda: Path(os.getenv(
        "DETAILS_CSV", ROOT / "species" / "details.csv")))
    sets_json: Path = field(default_factory=lambda: Path(os.getenv(
        "SETS_JSON", ROOT / "species" / "sets.json")))
    sprites_dir: Path = field(default_factory=lambda: Path(os.getenv(
        "SPRITES_DIR", ROOT / "species" / "sprites")))
    model_path: Path = field(default_factory=lambda: Path(os.getenv(
        "MODEL_PATH", ROOT / "models" / "ca100.pt")))
    upload_dir: Path = field(default_factory=lambda: Path(os.getenv(
        "UPLOAD_DIR", ROOT / "backend" / "uploads")))
    # Where photo files live; "local" = upload_dir on this server (see app/storage.py).
    storage_backend: str = field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))
    # A capture only counts if the model is at least this confident.
    match_threshold: float = field(default_factory=lambda: float(os.getenv("MATCH_THRESHOLD", "0.7")))
    # Score older photos (taken before photo scores, or before lighting was
    # judged) in the background after startup; SCORE_OLD_PHOTOS=0 turns it off.
    score_old_photos: bool = field(default_factory=lambda: os.getenv("SCORE_OLD_PHOTOS", "1") not in ("", "0", "false"))
    # The release version (bumped by hand for major updates) and the folder of built
    # Android APKs (CaptureAnimals-<version>.apk) offered to phones on older versions.
    release_json: Path = field(default_factory=lambda: Path(os.getenv("RELEASE_JSON", ROOT / "release.json")))
    android_apk_dir: Path | None = field(default_factory=lambda: Path(os.environ["ANDROID_APK_DIR"])
                                         if os.getenv("ANDROID_APK_DIR") else None)
    max_upload_mb: int = field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_MB", "15")))


settings = Settings()
