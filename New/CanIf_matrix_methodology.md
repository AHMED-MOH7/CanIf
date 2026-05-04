# How the Traceability Matrix Was Built — Methodology

> This document explains the exact process, rules, and decisions used to create  
> `CanIf_traceability_matrix.md`. Read this first if you need to update or audit the matrix.

---

## 1. What Is a Requirements-to-Code Traceability Matrix?

A **Traceability Matrix** is a table that links every requirement to the exact code that implements (or fails to implement) it.

**Why it matters:**
- Proves that every requirement has been considered
- Shows which requirements have code coverage and which don't
- Identifies code that exists without a backing requirement (potential scope creep)
- Used in automotive software audits (ISO 26262, ASPICE)

---

## 2. Inputs Used

| Input | File | What I extracted |
|-------|------|-----------------|
| Requirements | `Requirments/CanIf_SWS_AR403.csv` | All SWS_CANIF_XXXXX IDs + their descriptions |
| Source code | `OpenSAR/communication/CanIf/CanIf.c` | All functions, line numbers, logic flow |
| Header (API) | `OpenSAR/include/CanIf.h` | Function signatures + service IDs |
| Types | `OpenSAR/include/CanIf_ConfigTypes.h` | All structs, enums, data types |
| Config flags | `OpenSAR/app/config/GEN/CanIf_Cfg.h` | Which features are ON/OFF at compile time |
| Config data | `OpenSAR/app/config/GEN/CanIf_Cfg.c` | Actual PDU tables, HOH tables, callbacks |
| Full spec | `AUTOSAR_SWS_CANInterface.pdf` | Context for ambiguous requirements |

---

## 3. Step-by-Step Process

### Step 1 — Read and understand the entire code

Before touching requirements, I read `CanIf.c` completely (996 lines) and built a full mental model:
- Identified every function (30 total)
- Noted which are public API, which are internal helpers, which are callbacks
- Noted which are stubs (always return E_NOT_OK or do nothing)
- Identified all conditional compilation blocks (`#if CANIF_DLC_CHECK`, `#if defined(USE_CANTP)`, etc.)
- Mapped compile-time feature flags from `CanIf_Cfg.h`

This produced the **function inventory** in `CanIf_explain.md`.

### Step 2 — Parse and group the requirements

The CSV file has no grouping — all ~164 requirement IDs appear in one flat list. I:
1. Extracted every `SWS_CANIF_XXXXX` ID
2. Read each description carefully
3. Grouped them by **functional topic** (18 groups)

**Grouping rule used:** Put a requirement in the group of the primary function or feature it describes. If a requirement is about errors/validation for a specific function, it goes in that function's group.

### Step 3 — Map each requirement to code

For each requirement, I asked four questions:

**Q1: Is this requirement about a feature that is compile-time disabled?**  
→ If `STD_OFF` or `#if` guard prevents it → Status = 🔧 DISABLED  
→ These are NOT bugs — they are intentional configuration choices

**Q2: Is there a function in `CanIf.c` that directly implements this?**  
→ Yes + complete → Status = ✅ IMPLEMENTED  
→ Record function name + exact line numbers

**Q3: Is the function present but only partially implements the requirement?**  
→ Partial = function exists and handles the main case but misses a sub-condition  
→ Status = ⚠️ PARTIAL  
→ Record what IS done and what IS missing

**Q4: Is there no code at all for this requirement?**  
→ Status = ❌ NOT DONE  
→ Sub-type: 🆕 MISSING API = the entire function doesn't exist in the file

### Step 4 — Verify by cross-referencing

After mapping, I checked each group for consistency:
- Does every `VALIDATE(...)` call in the code match a requirement?
- Does every `Can_Write()` / `Can_SetControllerMode()` call satisfy the requirement that demands it?
- Are there code blocks with no requirement backing them?

---

## 4. Status Code Definitions

| Symbol | Name | Meaning | Example |
|--------|------|---------|---------|
| ✅ | IMPLEMENTED | Requirement fully satisfied by code | `CanIf_Init()` satisfies SWS_CANIF_00085 |
| ⚠️ | PARTIAL | Main behavior done, sub-condition missing | Transmit() checks mode but doesn't call DET for OFFLINE |
| ❌ | NOT DONE | No code implements this | Tx buffering — entire Group F |
| 🔧 | DISABLED | Feature intentionally turned off via compile flag | `CANIF_TRANSCEIVER_API = STD_OFF` |
| 🆕 | MISSING API | The entire function doesn't exist in the file | `CanIf_ControllerModeIndication()` |
| N/A | NOT APPLICABLE | Feature depends on another disabled feature | MetaData requirements when dynamic PDUs are OFF |

