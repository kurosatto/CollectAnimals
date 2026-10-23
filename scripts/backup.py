"""Backs up the game server's database and photos to another folder (e.g. D:).

Safe while the server runs: SQLite's own backup copies the database in one
consistent piece. Each run keeps a dated database copy (the newest --keep of
them) and adds new photos to one shared photos folder, so repeat runs are
quick and photos aren't stored twice. Photos of deleted accounts are removed
from the backup too, so deleting an account really deletes it.

    python scripts/backup.py --db C:/path/demo.db --uploads C:/path/demo_uploads --to D:/CaptureAnimals/backups

Run it daily with Windows Task Scheduler (Action: python, Arguments: the line above).
"""

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def backup_db(db: Path, to: Path, keep: int) -> Path:
    to.mkdir(parents=True, exist_ok=True)
    dest = to / f"{db.stem}-{datetime.now():%Y%m%d-%H%M%S}.db"
    src, out = sqlite3.connect(f"file:{db}?mode=ro", uri=True), sqlite3.connect(dest)
    with out:
        src.backup(out)
    src.close()
    out.close()
    for old in sorted(to.glob(f"{db.stem}-*.db"))[:-keep]:
        old.unlink()
    return dest


def sync_photos(uploads: Path, to: Path) -> tuple[int, int]:
    """Copies new or changed photos and removes ones deleted on the server."""
    added = removed = 0
    have = set()
    for f in uploads.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(uploads)
        have.add(rel)
        dest = to / rel
        if not dest.exists() or dest.stat().st_size != f.stat().st_size:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            added += 1
    if to.exists():
        for f in to.rglob("*"):
            if f.is_file() and f.relative_to(to) not in have:
                f.unlink()
                removed += 1
    return added, removed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True, type=Path, help="the server's SQLite file")
    ap.add_argument("--uploads", required=True, type=Path, help="the server's UPLOAD_DIR")
    ap.add_argument("--to", required=True, type=Path, help="backup folder, ideally on another drive")
    ap.add_argument("--keep", type=int, default=14, help="database copies to keep (default 14)")
    args = ap.parse_args()
    dest = backup_db(args.db, args.to / "db", args.keep)
    added, removed = sync_photos(args.uploads, args.to / "photos")
    print(f"Database -> {dest}; photos: {added} copied, {removed} removed")


if __name__ == "__main__":
    main()
