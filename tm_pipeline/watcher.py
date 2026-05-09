"""
Step 6 — File System Watcher.

Uses the watchdog library to monitor source and requirements directories.
When a change is detected, triggers an incremental TM update after a short
debounce window (to avoid firing on every save keystroke).
"""

import logging
import time
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


def start_watcher(config: dict, run_incremental_fn) -> None:
    """
    Start watching all configured source and requirements paths.
    Blocks until the user presses Ctrl-C.

    run_incremental_fn: callable(config) — called after each debounce window elapses.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        raise ImportError("watchdog required: pip install watchdog")

    debounce_seconds = config.get("watcher", {}).get("debounce_seconds", 5)
    watch_dirs = _collect_watch_dirs(config)

    if not watch_dirs:
        logger.warning("No directories to watch — watcher exiting immediately.")
        return

    handler = _DebouncedHandler(
        run_incremental_fn=run_incremental_fn,
        config=config,
        debounce_seconds=debounce_seconds,
        extensions=_extensions(config),
    )

    observer = Observer()
    for d in watch_dirs:
        observer.schedule(handler, str(d), recursive=True)
        logger.info("Watching: %s", d)

    observer.start()
    logger.info(
        "Watcher active — debounce=%.1fs. Press Ctrl-C to stop.", debounce_seconds
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Watcher stopping…")
    finally:
        observer.stop()
        observer.join()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _collect_watch_dirs(config: dict) -> list[Path]:
    dirs: list[Path] = []
    for d in config.get("source_code", {}).get("directories", []):
        p = Path(d)
        if p.exists():
            dirs.append(p)
        else:
            logger.warning("Watch dir does not exist — skipping: %s", p)
    req_file = config.get("requirements", {}).get("file_path", "")
    if req_file:
        parent = Path(req_file).parent
        if parent.exists() and parent not in dirs:
            dirs.append(parent)
    return dirs


def _extensions(config: dict) -> set[str]:
    exts = set(config.get("source_code", {}).get("file_extensions", {".c": ""}).keys())
    req_fmt = config.get("requirements", {}).get("format", "csv")
    fmt_to_ext = {"csv": ".csv", "excel": ".xlsx", "plain_text": ".txt", "json": ".json"}
    ext = fmt_to_ext.get(req_fmt)
    if ext:
        exts.add(ext)
    return exts


class _DebouncedHandler:
    """Watchdog event handler with a debounce timer."""

    def __init__(self, run_incremental_fn, config, debounce_seconds, extensions):
        try:
            from watchdog.events import FileSystemEventHandler
            self._base = FileSystemEventHandler
        except ImportError:
            self._base = object

        self._run = run_incremental_fn
        self._config = config
        self._debounce = debounce_seconds
        self._extensions = extensions
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    # watchdog calls dispatch() → on_any_event
    def dispatch(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in self._extensions:
            return
        self._schedule()

    def _schedule(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self):
        logger.info("Change detected — triggering incremental update…")
        try:
            self._run(self._config)
        except Exception as exc:
            logger.error("Incremental update failed: %s", exc)
