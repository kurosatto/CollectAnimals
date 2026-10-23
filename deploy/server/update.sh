#!/usr/bin/env bash
# Brings the server up to the latest main and restarts it (takes a few seconds).
#   sudo bash /opt/captureanimals/deploy/server/update.sh
set -euo pipefail
APP=/opt/captureanimals
DATA=/var/lib/captureanimals
[ -f "$DATA/game.db" ] && sudo -u game "$APP/.venv/bin/python" "$APP/scripts/backup.py" --db "$DATA/game.db" --uploads "$DATA/uploads" --to "$DATA/backups"
git -C "$APP" pull --ff-only origin main
"$APP/.venv/bin/pip" install -q -r "$APP/backend/requirements.txt"
chown -R game:game "$APP/backend"
systemctl restart captureanimals
sleep 5
curl -fsS http://127.0.0.1:8000/health && echo
