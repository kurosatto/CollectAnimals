import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", f"sqlite:///{ROOT / 'backend' / 'collectanimals.db'}"))
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-insecure-change-me"))
    token_ttl_minutes: int = field(default_factory=lambda: int(os.getenv("TOKEN_TTL_MINUTES", "10080")))
    species_csv: Path = field(default_factory=lambda: Path(os.getenv(
        "SPECIES_CSV", ROOT / "species" / "california_100.csv")))
    details_csv: Path = field(default_factory=lambda: Path(os.getenv(
        "DETAILS_CSV", ROOT / "species" / "details.csv")))
    ranges_json: Path = field(default_factory=lambda: Path(os.getenv(
        "RANGES_JSON", ROOT / "species" / "ranges.json")))
    hotspots_json: Path = field(default_factory=lambda: Path(os.getenv(
        "HOTSPOTS_JSON", ROOT / "species" / "hotspots.json")))
    model_path: Path = field(default_factory=lambda: Path(os.getenv(
        "MODEL_PATH", ROOT / "models" / "ca100.pt")))
    upload_dir: Path = field(default_factory=lambda: Path(os.getenv(
        "UPLOAD_DIR", ROOT / "backend" / "uploads")))
    # Where photo files live; "local" = upload_dir on this server (see app/storage.py).
    storage_backend: str = field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))
    # A capture only counts if the model is at least this confident.
    match_threshold: float = field(default_factory=lambda: float(os.getenv("MATCH_THRESHOLD", "0.7")))
    max_upload_mb: int = field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_MB", "15")))


settings = Settings()