---

## 5. How Code Locations Were Determined

For each mapped requirement, code location is specified as:

```
FunctionName() — line X (to line Y)
```

Line numbers were taken directly from `CanIf.c` as read:
- `CanIf_Init()` → lines 131–146
- `CanIf_InitController()` → lines 156–204
- `CanIf_PreInit_InitController()` → lines 206–222
- `CanIf_SetControllerMode()` → lines 226–318
- `CanIf_GetControllerMode()` → lines 322–335
- `CanIf_FindTxPduEntry()` → lines 344–354
- `CanIf_FindRxPduEntry()` → lines 358–364 (runtime only)
- `CanIf_Arc_GetReceiveHandler()` → lines 366–391 (runtime only)
- `CanIf_Arc_GetTransmitHandler()` → lines 393–418 (runtime only)
- `CanIf_Transmit()` → lines 423–482
- `CanIf_ReadRxPduData()` → lines 487–497
- `CanIf_ReadTxNotifStatus()` → lines 503–527
- `CanIf_ReadRxNotifStatus()` → lines 533–539
- `CanIf_SetPduMode()` → lines 544–628
- `CanIf_GetPduMode()` → lines 632–644
- `CanIf_SetDynamicTxId()` → lines 647–680 (runtime only)
- `CanIf_SetTransceiverMode()` → lines 684–691
- `CanIf_GetTransceiverMode()` → lines 693–700
- `CanIf_GetTrcvWakeupReason()` → lines 702–709
- `CanIf_SetTransceiverWakeupMode()` → lines 711–718
- `CanIf_CheckWakeup()` → lines 722–728
- `CanIf_CheckValidation()` → lines 730–736
- `CanIf_TxConfirmation()` → lines 742–761
- `CanIf_RxIndication()` → lines 763–898
- `CanIf_CancelTxConfirmation()` → lines 901–914
- `CanIf_ControllerBusOff()` → lines 917–941
- `CanIf_SetWakeupEvent()` → lines 943–961
- `CanIf_Arc_Error()` → lines 963–989
- `CanIf_Arc_GetChannelDefaultConfIndex()` → lines 991–994

---

## 6. Decisions Made During Mapping

### Decision 1: Architecture requirements vs. code requirements

Some requirements (SWS_CANIF_00023, SWS_CANIF_00662, etc.) describe the **design principle** of the module, not a specific code line. These were mapped to the module as a whole or to the relevant data structures in header files.

**Rule applied:** If a requirement is satisfied by the structure/design rather than a single function, map it to the config files or header files and mark ✅ if the design consistently follows the principle.

### Decision 2: Disabled features

When a feature is disabled by a compile flag (e.g., `CANIF_TRANSCEIVER_API = STD_OFF`), the requirements for that feature are marked 🔧 DISABLED — **not** ❌ NOT DONE.

**Reasoning:** The code *does* handle these correctly — it correctly excludes the feature. A "NOT DONE" would imply the developer forgot or made an error.

### Decision 3: Stub functions

Functions like `CanIf_ReadRxPduData()` exist in code but immediately return `E_NOT_OK` with a `VALIDATE(FALSE, ...)` call. These were mapped to their requirements as 🔧 DISABLED (the API exists for compilation compatibility but the feature is off).

### Decision 4: ArcCore extensions

`CanIf_Arc_Error()`, `CanIf_Arc_FindHrhChannel()`, `CanIf_Arc_GetChannelDefaultConfIndex()`, and `CanIf_PreInit_InitController()` have **no AUTOSAR requirement ID**. These were documented in the "Excess Code" section only.

### Decision 5: Configuration requirements

Many requirements describe what fields must exist in config structs (e.g., SWS_CANIF_00414 says each Tx PDU must have a TxConfirmation callback). These were mapped to:
- The struct field in `CanIf_ConfigTypes.h`
- AND the config data in `CanIf_Cfg.c`
- AND the code that uses that field at runtime

