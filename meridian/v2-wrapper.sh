#!/usr/bin/env bash
set -euo pipefail

# ── Config ───────────────────────────────────────────────────────────
MERIDIAN_HOST="${MERIDIAN_HOST:-127.0.0.1}"
MERIDIAN_PORT="${MERIDIAN_PORT:-3456}"
SHIM_HOST="${OPENCODE_MERIDIAN_SHIM_HOST:-127.0.0.1}"
SHIM_PORT="${OPENCODE_MERIDIAN_SHIM_PORT:-4568}"
LOG_DIR="${OPENCODE_MERIDIAN_LOG_DIR:-$HOME/.local/state/opencode-anthropic}"
MERIDIAN_LOG="$LOG_DIR/meridian.log"
SHIM_LOG="$LOG_DIR/shim.log"
PID_DIR="$LOG_DIR/pids"
SHIM_SCRIPT="${OPENCODE_MERIDIAN_SHIM_SCRIPT:-$HOME/.config/opencode/meridian-opencode-shim.js}"
TARGET_URL="${OPENCODE_MERIDIAN_TARGET:-http://$MERIDIAN_HOST:$MERIDIAN_PORT}"
MAX_LOG_SIZE="${MAX_LOG_SIZE:-5242880}"

mkdir -p "$LOG_DIR" "$PID_DIR"

# ── Helpers ──────────────────────────────────────────────────────────
port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

wait_for_http() {
  local url="$1" label="$2"
  for _ in $(seq 1 50); do
    curl -sf "$url" >/dev/null 2>&1 && return 0
    sleep 0.2
  done
  printf '✗ %s no respondió en %s\n' "$label" "$url" >&2
  return 1
}

rotate_log() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  local sz
  sz=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0)
  (( sz > MAX_LOG_SIZE )) && mv "$f" "${f}.old"
  return 0
}

resolve_meridian_cli() {
  [[ -n "${MERIDIAN_CLI:-}" ]] && { printf '%s\n' "$MERIDIAN_CLI"; return 0; }
  local npm_root
  npm_root="$(npm root -g 2>/dev/null || true)"
  [[ -n "$npm_root" && -f "$npm_root/@rynfar/meridian/dist/cli.js" ]] && {
    printf 'node %s/@rynfar/meridian/dist/cli.js\n' "$npm_root"; return 0
  }
  command -v meridian >/dev/null 2>&1 && { printf 'meridian\n'; return 0; }
  return 1
}

# ── Start services ───────────────────────────────────────────────────
start_meridian() {
  if port_in_use "$MERIDIAN_PORT"; then
    curl -sf "http://$MERIDIAN_HOST:$MERIDIAN_PORT/health" >/dev/null 2>&1 && return 0
    printf '✗ Puerto %s ocupado y no es Meridian\n' "$MERIDIAN_PORT" >&2; return 1
  fi
  local cli
  cli="$(resolve_meridian_cli)" || {
    printf '✗ No encontré Meridian. Instalalo con: npm install -g @rynfar/meridian\n' >&2; return 1
  }
  rotate_log "$MERIDIAN_LOG"
  printf '→ Levantando Meridian en http://%s:%s\n' "$MERIDIAN_HOST" "$MERIDIAN_PORT"
  # shellcheck disable=SC2086
  nohup env MERIDIAN_HOST="$MERIDIAN_HOST" MERIDIAN_PORT="$MERIDIAN_PORT" $cli >>"$MERIDIAN_LOG" 2>&1 &
  echo $! > "$PID_DIR/meridian.pid"
  wait_for_http "http://$MERIDIAN_HOST:$MERIDIAN_PORT/health" "Meridian"
}

