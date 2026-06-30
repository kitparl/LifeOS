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