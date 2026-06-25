"""Boot orchestrator for the TukiJuris API.

Runs BEFORE uvicorn starts. Responsibilities, in order:

    1. Wait for Postgres to accept connections.
    2. Verify required extensions are installed (vector, uuid-ossp, pg_trgm).
    3. Detect Alembic state: if `alembic_version` is missing, stamp baseline
       (the legacy SQLs in `infrastructure/sql/` already created the schema).
    4. Apply pending Alembic migrations to head.
    5. Verify critical tables exist after migrations.
    6. exec() into uvicorn so it becomes PID 1's child cleanly.

Logs use a fixed-width, greppable format:

    [BOOT  10%] WAIT  Database connection
    [BOOT  15%] OK    Database reachable
    ...
    [BOOT 100%] BOOT  Starting uvicorn on 0.0.0.0:8000

This makes the boot sequence auditable from `docker logs` alone, in any
environment (local, staging, prod) — which is the whole point.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from typing import Sequence

import asyncpg

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DSN_ENV = "DATABASE_URL_SYNC"  # plain `postgresql://...` — no driver suffix
ALEMBIC_BASELINE = "001_baseline"
DB_WAIT_TIMEOUT = 60.0  # seconds
REQUIRED_EXTENSIONS = ("vector", "uuid-ossp", "pg_trgm")
REQUIRED_TABLES = (
    "users",
    "refresh_tokens",
    "conversations",
    "messages",
    "organizations",
    "user_llm_keys",
)

# uvicorn flags differ between dev (reload, single worker) and prod (workers, no reload).
# Bootstrap is invoked by both Dockerfile (dev) and Dockerfile.prod, so we read the
# mode from env vars instead of hard-coding either preset.
#
# APP_ENV=production  → --workers $UVICORN_WORKERS (default 2), no --reload
# APP_ENV=development → --reload, single worker
def _build_uvicorn_args() -> list[str]:
    args = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    is_prod = os.environ.get("APP_ENV", "development") == "production"
    if is_prod:
        workers = os.environ.get("UVICORN_WORKERS", "2")
        args += ["--workers", workers, "--timeout-keep-alive", "120", "--access-log"]
    else:
        args += ["--reload"]
    args += ["--proxy-headers", "--forwarded-allow-ips", "*"]
    return args


# ---------------------------------------------------------------------------
# Logging — fixed-width, greppable, no colors (works in any log shipper)
# ---------------------------------------------------------------------------

def log(pct: int, status: str, msg: str) -> None:
    print(f"[BOOT {pct:>3}%] {status:<5} {msg}", flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_dsn() -> str:
    dsn = os.environ.get(DSN_ENV)
    if not dsn:
        log(0, "FAIL", f"{DSN_ENV} not set in environment")
        sys.exit(1)
    # asyncpg expects a plain postgres scheme
    return (
        dsn.replace("postgresql+asyncpg://", "postgresql://")
           .replace("postgresql+psycopg2://", "postgresql://")
    )


async def wait_for_db(dsn: str) -> None:
    log(5, "WAIT", "Database connection")
    deadline = time.monotonic() + DB_WAIT_TIMEOUT
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            conn = await asyncpg.connect(dsn)
            await conn.execute("SELECT 1")
            await conn.close()
            log(15, "OK", "Database reachable")
            return
        except Exception as e:  # noqa: BLE001
            last_err = e
            await asyncio.sleep(1.0)
    log(15, "FAIL", f"DB unreachable after {DB_WAIT_TIMEOUT:.0f}s: {last_err}")
    sys.exit(1)


async def check_extensions(dsn: str) -> None:
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch("SELECT extname FROM pg_extension")
        present = {r["extname"] for r in rows}
        missing = [e for e in REQUIRED_EXTENSIONS if e not in present]
        if missing:
            log(25, "WARN", f"Missing extensions: {missing} (check infrastructure/sql/init.sql)")
        else:
            log(25, "OK", f"Extensions active: {list(REQUIRED_EXTENSIONS)}")
    finally:
        await conn.close()


async def alembic_initialized(dsn: str) -> bool:
    conn = await asyncpg.connect(dsn)
    try:
        row = await conn.fetchrow(
            "SELECT to_regclass('public.alembic_version') AS t"
        )
        return row["t"] is not None
    finally:
        await conn.close()


def run_alembic(args: Sequence[str], pct_on_fail: int) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["alembic", *args],
        cwd="/app",
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        log(pct_on_fail, "FAIL", f"alembic {' '.join(args)} (exit {proc.returncode})")
        if proc.stdout:
            print(proc.stdout, file=sys.stderr, flush=True)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, flush=True)
        sys.exit(1)
    return proc


async def verify_schema(dsn: str) -> None:
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )
        present = {r["tablename"] for r in rows}
        missing = [t for t in REQUIRED_TABLES if t not in present]
        if missing:
            log(80, "FAIL", f"Required tables missing after migrations: {missing}")
            sys.exit(1)
        log(80, "OK", f"Schema verified ({len(REQUIRED_TABLES)}/{len(REQUIRED_TABLES)} core tables present)")
    finally:
        await conn.close()


async def current_revision(dsn: str) -> str | None:
    conn = await asyncpg.connect(dsn)
    try:
        row = await conn.fetchrow("SELECT version_num FROM alembic_version LIMIT 1")
        return row["version_num"] if row else None
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    started = time.monotonic()
    log(0, "BOOT", "TukiJuris API bootstrap starting")

    dsn = get_dsn()
    await wait_for_db(dsn)
    await check_extensions(dsn)

    if await alembic_initialized(dsn):
        rev = await current_revision(dsn)
        log(40, "SKIP", f"alembic_version present (current: {rev})")
    else:
        log(35, "STAMP", f"alembic_version absent — marking baseline ({ALEMBIC_BASELINE})")
        run_alembic(["stamp", ALEMBIC_BASELINE], pct_on_fail=35)
        log(40, "OK", f"Baseline stamped at {ALEMBIC_BASELINE}")

    log(50, "WAIT", "Running 'alembic upgrade head'")
    proc = run_alembic(["upgrade", "head"], pct_on_fail=50)
    # Alembic logs "Running upgrade ... -> ..." to stderr (its INFO logger),
    # not stdout. Search both streams to be safe.
    combined = (proc.stdout or "") + (proc.stderr or "")
    upgrade_lines = [line for line in combined.splitlines() if "Running upgrade" in line]
    applied = len(upgrade_lines)
    head_rev = await current_revision(dsn)
    if applied:
        log(60, "OK", f"Applied {applied} migration(s)")
        for line in upgrade_lines:
            # "INFO  [alembic.runtime.migration] Running upgrade A -> B, msg"
            tail = line.split("Running upgrade", 1)[1].strip()
            log(60, "→", tail)
        log(70, "OK", f"Head revision: {head_rev}")
    else:
        log(70, "SKIP", f"No pending migrations — head: {head_rev}")

    await verify_schema(dsn)

    elapsed = time.monotonic() - started
    log(95, "OK", f"Bootstrap complete in {elapsed:.2f}s")
    log(100, "BOOT", "Starting uvicorn on 0.0.0.0:8000")

    # Hand over PID to uvicorn so signals (SIGTERM from compose down) reach it directly.
    uvicorn_args = _build_uvicorn_args()
    os.execvp(uvicorn_args[0], uvicorn_args)


if __name__ == "__main__":
    asyncio.run(main())