start_shim() {
  [[ -f "$SHIM_SCRIPT" ]] || { printf '✗ No encontré shim en %s\n' "$SHIM_SCRIPT" >&2; return 1; }
  if port_in_use "$SHIM_PORT"; then
    curl -sf "http://$SHIM_HOST:$SHIM_PORT/health" >/dev/null 2>&1 && return 0
    printf '✗ Puerto %s ocupado y no es el shim\n' "$SHIM_PORT" >&2; return 1
  fi
  rotate_log "$SHIM_LOG"
  printf '→ Levantando shim en http://%s:%s\n' "$SHIM_HOST" "$SHIM_PORT"
  nohup env OPENCODE_MERIDIAN_SHIM_HOST="$SHIM_HOST" OPENCODE_MERIDIAN_SHIM_PORT="$SHIM_PORT" \
    OPENCODE_MERIDIAN_TARGET="$TARGET_URL" node "$SHIM_SCRIPT" >>"$SHIM_LOG" 2>&1 &
  echo $! > "$PID_DIR/shim.pid"
  wait_for_http "http://$SHIM_HOST:$SHIM_PORT/health" "Shim"
}

# ── Commands ─────────────────────────────────────────────────────────
stop_stack() {
  local stopped=0
  for svc in shim meridian; do
    local pidfile="$PID_DIR/$svc.pid"
    if [[ -f "$pidfile" ]]; then
      local pid; pid=$(<"$pidfile")
      kill -0 "$pid" 2>/dev/null && { kill "$pid" 2>/dev/null || true; stopped=1; }
      rm -f "$pidfile"
    fi
  done
  port_in_use "$SHIM_PORT" && { kill "$(lsof -ti tcp:"$SHIM_PORT")" 2>/dev/null || true; stopped=1; }
  port_in_use "$MERIDIAN_PORT" && { kill "$(lsof -ti tcp:"$MERIDIAN_PORT")" 2>/dev/null || true; stopped=1; }
  (( stopped )) && printf '✓ Stack detenido\n' || printf '✓ Nada corriendo en %s ni %s\n' "$MERIDIAN_PORT" "$SHIM_PORT"
}

print_help() {
  cat <<'EOF'
opencode-anthropic — OpenCode via Anthropic (Meridian + system prompt shim)

Uso:
  opencode-anthropic              Arranca stack y abre OpenCode interactivo
  opencode-anthropic run [args]   Arranca stack y ejecuta prompt directo
  opencode-anthropic --status     Estado de Meridian y shim
  opencode-anthropic --logs       Rutas de logs
  opencode-anthropic --tail       Seguir logs en vivo (Ctrl+C para salir)
  opencode-anthropic --restart    Reiniciar stack completo
  opencode-anthropic --stop       Detener Meridian y shim
  opencode-anthropic --help       Esta ayuda

Variables de entorno:
  MERIDIAN_HOST / MERIDIAN_PORT          default: 127.0.0.1:3456
  OPENCODE_MERIDIAN_SHIM_PORT           default: 4568
  OPENCODE_MERIDIAN_SYSTEM_PROMPT       System prompt para Anthropic
  MAX_LOG_SIZE                           Rotar logs a partir de (default: 5MB)
EOF
}

case "${1:-}" in
  --status)  printf '[Meridian]\n'
             curl -s "http://$MERIDIAN_HOST:$MERIDIAN_PORT/health" 2>/dev/null || printf '{"status":"down"}'
             printf '\n\n[Shim]\n'
             curl -s "http://$SHIM_HOST:$SHIM_PORT/health" 2>/dev/null || printf '{"status":"down"}'
             printf '\n'
             exit 0 ;;
  --logs)    printf 'Meridian: %s\nShim:     %s\n' "$MERIDIAN_LOG" "$SHIM_LOG"; exit 0 ;;
  --tail)    tail -f "$MERIDIAN_LOG" "$SHIM_LOG" 2>/dev/null; exit 0 ;;
  --restart) stop_stack; sleep 1; start_meridian; start_shim; printf '✓ Stack reiniciado\n'; exit 0 ;;
  --stop)    stop_stack; exit 0 ;;
  --help|-h) print_help; exit 0 ;;
esac

start_meridian
start_shim

export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-x}"
export ANTHROPIC_BASE_URL="http://$SHIM_HOST:$SHIM_PORT"

printf '→ OpenCode via Anthropic en %s\n' "$ANTHROPIC_BASE_URL"
exec opencode "$@"
