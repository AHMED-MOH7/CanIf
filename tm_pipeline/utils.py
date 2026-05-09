"""Shared utilities: hashing, JSON I/O, retry, logging."""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=getattr(logging, level.upper(), logging.INFO),
    )


def compute_hash(text: str) -> str:
    """Return first 16 hex chars of SHA-256 of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def load_json(path: str | Path) -> dict:
    """Load JSON from path; return {} if the file does not exist."""
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Serialise *data* to JSON at *path*, creating parent dirs as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def with_retry(fn, max_retries: int = 3, base_wait: float = 5.0):
    """
    Call fn(); on rate-limit / transient API errors retry with exponential backoff.
    Raises on the last attempt if still failing.
    """
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            msg = str(exc).lower()
            transient = any(k in msg for k in ("rate_limit", "429", "503", "timeout", "overloaded"))
            if transient and attempt < max_retries - 1:
                wait = base_wait * (2 ** attempt)
                logger.warning(
                    "Transient error (%s) — retrying in %.0fs (attempt %d/%d)",
                    exc, wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"All {max_retries} attempts failed")
