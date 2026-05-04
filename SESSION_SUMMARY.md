# Session Summary — CANIF Project Work Log

> **Read this file at the start of every new session to restore full context.**  
> Last updated: 2026-05-04

---

## 1. Project Overview

You are working on a graduation project titled:
**"Optimizing Software Development Life Cycle (SDLC) using Artificial Intelligence (AI)"**
- PDF: `D:\ASU\GradProject\CANIF\Optimizing_Software_Development_Life_Cycle_using_AI[1].pdf`
- The project has 4 categories: Analysis & Design, Implementation, Testing, Maintenance
- All TM work done so far belongs to **Category 2 — Implementation** (Code Traceability Check + Change Impact Propagation)

The specific module under analysis is **AUTOSAR CanIf (CAN Interface) AR 4.0.3** implemented in **OpenSAR** (open-source AUTOSAR stack).

---

## 2. Source Files

| File | Purpose |
|:---|:---|
| `D:\ASU\GradProject\CANIF\Requirments\CanIf_SWS_AR403.csv` | 273 AUTOSAR CanIf requirements (source of truth) |
| `D:\ASU\GradProject\CANIF\OpenSAR\communication\CanIf\CanIf.c` | CanIf implementation (OpenSAR) |
| `D:\ASU\GradProject\CANIF\TM (ALL 273 REQ in csv)\REQ-CODE-TM.txt` | **Traceability Matrix** — 104 rows (req → function mapping) |
| `D:\ASU\GradProject\CANIF\TM (ALL 273 REQ in csv)\Unmapped-RE-CODE.txt` | **Unmapped requirements** — 169 rows (reqs with no implementation) |
| `D:\ASU\GradProject\CANIF\TM (ALL 273 REQ in csv)\CanIf_Requirement_Change_Test_Specification.md` | **Test specification** — 13 test cases covering all change types |
| `D:\ASU\GradProject\CANIF\TM (ALL 273 REQ in csv)\Impact-Analyzer-Test-Specification.txt` | Older plain-text version of test spec (superseded, keep for reference) |
| `D:\ASU\GradProject\CANIF\TM_AutoGeneration_Guide.md` | **TM automation guide** — how to auto-generate + keep TM updated using LLM API |

---

## 3. Traceability Matrix (REQ-CODE-TM.txt) — What Was Done

### 3.1 Format
Changed from plain tab-separated text to **markdown table**:
```
| Req ID | CanIf.c function(s) / (description from csv) |
```

### 3.2 Corrections Made
Three requirements were **removed** from the TM (they were incorrectly mapped):

| Req ID | Was mapped to | Why removed |
|:---|:---|:---|
| `SWS_CANIF_00918` | `CanIf_ControllerBusOff` | Req requires security event `CANIF_SEV_ERRORSTATE_BUSOFF` — not implemented. `CanIf_ControllerBusOff()` only calls `CanIfBusOffNotification` and `CanIf_SetControllerMode`, no security event reporting. |
| `SWS_CANIF_00920` | `CanIf_Arc_Error` | Req requires `CanIf_ErrorNotification()` AUTOSAR API — not implemented. `CanIf_Arc_Error()` calls ArcCore-proprietary `CanIfErrorNotificaton` callback, which is NOT the AUTOSAR API. |
| `SWS_CANIF_00921` | `CanIf_Arc_Error` | Same reason as SWS_CANIF_00920. |

These three were **added to `Unmapped-RE-CODE.txt`** instead.

### 3.3 One Mapping Kept (user confirmed correct)
`SWS_CANIF_00551` → `CanIf_RxIndication` — kept in TM. User confirmed this is correct even though it was flagged as potentially duplicate.

### 3.4 Final Count
- **TM (mapped):** 104 rows
- **Unmapped:** 169 rows  
- **Total:** 104 + 169 = **273** ✓ (matches total CSV count)

---

## 4. Test Specification (CanIf_Requirement_Change_Test_Specification.md) — What Was Done

