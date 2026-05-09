# TM Pipeline — Architecture

---

## 0. Overview

### What the Tool Does and Why

You have two artifacts that must stay in sync:

| Artifact | Example | Problem |
|:---|:---|:---|
| **Requirements document** | *"SWS_CANIF_00308 — The service shall call `Can_SetControllerMode()`…"* | Which function actually implements this? |
| **C source code** | `CanIf_SetControllerMode()`, `CanIf_RxIndication()`, … 30 functions | Which requirement does each function satisfy? |

Doing this mapping by hand for 273 requirements × 30 functions is error-prone and breaks every time code or requirements change.
**`tm_pipeline` automates it end-to-end using AI.**

```mermaid
flowchart LR
    subgraph HAVE["What you start with"]
        R["Requirements Document\n273 SWS_CANIF_XXXXX items\neach saying 'the system SHALL…'"]
        C["C Source Code\n30+ functions across CanIf.c\nbody text · signatures · comments"]
        CFG["One config file\ntm_config.yaml\npaths · model · thresholds"]
    end

    TOOL{{"  tm_pipeline\n  AI-Driven TM Generator  "}}

    subgraph GET["What you get — automatically"]
        TM["Traceability Matrix\nREQ ID → Function(s)\nwith confidence score\nAUTO-REQ-CODE-TM.md"]
        GAP["Gap Report\nunmapped requirements\nwith reason\nAUTO-Unmapped-REQ.md"]
        JSON["Machine Report\ntm_report.json\nfor impact analysis & CI"]
        RQ["Review Queue\nLOW-confidence items\nflagged for human sign-off"]
    end

    R & C & CFG --> TOOL
    TOOL --> TM & GAP & JSON & RQ
```

---

### How It Works — Abstract Pipeline

Three stages run in sequence. The middle stage is where AI is used.

```mermaid
flowchart TD
    INPUT1["📄 Requirements file\nCSV · Excel · JSON · DOORS HTML · Plain text"]
    INPUT2["💻 Source files\nC · C++ · Python · Java"]
    INPUT3["⚙️ tm_config.yaml\nlanguage · model · paths · thresholds"]

    INPUT1 & INPUT2 & INPUT3 --> STAGE1

    subgraph STAGE1["① PARSE"]
        direction LR
        P1["Extract every requirement\n→ id  description  SHA-256 hash"]
        P2["Extract every function\n→ name  file  line  signature  body  inline refs  SHA-256 hash"]
    end

    STAGE1 --> STAGE2

    subgraph STAGE2["② MAP  —  2-Pass AI per requirement"]
        direction LR
        M1["Pass 1 — TF-IDF shortlist\nScore all functions against the requirement text\nKeep top-K candidates  cheap and fast"]
        M2["Pass 2 — LLM reasoning\nSend requirement + candidates to Claude or GPT\nModel returns MAPPED or UNMAPPED + confidence + reason"]
        M1 --> M2
    end

    STAGE2 --> STAGE3

    subgraph STAGE3["③ OUTPUT + VALIDATE"]
        direction LR
        O1["Write all TM files\ncheck integrity  mapped + unmapped = total\nflag LOW-confidence items for review"]
        O2["Save tm_state.json\nstores hashes of everything processed\nused by the next run"]
    end

    STAGE3 --> DONE["📁 Outputs ready"]

    subgraph MAINTAIN["Keep it up to date automatically"]
        INC["Incremental mode\nSHA-256 diff detects changes\nOnly the affected requirements are re-mapped\n90 %+ of LLM calls saved on typical edits"]
        WATCH["Watch mode\nFile-system watcher auto-triggers\nan incremental run on every save"]
        CI["CI/CD\nGitHub Actions runs on every push\nauto-commits updated TM back to the repo"]
    end

    O2 -.->|"read by next run"| INC
    INC & WATCH & CI -.->|"re-enter pipeline"| STAGE1
```

---

## 1. Module Map

Eight Python modules make up the package. Parsing is handled upstream by the SDLC pipeline.

```mermaid
graph TB
    subgraph entry["Entry Points"]
        MM["__main__.py\npython -m tm_pipeline"]
        CLI["CLI\n--config  --mode  --reqs-file  --fns-file  --log"]
    end

    subgraph upstream["Your SDLC Pipeline  (upstream)"]
        UP1["Requirement Analysis phase\n→ parsed_reqs.json"]
        UP2["Static Analysis phase\n→ parsed_functions.json"]
    end

    subgraph orch["Orchestrator"]
        MAIN["main.py\nrun_full\nrun_incremental\nrun_watch\nrun_validate"]
    end

    subgraph pipeline["Pipeline Steps"]
        S3["llm_mapper.py\nStep 1 — TF-IDF + LLM Mapping"]
        S4["output_generator.py\nStep 2 — Write Outputs"]
        S5["change_detector.py\nStep 3 — Detect Changes"]
        S6["watcher.py\nStep 4 — File Watcher"]
    end

    subgraph support["Support"]
        VA["validate.py\nIntegrity Checks"]
        UT["utils.py\nhash · save_json · with_retry"]
    end

    MM --> MAIN
    CLI --> MAIN
    UP1 & UP2 -->|"--reqs-file / --fns-file"| MAIN
    MAIN --> S3 & S4 & S5 & VA
    MAIN --> S6
    S6 -->|"debounced trigger"| MAIN

    S3 & S4 & VA --> UT
```

