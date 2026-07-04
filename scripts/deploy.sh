#!/usr/bin/env bash
set -euo pipefail

# ==== CONFIG ====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"      # one level up from scripts/
BACKEND_DIR="$REPO_DIR/backend"
FRONTEND_DIR="$REPO_DIR/frontend"
STATIC_DIR="$BACKEND_DIR/static"
VENV_DIR="$BACKEND_DIR/.venv"
SERVICE_NAME="lifeos"
BRANCH="main"
LOG_DIR="$(dirname "$REPO_DIR")"
LOG_FILE="$LOG_DIR/deploy-lifeos.log"
HISTORY_FILE="$LOG_DIR/deploy-lifeos-history.log"
LAST_GOOD_FILE="$LOG_DIR/deploy-lifeos-last-good"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
HEALTH_RETRIES="${HEALTH_RETRIES:-5}"
HEALTH_RETRY_DELAY="${HEALTH_RETRY_DELAY:-2}"

# ---- flags (default: full deploy) ----
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true
DO_ROLLBACK=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Deploy LifeOS on the VPS. By default rebuilds backend + frontend, then restarts services.
If restart or health check fails, automatically rolls back to the previous commit.

Options:
  --backend-only   Skip frontend install/build (backend code or deps changed only)
  --frontend-only  Skip backend pip install (UI changes only; still restarts service)
  --full           Deploy both backend and frontend (default)
  --rollback       Redeploy the last known-good commit (manual recovery)
  -h, --help       Show this help

Logs:
  Full output:     $LOG_FILE
  History:         $HISTORY_FILE
  Last good commit: $LAST_GOOD_FILE

Examples:
  ./scripts/deploy.sh                  # full deploy (auto-rollback on failure after restart)
  ./scripts/deploy.sh --backend-only   # Python/API changes only
  ./scripts/deploy.sh --rollback       # restore last successful deploy
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend-only)
            DEPLOY_FRONTEND=false
            shift
            ;;
        --frontend-only)
            DEPLOY_BACKEND=false
            shift
            ;;
        --full)
            DEPLOY_BACKEND=true
            DEPLOY_FRONTEND=true
            shift
            ;;
        --rollback)
            DO_ROLLBACK=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

DEPLOY_START=$(date +%s)
COMMIT_SHA="unknown"
DEPLOY_SCOPE="full"
$DEPLOY_BACKEND && $DEPLOY_FRONTEND && DEPLOY_SCOPE="full"
$DEPLOY_BACKEND && ! $DEPLOY_FRONTEND && DEPLOY_SCOPE="backend-only"
! $DEPLOY_BACKEND && $DEPLOY_FRONTEND && DEPLOY_SCOPE="frontend-only"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

record_history() {
    local status="$1"
    local message="${2:-}"
    local end
    end=$(date +%s)
    local duration=$((end - DEPLOY_START))
    printf '%s\t%s\t%s\t%s\t%ss\t%s\n' \
        "$(date '+%Y-%m-%d %H:%M:%S')" \
        "$status" \
        "$COMMIT_SHA" \
        "$DEPLOY_SCOPE" \
        "$duration" \
        "$message" >> "$HISTORY_FILE"
}

setup_backend() {
    log "Setting up backend..."
    cd "$BACKEND_DIR"

    if [ ! -d "$VENV_DIR" ]; then
        log "Creating virtualenv..."
        python3 -m venv "$VENV_DIR"
    fi

    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
}