### 4.1 Purpose
A **completely standalone, professional AUTOSAR-style document**. It does NOT reference any external system, tool, or project. It is a self-contained engineering reference showing: "if I change requirement X (Functional/NF/Cosmetic/etc.), what is the expected behavior/output?"

### 4.2 Important Constraint
**CRITICAL: This document has zero mentions of "impact analyzer", "delta-detector", "change propagation", or any tool.** The user was very explicit: "don't relate to anything this is the most important thing i need it independent document."

### 4.3 The 13 Test Cases

| TC ID | Req ID | Category | Function(s) Affected | Code Change Summary |
|:---|:---|:---|:---|:---|
| TC-CANIF-F-01 | SWS_CANIF_00308 | Functional | `CanIf_SetControllerMode` | Replace `Can_SetControllerMode()` with `Can_InitController()` — 6 call sites |
| TC-CANIF-F-02 | SWS_CANIF_00311 | Functional | `CanIf_SetControllerMode` | Line 236: `CANIF_E_PARAM_CONTROLLER` → `CANIF_E_PARAM_POINTER` |
| TC-CANIF-F-03 | SWS_CANIF_00864 | Functional | `CanIf_Init` | Line 140: `CANIF_GET_OFFLINE` → `CANIF_GET_ONLINE` |
| TC-CANIF-F-04 | SWS_CANIF_00162 | Functional | `CanIf_Transmit` | Line 481: `return E_OK` → `return E_NOT_OK` |
| TC-CANIF-NF-01 | SWS_CANIF_00308 | Non-Functional | `CanIf_SetControllerMode` | Line 226: `uint8 Controller` → `uint16 Controller` (ABI-breaking) |
| TC-CANIF-NF-02 | SWS_CANIF_00026 | Non-Functional | `CanIf_RxIndication` | Line 824: `CanDlc < ...` → `CanDlc != ...` |
| TC-CANIF-C-01 | SWS_CANIF_00423 | Cosmetic | `CanIf_RxIndication` | **NO CODE CHANGE** — editorial wording only |
| TC-CANIF-C-02 | SWS_CANIF_00552 | Cosmetic | `CanIf_RxIndication` | **NO CODE CHANGE** — cross-reference number updated |
| TC-CANIF-XD1N-01 | SWS_CANIF_00866 | Cross-Depend 1→2 | `CanIf_SetControllerMode` + `CanIf_ControllerBusOff` | PDU mode on STOPPED: `CANIF_TX_OFFLINE` → `CANIF_OFFLINE` in both functions |
| TC-CANIF-XD1N-02 | SWS_CANIF_00073 | Cross-Depend 1→3 | `CanIf_Transmit` + `CanIf_TxConfirmation` + `CanIf_RxIndication` | Line 778: remove `CANIF_GET_OFFLINE` from RxIndication drop-condition |
| TC-CANIF-XDN1-01 | SWS_CANIF_00311 + 00774 | Cross-Depend 2→1 | `CanIf_SetControllerMode` | Two changes in one function: swap error code + remove mode validation |
| TC-CANIF-XDN1-02 | SWS_CANIF_00389 + 00390 + 00902 | Cross-Depend 3→1 | `CanIf_RxIndication` | Add DET log on filter reject + move DLC check before filter + remove `#if CANIF_DLC_CHECK` guard |
| TC-CANIF-CB-01 | 00308+00026+00423+00073 | Combined | `CanIf_SetControllerMode` + `CanIf_Transmit` + `CanIf_TxConfirmation` + `CanIf_RxIndication` | All 4 change types simultaneously; has inner breakdown table + aggregated impact summary |

### 4.4 Document Structure
1. Purpose (standalone, no external system references)
2. Scope
3. Change Category Definitions table
4. Test Case Template — Column Definitions
5. 13 Test Cases (each in vertical `| Field | Details |` table)
6. Test Coverage Matrix
7. 7 Key Engineering Rules

---

## 5. TM Automation Guide (TM_AutoGeneration_Guide.md) — What Was Done

Created a deep step-by-step implementation guide for automatically generating and maintaining the TM using an enterprise LLM API.

### 5.1 Key Design Decisions

