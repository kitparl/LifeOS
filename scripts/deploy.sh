#!/usr/bin/env bash
set -euo pipefail

# ==== CONFIG ====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"      # one level up from scripts/
BACKEND_DIR="$REPO_DIR/backend"
FRONTEND_DIR="$REPO_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
SERVICE_NAME="lifeos"
BRANCH="main"
LOG_FILE="$REPO_DIR/../deploy-lifeos.log"   # kept outside repo, avoids git noise

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "===== Starting LifeOS deployment ====="

# ---- 1. Pull latest code ----
cd "$REPO_DIR"
log "Pulling latest changes from $BRANCH..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

# ---- 2. Backend: install deps ----
log "Setting up backend..."
cd "$BACKEND_DIR"

if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtualenv..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# ---- 3. Frontend: install deps + build ----
log "Building frontend..."
cd "$FRONTEND_DIR"
npm install --legacy-peer-deps
npm run build

# ---- 4. Restart backend service ----
log "Restarting backend service ($SERVICE_NAME)..."
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager -l | tee -a "$LOG_FILE"

# ---- 5. Reload Caddy ----
log "Reloading Caddy..."
sudo systemctl reload caddy

log "===== Deployment complete ====="