#!/usr/bin/env python3
"""Coverage enforcement script — backend-saas-test-coverage.

Reads the pytest-cov JSON report and checks per-module MUST/STRETCH thresholds
defined in apps/api/coverage-targets.yaml.

MUST violations: exit 1 (CI-blocking).
STRETCH misses:  print a warning and continue (exit 0).

Usage:
    python scripts/check_coverage.py [--report /path/to/coverage.json]

The script is run inside the tukijuris-api-1 container where /tmp/coverage.json
is the default output location of `pytest --cov-report=json:/tmp/coverage.json`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
TARGETS_FILE = REPO_ROOT / "coverage-targets.yaml"
DEFAULT_REPORT = Path("/tmp/coverage.json")


def _pct(summary: dict) -> float:
    """Extract percent_covered from a coverage summary dict."""
    return float(summary.get("percent_covered", 0.0))


def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser(description="Check per-module coverage targets.")
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"Path to coverage JSON report (default: {DEFAULT_REPORT})",
    )
    args = parser.parse_args()

    if not args.report.exists():
        print(f"ERROR: coverage report not found at {args.report}", file=sys.stderr)
        print("Run: pytest tests --cov=app --cov-report=json:/tmp/coverage.json", file=sys.stderr)
        return 1

    if not TARGETS_FILE.exists():
        print(f"ERROR: coverage targets file not found at {TARGETS_FILE}", file=sys.stderr)
        return 1

    with args.report.open() as f:
        report = json.load(f)

    with TARGETS_FILE.open() as f:
        targets = yaml.safe_load(f)

    # Build module coverage map: normalised path → percent
    coverage_map: dict[str, float] = {}
    for raw_path, data in report.get("files", {}).items():
        # Normalise: strip leading slashes and /app/ prefix added by Docker
        norm = raw_path.lstrip("/")
        if norm.startswith("app/"):
            coverage_map[norm] = _pct(data.get("summary", {}))

    must_failures: list[str] = []
    stretch_warnings: list[str] = []

    for module in targets.get("modules", []):
        path: str = module["path"]
        must: int = module["must"]
        stretch: int = module["stretch"]

        actual = coverage_map.get(path)
        if actual is None:
            # Module not present in the report — treat as 0%
            actual = 0.0

        if actual < must:
            must_failures.append(
                f"  MUST FAIL  {path}: {actual:.1f}% < {must}% required"
                f" (spec: {module.get('spec', '?')})"
            )
        elif actual < stretch:
            stretch_warnings.append(
                f"  STRETCH    {path}: {actual:.1f}% < {stretch}% goal"
                f" (spec: {module.get('spec', '?')})"
            )
        else:
            print(f"  OK         {path}: {actual:.1f}% ≥ {stretch}% (stretch)")

    # Global threshold
    global_cfg = targets.get("global", {})
    global_actual = _pct(report.get("totals", {}))
    global_must = global_cfg.get("must", 0)
    global_stretch = global_cfg.get("stretch", 0)

    if global_actual < global_must:
        must_failures.append(
            f"  MUST FAIL  [global]: {global_actual:.1f}% < {global_must}% required"
        )
    elif global_actual < global_stretch:
        stretch_warnings.append(
            f"  STRETCH    [global]: {global_actual:.1f}% < {global_stretch}% goal"
        )
    else:
        print(f"  OK         [global]: {global_actual:.1f}%")

    print()
    if stretch_warnings:
        print("⚠️  STRETCH targets not yet met (warning only):")
        for w in stretch_warnings:
            print(w)
        print()

    if must_failures:
        print("❌ MUST coverage targets violated (CI-blocking):")
        for f in must_failures:
            print(f)
        print()
        print(f"Total failures: {len(must_failures)}")
        return 1

    print(f"✅ All MUST coverage targets met. ({len(stretch_warnings)} stretch misses)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
