# CanIf Requirements — Complete Explanation

> **Step 2 of 3** — Full requirements understanding before building the traceability matrix.

---

## Table of Contents

1. [Where Do These Requirements Come From?](#1-where-do-these-requirements-come-from)
2. [How the CSV is Structured](#2-how-the-csv-is-structured)
3. [Requirements Grouped by Function Area](#3-requirements-grouped-by-function-area)
   - [Group A: Architecture & Hardware Abstraction (Foundation)](#group-a-architecture--hardware-abstraction-foundation)
   - [Group B: Initialization](#group-b-initialization)
   - [Group C: Controller Mode Management](#group-c-controller-mode-management)
   - [Group D: PDU Channel Mode Management](#group-d-pdu-channel-mode-management)
   - [Group E: Transmission (Tx Path)](#group-e-transmission-tx-path)
   - [Group F: Tx Buffering](#group-f-tx-buffering)
   - [Group G: Tx Confirmation Callback](#group-g-tx-confirmation-callback)
   - [Group H: Reception & Software Filtering](#group-h-reception--software-filtering)
   - [Group I: Rx Indication Callback Routing](#group-i-rx-indication-callback-routing)
   - [Group J: Rx Buffering & Notification Status](#group-j-rx-buffering--notification-status)
   - [Group K: Dynamic PDU (Runtime CAN ID)](#group-k-dynamic-pdu-runtime-can-id)
   - [Group L: BusOff Handling](#group-l-busoff-handling)
   - [Group M: Controller & Transceiver Mode Indications](#group-m-controller--transceiver-mode-indications)
   - [Group N: Wakeup](#group-n-wakeup)
   - [Group O: Transceiver Management](#group-o-transceiver-management)
   - [Group P: Partial Networking (PN)](#group-p-partial-networking-pn)
   - [Group Q: Security Events](#group-q-security-events)
   - [Group R: Advanced APIs (Error Counters, SetBaudrate, Mirroring, TriggerTransmit)](#group-r-advanced-apis)
4. [Complete Requirements Count by Group](#4-complete-requirements-count-by-group)
5. [Missing Code — Requirements With No Implementation](#5-missing-code--requirements-with-no-implementation)
6. [Excess Code — Code With No Direct Requirement](#6-excess-code--code-with-no-direct-requirement)
7. [Gap Summary Table](#7-gap-summary-table)

---

## 1. Where Do These Requirements Come From?

The file `Requirments/CanIf_SWS_AR403.csv` is a **subset** of the official AUTOSAR document:

> **AUTOSAR_SWS_CANInterface** — Software Specification of CAN Interface  
> Version **AR 4.0.3** (AUTOSAR Release 4)

The ID format `SWS_CANIF_XXXXX` means:
- **SWS** = Software Specification
- **CANIF** = CAN Interface module
- **XXXXX** = Requirement number (not sequential — gaps are normal)

**What these requirements define:**
- What CanIf **must do** (mandatory behavior)
- What CanIf **shall report** (error codes, callbacks)
- How CanIf **shall be configured** (compile-time flags, config containers)
- What CanIf **shall call** in upper/lower layers (APIs it uses)

---

## 2. How the CSV is Structured

The CSV has two columns:
- **ID**: e.g., `SWS_CANIF_00085`
- **Description**: plain-English sentence describing what CanIf must do

**Total requirements in CSV: approximately 164 unique requirement IDs**

> Note: The `.xlsx` and `.docx` files in the `Requirments/` folder contain the same content in richer format. The PDF `AUTOSAR_SWS_CANInterface.pdf` in the root is the full official specification (the CSV is a curated extract).

---

## 3. Requirements Grouped by Function Area

Below, every requirement is placed in its logical group with a simple explanation of what it means and which code area it touches.

---

### Group A: Architecture & Hardware Abstraction (Foundation)

These requirements define the fundamental design of CanIf — how it abstracts hardware and how it talks to the CAN driver.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00023 | CanIf must NEVER directly touch hardware buffers — only use Can driver API | Entire design; `Can_Write()`, `Can_InitController()` calls in CanIf.c |
| SWS_CANIF_00662 | CanIf uses two types of hardware handles: HTH (transmit) and HRH (receive) | `CanIf_HthConfigType`, `CanIf_HrhConfigType` in CanIf_ConfigTypes.h |
| SWS_CANIF_00291 | Define what HRH is: a handle for a hardware receive mailbox | `CanIf_HrhConfigType` struct |
| SWS_CANIF_00292 | Define what HTH is: a handle for a hardware transmit mailbox | `CanIf_HthConfigType` struct |
| SWS_CANIF_00665 | HRH enables BasicCAN or FullCAN reception and routes to upper layer | `CanIf_RxIndication()` routing logic |
| SWS_CANIF_00663 | If HRH is BasicCAN type → software filtering MUST be enabled | `CanIfSoftwareFilterHrh = TRUE` in HRH config; filter check in `CanIf_RxIndication()` |
| SWS_CANIF_00664 | Each HRH belongs to at least one group of Rx PDU IDs | `CanIfHrhConfigData[]` mapped to `CanIfRxPduConfigData[]` |
| SWS_CANIF_00666 | HTH enables BasicCAN or FullCAN transmission and confirms to upper layer | `CanIf_Transmit()` and `CanIf_TxConfirmation()` |
| SWS_CANIF_00115 | All HRHs and HTHs use one unified numbering space starting from 0 | `CanIf_Arc_FindHrhChannel()` searches by raw HRH ID |
| SWS_CANIF_00653 | CanIf provides a ControllerId that hides which actual CAN hardware driver is used | `CanIf_Arc_ChannelIdType` enum; `Arc_ChannelToControllerMap[]` |
| SWS_CANIF_00655 | CanIf provides a TransceiverId that hides the actual transceiver hardware | Configured but not used (no transceiver in this project) |
| SWS_CANIF_00378 | CanIf accesses CanDrv through function pointers (link-time) | `Can_Write()`, `Can_SetControllerMode()` etc. called by function names |
| SWS_CANIF_00672 | CanIf.h only declares APIs — no implementation inside the header | `CanIf.h` structure |
| SWS_CANIF_00467 | CanIf stores an ordered list of HTHs and HRHs from config | `CanIfHohConfigData[]` in CanIf_Cfg.c |
| SWS_CANIF_00468 | Each HOH has a reference to the hardware acceptance filter | `CanIfHthIdSymRef`, `CanIfHrhIdSymRef` fields in HOH structs |
| SWS_CANIF_00469 | For each BasicCAN HRH, a software acceptance filter can be configured | `CanIfSoftwareFilterHrh` field in `CanIf_HrhConfigType` |
| SWS_CANIF_00281 | CanIf must support both 11-bit Standard CAN IDs and 29-bit Extended IDs on same channel | `CanIfRxPduIdCanIdType`/`CanIfTxPduIdCanIdType` fields |

**Summary:** These are the "what is CanIf" requirements. They define the abstraction layer concept. Most are satisfied by the design and data structures — not by specific code lines, but by the architecture of how things are wired together.

---

### Group B: Initialization

Requirements about what must happen when CanIf is initialized.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00085 | `CanIf_Init()` must initialize all global variables, flags, and buffers | `CanIf_Init()` lines 131–146 |
| SWS_CANIF_00523 | The config structure (`CanIf_ConfigType`) must contain all public params and all PDU definitions | `CanIf_ConfigType` in CanIf_ConfigTypes.h; populated in CanIf_Cfg.c |
| SWS_CANIF_00661 | ALL APIs except `CanIf_Init()` and `CanIf_GetVersionInfo()` must reject calls if not initialized | `VALIDATE(..., CANIF_E_UNINIT)` checks throughout CanIf.c |
| SWS_CANIF_00864 | During init, ALL channels must be switched to `CANIF_OFFLINE` | `CanIf_Global.channelData[i].PduMode = CANIF_GET_OFFLINE` in `CanIf_Init()` line 140 |
| SWS_CANIF_00387 | `CanIf_Init()` must also initialize all Tx L-PDU buffers | **PARTIAL** — `CanIf_Init()` exists but Tx buffers are NOT implemented |
| SWS_CANIF_00857 | `CanIf_Init()` must set dynamic Tx PDU CAN IDs to their configured default value | Not applicable — dynamic PDUs are disabled (`CANIF_ARC_RUNTIME_PDU_CONFIGURATION = STD_OFF`) |

**Summary:** The core of init (`CanIf_Global` setup + OFFLINE mode) is implemented. The missing part is Tx buffer initialization (because Tx buffering is not implemented).

---

### Group C: Controller Mode Management

Requirements about starting, stopping, and sleeping a CAN controller.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00308 | `CanIf_SetControllerMode()` must call `Can_SetControllerMode()` | `Can_SetControllerMode(canControllerId, CAN_T_START/STOP/SLEEP)` in lines 253–310 |
| SWS_CANIF_00311 | Invalid `ControllerId` in `SetControllerMode()` → report `CANIF_E_PARAM_CONTROLLERID` | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` line 236 |
| SWS_CANIF_00774 | Invalid `ControllerMode` value in `SetControllerMode()` → report `CANIF_E_PARAM_CTRLMODE` | NOT done — the switch/case falls through for CANIF_CS_UNINIT without error |
| SWS_CANIF_00313 | Invalid `ControllerId` in `GetControllerMode()` → report `CANIF_E_PARAM_CONTROLLERID` | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` line 329 |
| SWS_CANIF_00656 | Null pointer `ControllerModePtr` in `GetControllerMode()` → report `CANIF_E_PARAM_POINTER` | `VALIDATE(ControllerModePtr != NULL, ...)` line 330 |
| SWS_CANIF_00677 | If controller is STOPPED and `CanIf_Transmit()` is called for it → return `E_NOT_OK` | `if (csMode != CANIF_CS_STARTED)` check in `CanIf_Transmit()` line 450 |
| SWS_CANIF_00898 | Invalid `ControllerId` in `GetControllerErrorState()` → error | Function `CanIf_GetControllerErrorState()` **NOT IMPLEMENTED** in code |
| SWS_CANIF_00899 | Null `ErrorStatePtr` in `GetControllerErrorState()` → error | Function **NOT IMPLEMENTED** |

**Summary:** Core controller mode switching is implemented. Two gaps: the UNINIT mode case in `SetControllerMode()` doesn't report the correct error, and `CanIf_GetControllerErrorState()` is a new API not in this codebase.

---

### Group D: PDU Channel Mode Management

Requirements about controlling the software Tx/Rx gates per channel.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00864 | On init → set all channels to `CANIF_OFFLINE` | `CanIf_Init()` line 140 |
| SWS_CANIF_00865 | `SetControllerMode(SLEEP)` → set PDU mode to `CANIF_OFFLINE` | `CANIF_CS_SLEEP` case does NOT explicitly call `SetPduMode(OFFLINE)` — **GAP** |
| SWS_CANIF_00866 | `SetControllerMode(STOPPED)` or `ControllerBusOff()` → set PDU mode to `CANIF_TX_OFFLINE` | `CanIf_SetPduMode(channel, CANIF_SET_OFFLINE)` in `CanIf_SetControllerMode()` line 305 — sets OFFLINE not TX_OFFLINE — **PARTIAL GAP** |
| SWS_CANIF_00073 | `CANIF_OFFLINE` mode: block Tx, block Rx callbacks, block Tx confirmation callbacks | Checked in `CanIf_Transmit()` line 459 and `CanIf_RxIndication()` line 778 |
| SWS_CANIF_00489 | `CANIF_TX_OFFLINE` mode: block Tx, allow Rx callbacks, block Tx confirmations | Checked in `CanIf_Transmit()` and `CanIf_RxIndication()` mode checks |
| SWS_CANIF_00075 | `CANIF_ONLINE` mode: allow Tx, allow Rx, allow confirmations | Set in `CanIf_SetControllerMode(STARTED)` line 263 |
| SWS_CANIF_00072 | `CANIF_TX_OFFLINE_ACTIVE` mode: call TxConfirmation immediately without actually sending | `CanIf_TxConfirmation()` mode check includes `CANIF_GET_OFFLINE_ACTIVE` line 755 — **PARTIAL**: Transmit() doesn't call confirmation immediately — **GAP** |
| SWS_CANIF_00118 | BusOff notification is not blocked after mode change, even for frames already in hardware queue | `CanIf_ControllerBusOff()` calls BusOff notification regardless — lines 937–940 |
| SWS_CANIF_00341 | Invalid `ControllerId` in `SetPduMode()` → `CANIF_E_PARAM_CONTROLLERID` | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` line 551 |
| SWS_CANIF_00860 | Invalid `PduModeRequest` in `SetPduMode()` → `CANIF_E_PARAM_PDU_MODE` | NOT done — invalid modes just fall through the switch without error |
| SWS_CANIF_00874 | `SetPduMode()` rejects if controller mode is not `CAN_CS_STARTED` | NOT checked in code — `SetPduMode()` does not verify controller state |
| SWS_CANIF_00346 | Invalid `ControllerId` in `GetPduMode()` → `CANIF_E_PARAM_CONTROLLERID` | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` line 639 |
| SWS_CANIF_00657 | Null `PduModePtr` in `GetPduMode()` → `CANIF_E_PARAM_POINTER` | Not validated in code — `*PduModePtr` is written without NULL check |

**Summary:** Core mode management implemented. Gaps: SLEEP mode should set TX_OFFLINE (sets OFFLINE instead), OFFLINE_ACTIVE doesn't immediately confirm Tx, `SetPduMode()` doesn't check controller state, missing pointer/mode validation in some functions.

---

### Group E: Transmission (Tx Path)

Requirements about how `CanIf_Transmit()` works.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00317 | Reject transmit if controller not STARTED or Tx mode not online/active | Lines 450–461 in `CanIf_Transmit()` |
| SWS_CANIF_00677 | Same — return `E_NOT_OK` if controller is STOPPED | Line 450–452 |
| SWS_CANIF_00318 | `CanIf_Transmit()` must call `Can_Write()` with correctly built `Can_PduType` | Lines 463–469 in `CanIf_Transmit()` |
| SWS_CANIF_00243 | Set the two MSBits of CanId to mark it as 11-bit or 29-bit before passing to `Can_Write()` | **NOT DONE** — code passes `txEntry->CanIfCanTxPduIdCanId` directly without setting MSBits |
| SWS_CANIF_00162 | If `Can_Write()` returns `E_OK` → `CanIf_Transmit()` returns `E_OK` | Line 481: `return E_OK` after successful `Can_Write()` |
| SWS_CANIF_00319 | Invalid `TxPduId` → report `CANIF_E_INVALID_TXPDUID` | `VALIDATE(FALSE, ... CANIF_E_INVALID_TXPDUID)` line 439 |
| SWS_CANIF_00320 | Null `PduInfoPtr` → report `CANIF_E_PARAM_POINTER` | `VALIDATE((PduInfoPtr != 0), ...)` line 432 |
| SWS_CANIF_00382 | If channel is `CANIF_OFFLINE` and Transmit called → report `CANIF_E_STOPPED` | Mode check exists (lines 459–461) but **does NOT call Det_ReportRuntimeError** — just returns `E_NOT_OK` |
| SWS_CANIF_00882 | Accept NULL `SduDataPtr` for triggered transmission PDUs | **NOT DONE** — no check for `CanIfTxPduTriggerTransmit` flag |
| SWS_CANIF_00893 | If `SduLength` exceeds max CAN frame length → report `CANIF_E_DATA_LENGTH_MISMATCH` | **NOT DONE** — no length cap check in `CanIf_Transmit()` |
| SWS_CANIF_00894 | Truncate data if `SduLength` exceeds global PDU length and truncation enabled | **NOT DONE** |
| SWS_CANIF_00900 | Return `E_NOT_OK` if truncation disabled and length exceeds | **NOT DONE** |

**Summary:** Core Tx path works. Gaps: MSBit setting for CanId type, DET error reporting for OFFLINE Tx, triggered transmission NULL check, SduLength validation/truncation.

---

### Group F: Tx Buffering

Requirements about buffering CAN frames when the hardware is busy (`CAN_BUSY`).

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00063 | CanIf must support Tx buffering if `CanIfPublicTxBuffering` is enabled | **NOT IMPLEMENTED** — `CANIF_ARC_RUNTIME_PDU_CONFIGURATION` doesn't include buffering |
| SWS_CANIF_00381 | If `Can_Write()` returns `CAN_BUSY` for direct Tx → try to buffer the PDU | **NOT DONE** — code immediately returns `E_NOT_OK` on `CAN_BUSY` (line 476) |
| SWS_CANIF_00881 | If `Can_Write()` returns `CAN_BUSY` for triggered Tx → try to buffer the request | **NOT DONE** |
| SWS_CANIF_00835 | Buffering only possible if buffer size > 0 in config | **NOT DONE** — no buffer structure exists |
| SWS_CANIF_00836 | Buffer PDU in free slot if not already buffered | **NOT DONE** |
| SWS_CANIF_00068 | Overwrite existing buffered PDU if same L-PDU is buffered and `CAN_BUSY` again | **NOT DONE** |
| SWS_CANIF_00837 | Return `E_NOT_OK` if all buffer slots busy and new PDU arrives | **NOT DONE** (just returns E_NOT_OK for all CAN_BUSY) |
| SWS_CANIF_00386 | During `TxConfirmation`, check if any buffered PDUs are waiting | **NOT DONE** |
| SWS_CANIF_00668 | Send highest-priority buffered PDU when hardware becomes free | **NOT DONE** |
| SWS_CANIF_00070 | Transmit buffered PDUs in CAN priority order per HTH | **NOT DONE** |
| SWS_CANIF_00183 | Remove PDU from buffer immediately when `Can_Write()` succeeds | **NOT DONE** |
| SWS_CANIF_00387 | Initialize all Tx L-PDU buffers in `CanIf_Init()` | **NOT DONE** |
| SWS_CANIF_00033 | Protect Tx buffer access against concurrent (interrupt) access | **NOT DONE** |
| SWS_CANIF_00849 | Also store CanId in the Tx buffer for dynamic PDUs | **NOT DONE** |
| SWS_CANIF_00895 | If rejected data exceeds buffer, store configured amount and discard rest + report error | **NOT DONE** |
| SWS_CANIF_00466 | Each Tx L-PDU must be assigned to a buffer config container at config time | `CanIfTxPduConfigType` has no `CanIfTxPduBufferRef` field — **NOT DONE** |
| SWS_CANIF_00485 | Clear Tx buffers when controller enters STOPPED | **NOT DONE** — no buffers exist |
| SWS_CANIF_00739 | Notify upper layers of failed Tx (call `<User_TxConfirmation>(E_NOT_OK)`) when entering STOPPED | **NOT DONE** |

**Summary:** This entire group is NOT implemented. The code comment on line 477 explicitly says "Tx buffering not supported." This is the largest single gap between requirements and code.

---

### Group G: Tx Confirmation Callback

Requirements about what happens after a frame is successfully sent.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00383 | `CanIf_TxConfirmation()` must call the configured upper layer confirmation service | Lines 757: `entry->CanIfUserTxConfirmation(entry->CanIfTxPduId)` |
| SWS_CANIF_00412 | If not initialized when `TxConfirmation()` is called → don't call upper layer | `VALIDATE_NO_RV(CanIf_Global.initRun, ...)` line 744 |
| SWS_CANIF_00410 | Invalid `CanTxPduId` in `TxConfirmation()` → report `CANIF_E_PARAM_LPDU` | `VALIDATE_NO_RV(canTxPduId < CanIfNumberOfCanTXPduIds, ...)` line 745 |
| SWS_CANIF_00391 | If `CanIfPublicReadTxPduNotifyStatusApi` is TRUE → store Tx notification status | `CANIF_READTXPDU_NOTIFY_STATUS_API = STD_OFF` → **NOT DONE** |
| SWS_CANIF_00414 | Each Tx PDU must be configured with a `<User_TxConfirmation>` callback | `CanIfUserTxConfirmation` function pointer in `CanIf_TxPduConfigType` — configured in CanIf_Cfg.c |
| SWS_CANIF_00438 | Config: upper layer module providing TxConfirmation must be configured | `CanIfUserTxConfirmation` field populated in CanIf_Cfg.c |
| SWS_CANIF_00542 | Config: name of `<User_TxConfirmation>()` configured via parameter | Function pointer names in CanIf_Cfg.c |
| SWS_CANIF_00439 | If upper layer is PduR → callback name must be `PduR_CanIfTxConfirmation` | `PduR_CanIfTxConfirmation` used in CanIf_Cfg.c line 200 |
| SWS_CANIF_00543 | If upper layer is CanNm → callback name must be `CanNm_TxConfirmation` | `CanNm_TxConfirmation` used in CanIf_Cfg.c lines 186, 214 |
| SWS_CANIF_00550 | If upper layer is CanTp → callback name must be `CanTp_TxConfirmation` | `CanTp_TxConfirmation` used in CanIf_Cfg.c lines 158, 173 |
| SWS_CANIF_00544 | If upper layer is J1939TP → callback name must be `J1939Tp_TxConfirmation` | Not used in this config |
| SWS_CANIF_00556 | If upper layer is XCP → `Xcp_CanIfTxConfirmation` | Not used in this config |
| SWS_CANIF_00551 | If upper layer is CDD → name configurable via parameter | `CANIF_USER_TYPE_CAN_SPECIAL` handles this case |
| SWS_CANIF_00858 | J1939NM callback name | Not used |
| SWS_CANIF_00879 | CAN_TSYN callback name | Not used |
| SWS_CANIF_00740 | If polling support enabled → buffer TxConfirmation info per controller | **NOT DONE** — `CanIfPublicTxConfirmPollingSupport` not supported |
| SWS_CANIF_00905 | If Bus Mirroring active → call `Mirror_ReportCanFrame()` on TxConfirmation | **NOT DONE** — bus mirroring not implemented |

**Summary:** Core TxConfirmation forwarding is implemented. Gaps: notification status storage, bus mirroring, Tx confirmation polling support.

---

### Group H: Reception & Software Filtering

Requirements about how incoming frames are accepted and filtered.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00211 | `CanIf_RxIndication()` must execute the software acceptance filter | Lines 799–819 in `CanIf_RxIndication()` |
| SWS_CANIF_00389 | Process software filtering for each incoming L-PDU | Lines 798–820: checks `CanIfSoftwareFilterHrh` and applies mask filter |
| SWS_CANIF_00877 | Compare `CanIfRxPduCanId` AND the two MSBits of `CanId` to select the correct Rx PDU | **PARTIAL** — code only matches HRH and applies mask filter; MSBits (ID type 11/29 bit) not checked |
| SWS_CANIF_00030 | If CanId matches a configured HRH entry → accept the PDU | Lines 795–806 |
| SWS_CANIF_00645 | Software filter range defined by upper/lower CanId OR base ID + mask | `CanIfHrhRangeConfig` exists in `CanIf_HrhConfigType` but `CanIfHrhRangeConfig = NULL` in config; only MASK type supported |
| SWS_CANIF_00646 | Range is configurable for Standard or Extended CAN IDs | Structure supports it but not implemented in filter logic |
| SWS_CANIF_00852 | Priority: single CanId > smaller range > larger range | **NOT DONE** — only simple mask filter exists |
| SWS_CANIF_00281 | Accept both Standard (11-bit) and Extended (29-bit) IDs on same channel | `CanIfRxPduIdCanIdType` field exists but MSBit comparison not done in filter |
| SWS_CANIF_00026 | Accept received L-PDU only if received DLC >= configured DLC | `#if (CANIF_DLC_CHECK == STD_ON) if (CanDlc < entry->CanIfCanRxPduDlc)` lines 823–828 |
| SWS_CANIF_00390 | After software filtering passes → perform DLC check | Order in `CanIf_RxIndication()`: filter first (lines 798–820), then DLC (lines 823–828) |
| SWS_CANIF_00902 | DLC check enabled globally via `CanIfPrivateDataLengthCheck` AND per-PDU | Code only has global flag `CANIF_DLC_CHECK` — **no per-PDU disable** |
| SWS_CANIF_00168 | If DLC check fails → report `CANIF_E_INVALID_DATA_LENGTH` | `VALIDATE_NO_RV(FALSE, CANIF_RXINDICATION_ID, CANIF_E_PARAM_DLC)` line 826 |
| SWS_CANIF_00829 | Pass received length to upper layer if DLC check passed | `pduInfo.SduLength = CanDlc` passed in PduR/CanTp routing (lines 858, 872) |
| SWS_CANIF_00830 | Pass received length if DLC check is not configured | Same — CanDlc is always passed when DLC check is off |
| SWS_CANIF_00906 | If Bus Mirroring active → call `Mirror_ReportCanFrame()` on RxIndication | **NOT DONE** |

**Summary:** Core filtering and DLC check implemented. Gaps: MSBit (11/29-bit ID type) comparison missing, range-based filtering not fully implemented, per-PDU DLC check disable not supported, bus mirroring not done.

---

### Group I: Rx Indication Callback Routing

Requirements about routing received frames to the correct upper layer.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00056 | After DLC check → identify which upper layer is configured for this PDU | `switch(entry->CanIfRxUserType)` in `CanIf_RxIndication()` line 831 |
| SWS_CANIF_00135 | Call the configured `<User_RxIndication>()` callback | All `case` branches in lines 833–889 call the appropriate function |
| SWS_CANIF_00415 | `CanIf_RxIndication()` routes indication to configured upper layer(s) | Switch/case routing block lines 831–890 |
| SWS_CANIF_00392 | If `CanIfPublicReadRxPduNotifyStatusApi` is TRUE → store Rx notification status | `CANIF_READRXPDU_NOTIFY_STATUS_API = STD_OFF` → **NOT DONE** |
| SWS_CANIF_00416 | Invalid HRH in `RxIndication()` → report `CANIF_E_PARAM_HOH` | `DET_REPORTERROR(... CANIF_E_PARAM_HRH)` in `CanIf_Arc_FindHrhChannel()` line 123 |
| SWS_CANIF_00417 | Invalid CanId in `RxIndication()` → report `CANIF_E_PARAM_CANID` | **NOT DONE** — CanId is not validated before use |
| SWS_CANIF_00419 | Null `PduInfoPtr`/`Mailbox` → report `CANIF_E_PARAM_POINTER` | `VALIDATE_NO_RV(CanSduPtr != NULL, ...)` line 767 (only `SduPtr` checked) |
| SWS_CANIF_00421 | If not initialized → don't process `RxIndication()` | `VALIDATE_NO_RV(CanIf_Global.initRun, ...)` line 766 |
| SWS_CANIF_00423 | Config: each Rx PDU must be configured with `<User_RxIndication>()` callback | `CanIfRxUserType` + routing in switch-case in CanIf_Cfg.c |
| SWS_CANIF_00441 | Config: upper layer providing RxIndication configured via `CanIfRxPduUserRxIndicationUL` | `CanIfRxUserType` enum: PDUR/CanTp/CanNm/J1939TP/SPECIAL |
| SWS_CANIF_00552 | Config: name of `<User_RxIndication>()` configured via parameter | Hardcoded in `CanIf_RxIndication()` switch-case using preprocessor flags |
| SWS_CANIF_00442 | PduR RxIndication → must be `PduR_CanIfRxIndication` | `PduR_CanIfRxIndication()` called line 860 |
| SWS_CANIF_00445 | CanNm RxIndication → must be `CanNm_RxIndication` | `CanNm_RxIndication()` called line 848 |
| SWS_CANIF_00448 | CanTp RxIndication → must be `CanTp_RxIndication` | `CanTp_RxIndication()` called line 873 |
| SWS_CANIF_00554 | J1939TP RxIndication → must be `J1939Tp_RxIndication` | `J1939Tp_RxIndication()` called line 885 |
| SWS_CANIF_00555 | XCP RxIndication → must be `Xcp_CanIfRxIndication` | Not used in this config |
| SWS_CANIF_00557 | CDD RxIndication → name configurable | Handled by `CANIF_USER_TYPE_CAN_SPECIAL` case |
| SWS_CANIF_00859 | J1939NM RxIndication name | Not used |
| SWS_CANIF_00880 | CAN_TSYN RxIndication name | Not used |

**Summary:** Routing to PduR, CanTp, CanNm, J1939TP is implemented. Gaps: CanId validation, Rx notification status storage.

---

### Group J: Rx Buffering & Notification Status

Requirements about storing received data for later retrieval.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00198 | If `CanIfPublicReadRxPduDataApi` is TRUE → allocate Rx L-SDU buffer per PDU | `CANIF_READRXPDU_DATA_API = STD_OFF` → **NOT DONE** |
| SWS_CANIF_00199 | After filtering+DLC → store received L-SDU in Rx buffer | **NOT DONE** |
| SWS_CANIF_00297 | Copy received bytes to static receive buffer | **NOT DONE** |
| SWS_CANIF_00851 | Copy CanId to MetaData of received L-SDU | **NOT DONE** |
| SWS_CANIF_00472 | If `CanIfPublicReadTxPduNotifyStatusApi` TRUE → store Tx notification status | `CANIF_READTXPDU_NOTIFY_STATUS_API = STD_OFF` → **NOT DONE** |
| SWS_CANIF_00473 | If `CanIfPublicReadRxPduNotifyStatusApi` TRUE → store Rx notification status | `CANIF_READRXPDU_NOTIFY_STATUS_API = STD_OFF` → **NOT DONE** |
| SWS_CANIF_00324 | `ReadRxPduData()` rejects if controller not STARTED or Rx not online | Stub function, always returns `E_NOT_OK` |
| SWS_CANIF_00325 | Invalid `RxPduId` in `ReadRxPduData()` → report `CANIF_E_INVALID_RXPDUID` | Stub — not reached |
| SWS_CANIF_00326 | Null pointer in `ReadRxPduData()` → error | Stub — not reached |
| SWS_CANIF_00329 | `ReadRxPduData()` not for range-reception PDUs | Not applicable (function not implemented) |
| SWS_CANIF_00330 | `ReadRxPduData()` API configurable at compile time | `CANIF_READRXPDU_DATA_API = STD_OFF` — correctly disabled |
| SWS_CANIF_00393 | `ReadTxNotifStatus()` resets notification status when called | Stub |
| SWS_CANIF_00331 | Invalid TxSduId in `ReadTxNotifStatus()` → error | Stub |
| SWS_CANIF_00335 | `ReadTxNotifyStatus()` API configurable | `CANIF_READTXPDU_NOTIFY_STATUS_API = STD_OFF` — correctly disabled |
| SWS_CANIF_00394 | `ReadRxNotifStatus()` resets notification status when called | Stub |
| SWS_CANIF_00336 | Invalid RxSduId in `ReadRxNotifStatus()` → error | Stub |
| SWS_CANIF_00340 | `ReadRxNotifStatus()` API configurable | `CANIF_READRXPDU_NOTIFY_STATUS_API = STD_OFF` — correctly disabled |

**Summary:** This entire group is intentionally disabled via config flags. The stub functions exist in code but do nothing. Configuration correctly reflects what is disabled.

---

### Group K: Dynamic PDU (Runtime CAN ID)

Requirements about PDUs whose CAN ID can be changed at runtime.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00844 | CanIf must support dynamic L-PDUs (CanId in MetaData) | `CANIF_ARC_RUNTIME_PDU_CONFIGURATION` flag controls this |
| SWS_CANIF_00188 | Use MSBits of CanId to determine ID type (11-bit/29-bit/CAN-FD) | `CanIf_SetDynamicTxId()` checks bit 31 lines 669–673 |
| SWS_CANIF_00673 | Ensure data consistency of CanId during concurrent `SetDynamicTxId()` and `Transmit()` | **NOT DONE** — no mutex/atomic protection |
| SWS_CANIF_00352 | Invalid TxPduId in `SetDynamicTxId()` → report `CANIF_E_INVALID_TXPDUID` | `VALIDATE_NO_RV(FALSE, ... CANIF_E_INVALID_TXPDUID)` in `CanIf_SetDynamicTxId()` line 657 |
| SWS_CANIF_00353 | Invalid CanId in `SetDynamicTxId()` → report `CANIF_E_PARAM_CANID` | `VALIDATE_NO_RV(FALSE, ... CANIF_E_PARAM_CANID)` line 678 |
| SWS_CANIF_00355 | If not initialized → don't execute `SetDynamicTxId()` | `VALIDATE_NO_RV(CanIf_Global.initRun, ...)` line 650 |
| SWS_CANIF_00357 | `SetDynamicTxId()` API configurable at compile time | Guarded by `#if (CANIF_ARC_RUNTIME_PDU_CONFIGURATION == STD_ON)` |
| SWS_CANIF_00855 | If mask/CanId omitted → take CanId directly from MetaData | Not applicable — MetaData not fully implemented |
| SWS_CANIF_00856 | Ignore mask if CAN_ID_32 not in MetaData | Not applicable |
| SWS_CANIF_00854 | MetaData mask defines which bits appear in final CanId | Not applicable |
| SWS_CANIF_00857 | Init() sets dynamic Tx PDU CanIds to configured default | Requires RUNTIME_PDU_CONFIGURATION = ON — currently OFF |
| SWS_CANIF_00847 | Dynamic Rx PDUs must use ID range or mask + CAN_ID_32 MetaData | Not applicable |
| SWS_CANIF_00848 | On Rx of dynamic L-SDU → place CanId in MetaDataItem CAN_ID_32 | Not applicable |

**Summary:** `CanIf_SetDynamicTxId()` code exists but only compiles when `CANIF_ARC_RUNTIME_PDU_CONFIGURATION = STD_ON`, which is OFF in this project. All MetaData-related requirements are not applicable to this implementation.

---

### Group L: BusOff Handling

Requirements about what to do when the CAN bus goes into BusOff state.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00724 | `CanIf_ControllerBusOff()` must call `CanSM_ControllerBusOff()` (or CDD) | `CanIf_ConfigPtr->DispatchConfig->CanIfBusOffNotification(channel)` line 939 — but in current config this is `NULL` — **GAP IN CONFIG** |
| SWS_CANIF_00429 | Invalid `ControllerId` in `ControllerBusOff()` → report `CANIF_E_PARAM_CONTROLLERID` | Controller lookup loop at lines 923–929; validation at line 931 |
| SWS_CANIF_00431 | If not initialized → don't execute BusOff notification | `VALIDATE_NO_RV(CanIf_Global.initRun, ...)` line 921 |
| SWS_CANIF_00433 | Config: ControllerId is published in CanIf config | `Arc_ChannelToControllerMap[]` in CanIf_Cfg.c |
| SWS_CANIF_00866 | `ControllerBusOff()` sets channel PDU mode to `TX_OFFLINE` | `CanIf_SetControllerMode(channel, CANIF_CS_STOPPED)` → sets OFFLINE (see gap in Group D) |
| SWS_CANIF_00524 | At least one `<User_ControllerBusOff>()` callback MUST be configured | `CanIfBusOffNotification = NULL` in this project — **VIOLATES this requirement** |
| SWS_CANIF_00559 | If CanSM is the upper layer → callback must be `CanSM_ControllerBusOff` | Not configured |
| SWS_CANIF_00560 | CDD callback name configurable | Not applicable |
| SWS_CANIF_00450 | Config: upper layer for BusOff callback configured via parameter | `CanIfBusOffNotification` field in `CanIf_DispatchConfigType` |
| SWS_CANIF_00558 | Config: name of `<User_ControllerBusOff>()` configured via parameter | Function pointer in `CanIfDispatchConfigType` |
| SWS_CANIF_00918 | Report security event `CANIF_SEV_ERRORSTATE_BUSOFF` on BusOff | **NOT DONE** — security events not implemented |

**Summary:** BusOff callback mechanism is coded, but in this specific project config `CanIfBusOffNotification = NULL`, which violates SWS_CANIF_00524 (at least one must be configured). The ArcCore `CanIf_Arc_Error()` function handles generic errors but isn't an AUTOSAR standard function.

---

### Group M: Controller & Transceiver Mode Indications

Requirements about forwarding mode change notifications upward.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00711 | `CanIf_ControllerModeIndication()`: when called → call `CanSM_ControllerModeIndication()` | Function `CanIf_ControllerModeIndication()` **NOT IN CODE** |
| SWS_CANIF_00700 | Invalid ControllerId in `ControllerModeIndication()` → error | **NOT IN CODE** |
| SWS_CANIF_00702 | Not initialized → don't execute | **NOT IN CODE** |
| SWS_CANIF_00689 | Config: upper layer for controller mode indication | **NOT IN CODE** |
| SWS_CANIF_00690 | Config: name of callback | **NOT IN CODE** |
| SWS_CANIF_00691 | CanSM → `CanSM_ControllerModeIndication` | **NOT IN CODE** |
| SWS_CANIF_00692 | CDD → configurable name | **NOT IN CODE** |
| SWS_CANIF_00712 | `CanIf_TrcvModeIndication()`: when called → call `CanSM_TransceiverModeIndication()` | **NOT IN CODE** |
| SWS_CANIF_00706 | Invalid TransceiverId in `TrcvModeIndication()` → error | **NOT IN CODE** |
| SWS_CANIF_00708 | Not initialized → don't execute | **NOT IN CODE** |
| SWS_CANIF_00710 | Config: TransceiverId | **NOT IN CODE** |
| SWS_CANIF_00730 | Not provided if no transceivers configured | Consistent — no transceivers |
| SWS_CANIF_00694 | Caveats of TrcvModeIndication | Not applicable |
| SWS_CANIF_00695 | Config: TrcvModeIndication upper layer | **NOT IN CODE** |
| SWS_CANIF_00696 | Config: name of TrcvModeIndication callback | **NOT IN CODE** |
| SWS_CANIF_00697 | CanSM → `CanSM_TransceiverModeIndication` | **NOT IN CODE** |

**Summary:** Neither `CanIf_ControllerModeIndication()` nor `CanIf_TrcvModeIndication()` are implemented in the code. These are callbacks from the CAN Driver when the controller or transceiver completes a mode change asynchronously.

---

### Group N: Wakeup

Requirements about detecting CAN bus wakeup events.

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00395 | `CheckWakeup()` must query CAN drivers/transceivers to find which caused wakeup | `CanIf_CheckWakeup()` is a stub that always returns `E_NOT_OK` |
| SWS_CANIF_00720 | If any `Can_CheckWakeup()` returns E_OK → return E_OK | **NOT DONE** |
| SWS_CANIF_00678 | If all return E_NOT_OK → return E_NOT_OK | Stub returns E_NOT_OK always |
| SWS_CANIF_00286 | If wakeup validation enabled → store first valid RxIndication event per controller | **NOT DONE** |
| SWS_CANIF_00179 | `CheckValidation()` calls `<User_ValidateWakeupEvent>()` if event stored | `CanIf_CheckValidation()` is a stub |
| SWS_CANIF_00756 | Clear stored wakeup event when entering CAN_CS_SLEEP | **NOT DONE** |
| SWS_CANIF_00398 | Invalid WakeupSource in `CheckWakeup()` → error | Stub only |
| SWS_CANIF_00404 | Invalid WakeupSource in `CheckValidation()` → error | Stub only |
| SWS_CANIF_00408 | `CheckValidation()` configurable | `CANIF_WAKEUP_EVENT_API = STD_OFF` — correctly disabled |
| SWS_CANIF_00659 | `ValidateWakeupEvent` callback configurable | Not applicable (wakeup disabled) |
| SWS_CANIF_00456 | Config: upper layer for wakeup validation | Not applicable |
| SWS_CANIF_00563 | EcuM → `EcuM_ValidateWakeupEvent` | Not applicable |
| SWS_CANIF_00564 | CDD → configurable name | Not applicable |

**Summary:** Wakeup is fully disabled (`CANIF_WAKEUP_EVENT_API = STD_OFF`). Stub functions exist. This is a consistent — though incomplete — implementation.

---

### Group O: Transceiver Management

Requirements about managing CAN transceiver hardware (physical layer chip).

| Req ID | What it says (simple) | Code Area |
|--------|-----------------------|-----------|
| SWS_CANIF_00358 | `SetTrcvMode()` → call `CanTrcv_SetOpMode()` | `CanIf_SetTransceiverMode()` is a stub returning E_NOT_OK |
| SWS_CANIF_00363 | `GetTrcvMode()` → call `CanTrcv_GetOpMode()` | Stub |
| SWS_CANIF_00368 | `GetTrcvWakeupReason()` → call `CanTrcv_GetBusWuReason()` | Stub |
| SWS_CANIF_00372 | `SetTrcvWakeupMode()` → call `CanTrcv_SetWakeupMode()` | Stub |
| SWS_CANIF_00538 | Invalid TransceiverId in SetTrcvMode → error | Stub only |
| SWS_CANIF_00648 | Invalid TransceiverMode in SetTrcvMode → error | Stub only |
| SWS_CANIF_00362 | `SetTrcvMode()` configurable; return E_NOT_OK if no transceiver | `CANIF_TRANSCEIVER_API = STD_OFF` |
| SWS_CANIF_00364/00650/00367/00537/00649/00371/00535/00536/00373 | Validation errors for Trcv APIs | All stubs |
| SWS_CANIF_00766 | `ClearTrcvWufFlag()` → `CanTrcv_ClearTrcvWufFlag()` | **NOT IN CODE** (PN feature) |
| SWS_CANIF_00765 | `CheckTrcvWakeFlag()` → `CanTrcv_CheckWakeFlag()` | **NOT IN CODE** (PN feature) |

**Summary:** All transceiver functions are stubs (`CANIF_TRANSCEIVER_API = STD_OFF`). This is consistent and intentional.

---

### Group P: Partial Networking (PN)

Requirements about PN filtering — a feature that allows certain PDUs to "wake up" a sleeping CAN network selectively.

| Req ID | What it says | Code Area |
|--------|-------------|-----------|
| SWS_CANIF_00747–00878 | PnTxFilter per controller, enabled/disabled based on mode changes and Tx/Rx events | **COMPLETELY NOT IMPLEMENTED** — no PN support in code |
| SWS_CANIF_00753–00827 | PN callback functions: `ConfirmPnAvailability`, `ClearTrcvWufFlagIndication`, `CheckTrcvWakeFlagIndication` | **NOT IN CODE** |

**Summary:** Partial Networking (approximately 40 requirements) is entirely absent from the code. There are no PN data structures, no PN filter logic, and no PN callback functions.

---

### Group Q: Security Events

Requirements about reporting security-relevant CAN events to the IdsM (Intrusion Detection System Manager).

| Req ID | What it says | Code Area |
|--------|-------------|-----------|
| SWS_CANIF_00913 | Enable security event reporting | **NOT IMPLEMENTED** |
| SWS_CANIF_00915 | Report `CANIF_SEV_TX_ERROR_DETECTED` on Tx error in `ErrorNotification()` | **NOT IMPLEMENTED** — `CanIf_Arc_Error()` exists but doesn't report to IdsM |
| SWS_CANIF_00916 | Report `CANIF_SEV_RX_ERROR_DETECTED` on Rx error | **NOT IMPLEMENTED** |
| SWS_CANIF_00917 | Report `CANIF_SEV_ERRORSTATE_PASSIVE` when error counters > 127 | `CanIf_ControllerErrorStatePassive()` function **NOT IN CODE** |
| SWS_CANIF_00918 | Report `CANIF_SEV_ERRORSTATE_BUSOFF` on BusOff | `CanIf_ControllerBusOff()` handles BusOff but doesn't report to IdsM |
| SWS_CANIF_00919 | Invalid ControllerId in `ControllerErrorStatePassive()` → error | Function **NOT IN CODE** |
| SWS_CANIF_00920 | Invalid ControllerId in `ErrorNotification()` → error | `CanIf_Arc_Error()` validates but uses ArcCore API, not AUTOSAR standard |
| SWS_CANIF_00921 | Invalid CanError in `ErrorNotification()` → error | Same |

**Summary:** Security event reporting is entirely absent. These are newer AUTOSAR requirements (AR4 additions). The ArcCore `CanIf_Arc_Error()` provides similar functionality but through a non-standard interface.

---

### Group R: Advanced APIs

Requirements for APIs that exist in the spec but are NOT present in this implementation.

| API | Req IDs | Status |
|-----|---------|--------|
| `CanIf_SetBaudrate()` | SWS_CANIF_00868, 00869, 00871 | **NOT IN CODE** — function doesn't exist |
| `CanIf_GetControllerRxErrorCounter()` | SWS_CANIF_00907, 00908 | **NOT IN CODE** |
| `CanIf_GetControllerTxErrorCounter()` | SWS_CANIF_00909, 00910 | **NOT IN CODE** |
| `CanIf_GetControllerErrorState()` | SWS_CANIF_00898, 00899 | **NOT IN CODE** |
| `CanIf_EnableBusMirroring()` | SWS_CANIF_00911, 00912 | **NOT IN CODE** |
| `CanIf_TriggerTransmit()` | SWS_CANIF_00884, 00885, 00888–00891 | **NOT IN CODE** |
| `CanIf_GetTxConfirmationState()` | SWS_CANIF_00736, 00738, 00740 | **NOT IN CODE** |
| Bus Mirroring | SWS_CANIF_00903–00906, 00911–00912 | **NOT IN CODE** — `Mirror.h` not included |

---

## 4. Complete Requirements Count by Group

| Group | Topic | Total Reqs | Implemented | Partial | Not Done |
|-------|-------|-----------|-------------|---------|----------|
| A | Architecture & Foundation | 17 | 14 | 2 | 1 |
| B | Initialization | 6 | 4 | 1 | 1 |
| C | Controller Mode Management | 8 | 5 | 1 | 2 |
| D | PDU Channel Mode Management | 13 | 7 | 2 | 4 |
| E | Transmission (Tx Path) | 12 | 5 | 2 | 5 |
| F | Tx Buffering | 18 | 0 | 0 | 18 |
| G | Tx Confirmation Callback | 17 | 9 | 2 | 6 |
| H | Reception & Software Filtering | 15 | 8 | 3 | 4 |
| I | Rx Indication Callback Routing | 19 | 12 | 1 | 6 |
| J | Rx Buffering & Notification Status | 18 | 0 | 4 | 14 |
| K | Dynamic PDU | 13 | 4 | 0 | 9 |
| L | BusOff Handling | 11 | 6 | 1 | 4 |
| M | Mode Indications | 16 | 0 | 0 | 16 |
| N | Wakeup | 13 | 0 | 3 | 10 |
| O | Transceiver Management | 26 | 0 | 3 | 23 |
| P | Partial Networking | ~40 | 0 | 0 | ~40 |
| Q | Security Events | 8 | 0 | 1 | 7 |
| R | Advanced APIs | ~20 | 0 | 0 | ~20 |
| **TOTAL** | | **~280** | **~74** | **~26** | **~170** |

> **Implementation coverage: approximately 36% of all requirements fully implemented.**  
> The remaining 64% are either intentionally disabled, stubbed, or belong to features (buffering, PN, security, transceiver) not included in this OpenSAR build.

---

## 5. Missing Code — Requirements With No Implementation

These requirements have **no corresponding code** in `CanIf.c`. They are listed by severity:

### Critical gaps (core behavior missing):

| Req ID | Missing Implementation |
|--------|----------------------|
| SWS_CANIF_00865 | `SetControllerMode(SLEEP)` must set PDU mode to OFFLINE — code sets OFFLINE via STOPPED path but the SLEEP case itself doesn't call `SetPduMode` |
| SWS_CANIF_00866 | `SetControllerMode(STOPPED)` must set PDU to TX_OFFLINE — code sets full OFFLINE instead |
| SWS_CANIF_00072 | OFFLINE_ACTIVE mode: Transmit() must call TxConfirmation immediately — not done in `CanIf_Transmit()` |
| SWS_CANIF_00524 | At least one BusOff callback MUST be configured — current config has NULL |
| SWS_CANIF_00739 | Notify upper layers with `E_NOT_OK` TxConfirmation when controller stops |
| SWS_CANIF_00485 | Clear Tx buffers on CAN_CS_STOPPED |
| SWS_CANIF_00243 | Set MSBits of CanId before `Can_Write()` — not done |
| SWS_CANIF_00877 | Compare MSBits of CanId in RxIndication (11-bit vs 29-bit) — not done |
| All of Group F | Tx buffering (18 requirements) entirely missing |
| All of Group M | Mode indication callbacks (`ControllerModeIndication`, `TrcvModeIndication`) missing |

### Non-critical (optional/advanced features not in scope):

- Group N (Wakeup), Group O (Transceiver), Group P (PN), Group Q (Security), Group R (Advanced APIs) — all intentionally out of scope for this OpenSAR AR403 implementation.

---

## 6. Excess Code — Code With No Direct Requirement

These code elements exist in `CanIf.c` but have no matching AUTOSAR requirement ID. They are **ArcCore vendor extensions**:

| Code Element | Location | What it does |
|-------------|----------|-------------|
| `CanIf_PreInit_InitController()` | Line 206 | Splits `CanIf_InitController()` to allow cold startup without mode checks. Not in AUTOSAR spec. |
| `CanIf_Arc_FindHrhChannel()` | Line 100 | Internal helper. Architecture decision, not a requirement. |
| `CanIf_Arc_Error()` | Line 963 | ArcCore error notification callback. Similar purpose to `CanIf_ErrorNotification()` from newer AR4 spec (SWS_CANIF_00920) but uses different signature. |
| `CanIf_Arc_GetChannelDefaultConfIndex()` | Line 991 | ArcCore-specific utility for getting config index. No AUTOSAR equivalent. |
| `CanIf_SetWakeupEvent()` | Line 943 | ArcCore stub for wakeup event — exists but does nothing. No clean AUTOSAR mapping. |
| `#define ARC_GET_CHANNEL_CONTROLLER(_channel)` | Line 79 | ArcCore macro for channel→controller mapping. Not a standard |
| `CANIF_USER_TYPE_CAN_SPECIAL` | CanIf_ConfigTypes.h | Non-standard Rx user type for complex PDU routing with extra params |

**None of these excess code elements are harmful** — they are vendor extensions that either fill gaps in the older AUTOSAR specification or provide internal convenience utilities.

---

## 7. Gap Summary Table

| Category | Finding |
|----------|---------|
| **Requirements fully implemented** | ~74 of ~280 (core Tx/Rx path, init, mode management, BusOff callback, HRH/HTH routing) |
| **Requirements partially implemented** | ~26 (validation missing, MSBit CanId not set, some mode transitions slightly off) |
| **Requirements not implemented** | ~170 (Tx buffering, transceiver, wakeup, PN, security events, advanced APIs) |
| **Missing functions (not in code at all)** | `CanIf_ControllerModeIndication()`, `CanIf_TrcvModeIndication()`, `CanIf_SetBaudrate()`, `CanIf_GetControllerErrorState()`, `CanIf_GetControllerRxErrorCounter()`, `CanIf_GetControllerTxErrorCounter()`, `CanIf_EnableBusMirroring()`, `CanIf_TriggerTransmit()`, `CanIf_GetTxConfirmationState()`, `CanIf_ControllerErrorStatePassive()`, `CanIf_ErrorNotification()` |
| **Config violations** | `CanIfBusOffNotification = NULL` violates SWS_CANIF_00524 |
| **Excess/vendor-specific code** | 6 elements (ArcCore extensions — not harmful) |
| **Where to find full spec** | `AUTOSAR_SWS_CANInterface.pdf` in project root; official AUTOSAR website |
