# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt email-validator
cp .env.example .env   # ENV=dev → development mode (default for local)
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install --legacy-peer-deps && npm start
# npm start reads backend/.env ENV=dev → production=false (development config)

# Heroku: heroku config:set ENV=production COOKIE_SECURE=true
# Deploy guide: docs/DEPLOY_HEROKU.md

cd /Users/pranshu.bisht/Documents/personal-work/LifeOS/backend


./.venv/bin/uvicorn app.main:app --app-dir backend --reload --port 8000

# Project Logs

## live tail (the usual one)
sudo journalctl -u lifeos -f

## last 200 lines
sudo journalctl -u lifeos -n 200 --no-pager

## only errors/tracebacks
sudo journalctl -u lifeos -p err -n 100 --no-pager

## time-scoped
sudo journalctl -u lifeos --since "1 hour ago"
sudo journalctl -u lifeos --since today

## search for something specific (e.g. Telegram polling)
sudo journalctl -u lifeos --since today | grep -i telegram

## is it even up? shows state plus the last ~10 log lines
sudo systemctl status lifeos