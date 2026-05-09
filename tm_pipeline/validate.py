"""
TM Integrity Validator.

Checks performed:
  1. Count integrity  : mapped + unmapped == total_requirements
  2. No duplicate IDs : each req ID appears exactly once
  3. No empty mappings: every mapped req has >= 1 function
  4. No phantom fns   : warn if a mapped function has no file location
  5. Confidence cover : warn if > 10% of mappings are LOW confidence
  6. Staleness check  : warn if state is older than source files by > 24h
"""

import logging
from datetime import datetime
from pathlib import Path

from .utils import load_json

logger = logging.getLogger(__name__)


def run_validation(report_path: str, state_path: str | None = None) -> bool:
    """
    Run all checks.  Returns True if all hard checks pass (warnings do not fail).
    """
    report = load_json(report_path)
    if not report:
        logger.error("Report not found or empty: %s", report_path)
        return False

    state = load_json(state_path) if state_path else {}

    results = [
        _check_count_integrity(report),
        _check_no_duplicate_ids(report),
        _check_no_empty_mappings(report),
        _check_no_phantom_functions(report),     # warning only
        _check_confidence_coverage(report),       # warning only
    ]
    if state:
        results.append(_check_staleness(state, report_path))   # warning only

    passed = all(results)
    if passed:
        logger.info("✓ All validation checks PASSED")
    else:
        logger.error("✗ One or more validation checks FAILED")
    return passed


# ── Individual checks ─────────────────────────────────────────────────────────

def _check_count_integrity(report: dict) -> bool:
    total    = report.get("total_requirements", 0)
    mapped   = report.get("total_mapped",   0)
    unmapped = report.get("total_unmapped", 0)
    if mapped + unmapped == total:
        logger.info("✓ Count integrity: %d + %d = %d", mapped, unmapped, total)
        return True
    logger.error(
        "✗ Count integrity FAILED: %d + %d = %d  ≠  expected %d",
        mapped, unmapped, mapped + unmapped, total,
    )
    return False


def _check_no_duplicate_ids(report: dict) -> bool:
    ids: list[str] = (
        [r["req_id"] for r in report.get("mappings", [])]
        + [r["req_id"] for r in report.get("unmapped", [])]
    )
    seen: set[str] = set()
    dupes: set[str] = set()
    for rid in ids:
        if rid in seen:
            dupes.add(rid)
        seen.add(rid)
    if not dupes:
        logger.info("✓ No duplicate requirement IDs")
        return True
    logger.error("✗ Duplicate req IDs: %s", sorted(dupes))
    return False


def _check_no_empty_mappings(report: dict) -> bool:
    empty = [r["req_id"] for r in report.get("mappings", []) if not r.get("functions")]
    if not empty:
        logger.info("✓ No mapped requirements with zero functions")
        return True
    logger.error("✗ Mapped requirements with no functions: %s", empty)
    return False


def _check_no_phantom_functions(report: dict) -> bool:
    phantoms = [
        (r["req_id"], fn["name"])
        for r in report.get("mappings", [])
        for fn in r.get("functions", [])
        if not fn.get("file") and not fn.get("line_start")
    ]
    if not phantoms:
        logger.info("✓ No phantom function mappings")
    else:
        logger.warning("⚠ Possible phantom mappings (no file location): %s", phantoms[:5])
    return True   # warning only


def _check_confidence_coverage(report: dict) -> bool:
    all_fns = [fn for r in report.get("mappings", []) for fn in r.get("functions", [])]
    total   = len(all_fns)
    if total == 0:
        return True
    low     = sum(1 for fn in all_fns if fn.get("confidence", "").upper() == "LOW")
    pct     = low / total * 100
    if pct <= 10:
        logger.info("✓ LOW-confidence mappings: %d / %d (%.1f%%)", low, total, pct)
    else:
        logger.warning(
            "⚠ HIGH proportion of LOW-confidence mappings: %d / %d (%.1f%%) — review recommended",
            low, total, pct,
        )
    return True   # warning only


def _check_staleness(state: dict, report_path: str) -> bool:
    last_run_str = state.get("last_run")
    if not last_run_str:
        return True
    try:
        last_run  = datetime.fromisoformat(last_run_str)
        mtime     = datetime.fromtimestamp(Path(report_path).stat().st_mtime)
        age_hours = (mtime - last_run).total_seconds() / 3600
        if age_hours > 24:
            logger.warning(
                "⚠ State is %.1f hours older than report file — consider running --mode full",
                age_hours,
            )
        else:
            logger.info("✓ State freshness: %.1f hours", max(age_hours, 0))
    except Exception:
        pass
    return True   # warning only