---

## 2. Module Dependencies

Arrows show `import` relationships. `utils.py` is the only shared leaf.

```mermaid
graph LR
    MM["__main__.py"] --> MAIN["main.py"]

    MAIN --> S3["llm_mapper.py"]
    MAIN --> S4["output_generator.py"]
    MAIN --> S5["change_detector.py"]
    MAIN --> VA["validate.py"]
    MAIN --> S6["watcher.py"]

    S3 & S4 & VA --> UT["utils.py"]

    S6 -->|"calls run_incremental callback"| MAIN
```

---

## 3. Full Run Flow  (`--mode full`)

Every requirement is mapped from scratch. Used when there is no previous state or when a complete refresh is needed.

```mermaid
flowchart TD
    A(["python -m tm_pipeline --mode full\n  --reqs-file parsed_reqs.json\n  --fns-file  parsed_functions.json"]) --> B["Load tm_config.yaml"]

    B --> C["Load  parsed_reqs.json\n→ list of req dicts  { id, description, hash }"]
    B --> D["Load  parsed_functions.json\n→ list of function dicts  { name, file, line_start, … hash }"]

    C --> E{any reqs?}
    E -- No --> FAIL(["Abort — no requirements loaded"])
    E -- Yes --> F["llm_mapper  ·  run_mapping\nFor each req:\n  Pass 1 — TF-IDF shortlist top-K fns\n  Pass 2 — LLM call with candidates\n→ list of LLMResult dicts"]
    D --> F

    F --> G["output_generator  ·  generate_all_outputs\n① AUTO-REQ-CODE-TM.md\n② AUTO-Unmapped-REQ.md\n③ tm_report.json\n④ tm_review_queue.md"]
    G --> H["Save  tm_state.json\nreq_hashes + fn_hashes + tm + unmapped + last_run"]
    H --> I["validate  ·  run_validation\nCount integrity · No dup IDs\nEmpty mappings · Phantom fns\nLOW-confidence % · Staleness"]
    I --> J(["Done"])
```

---

## 4. Incremental Run Flow  (`--mode incremental`)

Only re-maps requirements affected by changes since the last run. Reads and updates `tm_state.json`.

```mermaid
flowchart TD
    A(["python -m tm_pipeline --mode incremental"]) --> B["Load tm_config.yaml"]
    B --> C{"tm_state.json\nexists?"}
    C -- No --> D(["Fallback → Full Run"])
    C -- Yes --> E["Load state\n{ req_hashes, fn_hashes, tm, unmapped }"]

    E --> F["Load  parsed_reqs.json\n→ list of req dicts"]
    E --> G["Load  parsed_functions.json\n→ list of function dicts"]

    F --> H["change_detector  ·  detect_changes\nCompare SHA-256 hashes\nnew / modified / deleted reqs & fns"]
    G --> H

    H --> I["change_detector  ·  compute_reqs_to_remap\nRule 1  new or modified reqs\nRule 2  reqs mapped to changed fns\nRule 3  new public fns → all unmapped reqs"]

    I --> J{"anything\nto remap?"}
    J -- No --> K(["Done — outputs are up to date"])
    J -- Yes --> L["llm_mapper  ·  run_mapping\nonly the affected subset of reqs"]

    L --> M["change_detector  ·  apply_incremental_results\nMerge LLM results into state\nHandle deletions + refresh hashes"]
    M --> N["change_detector  ·  state_to_results\nReconstruct full results list from state"]
    N --> O["output_generator  ·  generate_all_outputs\nRewrite all TM output files"]
    O --> P["Save updated  tm_state.json"]
    P --> Q["validate"]
    Q --> R(["Done"])
```

---

## 5. Watch Mode Flow  (`--mode watch`)

Runs one incremental pass on startup, then blocks and re-runs after each debounced file-change event.

```mermaid
flowchart TD
    A(["python -m tm_pipeline --mode watch"]) --> B["Run Incremental once on start"]
    B --> C["watcher  ·  start_watcher\nObserver on:\n  parsed_reqs.json parent dir\n  parsed_functions.json parent dir"]

    C --> D{{"Watching…\n(blocking)"}}
    D -->|"*.json saved"| E["Reset debounce timer\n(default 5 s)"]
    E --> F{"Another save\nbefore timer fires?"}
    F -- Yes --> E
    F -- No  --> G["_DebouncedHandler._fire\nTrigger run_incremental(config)"]
    G --> H["Outputs updated"]
    H --> D
    D -->|"Ctrl-C"| I(["Stop"])
```

---

