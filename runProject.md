# LifeOS — run & VPS cheatsheet

Assumes the VPS layout from `docs/SSL_CADDY.md`:
- Repo at something like `/home/ubuntu/LifeOS`
- systemd unit: `lifeos` (uvicorn on `127.0.0.1:8000`)
- Caddy reverse-proxies HTTPS → that port
- Uploads preferably under `/var/lib/lifeos/uploads` (outside the git tree)

---

## Local development

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # ENV=dev
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install --legacy-peer-deps && npm start
# App: http://localhost:4200  |  API: http://localhost:8000

# Optional: build SPA into backend/static (mirrors production)
npm run build:frontend        # from repo root

# Tests / lint
cd backend && source .venv/bin/activate
pytest -q
ruff check app --select F401,F841,F823
```

---

## Deploy on the VPS

Prefer the existing script (pulls `main`, installs deps, builds frontend, restarts `lifeos`, reloads Caddy, health-checks, auto-rolls back on failure):

```bash
cd ~/LifeOS

./scripts/deploy.sh                 # full (backend + frontend)
./scripts/deploy.sh --backend-only  # API / Python only
./scripts/deploy.sh --frontend-only # UI only (still restarts lifeos)
./scripts/deploy.sh --rollback      # restore last known-good commit
./scripts/deploy.sh -h
```

Deploy logs (script writes these next to the repo parent):

```bash
tail -f ~/deploy-lifeos.log
tail -20 ~/deploy-lifeos-history.log
cat ~/deploy-lifeos-last-good
```

Manual one-off (if you skip the script):

```bash
cd ~/LifeOS
git fetch origin && git checkout main && git reset --hard origin/main
cd backend && source .venv/bin/activate && pip install -r requirements.txt
cd .. && npm run build:frontend
sudo systemctl restart lifeos
sudo systemctl reload caddy
curl -sf http://127.0.0.1:8000/health && echo OK
```

---

## Service control (`lifeos`)

```bash
sudo systemctl status lifeos
sudo systemctl start lifeos
sudo systemctl stop lifeos
sudo systemctl restart lifeos
sudo systemctl reload lifeos          # only if unit supports it; prefer restart
sudo systemctl enable lifeos          # start on boot
sudo systemctl disable lifeos

# After editing /etc/systemd/system/lifeos.service
sudo systemctl daemon-reload
sudo systemctl restart lifeos
```

Inspect the unit:

```bash
systemctl cat lifeos
sudo systemctl show lifeos -p ActiveState,SubState,MainPID,FragmentPath
```

---

## Logs

```bash
# Live tail
sudo journalctl -u lifeos -f

# Last N lines
sudo journalctl -u lifeos -n 200 --no-pager

# Errors / tracebacks only
sudo journalctl -u lifeos -p err -n 100 --no-pager

# Time window
sudo journalctl -u lifeos --since "1 hour ago"
sudo journalctl -u lifeos --since today
sudo journalctl -u lifeos --since "2026-09-13 10:00" --until "2026-09-13 12:00"

# Filter topics
sudo journalctl -u lifeos --since today | grep -i telegram
sudo journalctl -u lifeos --since today | grep -iE 'error|traceback|exception'
sudo journalctl -u lifeos --since today | grep -E 'APScheduler started|Registered job'
```

Caddy (TLS / reverse proxy):

```bash
sudo systemctl status caddy
sudo journalctl -u caddy -f
sudo journalctl -u caddy -n 100 --no-pager
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

---

## Health & quick checks

```bash
# Local (behind Caddy)
curl -s http://127.0.0.1:8000/health | jq .

# Public
curl -s https://YOUR_DOMAIN/health | jq .

# Is anything listening?
ss -lntp | grep -E ':8000|:443|:80'
curl -sI https://YOUR_DOMAIN | head -20
```

---

## Config / env on the VPS

```bash
# Edit env (then restart)
nano ~/LifeOS/backend/.env
sudo systemctl restart lifeos

# Confirm production-critical vars are set (values redacted)
cd ~/LifeOS/backend
grep -E '^(ENV|SECRET_KEY|INTEGRATION_ENC_KEY|COOKIE_SECURE|CORS_ORIGINS|PUBLIC_BASE_URL|ADMIN_GATE_|DATABASE_URL|UPLOAD_DIR|STORAGE_BACKEND)=' .env \
  | sed -E 's/(SECRET_KEY|INTEGRATION_ENC_KEY|ADMIN_GATE_PASSWORD_HASH)=.*/\1=***/'
```

Remember: with `ENV=production`, startup fails if `SECRET_KEY` is still the default or `INTEGRATION_ENC_KEY` is empty.

---

## Database

```bash
# SQLite (default local / simple VPS setups)
ls -lh ~/LifeOS/backend/*.db 2>/dev/null
sqlite3 ~/LifeOS/backend/lifeos_dev.db '.tables'
# Backup
cp ~/LifeOS/backend/lifeos_dev.db ~/backups/lifeos-$(date +%F).db

# Postgres (if DATABASE_URL points there)
# echo $DATABASE_URL from .env, then:
# pg_dump "$DATABASE_URL" > ~/backups/lifeos-$(date +%F).sql
```

---

## Uploads / disk

Keep `UPLOAD_DIR` outside the repo so deploys do not wipe files (see `docs/FILE_STORAGE.md`).

```bash
# Disk pressure
df -h
du -sh /var/lib/lifeos/uploads 2>/dev/null || du -sh ~/LifeOS/backend/uploads

# Permissions (service user must own the upload dir)
sudo chown -R ubuntu:ubuntu /var/lib/lifeos/uploads
sudo chmod -R u+rwX /var/lib/lifeos/uploads

# Optional: migrate local files → S3/R2 (from backend venv)
cd ~/LifeOS/backend && source .venv/bin/activate
python -m app.modules.files.backfill --target s3
# After verifying:
# python -m app.modules.files.backfill --target s3 --delete-local
```

---

## Learning-track seeder (ops)

```bash
cd ~/LifeOS/backend && source .venv/bin/activate
python -m app.modules.learning.seeder ai-systems-engineering --email you@example.com
```

---

## Git / recovery

```bash
cd ~/LifeOS
git status
git log --oneline -15
git rev-parse --short HEAD

# Emergency: hard reset to a known commit, then full redeploy
git reset --hard <commit>
./scripts/deploy.sh --full

# Or use the recorded last-good commit
./scripts/deploy.sh --rollback
```

---

## Host hygiene (occasional)

```bash
# What is using CPU/RAM?
htop    # or: top
free -h
systemctl --failed

# Free journal space if disk is tight
sudo journalctl --disk-usage
sudo journalctl --vacuum-time=14d
```