### Decision 6: Partial vs. Not Done

A requirement is **PARTIAL** (not NOT DONE) when:
- The main functionality works
- But one specific error code, DET call, or edge case is missing
- The omission is detectable only by looking at the specific requirement text

A requirement is **NOT DONE** when:
- No code path even attempts the behavior
- The code comment explicitly says "not supported"
- The entire function is missing from the file

---

## 7. Validation Check — Coverage of Code

As a final cross-check, every significant code block in `CanIf.c` was verified to have at least one requirement mapped to it:

| Code Block | Requirement(s) |
|-----------|---------------|
| `VALIDATE_NO_RV(ConfigPtr != 0, ...)` in Init | SWS_CANIF_00085 |
| `CanIf_Global.channelData[i].PduMode = CANIF_GET_OFFLINE` | SWS_CANIF_00864 |
| `CanIf_PreInit_InitController()` call in Init | ArcCore extension (no AUTOSAR req) |
| `Can_SetControllerMode(CAN_T_START)` | SWS_CANIF_00308 |
| `CanIf_SetPduMode(channel, CANIF_SET_ONLINE)` in SetControllerMode | SWS_CANIF_00075 |
| `CanIf_SetPduMode(channel, CANIF_SET_OFFLINE)` in SetControllerMode | SWS_CANIF_00073 |
| `if (csMode != CANIF_CS_STARTED)` in Transmit | SWS_CANIF_00317, SWS_CANIF_00677 |
| `if (pduMode != CANIF_GET_TX_ONLINE && != CANIF_GET_ONLINE)` | SWS_CANIF_00317, SWS_CANIF_00073 |
| `Can_Write(txEntry->CanIfCanTxPduHthRef->CanIfHthIdSymRef, &canPdu)` | SWS_CANIF_00318 |
| `if (rVal == CAN_BUSY) return E_NOT_OK` | SWS_CANIF_00381 (partial — no buffering) |
| `if (rVal == CAN_NOT_OK) return E_NOT_OK` | SWS_CANIF_00162 (inverse) |
| `return E_OK` at end of Transmit | SWS_CANIF_00162 |
| Software filter MASK check in RxIndication | SWS_CANIF_00211, SWS_CANIF_00389 |
| `if (CanDlc < entry->CanIfCanRxPduDlc)` | SWS_CANIF_00026, SWS_CANIF_00390 |
| PduR routing `PduR_CanIfRxIndication()` | SWS_CANIF_00442, SWS_CANIF_00135 |
| CanTp routing `CanTp_RxIndication()` | SWS_CANIF_00448, SWS_CANIF_00135 |
| CanNm routing `CanNm_RxIndication()` | SWS_CANIF_00445, SWS_CANIF_00135 |
| J1939Tp routing `J1939Tp_RxIndication()` | SWS_CANIF_00554, SWS_CANIF_00135 |
| `entry->CanIfUserTxConfirmation(...)` | SWS_CANIF_00383 |
| `CanIf_SetControllerMode(channel, CANIF_CS_STOPPED)` in BusOff | SWS_CANIF_00724, SWS_CANIF_00866 |
| `CanIfBusOffNotification(channel)` | SWS_CANIF_00724 |
| `CanIfErrorNotificaton(Controller, Error)` in Arc_Error | SWS_CANIF_00920 (partial) |

All significant code blocks have at least one requirement. No "orphan" code was found beyond the six ArcCore extensions noted above.

---

## 8. How to Update the Matrix

When code changes:
1. Find which function was changed
2. Look up that function's requirements in Group column of the matrix
3. Re-evaluate status (✅ / ⚠️ / ❌ / 🔧)
4. Update the Notes column with what changed

When requirements change:
1. Find the requirement ID in the matrix
2. Check if new description adds new code obligations
3. Add a new row if it's a new requirement
4. Update status if existing code now satisfies or breaks it

---

## 9. Tools Used

| Task | Method |
|------|--------|
| Read source code | Full file read (996 lines), read header files |
| Extract requirement IDs | Manual parsing of CSV text blob |
| Group requirements | Semantic analysis of requirement text |
| Map requirements to code | Line-by-line code reading + requirement matching |
| Identify gaps | Cross-referencing both directions (req→code, code→req) |
| Write matrix | Markdown table format, one row per requirement |
