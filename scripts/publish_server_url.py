"""Tell the phone app where the game server is.

The demo runs on a PC behind a Cloudflare quick tunnel whose address changes on
every restart. The app reads server.json from this repo's `server-url` branch
(raw.githubusercontent.com caches it for a few minutes), so after restarting the
tunnel run:

    python scripts/publish_server_url.py                 # address from logs/tunnel.log
    python scripts/publish_server_url.py --url https://example.trycloudflare.com

It commits server.json on the server-url branch and pushes it, without touching
your checkout (it uses a temporary clone of that one branch).
"""

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="the server address (default: the last one in --log)")
    ap.add_argument("--log", default=str(ROOT / "logs" / "tunnel.log"), help="cloudflared's output")
    args = ap.parse_args()

    url = args.url
    if not url:
        found = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", Path(args.log).read_text(errors="ignore"))
        if not found:
            raise SystemExit(f"no trycloudflare.com address in {args.log}; pass --url")
        url = found[-1]
    url = url.rstrip("/")

    remote = git("remote", "get-url", "origin", cwd=ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        git("clone", "--quiet", "--depth", "1", "--branch", "server-url", remote, tmp, cwd=ROOT)
        path = Path(tmp) / "server.json"
        if json.loads(path.read_text()).get("url") == url:
            print(f"already published: {url}")
            return
        path.write_text(json.dumps({"url": url}) + "\n")
        git("commit", "--quiet", "-am", f"Game server is at {url}", cwd=tmp)
        git("push", "--quiet", "origin", "server-url", cwd=tmp)
    print(f"published {url}; phones pick it up within a few minutes")


if __name__ == "__main__":
    main()
