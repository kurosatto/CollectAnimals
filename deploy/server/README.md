# Free always-on game server

Runs the game server on an **Oracle Cloud Always Free** virtual machine with a free
fixed address from **DuckDNS** and free HTTPS from **Caddy**. Cost: $0 a month. It
should carry the game well past 100 players a day; move to a paid server only after that.
The money side is in the project's `finances/hosting-plan.md`.

The PC goes back to being only for training and builds. The app finds the server
through `server.json` as before, so no app update is needed, and the address no
longer changes on restarts.

## What only kuro can do (about 30 minutes, all free)

1. **Oracle Cloud account**: sign up at https://signup.cloud.oracle.com. It asks for a
   card to check your identity, but Always Free resources are never charged. Pick a
   US home region near you (it can't be changed later).
   - Recommended: then choose **Upgrade to Pay As You Go** in Billing, and set a
     **$1 budget alert**. You still pay $0 while you only use Always Free resources,
     but Oracle stops reclaiming "idle" free VMs on upgraded accounts. A quiet game
     server can look idle, so this protects it.
2. **Create the VM**: Compute → Instances → Create.
   - Image: **Canonical Ubuntu 24.04**. Shape: **Ampere A1 (VM.Standard.A1.Flex)**,
     **2 OCPU, 12 GB** (or less; anything Always Free eligible works).
   - Networking: keep "Assign a public IPv4 address". Download the SSH private key.
   - If it says "out of capacity", try another availability domain or try again later.
3. **Open the web ports**: on the instance page, open the subnet → Security List →
   Add Ingress Rules: source `0.0.0.0/0`, TCP, destination ports `80,443`.
4. **Fixed address**: sign in at https://www.duckdns.org (with GitHub or Google),
   add a subdomain such as `captureanimals`, and set its IP to the VM's public IP.
   Copy the **token** shown at the top.
5. **(Optional) Reset emails**: make a separate Gmail account for the game, turn on
   2-Step Verification, and create an **app password** at
   https://myaccount.google.com/apppasswords.

Then hand the VM's IP, the SSH key file and the DuckDNS name and token to Claude (the PC
session), which can do the rest.

## Setting it up (Claude or kuro)

```bash
ssh -i oracle.key ubuntu@<VM IP>
git clone https://github.com/kurosatto/CollectAnimals.git && cd CollectAnimals
sudo DOMAIN=captureanimals.duckdns.org DUCKDNS_TOKEN=<token> bash deploy/server/setup.sh
```

Copy the game over from the PC (stop the PC server first, so nothing is left behind):

```bash
python deploy/server/copy_to_server.py --host ubuntu@<VM IP> --ssh-key oracle.key \
  --db <demo worktree>/backend/demo.db --uploads <demo worktree's UPLOAD_DIR> \
  --model <AnimalCollect>/models/ca100.pt --keys <demo worktree>/backend
curl https://captureanimals.duckdns.org/health
python scripts/publish_server_url.py --url https://captureanimals.duckdns.org
```

The last line tells the app the new address. Players already signed in stay signed
in, because `.secret_key` moves too.

Email: put the Gmail details in `/etc/captureanimals.env` (`SMTP_HOST=smtp.gmail.com`,
`SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`), then `sudo systemctl restart captureanimals`.

## Day to day

- **Update after a merge**: `sudo bash /opt/captureanimals/deploy/server/update.sh`
  (backs up, pulls `main`, restarts).
- **New model**: copy it to `/var/lib/captureanimals/models/model.pt`, then
  `sudo systemctl restart captureanimals`.
- **APK downloads**: set `ANDROID_APK_DIR` in `/etc/captureanimals.env` to a folder
  holding `CaptureAnimals-<version>.apk` (only needed for the demo APK; Play updates itself).
- **Logs**: `journalctl -u captureanimals -f`. **Health**: `https://<address>/health`.
- **Backups**: every night to `/var/lib/captureanimals/backups` (14 database copies plus a
  photo mirror). Also turn on Oracle's free boot volume backups (Block Storage → Boot
  Volumes → Backup Policies → Bronze), and now and then copy the backups folder to the PC.

## When to pay

Stay free until there are 100+ players a day. Then, in order: a domain (~$10.50 a year)
and email from it, photos on Cloudflare R2 (free to 10 GB), and only if Oracle
proves unreliable a ~$5–8 a month server. `setup.sh` works on any Ubuntu server,
so moving is the same steps with a backup.
