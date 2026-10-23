"""Copies the game's data from the PC to the new server, once, when moving.

Takes a consistent copy of the database (fine while the PC server runs), then sends
it with the photos, the model and the two key files over SSH (scp, built into
Windows 10 and later) and puts them in place on the server:

    python deploy/server/copy_to_server.py --host ubuntu@203.0.113.7 --ssh-key C:/Users/me/.ssh/oracle.key ^
        --db C:/Users/me/Desktop/AnimalCollect-demo/backend/demo.db ^
        --uploads C:/Users/me/Desktop/AnimalCollect-demo/backend/uploads ^
        --model C:/Users/me/Desktop/AnimalCollect/models/ca100.pt ^
        --keys C:/Users/me/Desktop/AnimalCollect-demo/backend

The key files keep everyone logged in (.secret_key) and keep browser notifications
working (.vapid_private.pem). Stop the PC server right before running this, so no
new photo lands on the PC after the copy.
"""

import argparse
import sqlite3
import subprocess
import tempfile
from pathlib import Path

APP, DATA = "/opt/captureanimals", "/var/lib/captureanimals"


def run(*cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", required=True, help="user@address of the server")
    ap.add_argument("--ssh-key", help="private key for SSH (the one Oracle gave you)")
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--uploads", required=True, type=Path)
    ap.add_argument("--model", required=True, type=Path)
    ap.add_argument("--keys", required=True, type=Path, help="folder with .secret_key and .vapid_private.pem")
    args = ap.parse_args()
    ssh_opts = ["-i", args.ssh_key] if args.ssh_key else []

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "move"
        stage.mkdir()
        src, out = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True), sqlite3.connect(stage / "game.db")
        with out:
            src.backup(out)
        src.close()
        out.close()
        files = [str(stage / "game.db"), str(args.model)]
        files += [str(args.keys / k) for k in (".secret_key", ".vapid_private.pem") if (args.keys / k).exists()]
        run("ssh", *ssh_opts, args.host, "rm -rf ~/move && mkdir -p ~/move/uploads")
        run("scp", *ssh_opts, *files, f"{args.host}:move/")
        run("scp", *ssh_opts, "-r", f"{args.uploads}/.", f"{args.host}:move/uploads/")

    model = args.model.name
    run("ssh", *ssh_opts, args.host, " && ".join([
        "sudo systemctl stop captureanimals",
        f"sudo mv ~/move/game.db {DATA}/game.db",
        f"sudo mv ~/move/{model} {DATA}/models/model.pt",
        f"sudo cp -r ~/move/uploads/. {DATA}/uploads/",
        f"(sudo mv ~/move/.secret_key ~/move/.vapid_private.pem {APP}/backend/ 2>/dev/null || true)",
        f"sudo chown -R game:game {DATA} {APP}/backend",
        "sudo systemctl start captureanimals",
        "rm -rf ~/move",
    ]))
    print("Copied. Check it with: curl https://<your address>/health")


if __name__ == "__main__":
    main()
