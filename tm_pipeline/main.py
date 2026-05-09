"""
TM Pipeline — Entry Point.

Inputs come from your SDLC pipeline (Requirement Analysis + Static Analysis phases).

Usage:
  python -m tm_pipeline --config tm_config.yaml --mode full \
      --reqs-file path/to/parsed_reqs.json \
      --fns-file  path/to/parsed_functions.json

  python -m tm_pipeline --config tm_config.yaml --mode validate

Required JSON formats
---------------------
  parsed_reqs.json      list of { "id", "description" [, "hash"] }
  parsed_functions.json list of { "name", "file", "line_start", "line_end",
                                   "signature", "body_text", "comments",
                                   "inline_refs" [, "hash"] }
  "hash" is optional — computed automatically if absent.

Modes:
  full        Map all requirements, write all outputs.
  incremental Load stored state, re-map only what changed.
  watch       Run incremental once on start, then watch for file changes.
  validate    Check integrity of the last tm_report.json (no inputs needed).
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

from .llm_mapper       import run_mapping
from .output_generator import generate_all_outputs
from .change_detector  import (
    detect_changes,
    compute_reqs_to_remap,
    apply_incremental_results,
    state_to_results,
)
from .validate         import run_validation
from .utils            import load_json, save_json, compute_hash
from .watcher          import start_watcher


# ── Logging setup ─────────────────────────────────────────────────────────────

def _setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# ── Config loader ─────────────────────────────────────────────────────────────

def _load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(p, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg:
        raise ValueError("Config file is empty or invalid YAML.")
    return cfg


# ── Input loader ──────────────────────────────────────────────────────────────

def _ensure_hashes_reqs(reqs: list[dict]) -> None:
    for r in reqs:
        if not r.get("hash"):
            r["hash"] = compute_hash(r.get("id", "") + r.get("description", ""))


def _ensure_hashes_fns(fns: list[dict]) -> None:
    for f in fns:
        if not f.get("hash"):
            f["hash"] = compute_hash(f.get("body_text", "") or f.get("name", ""))


def _load_inputs(reqs_file: str, fns_file: str) -> tuple[list[dict], list[dict]]:
    """
    Load pre-parsed requirements and functions from JSON files produced by
    the Requirement Analysis and Static Analysis phases of the SDLC pipeline.
    """
    logger = logging.getLogger(__name__)

    logger.info("Loading requirements from %s", reqs_file)
    reqs = load_json(reqs_file)
    if not isinstance(reqs, list):
        raise ValueError(
            f"--reqs-file must be a JSON array of requirement objects, "
            f"got {type(reqs).__name__}"
        )
    _ensure_hashes_reqs(reqs)
    logger.info("Loaded %d requirements", len(reqs))

    logger.info("Loading functions from %s", fns_file)
    fns = load_json(fns_file)
    if not isinstance(fns, list):
        raise ValueError(
            f"--fns-file must be a JSON array of function objects, "
            f"got {type(fns).__name__}"
        )
    _ensure_hashes_fns(fns)
    logger.info("Loaded %d functions", len(fns))

    return reqs, fns


# ── Shared helpers ────────────────────────────────────────────────────────────

def _index_by_id(items: list[dict], key: str) -> dict:
    return {item[key]: item for item in items}


def _state_path(config: dict) -> str:
    return config["output"].get("state_file", "tm_state.json")


def _run_post_validation(config: dict) -> None:
    report_path = config["output"].get("report_file", "tm_report.json")
    if Path(report_path).exists():
        run_validation(report_path, _state_path(config))


# ── Mode: full ────────────────────────────────────────────────────────────────

def run_full(config: dict, reqs_file: str, fns_file: str) -> None:
    """Map all requirements and write all outputs."""
    logger = logging.getLogger(__name__)
    logger.info("=== FULL RUN ===")

    reqs, functions = _load_inputs(reqs_file, fns_file)

    if not reqs:
        logger.error("No requirements loaded — aborting.")
        sys.exit(1)
    if not functions:
        logger.warning("No functions loaded — all requirements will be UNMAPPED.")

    reqs_by_id  = _index_by_id(reqs,      "id")
    fns_by_name = _index_by_id(functions, "name")

    results   = run_mapping(reqs, functions, config)
    new_state = generate_all_outputs(results, reqs_by_id, fns_by_name, config)
    save_json(new_state, _state_path(config))
    logger.info("State saved → %s", _state_path(config))

    _run_post_validation(config)
    logger.info("=== FULL RUN COMPLETE ===")


# ── Mode: incremental ─────────────────────────────────────────────────────────

def run_incremental(config: dict, reqs_file: str, fns_file: str) -> None:
    """Detect changes against stored state, re-map only affected requirements."""
    logger = logging.getLogger(__name__)
    logger.info("=== INCREMENTAL RUN ===")

    state = load_json(_state_path(config))
    if not state:
        logger.info("No prior state found — falling back to full run.")
        run_full(config, reqs_file, fns_file)
        return

    reqs, functions = _load_inputs(reqs_file, fns_file)

    reqs_by_id  = _index_by_id(reqs,      "id")
    fns_by_name = _index_by_id(functions, "name")

    changes  = detect_changes(reqs, functions, state)
    to_remap = compute_reqs_to_remap(changes, state)

    if not to_remap:
        logger.info("Nothing changed — outputs are up to date.")
        return

    reqs_to_map = [r for r in reqs if r["id"] in to_remap]
    logger.info("Re-mapping %d / %d requirements", len(reqs_to_map), len(reqs))

    new_results   = run_mapping(reqs_to_map, functions, config)
    updated_state = apply_incremental_results(
        new_results, changes, state, reqs_by_id, fns_by_name
    )

    all_results = state_to_results(updated_state, reqs)
    generate_all_outputs(all_results, reqs_by_id, fns_by_name, config,
                         existing_state=updated_state)
    save_json(updated_state, _state_path(config))
    logger.info("State saved → %s", _state_path(config))

    _run_post_validation(config)
    logger.info("=== INCREMENTAL RUN COMPLETE ===")


# ── Mode: watch ───────────────────────────────────────────────────────────────

def run_watch(config: dict, reqs_file: str, fns_file: str) -> None:
    logger = logging.getLogger(__name__)
    logger.info("=== WATCH MODE ===")

    run_incremental(config, reqs_file, fns_file)

    def _trigger(cfg: dict) -> None:
        run_incremental(cfg, reqs_file, fns_file)

    start_watcher(config, _trigger)


# ── Mode: validate ────────────────────────────────────────────────────────────

def run_validate(config: dict, **_) -> None:
    logger = logging.getLogger(__name__)
    logger.info("=== VALIDATE ===")
    report_path = config["output"].get("report_file", "tm_report.json")
    state_path  = _state_path(config)
    ok = run_validation(report_path, state_path if Path(state_path).exists() else None)
    if not ok:
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="tm_pipeline",
        description="AI-Driven Requirements-to-Code Traceability Matrix Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Input JSON formats:\n"
            "  --reqs-file  list of { id, description [, hash] }\n"
            "  --fns-file   list of { name, file, line_start, line_end,\n"
            "               signature, body_text, comments, inline_refs [, hash] }\n"
        ),
    )
    parser.add_argument(
        "--config", "-c",
        default="tm_config.yaml",
        help="Path to YAML config file (default: tm_config.yaml)",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["full", "incremental", "watch", "validate"],
        default="incremental",
        help="Run mode (default: incremental)",
    )
    parser.add_argument(
        "--reqs-file",
        default=None,
        metavar="PATH",
        help="Pre-parsed requirements JSON (required for full/incremental/watch)",
    )
    parser.add_argument(
        "--fns-file",
        default=None,
        metavar="PATH",
        help="Pre-parsed functions JSON (required for full/incremental/watch)",
    )
    parser.add_argument(
        "--log", "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )

    args = parser.parse_args(argv)
    _setup_logging(args.log)

    # validate mode does not need input files
    if args.mode != "validate":
        if not args.reqs_file:
            parser.error("--reqs-file is required for mode: " + args.mode)
        if not args.fns_file:
            parser.error("--fns-file is required for mode: " + args.mode)

    config = _load_config(args.config)

    dispatch = {
        "full":        run_full,
        "incremental": run_incremental,
        "watch":       run_watch,
        "validate":    run_validate,
    }
    dispatch[args.mode](config, reqs_file=args.reqs_file, fns_file=args.fns_file)


if __name__ == "__main__":
    main()
