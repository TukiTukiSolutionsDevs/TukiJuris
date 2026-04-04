"""
Scheduler for automatic legal document scraping.

Runs scrapers periodically to keep the knowledge base up to date.
Can be run in two modes:
  - One-shot: runs all scrapers once and exits (default)
  - Daemon: runs scrapers at configured intervals until stopped (--daemon)

Usage:
    python -m services.ingestion.scrapers.scheduler [db_url] [--daemon]
"""

import asyncio
import logging
import sys
from datetime import datetime, UTC

from services.ingestion.scrapers.el_peruano import ElPeruanoScraper
from services.ingestion.scrapers.indecopi_scraper import IndecopiScraper
from services.ingestion.scrapers.tc_enhanced import TCEnhancedScraper

logger = logging.getLogger("scraper.scheduler")

DB_URL = "postgresql://postgres:postgres@localhost:5432/agente_derecho"

# Scraper schedule configuration
# interval_hours: how often to run each scraper
# enabled: whether to include in scheduled runs
SCHEDULE = {
    "el_peruano": {
        "interval_hours": 24,
        "enabled": True,
        "description": "El Peruano — Diario Oficial (leyes, DS, resoluciones)",
    },
    "tc": {
        "interval_hours": 168,  # weekly
        "enabled": True,
        "description": "Tribunal Constitucional — sentencias y precedentes",
    },
    "indecopi": {
        "interval_hours": 168,  # weekly
        "enabled": True,
        "description": "INDECOPI — resoluciones y precedentes de observancia obligatoria",
    },
}


def build_scraper(name: str, db_url: str):
    """Instantiate the correct scraper by name."""
    if name == "el_peruano":
        return ElPeruanoScraper(db_url)
    if name == "tc":
        return TCEnhancedScraper(db_url)
    if name == "indecopi":
        return IndecopiScraper(db_url)
    raise ValueError(f"Unknown scraper: {name}")


async def run_scraper(name: str, db_url: str) -> dict:
    """Run a single named scraper and return its result dict."""
    scraper = build_scraper(name, db_url)
    logger.info(f"Running scraper: {name}")
    start = datetime.now(UTC)
    result = await scraper.run()
    elapsed = (datetime.now(UTC) - start).total_seconds()
    result["scraper"] = name
    result["elapsed_seconds"] = round(elapsed, 2)
    result["ran_at"] = start.isoformat()
    return result


async def run_all_scrapers(db_url: str) -> dict:
    """
    Run all enabled scrapers sequentially and return combined results.

    Scrapers run one at a time to avoid overwhelming the DB or remote servers.
    Each scraper handles its own errors internally — a failure in one does not
    stop the others.
    """
    combined = {
        "docs": 0,
        "chunks": 0,
        "skipped": 0,
        "scrapers": {},
        "started_at": datetime.now(UTC).isoformat(),
    }

    for name, config in SCHEDULE.items():
        if not config["enabled"]:
            logger.info(f"Skipping disabled scraper: {name}")
            continue

        try:
            result = await run_scraper(name, db_url)
            combined["docs"] += result.get("docs", 0)
            combined["chunks"] += result.get("chunks", 0)
            combined["skipped"] += result.get("skipped", 0)
            combined["scrapers"][name] = result
            logger.info(
                f"[{name}] docs={result.get('docs', 0)}, "
                f"chunks={result.get('chunks', 0)}, "
                f"skipped={result.get('skipped', 0)}, "
                f"elapsed={result.get('elapsed_seconds', '?')}s"
            )
        except Exception as exc:
            logger.error(f"[{name}] Unexpected error: {exc}", exc_info=True)
            combined["scrapers"][name] = {"error": str(exc)}

    combined["finished_at"] = datetime.now(UTC).isoformat()
    return combined


async def scheduler_loop(db_url: str):
    """
    Main scheduler loop — runs scrapers at their configured intervals.

    Checks every hour whether any scraper is due to run.
    Persists last-run timestamps in memory only (process-lifetime).
    For production use, persist last_run to DB or a state file.
    """
    last_run: dict[str, datetime] = {}
    logger.info("Scheduler daemon started. Checking every hour.")

    while True:
        now = datetime.now(UTC)

        for name, config in SCHEDULE.items():
            if not config["enabled"]:
                continue

            interval_seconds = config["interval_hours"] * 3600
            last = last_run.get(name)

            if last is None or (now - last).total_seconds() >= interval_seconds:
                logger.info(
                    f"[scheduler] {name} is due — last ran: "
                    f"{'never' if last is None else last.isoformat()}"
                )
                try:
                    result = await run_scraper(name, db_url)
                    last_run[name] = now
                    logger.info(
                        f"[scheduler] {name} completed — "
                        f"docs={result.get('docs', 0)}, chunks={result.get('chunks', 0)}"
                    )
                except Exception as exc:
                    logger.error(f"[scheduler] {name} failed: {exc}", exc_info=True)
                    # Still update last_run to avoid retrying immediately on persistent failures
                    last_run[name] = now
            else:
                next_run_seconds = interval_seconds - (now - last).total_seconds()
                next_run_hours = round(next_run_seconds / 3600, 1)
                logger.debug(f"[scheduler] {name} not due yet — next run in ~{next_run_hours}h")

        # Check again in one hour
        logger.info("[scheduler] Next check in 1 hour.")
        await asyncio.sleep(3600)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    db = DB_URL
    daemon_mode = False

    for arg in sys.argv[1:]:
        if arg == "--daemon":
            daemon_mode = True
        elif not arg.startswith("--"):
            db = arg

    if daemon_mode:
        logger.info(f"Starting scheduler daemon with DB: {db}")
        asyncio.run(scheduler_loop(db))
    else:
        logger.info(f"Running all scrapers once with DB: {db}")
        result = asyncio.run(run_all_scrapers(db))
        print("\n=== Scraper Results ===")
        print(f"Total docs inserted : {result['docs']}")
        print(f"Total chunks inserted: {result['chunks']}")
        print(f"Total skipped        : {result['skipped']}")
        print(f"Started at           : {result.get('started_at', 'N/A')}")
        print(f"Finished at          : {result.get('finished_at', 'N/A')}")
        print("\nPer-scraper breakdown:")
        for name, stats in result.get("scrapers", {}).items():
            if "error" in stats:
                print(f"  {name}: ERROR — {stats['error']}")
            else:
                print(
                    f"  {name}: docs={stats.get('docs', 0)}, "
                    f"chunks={stats.get('chunks', 0)}, "
                    f"skipped={stats.get('skipped', 0)}, "
                    f"elapsed={stats.get('elapsed_seconds', '?')}s"
                )
