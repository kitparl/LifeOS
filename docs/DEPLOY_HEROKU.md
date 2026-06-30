# Deploy LifeOS to Heroku (GitHub Student)

Deploy LifeOS as a **single Heroku app**: Angular frontend (static) + FastAPI API + Heroku Postgres.

Estimated cost with [GitHub Student Developer Pack](https://education.github.com/pack) Heroku credits: **~$10–13/month** (Eco/Basic dyno + Essential Postgres).

---

## Architecture

```
Browser → https://your-app.herokuapp.com
            ├── /api/v1/*  → FastAPI
            ├── /health    → FastAPI
            └── /*         → Angular SPA (static)
```

Build: Node builds Angular → copies to `backend/static/` → Python runs uvicorn.

---

## Prerequisites

1. [Heroku account](https://signup.heroku.com/) linked to GitHub Education benefits
2. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
3. Git repo pushed to GitHub (or deploy via CLI)
4. OpenAI key (optional, for AI features)

---

## Step 1 — Create the Heroku app

```bash
cd /path/to/LifeOS
heroku login
heroku create lifeos-yourname   # pick a unique name
```

---

## Step 2 — Add Postgres

```bash
heroku addons:create heroku-postgresql:essential-0
```

This sets `DATABASE_URL` automatically. The app converts it to `postgresql+asyncpg://` on startup.

---

## Step 3 — Set config vars

```bash
# Required — generate a long random string
heroku config:set ENV=production
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"

# Required for HTTPS cookies (login refresh)
heroku config:set COOKIE_SECURE=true

# Your app URL (replace with your app name)
heroku config:set CORS_ORIGINS=https://lifeos-yourname.herokuapp.com

# Optional — AI features
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set AI_CHAT_MODEL=gpt-4o-mini
heroku config:set AI_EMBEDDING_MODEL=text-embedding-3-small
```

Verify:

```bash
heroku config
```

---

## Step 4 — Enable buildpacks (Node + Python)

Node must run **before** Python so the Angular build completes first:

```bash
heroku buildpacks:clear
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
```

---

## Step 5 — Deploy

### Option A — GitHub integration (recommended)

1. Heroku Dashboard → your app → **Deploy**
2. **Deployment method** → GitHub → connect repo
3. Enable **Automatic deploys** from `main` (optional)
4. **Manual deploy** → Deploy Branch

### Option B — Heroku CLI

```bash
git push heroku main
```

---

## Step 6 — Verify

```bash
heroku open
heroku logs --tail
curl https://lifeos-yourname.herokuapp.com/health
```

1. Open the app URL in a browser
2. Register a new account
3. Log in and create a task or goal

If login fails after register, check `COOKIE_SECURE=true` and that you use **https://** (not http).

---

## Dyno type (budget ~$13/mo)

| Component | Suggested plan | ~Cost |
|-----------|----------------|-------|
| Web dyno | Eco or Basic | $5–7/mo |
| Postgres | essential-0 | $5/mo |

```bash
# Eco dyno (sleeps after 30 min inactivity — fine for personal use)
heroku ps:type eco

# Or Basic for always-on (no sleep)
heroku ps:type basic
```

Use GitHub Education Heroku credits before paying out of pocket.

---

## Troubleshooting

### Build fails on `npm install`

The root `package.json` uses `--legacy-peer-deps` for Angular service worker peer deps.

### Build fails — no `backend/static`

Check build log for `heroku-postbuild`. Output must land in `backend/static/` from `frontend/dist/frontend/browser/`.

### `Application error` / H10

```bash
heroku logs --tail
```

Common causes: missing `SECRET_KEY`, invalid `DATABASE_URL`, or port not bound to `$PORT` (Procfile handles this).

### Database connection errors

Ensure Postgres addon is attached:

```bash
heroku addons
heroku pg:info
```

### Uploads disappear after restart

Heroku filesystem is **ephemeral**. For persistent files, set S3 config vars (`S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) or accept local-only uploads for personal alpha.

### App sleeps (Eco dyno)

First request after idle may take 10–30s. Upgrade to Basic or ping `/health` with an external cron if needed.

---

## Updating the deployment

```bash
git push heroku main
# or merge to main if using GitHub auto-deploy
```

---

## Local production-like test

```bash
# Build frontend into backend/static
npm run heroku-postbuild --prefix .

# Run API (from backend with venv)
cd backend && source .venv/bin/activate
export DATABASE_URL=sqlite+aiosqlite:///./lifeos_dev.db
export SECRET_KEY=local-test
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000
```

---

## Next steps

See [improvements/v1.md](../improvements/v1.md) for production hardening before a public launch.
