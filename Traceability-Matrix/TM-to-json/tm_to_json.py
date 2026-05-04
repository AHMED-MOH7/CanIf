"""
Convert REQ-CODE-TM.txt (markdown table) to JSON format.

Usage:
    python tm_to_json.py
    python tm_to_json.py --tm "path/to/REQ-CODE-TM.txt" --out "path/to/output.json"

Output JSON contains:
    - metadata       : module info and counts
    - mappings       : list of {req_id, functions[], description}
    - function_index : reverse lookup {function_name -> [req_id, ...]}
"""

import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# ── defaults ────────────────────────────────────────────────────────────────
DEFAULT_TM  = r"Traceability-Matrix\REQ-CODE-TM.txt"
DEFAULT_OUT = r"Traceability-Matrix\TM-to-json\REQ-CODE-TM.json"

# ── parser ───────────────────────────────────────────────────────────────────
# Matches a valid table data row:  | SWS_CANIF_xxxxx | ... |
ROW_PATTERN = re.compile(r"^\|\s*(\S+)\s*\|\s*(.+?)\s*\|$")


def parse_second_column(raw: str) -> tuple[list[str], str]:
    """
    Split  'Func1, Func2 / (description text)'
    into   (['Func1', 'Func2'], 'description text')

    Handles rows that have no description parentheses gracefully.
    """
    if " / (" in raw:
        fn_part, rest = raw.split(" / (", 1)
        description = rest[:-1] if rest.endswith(")") else rest
    elif " / " in raw:
        fn_part, description = raw.split(" / ", 1)
    else:
        fn_part = raw
        description = ""

    functions = [f.strip() for f in fn_part.split(",") if f.strip()]
    return functions, description.strip()


def parse_tm(tm_path: str) -> list[dict]:
    mappings = []
    with open(tm_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            m = ROW_PATTERN.match(line)
            if not m:
                continue                          # skip title, blank, separator rows
            req_id = m.group(1).strip()
            if req_id.lower() in ("req id", "---"):
                continue                          # skip header row
            functions, description = parse_second_column(m.group(2))
            mappings.append({
                "req_id":      req_id,
                "functions":   functions,
                "description": description,
            })
    return mappings


def build_function_index(mappings: list[dict]) -> dict[str, list[str]]:
    """Reverse lookup: function name → list of req IDs that map to it."""
    index: dict[str, list[str]] = {}
    for entry in mappings:
        for fn in entry["functions"]:
            index.setdefault(fn, []).append(entry["req_id"])
    return dict(sorted(index.items()))


def build_json(mappings: list[dict], tm_path: str) -> dict:
    function_index = build_function_index(mappings)
    return {
        "metadata": {
            "module":          "CanIf",
            "standard":        "AUTOSAR AR 4.0.3",
            "source_file":     Path(tm_path).name,
            "total_mappings":  len(mappings),
            "total_functions": len(function_index),
            "generated":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "mappings":       mappings,
        "function_index": function_index,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert REQ-CODE-TM.txt to JSON")
    parser.add_argument("--tm",  default=DEFAULT_TM,  help="Path to REQ-CODE-TM.txt")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output JSON file path")
    args = parser.parse_args()

    tm_path  = Path(args.tm)
    out_path = Path(args.out)

    if not tm_path.exists():
        print(f"ERROR: TM file not found: {tm_path}")
        raise SystemExit(1)

    print(f"Reading : {tm_path}")
    mappings = parse_tm(str(tm_path))

    result = build_json(mappings, str(tm_path))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Written : {out_path}")
    print(f"  Mapped requirements : {result['metadata']['total_mappings']}")
    print(f"  Unique functions    : {result['metadata']['total_functions']}")
    print()
    print("Function index preview:")
    for fn, reqs in result["function_index"].items():
        print(f"  {fn:<40} {len(reqs)} req(s)")


if __name__ == "__main__":
    main()
