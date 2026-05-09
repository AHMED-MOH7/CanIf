"""
Step 5 — Incremental Change Detector.

Compares current req/function hashes against the stored state to find
exactly which requirements need to be re-mapped.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def detect_changes(reqs: list[dict], functions: list[dict], state: dict) -> dict:
    """
    Compare current file state against stored hashes.
    Returns a dict with six lists: new/modified/deleted for both reqs and functions.
    """
    req_hashes = state.get("req_hashes", {})
    fn_hashes  = state.get("fn_hashes",  {})

    current_req_ids  = {r["id"]   for r in reqs}
    current_fn_names = {f["name"] for f in functions}

    changes: dict[str, list[str]] = {
        "new_reqs":      [],
        "modified_reqs": [],
        "deleted_reqs":  [],
        "new_fns":       [],
        "modified_fns":  [],
        "deleted_fns":   [],
    }

    # Requirements
    for req in reqs:
        old = req_hashes.get(req["id"])
        if old is None:
            changes["new_reqs"].append(req["id"])
        elif old != req["hash"]:
            changes["modified_reqs"].append(req["id"])

    for rid in req_hashes:
        if rid not in current_req_ids:
            changes["deleted_reqs"].append(rid)

    # Functions
    for fn in functions:
        old = fn_hashes.get(fn["name"])
        if old is None:
            changes["new_fns"].append(fn["name"])
        elif old != fn["hash"]:
            changes["modified_fns"].append(fn["name"])

    for fname in fn_hashes:
        if fname not in current_fn_names:
            changes["deleted_fns"].append(fname)

    logger.info(
        "Changes detected — reqs: +%d ~%d -%d  |  fns: +%d ~%d -%d",
        len(changes["new_reqs"]),      len(changes["modified_reqs"]),  len(changes["deleted_reqs"]),
        len(changes["new_fns"]),       len(changes["modified_fns"]),   len(changes["deleted_fns"]),
    )
    return changes


def compute_reqs_to_remap(changes: dict, state: dict) -> set[str]:
    """
    Determine which requirement IDs must be re-mapped given a change set.

    Rules:
      1. All new or modified requirements → re-map directly.
      2. Any requirement previously mapped to a changed/deleted function
         → must be re-evaluated (the function body may now implement it
           differently, or no longer implement it at all).
      3. A new public function → offer it to all currently-unmapped
         requirements (it might now implement them).
    """
    to_remap: set[str] = set()

    # Rule 1
    to_remap.update(changes["new_reqs"])
    to_remap.update(changes["modified_reqs"])

    # Rule 2 — requirements whose mapped functions changed
    current_tm = state.get("tm", {})
    for fn_name in changes["modified_fns"] + changes["deleted_fns"]:
        for req_id, mapped_fns in current_tm.items():
            if fn_name in mapped_fns:
                to_remap.add(req_id)

    # Rule 3 — new public functions may now satisfy previously-unmapped reqs
    for fn_name in changes["new_fns"]:
        is_internal = (
            fn_name.startswith("_")
            or any(fn_name.endswith(s) for s in ("_internal", "_helper", "_priv", "_local"))
        )
        if not is_internal:
            to_remap.update(state.get("unmapped", {}).keys())

    logger.info("%d requirements scheduled for re-mapping", len(to_remap))
    return to_remap


def apply_incremental_results(
    new_results: list[dict],
    changes:     dict,
    state:       dict,
    reqs_by_id:  dict[str, dict],
    fns_by_name: dict[str, dict],
) -> dict:
    """
    Merge new LLM results into the existing state dict (in-place update).
    Also handles deletions and hash updates.
    Returns the updated state.
    """
    # Remove deleted requirements from state
    for req_id in changes["deleted_reqs"]:
        state["tm"].pop(req_id, None)
        state["unmapped"].pop(req_id, None)
        state["req_hashes"].pop(req_id, None)

    # Remove deleted functions from all mappings
    for fn_name in changes["deleted_fns"]:
        state["fn_hashes"].pop(fn_name, None)
        for req_id in list(state["tm"].keys()):
            if fn_name in state["tm"][req_id]:
                state["tm"][req_id].remove(fn_name)
                if not state["tm"][req_id]:
                    # No functions left → move to unmapped
                    state["unmapped"][req_id] = "All mapped functions were deleted from source"
                    del state["tm"][req_id]

    # Merge new LLM results
    for result in new_results:
        rid = result["req_id"]
        if result.get("status") == "MAPPED" and result.get("mappings"):
            state["tm"][rid]      = [m["function"] for m in result["mappings"]]
            state["unmapped"].pop(rid, None)
        else:
            state["unmapped"][rid] = result.get("unmapped_reason", "")
            state["tm"].pop(rid, None)

    # Refresh hashes for all currently-known reqs and functions
    for req in reqs_by_id.values():
        state["req_hashes"][req["id"]] = req["hash"]
    for fn in fns_by_name.values():
        state["fn_hashes"][fn["name"]] = fn["hash"]

    state["last_run"] = datetime.now().isoformat()
    return state


def state_to_results(state: dict, reqs: list[dict]) -> list[dict]:
    """
    Reconstruct a full flat results list from the stored state.
    Used by incremental mode to regenerate output files after a partial update.
    Confidence is set to MEDIUM for state-derived mappings (original LLM confidence
    is not stored — it is preserved in tm_report.json from the previous full run).
    """
    results: list[dict] = []
    for req in reqs:
        rid = req["id"]
        if rid in state.get("tm", {}):
            fn_names = state["tm"][rid]
            results.append({
                "req_id":  rid,
                "status":  "MAPPED",
                "mappings": [
                    {"function": fn, "confidence": "MEDIUM", "reason": "From persisted state"}
                    for fn in fn_names
                ],
            })
        else:
            results.append({
                "req_id":          rid,
                "status":          "UNMAPPED",
                "mappings":        [],
                "unmapped_reason": state.get("unmapped", {}).get(rid, "No implementation found"),
            })
    return results