| Decision | Choice | Reason |
|:---|:---|:---|
| LLM shortlisting | TF-IDF (fallback) or Embeddings API | Avoid O(reqs × functions) API calls |
| LLM reasoning | One call per req with top-8 candidates | Accurate, targeted, cost-controlled |
| Config | `tm_config.yaml` — all module-specific paths | General purpose — new module = new config file only |
| Update strategy | Incremental (hash-based change detection) | Re-run LLM only for changed items |
| Code parser | tree-sitter (AST) for C/C++ | Handles macros, `#ifdef`, complex constructs |
| Output | `.md` (human) + `.json` (machine) | TM for humans, `tm_report.json` for impact analyzer |

### 5.2 Pipeline Architecture
```
Requirements file → REQ PARSER → [{id, description, hash}]
Source files      → CODE PARSER → [{name, signature, body, hash}]
                                          ↓
                              CHANGE DETECTOR (hash diff vs tm_state.json)
                                          ↓
                              LLM MAPPER (only changed subset)
                              Pass 1: TF-IDF shortlist → top-8 candidates per req
                              Pass 2: LLM API call → {MAPPED/UNMAPPED, confidence}
                                          ↓
                              OUTPUT GENERATOR
                              → REQ-CODE-TM.md
                              → Unmapped-REQ.md
                              → tm_report.json  ← consumed by impact analyzer
                              → tm_state.json   ← incremental state
```

### 5.3 Two Operating Modes
- `--mode full` : Parse and map everything from scratch
- `--mode incremental` : Detect file changes by hash, re-map only what changed

### 5.4 CI/CD Integration Provided
- Git pre-commit hook (bash)
- GitHub Actions workflow YAML
- GitLab CI job YAML
- Local file-watcher (watchdog)

### 5.5 Enterprise LLM API
- API key via environment variable `TM_LLM_API_KEY` (never hardcoded)
- Supports Anthropic Claude (default), OpenAI, Azure OpenAI
- Switch provider by changing `llm.provider` in `tm_config.yaml`
- Exponential backoff retry for rate limits

### 5.6 Next Step
User said: **"i will give you later so you implement it"** — the guide is the spec. When user asks, implement the actual Python code for `tm_pipeline/` directory.

---

## 6. Key CanIf.c Code Locations (Reference)

| Function | Line | Notes |
|:---|:---|:---|
| `CanIf_Arc_FindHrhChannel` | 100 | Static helper, maps HRH to channel |
| `CanIf_Init` | 131 | Sets `PduMode = CANIF_GET_OFFLINE` at line 140, `ControllerMode = CANIF_CS_STOPPED` at line 139 |
| `CanIf_SetControllerMode` | 226 | ControllerId validation at line 236; switch-case with 6 `Can_SetControllerMode()` calls |
| `CanIf_Transmit` | 423 | Calls `Can_Write()` at line 469; returns `E_OK` at line 481 |
| `CanIf_TxConfirmation` | 742 | Mode check at line 754; calls `entry->CanIfUserTxConfirmation()` at line 757 |
| `CanIf_RxIndication` | 763 | Channel lookup at 770; mode check (drop condition) at 778; software filter at 800–820; DLC check at 824 (guarded by `#if CANIF_DLC_CHECK == STD_ON`) |
| `CanIf_ControllerBusOff` | 917 | Calls `CanIf_SetControllerMode(channel, CANIF_CS_STOPPED)` at 935; NO security event reporting |
| `CanIf_Arc_Error` | 963 | ArcCore-proprietary error callback — NOT the AUTOSAR `CanIf_ErrorNotification()` API |

---

## 7. What Still Needs to Be Done (Next Sessions)

1. **Implement the TM automation pipeline** (`tm_pipeline/` Python code) — user will ask for this
2. **Impact Analyzer** — Phase 2 of the change-propagation system; reads `tm_report.json` and outputs which functions are affected by a changed requirement
3. Other SDLC AI project categories (Analysis & Design, Testing, Maintenance) — separate work items

---

*End of Session Summary*
