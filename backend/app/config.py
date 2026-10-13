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
    species_csv: Path = field(default_factory=lambda: Path(os.getenv(
        "SPECIES_CSV", ROOT / "species" / "california_100.csv")))
    details_csv: Path = field(default_factory=lambda: Path(os.getenv(
        "DETAILS_CSV", ROOT / "species" / "details.csv")))
    ranges_json: Path = field(default_factory=lambda: Path(os.getenv(
        "RANGES_JSON", ROOT / "species" / "ranges.json")))
    hotspots_json: Path = field(default_factory=lambda: Path(os.getenv(
        "HOTSPOTS_JSON", ROOT / "species" / "hotspots.json")))
    sprites_dir: Path = field(default_factory=lambda: Path(os.getenv(
        "SPRITES_DIR", ROOT / "species" / "sprites")))
    model_path: Path = field(default_factory=lambda: Path(os.getenv(
        "MODEL_PATH", ROOT / "models" / "ca100.pt")))
    upload_dir: Path = field(default_factory=lambda: Path(os.getenv(
        "UPLOAD_DIR", ROOT / "backend" / "uploads")))
    # A capture only counts if the model is at least this confident.
    match_threshold: float = field(default_factory=lambda: float(os.getenv("MATCH_THRESHOLD", "0.7")))
    max_upload_mb: int = field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_MB", "15")))


settings = Settings()
