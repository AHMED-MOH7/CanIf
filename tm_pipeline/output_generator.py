"""
Step 4 — TM Output Generator.

Writes:
  REQ-CODE-TM.md          human-readable traceability matrix
  Unmapped-REQ.md         unmapped requirements with reasons
  tm_report.json          machine-readable report (consumed by Impact Analyzer)
  tm_review_queue.md      LOW-confidence items for human review
  tm_state.json           incremental state (hashes + current TM snapshot)
"""

import logging
from datetime import datetime
from pathlib import Path

from .utils import save_json

logger = logging.getLogger(__name__)


# ── Public entry point ────────────────────────────────────────────────────────

def generate_all_outputs(
    all_results:    list[dict],
    reqs_by_id:     dict[str, dict],
    fns_by_name:    dict[str, dict],
    config:         dict,
    existing_state: dict | None = None,
) -> dict:
    """
    Split results into mapped/unmapped, run integrity check, write all files.
    Returns the new state dict (caller must save it to disk).
    """
    mapped   = [r for r in all_results
                if r.get("status") == "MAPPED" and r.get("mappings")]
    unmapped = [r for r in all_results
                if r.get("status") != "MAPPED" or not r.get("mappings")]

    _check_integrity(mapped, unmapped, len(reqs_by_id))

    out = config["output"]
    _write_tm_md(mapped, reqs_by_id, fns_by_name, out["tm_file"])
    _write_unmapped_md(unmapped, reqs_by_id, out["unmapped_file"])
    _write_report_json(mapped, unmapped, reqs_by_id, fns_by_name, out["report_file"])
    _write_review_queue(
        mapped,
        out.get("review_queue_file", "tm_review_queue.md"),
        config,
    )

    return _build_state(all_results, reqs_by_id, fns_by_name)


# ── REQ-CODE-TM.md ────────────────────────────────────────────────────────────

def _write_tm_md(
    mapped:      list[dict],
    reqs_by_id:  dict[str, dict],
    fns_by_name: dict[str, dict],
    out_path:    str,
) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Requirements-to-Code Traceability Matrix",
        "",
        f"> **Generated:** {ts}  ",
        f"> **Total Mapped:** {len(mapped)}",
        "> **Note:** AUTO-GENERATED — do not edit manually.",
        "",
        "| Req ID | Function(s) | Confidence | Description |",
        "|:---|:---|:---:|:---|",
    ]
    for result in sorted(mapped, key=lambda r: r["req_id"]):
        req_id  = result["req_id"]
        desc    = _truncate(reqs_by_id.get(req_id, {}).get("description", ""), 120)
        fn_parts = []
        for m in result.get("mappings", []):
            fn_obj = fns_by_name.get(m["function"], {})
            fname  = Path(fn_obj.get("file", "")).name
            lstart = fn_obj.get("line_start", "")
            loc    = f"{fname}:{lstart}" if fname else ""
            fn_parts.append(f"`{m['function']}`" + (f" ({loc})" if loc else ""))
        fns_str = ", ".join(fn_parts) or "—"
        conf    = (result["mappings"][0]["confidence"] if result.get("mappings") else "—")
        lines.append(f"| {req_id} | {fns_str} | {conf} | {desc} |")
    lines.append("")
    _write_text(out_path, "\n".join(lines))
    logger.info("Wrote TM → %s  (%d rows)", out_path, len(mapped))


# ── Unmapped-REQ.md ───────────────────────────────────────────────────────────

def _write_unmapped_md(
    unmapped:   list[dict],
    reqs_by_id: dict[str, dict],
    out_path:   str,
) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Unmapped Requirements",
        "",
        f"> **Generated:** {ts}  ",
        f"> **Total Unmapped:** {len(unmapped)}",
        "> **Note:** AUTO-GENERATED — do not edit manually.",
        "",
        "| Req ID | Description (excerpt) | Reason Not Mapped |",
        "|:---|:---|:---|",
    ]
    for result in sorted(unmapped, key=lambda r: r["req_id"]):
        req_id = result["req_id"]
        desc   = _truncate(reqs_by_id.get(req_id, {}).get("description", ""), 100)
        reason = result.get("unmapped_reason", "No reason provided")
        lines.append(f"| {req_id} | {desc} | {reason} |")
    lines.append("")
    _write_text(out_path, "\n".join(lines))
    logger.info("Wrote Unmapped → %s  (%d rows)", out_path, len(unmapped))


