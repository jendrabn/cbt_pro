#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/var/www/cbt_pro}"
APP_BRANCH="${APP_BRANCH:-main}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-$VENV_DIR/bin/python}"
PIP_BIN="${PIP_BIN:-$VENV_DIR/bin/pip}"
NPM_BIN="${NPM_BIN:-npm}"
SYSTEMD_SERVICES="${SYSTEMD_SERVICES:-cbt_pro-gunicorn cbt_pro-celery}"
RUN_DAEMON_RELOAD="${RUN_DAEMON_RELOAD:-0}"
RUN_PIP_INSTALL="${RUN_PIP_INSTALL:-1}"
RUN_NPM_CI="${RUN_NPM_CI:-1}"
RUN_BUILD_CSS="${RUN_BUILD_CSS:-1}"
RUN_MIGRATE="${RUN_MIGRATE:-1}"
RUN_COLLECTSTATIC="${RUN_COLLECTSTATIC:-1}"
RUN_DEPLOY_CHECK="${RUN_DEPLOY_CHECK:-1}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "ERROR: $*"
  exit 1
}

require_file() {
  local path="$1"
  [[ -e "$path" ]] || fail "File atau direktori tidak ditemukan: $path"
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || fail "Command tidak ditemukan: $cmd"
}

run_systemctl() {
  if [[ "$EUID" -eq 0 ]]; then
    systemctl "$@"
  else
    sudo -n systemctl "$@"
  fi
}

restart_services() {
  if [[ -z "${SYSTEMD_SERVICES// }" ]]; then
    log "Lewati restart service karena SYSTEMD_SERVICES kosong."
    return
  fi

  if [[ "$RUN_DAEMON_RELOAD" == "1" ]]; then
    log "Reload konfigurasi systemd"
    run_systemctl daemon-reload
  fi

  for service in $SYSTEMD_SERVICES; do
    log "Restart service: $service"
    run_systemctl restart "$service"
    run_systemctl is-active --quiet "$service" || fail "Service tidak aktif setelah restart: $service"
  done
}

require_file "$APP_DIR"
require_file "$APP_DIR/.git"
require_file "$APP_DIR/.env"
require_file "$APP_DIR/requirements.txt"
require_file "$PYTHON_BIN"
require_file "$PIP_BIN"
require_cmd git

if [[ "$RUN_NPM_CI" == "1" || "$RUN_BUILD_CSS" == "1" ]]; then
  require_file "$APP_DIR/package.json"
  require_file "$APP_DIR/package-lock.json"
  require_cmd "$NPM_BIN"
fi

if [[ -n "${SYSTEMD_SERVICES// }" && "$EUID" -ne 0 ]]; then
  require_cmd sudo
fi

cd "$APP_DIR"
mkdir -p logs media staticfiles

if [[ -n "$(git status --porcelain)" ]]; then
  fail "Working tree di server tidak bersih. Commit atau buang perubahan lokal dulu."
fi

log "Fetch branch $APP_BRANCH dari remote $GIT_REMOTE"
git fetch --prune "$GIT_REMOTE"

if git show-ref --verify --quiet "refs/heads/$APP_BRANCH"; then
  git checkout "$APP_BRANCH"
else
  git checkout -B "$APP_BRANCH" "$GIT_REMOTE/$APP_BRANCH"
fi

log "Sinkronisasi kode terbaru"
git pull --ff-only "$GIT_REMOTE" "$APP_BRANCH"

if [[ "$RUN_PIP_INSTALL" == "1" ]]; then
  log "Install dependency Python"
  "$PIP_BIN" install -r requirements.txt
fi

if [[ "$RUN_NPM_CI" == "1" ]]; then
  log "Install dependency frontend"
  "$NPM_BIN" ci
fi

if [[ "$RUN_BUILD_CSS" == "1" ]]; then
  log "Build CSS"
  "$NPM_BIN" run build:css
fi

if [[ "$RUN_MIGRATE" == "1" ]]; then
  log "Jalankan migrasi database"
  "$PYTHON_BIN" manage.py migrate --noinput
fi

if [[ "$RUN_COLLECTSTATIC" == "1" ]]; then
  log "Collect static files"
  "$PYTHON_BIN" manage.py collectstatic --noinput
fi

if [[ "$RUN_DEPLOY_CHECK" == "1" ]]; then
  log "Jalankan Django deploy check"
  "$PYTHON_BIN" manage.py check --deploy
fi

restart_services

log "Deploy selesai pada commit $(git rev-parse --short HEAD)"