## 6. Validate-Only Flow  (`--mode validate`)

No LLM calls, no file writes. Reads the last `tm_report.json` and checks integrity.

```mermaid
flowchart TD
    A(["python -m tm_pipeline --mode validate"]) --> B["Load tm_config.yaml"]
    B --> C["Read  tm_report.json"]
    B --> D["Read  tm_state.json  (optional)"]

    C --> E["_check_count_integrity\nmapped + unmapped == total  HARD"]
    C --> F["_check_no_duplicate_ids\neach req_id appears once  HARD"]
    C --> G["_check_no_empty_mappings\nevery MAPPED req has ≥ 1 fn  HARD"]
    C --> H["_check_no_phantom_functions\nwarn if fn has no file location  WARN"]
    C --> I["_check_confidence_coverage\nwarn if LOW > 10%  WARN"]
    D --> J["_check_staleness\nwarn if state > 24 h older than report  WARN"]

    E & F & G & H & I & J --> K{"all hard\nchecks pass?"}
    K -- Yes --> L(["Exit 0 — PASSED"])
    K -- No  --> M(["Exit 1 — FAILED"])
```

---

## 7. Two-Pass LLM Mapping Strategy

Inside `llm_mapper.run_mapping()` — called once per requirement.

```mermaid
flowchart LR
    REQ["Requirement\n{ id, description }"]
    FNS["All Functions\n{ name, body_text,\nsignature, comments,\ninline_refs }"]

    REQ --> P1["Pass 1 — TF-IDF\nbuild_function_text per fn\ntfidf_shortlist → top-K indices"]
    FNS --> P1

    P1 --> CAND["Top-K candidates\n+ inline-ref fns always included"]

    CAND --> P2["Pass 2 — LLM\nbuild_user_prompt\ncall_llm\n  anthropic  →  client.messages.create\n  openai     →  chat.completions.create"]

    P2 --> PARSE["_parse_response\nstrip markdown fences\nJSON decode\nfallback on parse error"]

    PARSE --> CONF["apply_confidence_rules\nupgrade to HIGH if\nreq ID found in fn inline_refs"]

    CONF --> RES["LLMResult\n{ req_id,\n  status: MAPPED/UNMAPPED,\n  mappings: [{ function,\n               confidence,\n               reason }],\n  unmapped_reason }"]
```

---

## 8. Key Data Structures

Shapes and arrows show what data each module produces and consumes.

```mermaid
graph TD
    subgraph inputs["External Inputs"]
        CFG["tm_config.yaml"]
        RF["Requirements file\n.json / .csv / .xlsx\n/ .html / .txt"]
        SRC["Source files\n.c / .h / .py / .java"]
        ST_IN["tm_state.json  (prior run)"]
    end

    subgraph types["Core Data Types"]
        REQ_T["Requirement dict\n{ id, description, hash }"]
        FN_T["Function dict\n{ name, file, line_start, line_end,\n  signature, body_text,\n  comments, inline_refs, hash }"]
        RES_T["LLMResult dict\n{ req_id, status,\n  mappings, unmapped_reason }"]
        CHG_T["ChangeSet dict\n{ new/modified/deleted reqs,\n  new/modified/deleted fns }"]
        STATE_T["State dict\n{ last_run, req_hashes,\n  fn_hashes, tm, unmapped }"]
    end

    subgraph outputs["Generated Outputs"]
        TM_MD["AUTO-REQ-CODE-TM.md"]
        UN_MD["AUTO-Unmapped-REQ.md"]
        REP_J["tm_report.json"]
        REV_MD["tm_review_queue.md"]
        ST_OUT["tm_state.json"]
    end

    CFG & RF --> REQ_T
    CFG & SRC --> FN_T
    ST_IN & REQ_T & FN_T --> CHG_T
    REQ_T & FN_T --> RES_T
    CHG_T & RES_T --> STATE_T

    RES_T --> TM_MD & UN_MD & REP_J & REV_MD
    STATE_T --> ST_OUT
```

---

## 9. File & Output Map

```mermaid
graph LR
    subgraph pkg["tm_pipeline/  (package)"]
        direction TB
        MM2["__main__.py"]
        MAIN2["main.py"]
        S32["llm_mapper.py"]
        S42["output_generator.py"]
        S52["change_detector.py"]
        S62["watcher.py"]
        VA2["validate.py"]
        UT2["utils.py"]
    end

    subgraph cfg["Config"]
        CFG2["tm_config.yaml"]
    end

    subgraph ci["CI/CD"]
        GHA[".github/workflows/\ntm_update.yml"]
    end

    subgraph out["Generated Outputs"]
        TM2["AUTO-REQ-CODE-TM.md"]
        UN2["AUTO-Unmapped-REQ.md"]
        REP2["tm_report.json"]
        REV2["tm_review_queue.md"]
        ST2["tm_state.json"]
    end

    CFG2 --> MAIN2
    pkg --> out
    GHA -->|"runs on push"| MAIN2
```
