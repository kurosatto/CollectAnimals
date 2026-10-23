#!/usr/bin/env bash
# Sets up the Capture Animals game server on a fresh Ubuntu 24.04 VM (Oracle Cloud
# Always Free Arm, or any cheap VPS later). Safe to run again: it only fills in what's missing.
#
#   sudo DOMAIN=captureanimals.duckdns.org DUCKDNS_TOKEN=... bash setup.sh
#
# Afterwards copy the game's data over from the PC (copy_to_server.py), then see README.md.
set -euo pipefail

: "${DOMAIN:?set DOMAIN, e.g. captureanimals.duckdns.org}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"
REPO="${REPO:-https://github.com/kurosatto/CollectAnimals.git}"
APP=/opt/captureanimals
DATA=/var/lib/captureanimals
ENV_FILE=/etc/captureanimals.env

export DEBIAN_FRONTEND=noninteractive
echo "== Packages"
apt-get update -q
apt-get install -y -q python3-venv python3-pip git sqlite3 caddy iptables-persistent

echo "== Swap (a safety net while the model loads)"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

echo "== Firewall: Oracle's Ubuntu image blocks everything but SSH, so open web ports"
for port in 80 443; do
  iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null || iptables -I INPUT 1 -p tcp --dport "$port" -j ACCEPT
done
netfilter-persistent save

echo "== Game user, code and Python packages"
id game >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin game
mkdir -p "$DATA"/{uploads,models,backups}
[ -d "$APP/.git" ] || git clone --branch main "$REPO" "$APP"
git -C "$APP" config --global --add safe.directory "$APP"
python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install -q --upgrade pip
"$APP/.venv/bin/pip" install -q -r "$APP/backend/requirements.txt"
# CPU-only PyTorch (on Arm the regular wheels are CPU-only already) and timm for the model.
"$APP/.venv/bin/pip" install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu
"$APP/.venv/bin/pip" install -q timm
chown -R game:game "$DATA" "$APP/backend"

echo "== Settings ($ENV_FILE; edit it later for email and moderators)"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<CONF
PUBLIC=1
DATABASE_URL=sqlite:///$DATA/game.db
UPLOAD_DIR=$DATA/uploads
MODEL_PATH=$DATA/models/model.pt
ADMIN_USERNAMES=admin
# Optional: a contact address for the privacy policy page.
CONTACT_EMAIL=
# Password reset emails (free with a Gmail app password; see README.md).
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
MAIL_FROM=
CONF
  chmod 640 "$ENV_FILE" && chgrp game "$ENV_FILE"
fi

echo "== Game service (starts on boot, restarts if it crashes)"
cat > /etc/systemd/system/captureanimals.service <<UNIT
[Unit]
Description=Capture Animals game server
After=network-online.target

[Service]
User=game
Group=game
WorkingDirectory=$APP/backend
EnvironmentFile=$ENV_FILE
# One process: the rate limits live in memory (app/limits.py).
ExecStart=$APP/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now captureanimals

echo "== HTTPS for $DOMAIN (Caddy gets and renews the certificate by itself)"
cat > /etc/caddy/Caddyfile <<CADDY
$DOMAIN {
	encode gzip
	request_body {
		max_size 25MB
	}
	reverse_proxy 127.0.0.1:8000 {
		# The game reads the player's address from this header (app/limits.py), so set it
		# here; a value sent by the player would let them dodge the login limits.
		header_up CF-Connecting-IP {remote_host}
	}
}
CADDY
systemctl reload caddy || systemctl restart caddy

echo "== Scheduled jobs: DuckDNS address, nightly backup"
{
if [ -n "$DUCKDNS_TOKEN" ]; then
  echo "# Keeps $DOMAIN pointing at this server (only matters if its IP ever changes)."
  echo "*/10 * * * * root curl -fsS 'https://www.duckdns.org/update?domains=${DOMAIN%%.duckdns.org}&token=$DUCKDNS_TOKEN&ip=' >/dev/null 2>&1"
fi
cat <<CRON
# Nightly backup at 04:30 UTC: database copy (14 kept) and a mirror of the photos.
30 4 * * * game $APP/.venv/bin/python $APP/scripts/backup.py --db $DATA/game.db --uploads $DATA/uploads --to $DATA/backups >> $DATA/backups/backup.log 2>&1
CRON
} > /etc/cron.d/captureanimals
chmod 600 /etc/cron.d/captureanimals  # holds the DuckDNS token

echo
echo "Done. Next: copy the data from the PC (deploy/server/copy_to_server.py), then"
echo "  sudo systemctl restart captureanimals && curl -s https://$DOMAIN/health"