# ── tm_report.json ────────────────────────────────────────────────────────────

def _write_report_json(
    mapped:      list[dict],
    unmapped:    list[dict],
    reqs_by_id:  dict[str, dict],
    fns_by_name: dict[str, dict],
    out_path:    str,
) -> None:
    report = {
        "generated_at":       datetime.now().isoformat(),
        "total_requirements": len(reqs_by_id),
        "total_mapped":       len(mapped),
        "total_unmapped":     len(unmapped),
        "integrity_check":    "PASS",
        "mappings": [
            {
                "req_id":      r["req_id"],
                "status":      "MAPPED",
                "description": _truncate(reqs_by_id.get(r["req_id"], {}).get("description", ""), 200),
                "functions": [
                    {
                        "name":       m["function"],
                        "file":       fns_by_name.get(m["function"], {}).get("file", ""),
                        "line_start": fns_by_name.get(m["function"], {}).get("line_start", 0),
                        "confidence": m.get("confidence", "MEDIUM"),
                        "reason":     m.get("reason", ""),
                    }
                    for m in r.get("mappings", [])
                ],
            }
            for r in sorted(mapped, key=lambda x: x["req_id"])
        ],
        "unmapped": [
            {
                "req_id":      r["req_id"],
                "description": _truncate(reqs_by_id.get(r["req_id"], {}).get("description", ""), 200),
                "reason":      r.get("unmapped_reason", ""),
            }
            for r in sorted(unmapped, key=lambda x: x["req_id"])
        ],
    }
    save_json(report, out_path)
    logger.info("Wrote report → %s", out_path)


# ── tm_review_queue.md ────────────────────────────────────────────────────────

def _write_review_queue(
    mapped:   list[dict],
    out_path: str,
    config:   dict,
) -> None:
    accept = set(config.get("confidence", {}).get("accept_mappings", ["HIGH", "MEDIUM"]))
    low_items = [
        (r["req_id"], m)
        for r in mapped
        for m in r.get("mappings", [])
        if m.get("confidence", "LOW") not in accept
    ]
    if not low_items:
        logger.info("No LOW-confidence items — review queue is empty.")
        return
    lines = [
        "# TM Review Queue — Low-Confidence Mappings",
        "",
        f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> **Items requiring manual review:** {len(low_items)}",
        "",
        "| Req ID | Function | Confidence | Reason |",
        "|:---|:---|:---:|:---|",
    ]
    for req_id, m in sorted(low_items, key=lambda x: x[0]):
        lines.append(
            f"| {req_id} | `{m['function']}` | {m.get('confidence', 'LOW')} | {m.get('reason', '')} |"
        )
    lines.append("")
    _write_text(out_path, "\n".join(lines))
    logger.info("Wrote review queue → %s  (%d items)", out_path, len(low_items))


# ── State builder ─────────────────────────────────────────────────────────────

def _build_state(
    all_results: list[dict],
    reqs_by_id:  dict[str, dict],
    fns_by_name: dict[str, dict],
) -> dict:
    tm: dict[str, list[str]] = {}
    unmapped_state: dict[str, str] = {}
    for r in all_results:
        rid = r["req_id"]
        if r.get("status") == "MAPPED" and r.get("mappings"):
            tm[rid] = [m["function"] for m in r["mappings"]]
        else:
            unmapped_state[rid] = r.get("unmapped_reason", "")
    return {
        "last_run":    datetime.now().isoformat(),
        "req_hashes":  {rid: req["hash"] for rid, req in reqs_by_id.items()},
        "fn_hashes":   {name: fn["hash"] for name, fn in fns_by_name.items()},
        "tm":          tm,
        "unmapped":    unmapped_state,
    }


# ── Integrity check ───────────────────────────────────────────────────────────

def _check_integrity(mapped: list[dict], unmapped: list[dict], total: int) -> None:
    actual = len(mapped) + len(unmapped)
    if actual != total:
        raise RuntimeError(
            f"INTEGRITY FAILURE: mapped({len(mapped)}) + unmapped({len(unmapped)}) "
            f"= {actual}  ≠  expected {total}. "
            "Check for duplicate IDs or parser errors."
        )
    logger.info(
        "✓ Integrity check passed: %d mapped + %d unmapped = %d total",
        len(mapped), len(unmapped), total,
    )


# ── File I/O helper ───────────────────────────────────────────────────────────

def _write_text(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s[:n] + "…" if len(s) > n else s