setup_frontend() {
    log "Building frontend..."
    cd "$FRONTEND_DIR"
    npm install --legacy-peer-deps
    npm run build

    log "Copying frontend build to $STATIC_DIR..."
    mkdir -p "$STATIC_DIR"
    rm -rf "${STATIC_DIR:?}/"*
    cp -r dist/frontend/browser/* "$STATIC_DIR/"
}

health_check() {
    if ! command -v curl >/dev/null 2>&1; then
        log "curl not found — skipping health check."
        return 0
    fi

    log "Health check: $HEALTH_URL (up to ${HEALTH_RETRIES} attempts)"
    local attempt
    for ((attempt = 1; attempt <= HEALTH_RETRIES; attempt++)); do
        if curl -sf "$HEALTH_URL" >/dev/null; then
            log "Health check passed (attempt $attempt)."
            return 0
        fi
        log "Health check attempt $attempt/$HEALTH_RETRIES failed — retrying in ${HEALTH_RETRY_DELAY}s..."
        sleep "$HEALTH_RETRY_DELAY"
    done
    return 1
}

restart_service() {
    log "Restarting backend service ($SERVICE_NAME)..."
    sudo systemctl restart "$SERVICE_NAME"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l | tee -a "$LOG_FILE"
    health_check || return 1
}

reload_caddy() {
    log "Reloading Caddy..."
    sudo systemctl reload caddy
}

run_deploy_steps() {
    if $DEPLOY_BACKEND; then
        setup_backend
    else
        log "Skipping backend setup."
    fi

    if $DEPLOY_FRONTEND; then
        setup_frontend
    else
        log "Skipping frontend build."
    fi

    restart_service || return 1
    reload_caddy
    return 0
}

rollback_to_commit() {
    local target_full="$1"
    local reason="$2"
    local target_short
    target_short="$(git -C "$REPO_DIR" rev-parse --short "$target_full")"

    trap - ERR
    log "===== ROLLBACK: $reason — reverting to $target_short ====="
    DEPLOY_SCOPE="rollback"
    COMMIT_SHA="$target_short"

    cd "$REPO_DIR"
    git reset --hard "$target_full"

    # Rebuild everything for the old commit so backend/static match that version.
    local saved_backend=$DEPLOY_BACKEND
    local saved_frontend=$DEPLOY_FRONTEND
    DEPLOY_BACKEND=true
    DEPLOY_FRONTEND=true

    if run_deploy_steps; then
        echo "$target_full" > "$LAST_GOOD_FILE"
        record_history "ROLLED_BACK" "reverted to $target_short after: $reason"
        log "===== Rollback successful — running $target_short ====="
        DEPLOY_BACKEND=$saved_backend
        DEPLOY_FRONTEND=$saved_frontend
        return 0
    fi

    DEPLOY_BACKEND=$saved_backend
    DEPLOY_FRONTEND=$saved_frontend
    record_history "ROLLBACK_FAILED" "could not restore $target_short after: $reason"
    log "ERROR: Rollback failed. Manual fix required:"
    log "  sudo systemctl status $SERVICE_NAME"
    log "  sudo journalctl -u $SERVICE_NAME -n 100"
    log "  ./scripts/deploy.sh --rollback"
    return 1
}

on_error() {
    local exit_code=$?
    log "ERROR: Deployment failed before restart (exit $exit_code)."
    log "Your app is still running the previous version — no rollback needed."
    record_history "FAILED" "exit $exit_code before restart — previous version still live"
    exit "$exit_code"
}

print_history_summary() {
    echo ""
    echo "Deployment history (last 5):"
    echo "  timestamp               status        commit  scope          duration  note"
    tail -5 "$HISTORY_FILE" 2>/dev/null | while IFS=$'\t' read -r ts status sha scope dur note; do
        printf '  %-23s %-13s %-7s %-14s %-9s %s\n' "$ts" "$status" "$sha" "$scope" "$dur" "$note"
    done
}

# ---- Manual rollback ----
if $DO_ROLLBACK; then
    trap - ERR
    log "===== Manual rollback requested ====="
    if [ ! -f "$LAST_GOOD_FILE" ]; then
        log "ERROR: No last-good commit recorded at $LAST_GOOD_FILE"
        log "Find a working commit with: git log --oneline -10"
        log "Then run: git reset --hard <commit> && ./scripts/deploy.sh --full"
        exit 1
    fi
    TARGET="$(tr -d '[:space:]' < "$LAST_GOOD_FILE")"
    rollback_to_commit "$TARGET" "manual --rollback"
    print_history_summary
    exit 0
fi

trap on_error ERR

log "===== Starting LifeOS deployment ($DEPLOY_SCOPE) ====="

# ---- 1. Pull latest code (save pre-deploy commit for auto-rollback) ----
cd "$REPO_DIR"
PREVIOUS_SHA="$(git rev-parse HEAD)"
log "Current commit before pull: $(git rev-parse --short HEAD)"

log "Pulling latest changes from $BRANCH..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"
COMMIT_SHA="$(git rev-parse --short HEAD)"
log "Deploying commit $COMMIT_SHA ($(git log -1 --format='%s'))"

# ---- 2–5. Build + restart ----
if ! run_deploy_steps; then
    trap - ERR
    log "ERROR: Service failed after deploy of $COMMIT_SHA."
    rollback_to_commit "$PREVIOUS_SHA" "restart/health check failed for $COMMIT_SHA" || true
    print_history_summary
    exit 1
fi

trap - ERR
echo "$(git -C "$REPO_DIR" rev-parse HEAD)" > "$LAST_GOOD_FILE"
log "===== Deployment complete (commit $COMMIT_SHA) ====="
record_history "SUCCESS" "commit $COMMIT_SHA"
print_history_summary
