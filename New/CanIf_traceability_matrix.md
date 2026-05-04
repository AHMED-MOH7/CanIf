# CanIf — Requirements-to-Code Traceability Matrix

> **Step 3 of 3** — Full bidirectional traceability between AUTOSAR SWS requirements and `CanIf.c`.  
> Source: `OpenSAR/communication/CanIf/CanIf.c` (996 lines)  
> Requirements: `Requirments/CanIf_SWS_AR403.csv` (~164 IDs from AUTOSAR AR 4.0.3)

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | **IMPLEMENTED** — Requirement fully satisfied by code |
| ⚠️ | **PARTIAL** — Main behavior done; a sub-condition or error code is missing |
| ❌ | **NOT DONE** — No code implements this requirement |
| 🔧 | **DISABLED** — Feature intentionally off via compile-time flag |
| 🆕 | **MISSING API** — The entire function does not exist in `CanIf.c` |
| N/A | **NOT APPLICABLE** — Depends on another feature that is disabled |

---

## Group A — Architecture & Hardware Abstraction

*Requirements that define what CanIf IS and how it communicates with the CAN driver.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00023 | Never access hardware buffers directly — use only Can driver API | ✅ | All hardware access via `Can_Write()`, `Can_SetControllerMode()`, `Can_InitController()` | Throughout CanIf.c | Every low-level operation delegates to Can driver |
| SWS_CANIF_00378 | Access CanDrv API via function pointers at link time | ✅ | `Can_Write()`, `Can_SetControllerMode()`, `Can_InitController()` called by name | 200, 253–308, 469 | Link-time resolution via Can.h declarations |
| SWS_CANIF_00672 | `CanIf.h` contains only extern declarations | ✅ | `OpenSAR/include/CanIf.h` | — | Header has only declarations, no implementation |
| SWS_CANIF_00662 | Use HTH for Tx hardware handle and HRH for Rx hardware handle | ✅ | `CanIf_HthConfigType`, `CanIf_HrhConfigType` in CanIf_ConfigTypes.h; used in CanIf_Cfg.c | — | Both types fully defined and used |
| SWS_CANIF_00291 | HRH = handle referencing a logical hardware receive mailbox | ✅ | `CanIf_HrhConfigType` struct; `CanIfHrhIdSymRef` field | CanIf_ConfigTypes.h:84–111 | Definition + usage in RxIndication |
| SWS_CANIF_00292 | HTH = handle referencing a logical hardware transmit mailbox | ✅ | `CanIf_HthConfigType` struct; `CanIfHthIdSymRef` field | CanIf_ConfigTypes.h:118–134 | Definition + usage in Transmit |
| SWS_CANIF_00665 | HRH enables BasicCAN/FullCAN reception and routes to upper layer | ✅ | `CanIf_RxIndication()` routing switch-case | 831–890 | BasicCAN used in config; routing implemented |
| SWS_CANIF_00663 | If HRH is BasicCAN → software filtering must be enabled | ✅ | `CanIfSoftwareFilterHrh = TRUE` in config; filter check in `CanIf_RxIndication()` | 798–800, CanIf_Cfg.c:106,119 | Both LS and HS channels have filter enabled |
| SWS_CANIF_00664 | Each HRH belongs to a group of Rx L-SDU IDs | ✅ | `CanIfHrhConfigData[]` referenced by `CanIfCanRxPduHrhRef` in Rx PDU table | CanIf_Cfg.c:101–125, 238 | HRH↔PDU mapping established in config |
| SWS_CANIF_00666 | HTH enables BasicCAN/FullCAN transmission and confirms to upper layer | ✅ | `CanIf_Transmit()` uses HTH; `CanIf_TxConfirmation()` confirms | 469, 742–761 | Full Tx path through HTH |
| SWS_CANIF_00667 | Each HTH belongs to a group of Tx L-PDU IDs | ✅ | `CanIfHthConfigData[]` referenced by `CanIfCanTxPduHthRef` in Tx PDU table | CanIf_Cfg.c:79–99, 159 | HTH↔PDU mapping in config |
| SWS_CANIF_00115 | All HRHs and HTHs use a single shared numbering space starting from 0 | ✅ | `CanIf_Arc_FindHrhChannel()` searches by raw HRH ID across all HOHs | 100–126 | Numeric HRH IDs from Can driver used directly |
| SWS_CANIF_00653 | Provide ControllerId that abstracts from physical CAN controllers | ✅ | `CanIf_Arc_ChannelIdType` enum; `Arc_ChannelToControllerMap[]` | CanIf_Cfg.h:56–61, CanIf_Cfg.c:37–41 | CANIF_CHL_LS=0, CANIF_CHL_HS=1 |
| SWS_CANIF_00655 | Provide TransceiverId that abstracts from transceiver hardware | 🔧 | No transceiver driver configured | CanIf_Cfg.h | `CANIF_TRANSCEIVER_API = STD_OFF` |
| SWS_CANIF_00467 | Configure and store an ordered list of HTHs and HRHs for all HOHs | ✅ | `CanIfHohConfigData[]` array in CanIf_Cfg.c | CanIf_Cfg.c:127–143 | Two HOH entries (LS and HS) with EOL markers |
| SWS_CANIF_00468 | Each HOH references a hardware acceptance filter | ✅ | `CanIfHthIdSymRef` / `CanIfHrhIdSymRef` fields | CanIf_ConfigTypes.h:103, 130 | `Can0Hrh`, `Can2Hrh`, `Can0Hth`, `Can2Hth` |
| SWS_CANIF_00469 | Configure software acceptance filter per BasicCAN HRH | ✅ | `CanIfSoftwareFilterHrh` boolean field; used in `CanIf_RxIndication()` | CanIf_ConfigTypes.h:93; CanIf.c:800 | Config sets TRUE; code checks it |
| SWS_CANIF_00211 | Execute software acceptance filter in `CanIf_RxIndication()` | ✅ | `CanIf_RxIndication()` — MASK filter logic | 798–820 | Only MASK type supported; others report DET error |
| SWS_CANIF_00877 | Compare CanIfRxPduCanId AND the two MSBits of CanId to select Rx PDU | ⚠️ | `CanIf_RxIndication()` — mask filter at line 804 | 803–806 | Mask comparison done; MSBit (11/29-bit type) NOT compared |
| SWS_CANIF_00281 | Accept both 11-bit Standard and 29-bit Extended IDs on same channel | ⚠️ | `CanIfRxPduIdCanIdType` field exists; `CanIfTxPduIdCanIdType` exists | CanIf_ConfigTypes.h:250, 192 | Type fields defined but ID type not checked in filter |
| SWS_CANIF_00382 | If PDU channel mode = OFFLINE and Transmit called → report CANIF_E_STOPPED | ⚠️ | `CanIf_Transmit()` mode check | 459–461 | Returns `E_NOT_OK` but does NOT call `Det_ReportRuntimeError()` |

---

## Group B — Initialization

*Requirements about what `CanIf_Init()` must do.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00085 | `CanIf_Init()` initializes global variables, flags, and buffers | ✅ | `CanIf_Init()` | 131–146 | Sets `initRun`, `ControllerMode`, `PduMode` for all channels |
| SWS_CANIF_00523 | Config structure `CanIf_ConfigType` includes all public params and L-PDU defs | ✅ | `CanIf_ConfigType` struct; populated in `CanIf_Cfg.c` | CanIf_ConfigTypes.h:381–401; CanIf_Cfg.c:299–307 | Full config hierarchy defined |
| SWS_CANIF_00661 | All APIs except `CanIf_Init()` and `CanIf_GetVersionInfo()` reject if not initialized | ✅ | `VALIDATE(..., CANIF_E_UNINIT)` in every public function | 162, 235, 328, 431, 550, 638, 744, 766, 921, 947 | `initRun` flag checked at top of every function |
| SWS_CANIF_00864 | Init sets all channels to `CANIF_OFFLINE` | ✅ | `CanIf_Init()` | 140 | `CanIf_Global.channelData[i].PduMode = CANIF_GET_OFFLINE` |
| SWS_CANIF_00387 | `CanIf_Init()` initializes every Tx L-PDU buffer | ❌ | `CanIf_Init()` | 131–146 | No Tx buffer structures exist — Tx buffering not implemented |
| SWS_CANIF_00857 | `CanIf_Init()` sets dynamic Tx PDU CanIds to configured default values | 🔧 | — | — | `CANIF_ARC_RUNTIME_PDU_CONFIGURATION = STD_OFF`; dynamic PDUs disabled |

---

## Group C — Controller Mode Management

*Requirements about `CanIf_SetControllerMode()` and `CanIf_GetControllerMode()`.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00308 | `SetControllerMode()` calls `Can_SetControllerMode()` | ✅ | `CanIf_SetControllerMode()` | 253, 264, 275, 285, 296, 306 | Called for all mode transitions |
| SWS_CANIF_00311 | Invalid ControllerId in `SetControllerMode()` → `CANIF_E_PARAM_CONTROLLERID` | ✅ | `CanIf_SetControllerMode()` | 236 | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` |
| SWS_CANIF_00774 | Invalid ControllerMode in `SetControllerMode()` → `CANIF_E_PARAM_CTRLMODE` | ❌ | `CanIf_SetControllerMode()` | 246–316 | `CANIF_CS_UNINIT` case falls through silently; no DET error reported |
| SWS_CANIF_00313 | Invalid ControllerId in `GetControllerMode()` → `CANIF_E_PARAM_CONTROLLERID` | ✅ | `CanIf_GetControllerMode()` | 329 | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` |
| SWS_CANIF_00656 | Null ControllerModePtr in `GetControllerMode()` → `CANIF_E_PARAM_POINTER` | ✅ | `CanIf_GetControllerMode()` | 330 | `VALIDATE(ControllerModePtr != NULL, ...)` |
| SWS_CANIF_00677 | Controller STOPPED + Transmit called → return `E_NOT_OK` (no `Can_Write`) | ✅ | `CanIf_Transmit()` | 446–452 | `CanIf_GetControllerMode()` checked; returns `E_NOT_OK` if not STARTED |
| SWS_CANIF_00898 | Invalid ControllerId in `GetControllerErrorState()` → `CANIF_E_PARAM_CONTROLLERID` | 🆕 | — | — | `CanIf_GetControllerErrorState()` does not exist in `CanIf.c` |
| SWS_CANIF_00899 | Null ErrorStatePtr in `GetControllerErrorState()` → `CANIF_E_PARAM_POINTER` | 🆕 | — | — | Same — function missing |

---

## Group D — PDU Channel Mode Management

*Requirements about `CanIf_SetPduMode()` and `CanIf_GetPduMode()` and their effects.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00864 | Init sets all channels to `CANIF_OFFLINE` | ✅ | `CanIf_Init()` | 140 | (Also in Group B) |
| SWS_CANIF_00865 | `SetControllerMode(SLEEP)` sets PDU mode to `CANIF_OFFLINE` | ⚠️ | `CanIf_SetControllerMode()` — SLEEP case | 271–289 | SLEEP case calls `Can_SetControllerMode(CAN_T_SLEEP)` but does NOT explicitly call `SetPduMode(OFFLINE)` |
| SWS_CANIF_00866 | `SetControllerMode(STOPPED)` or `ControllerBusOff()` → PDU mode = `CANIF_TX_OFFLINE` | ⚠️ | `CanIf_SetControllerMode()` STOPPED case; `CanIf_ControllerBusOff()` | 305, 935 | Code sets full `CANIF_OFFLINE` (not `TX_OFFLINE`); spec requires `TX_OFFLINE` to keep Rx active |
| SWS_CANIF_00073 | `CANIF_OFFLINE`: block Tx, block Rx callbacks, block Tx confirmations | ✅ | `CanIf_Transmit()` mode check; `CanIf_RxIndication()` mode check; `CanIf_TxConfirmation()` mode check | 459, 778, 754 | All three paths check for OFFLINE and reject |
| SWS_CANIF_00489 | `CANIF_TX_OFFLINE`: block Tx, allow Rx, block Tx confirmations | ✅ | `CanIf_Transmit()` mode check; `CanIf_RxIndication()` mode check | 459, 778 | `CANIF_GET_TX_ONLINE` excluded from allowed Tx modes; `CANIF_GET_TX_ONLINE` excluded from blocked Rx modes |
| SWS_CANIF_00075 | `CANIF_ONLINE`: allow Tx, allow Rx, allow confirmations | ✅ | `CanIf_SetControllerMode()` STARTED case calls `SetPduMode(ONLINE)` | 263 | Full online mode set on STARTED |
| SWS_CANIF_00072 | `CANIF_TX_OFFLINE_ACTIVE`: call TxConfirmation immediately without sending | ⚠️ | `CanIf_TxConfirmation()` checks for OFFLINE_ACTIVE | 754–758 | Confirmation callback allowed in OFFLINE_ACTIVE — but `CanIf_Transmit()` does NOT call confirmation immediately; it just returns E_NOT_OK |
| SWS_CANIF_00118 | BusOff notification not blocked after mode change for frames in hardware queue | ✅ | `CanIf_ControllerBusOff()` | 937–940 | BusOff callback called regardless of previous mode state |
| SWS_CANIF_00341 | Invalid ControllerId in `SetPduMode()` → `CANIF_E_PARAM_CONTROLLERID` | ✅ | `CanIf_SetPduMode()` | 551 | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` |
| SWS_CANIF_00860 | Invalid PduModeRequest in `SetPduMode()` → `CANIF_E_PARAM_PDU_MODE` | ❌ | `CanIf_SetPduMode()` | 555–625 | Invalid modes fall through switch silently; no DET error |
| SWS_CANIF_00874 | `SetPduMode()` rejects if controller not in `CAN_CS_STARTED` | ❌ | `CanIf_SetPduMode()` | 544–628 | No controller mode check before changing PDU mode |
| SWS_CANIF_00346 | Invalid ControllerId in `GetPduMode()` → `CANIF_E_PARAM_CONTROLLERID` | ✅ | `CanIf_GetPduMode()` | 639 | `VALIDATE(channel < CANIF_CHANNEL_CNT, ...)` |
| SWS_CANIF_00657 | Null PduModePtr in `GetPduMode()` → `CANIF_E_PARAM_POINTER` | ❌ | `CanIf_GetPduMode()` | 641 | `*PduModePtr` written without NULL check; no VALIDATE for pointer |

---

## Group E — Transmission (Tx Path)

*Requirements about how `CanIf_Transmit()` works.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00317 | Reject Transmit if controller not STARTED or Tx path not online/active | ✅ | `CanIf_Transmit()` | 446–461 | Checks both controller mode and PDU mode |
| SWS_CANIF_00318 | `Transmit()` calls `Can_Write()` with correct `Can_PduType` fields | ✅ | `CanIf_Transmit()` | 463–469 | `id`, `length`, `sdu`, `swPduHandle` all correctly filled |
| SWS_CANIF_00243 | Set two MSBits of CanId (ID extension + CAN-FD flags) before `Can_Write()` | ❌ | `CanIf_Transmit()` | 463 | `canPdu.id = txEntry->CanIfCanTxPduIdCanId` — MSBits NOT set; raw configured ID passed |
| SWS_CANIF_00162 | If `Can_Write()` returns `E_OK` → `CanIf_Transmit()` returns `E_OK` | ✅ | `CanIf_Transmit()` | 481 | `return E_OK` executed only if `Can_Write` didn't return BUSY or NOT_OK |
| SWS_CANIF_00319 | Invalid TxPduId in `Transmit()` → report `CANIF_E_INVALID_TXPDUID` | ✅ | `CanIf_Transmit()` | 438–440 | `VALIDATE(FALSE, CANIF_TRANSMIT_ID, CANIF_E_INVALID_TXPDUID)` when txEntry == 0 |
| SWS_CANIF_00320 | Null PduInfoPtr in `Transmit()` → report `CANIF_E_PARAM_POINTER` | ✅ | `CanIf_Transmit()` | 432 | `VALIDATE((PduInfoPtr != 0), CANIF_TRANSMIT_ID, CANIF_E_PARAM_POINTER)` |
| SWS_CANIF_00382 | PDU channel mode = OFFLINE + Transmit → report `CANIF_E_STOPPED` to DET | ⚠️ | `CanIf_Transmit()` | 459–461 | Returns `E_NOT_OK` correctly but does NOT call `Det_ReportRuntimeError()` with `CANIF_E_STOPPED` |
| SWS_CANIF_00882 | Accept NULL `SduDataPtr` for triggered-transmission PDUs | ❌ | `CanIf_Transmit()` | 423–482 | No `CanIfTxPduTriggerTransmit` field in config; NULL not checked or handled |
| SWS_CANIF_00893 | `SduLength` exceeds max (8 classic / 64 FD) → report `CANIF_E_DATA_LENGTH_MISMATCH` | ❌ | `CanIf_Transmit()` | 423–482 | No SduLength bounds check |
| SWS_CANIF_00894 | If `SduLength` exceeds global PDU length and truncation enabled → truncate | ❌ | `CanIf_Transmit()` | 423–482 | No truncation logic |
| SWS_CANIF_00900 | If `SduLength` exceeds global PDU length and truncation disabled → `E_NOT_OK` | ❌ | `CanIf_Transmit()` | 423–482 | No length vs global PDU check |

---

## Group F — Tx Buffering

*Requirements about buffering CAN frames when hardware is busy (`CAN_BUSY`).*  
**Note: This entire group is NOT implemented. The code on line 477 explicitly states "Tx buffering not supported".**

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00063 | Support Tx L-PDU buffering if `CanIfPublicTxBuffering` is enabled | ❌ | — | — | No buffer data structures; no `CanIfPublicTxBuffering` flag in config |
| SWS_CANIF_00381 | If `Can_Write()` returns `CAN_BUSY` for direct Tx → try to buffer the PDU | ❌ | `CanIf_Transmit()` | 475–479 | Returns `E_NOT_OK` immediately on `CAN_BUSY` — comment: "Tx buffering not supported" |
| SWS_CANIF_00881 | If `Can_Write()` returns `CAN_BUSY` for triggered Tx → try to buffer request | ❌ | `CanIf_Transmit()` | 475–479 | Same — no triggered Tx support |
| SWS_CANIF_00835 | Buffering only possible if assigned buffer size > 0 | ❌ | — | — | No buffer size config in `CanIf_TxPduConfigType` |
| SWS_CANIF_00836 | Buffer Tx L-PDU in a free buffer element if not already buffered | ❌ | — | — | No buffer array |
| SWS_CANIF_00068 | Overwrite existing buffered L-PDU if same PDU is already in buffer | ❌ | — | — | No buffer |
| SWS_CANIF_00837 | Buffer full for new PDU → `E_NOT_OK` | ❌ | — | — | No buffer — currently all CAN_BUSY returns E_NOT_OK |
| SWS_CANIF_00386 | During `TxConfirmation` → check for pending buffered PDUs | ❌ | `CanIf_TxConfirmation()` | 742–761 | No buffer check after confirmation |
| SWS_CANIF_00668 | Send highest-priority pending buffered PDU after hardware becomes free | ❌ | — | — | No buffer, no priority queue |
| SWS_CANIF_00070 | Transmit buffered PDUs in CAN priority order (per HTH) | ❌ | — | — | No buffer |
| SWS_CANIF_00183 | Remove PDU from buffer immediately when `Can_Write()` returns `E_OK` | ❌ | — | — | No buffer |
| SWS_CANIF_00387 | `CanIf_Init()` initializes all Tx L-PDU buffers | ❌ | `CanIf_Init()` | 131–146 | No buffer initialization |
| SWS_CANIF_00033 | Protect Tx buffer access against concurrent access | ❌ | — | — | No buffer, no critical sections |
| SWS_CANIF_00849 | For dynamic PDUs, also store CanId in Tx buffer | ❌ | — | — | No buffer |
| SWS_CANIF_00895 | If rejected data exceeds buffer size → store configured amount, discard rest, report error | ❌ | — | — | No buffer |
| SWS_CANIF_00466 | Each Tx L-PDU assigned to `CanIfBufferCfg` at config time | ❌ | `CanIf_TxPduConfigType` struct | CanIf_ConfigTypes.h:161–207 | No `CanIfTxPduBufferRef` field in the struct |
| SWS_CANIF_00485 | When controller enters `CAN_CS_STOPPED` → clear its Tx buffers | ❌ | `CanIf_SetControllerMode()` STOPPED case | 291–311 | No buffer to clear |
| SWS_CANIF_00739 | On `CAN_CS_STOPPED` → call `<User_TxConfirmation>(id, E_NOT_OK)` for all outstanding Tx | ❌ | `CanIf_SetControllerMode()` STOPPED case | 291–311 | No outstanding Tx tracking; no failure notification to upper layers |

---

## Group G — Tx Confirmation Callback

*Requirements about forwarding Tx done events to upper layers.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00383 | `TxConfirmation()` identifies upper layer and calls `<User_TxConfirmation>()` | ✅ | `CanIf_TxConfirmation()` | 750–758 | Looks up config entry; calls `entry->CanIfUserTxConfirmation(entry->CanIfTxPduId)` |
| SWS_CANIF_00412 | Not initialized when `TxConfirmation()` called → don't call upper layer | ✅ | `CanIf_TxConfirmation()` | 744 | `VALIDATE_NO_RV(CanIf_Global.initRun, ...)` |
| SWS_CANIF_00410 | Invalid `CanTxPduId` in `TxConfirmation()` → report `CANIF_E_PARAM_LPDU` | ✅ | `CanIf_TxConfirmation()` | 745 | Bounds check against `CanIfNumberOfCanTXPduIds` |
| SWS_CANIF_00391 | If `CanIfPublicReadTxPduNotifyStatusApi` TRUE → store Tx notification status | 🔧 | — | — | `CANIF_READTXPDU_NOTIFY_STATUS_API = STD_OFF`; not compiled |
| SWS_CANIF_00414 | Each Tx PDU must be configured with a `<User_TxConfirmation>` callback | ✅ | `CanIfUserTxConfirmation` function pointer in `CanIf_TxPduConfigType` | CanIf_ConfigTypes.h:197; CanIf_Cfg.c:158,173,186,200,214 | All 5 Tx PDUs have callbacks configured |
| SWS_CANIF_00438 | Config: upper layer module for TxConfirmation configured | ✅ | `CanIfUserTxConfirmation` field in Tx PDU config | CanIf_Cfg.c:158,173,186,200,214 | CanTp, CanNm, PduR all configured |
| SWS_CANIF_00542 | Config: name of `<User_TxConfirmation>()` configured | ✅ | Function pointer values in CanIf_Cfg.c | CanIf_Cfg.c:158,173,186,200,214 | Specific function names assigned |
| SWS_CANIF_00439 | PduR Tx confirmation → must be `PduR_CanIfTxConfirmation` | ✅ | CanIf_Cfg.c | 200 | `PduR_CanIfTxConfirmation` used for TxMsgTime |
| SWS_CANIF_00543 | CanNm Tx confirmation → must be `CanNm_TxConfirmation` | ✅ | CanIf_Cfg.c | 186, 214 | `CanNm_TxConfirmation` used for LS_NM_TX and HS_NM_TX |
| SWS_CANIF_00550 | CanTp Tx confirmation → must be `CanTp_TxConfirmation` | ✅ | CanIf_Cfg.c | 158, 173 | `CanTp_TxConfirmation` used for TxDiagP2P and TxDiagP2A |
| SWS_CANIF_00544 | J1939TP Tx confirmation → `J1939Tp_TxConfirmation` | N/A | — | — | J1939TP not used in this configuration |
| SWS_CANIF_00556 | XCP Tx confirmation → `Xcp_CanIfTxConfirmation` | N/A | — | — | XCP not used |
| SWS_CANIF_00551 | CDD Tx confirmation → configurable name | ✅ | `CANIF_USER_TYPE_CAN_SPECIAL` case | CanIf_RxIndication: 833–843 | Custom function pointer mechanism exists |
| SWS_CANIF_00858 | J1939NM Tx confirmation → `J1939Nm_TxConfirmation` | N/A | — | — | Not used |
| SWS_CANIF_00879 | CAN_TSYN Tx confirmation → `CanTSyn_TxConfirmation` | N/A | — | — | Not used |
| SWS_CANIF_00740 | If polling support enabled → buffer TxConfirmation info per controller | 🔧 | — | — | `CanIfPublicTxConfirmPollingSupport` not implemented |
| SWS_CANIF_00905 | Bus Mirroring active → call `Mirror_ReportCanFrame()` on TxConfirmation | 🔧 | — | — | Bus Mirroring not implemented; `Mirror.h` not included |

---

## Group H — Reception & Software Filtering

*Requirements about how `CanIf_RxIndication()` accepts and filters frames.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00389 | `RxIndication()` processes software filtering if configured | ✅ | `CanIf_RxIndication()` | 798–820 | Filter applied for BasicCAN HRH with `CanIfSoftwareFilterHrh = TRUE` |
| SWS_CANIF_00390 | After software filtering passes → perform DLC check | ✅ | `CanIf_RxIndication()` | 823–828 | Order: filter (798–820) → DLC check (823–828) |
| SWS_CANIF_00211 | Execute software acceptance filter from SWS_CANIF_00469 | ✅ | `CanIf_RxIndication()` | 799–820 | MASK filter: `(CanId & mask) == (config_CanId & mask)` |
| SWS_CANIF_00877 | Compare CanIfRxPduCanId AND MSBits of received CanId | ⚠️ | `CanIf_RxIndication()` | 803–806 | Mask comparison done; 11-bit vs 29-bit type NOT compared |
| SWS_CANIF_00030 | If CanId matches HRH configuration → accept the PDU | ✅ | `CanIf_RxIndication()` | 795–806 | HRH match + mask filter = acceptance |
| SWS_CANIF_00645 | Range filter defined by upper/lower limit OR base ID + mask | ⚠️ | `CanIf_HrhRangeConfigType` struct exists; `CanIfHrhRangeConfig = NULL` in config | CanIf_ConfigTypes.h:66–76; CanIf_Cfg.c:109,123 | Range config struct defined but never populated or used in filter |
| SWS_CANIF_00646 | Range is configurable for Standard or Extended CAN IDs | ⚠️ | `CanIf_HrhRangeConfigType` struct | CanIf_ConfigTypes.h:66–76 | Struct exists; not used in code |
| SWS_CANIF_00852 | Priority: single CanId > smaller range > larger range in overlapping case | ❌ | `CanIf_RxIndication()` | 793–894 | No priority logic; first-match-in-loop wins |
| SWS_CANIF_00281 | Accept both Standard and Extended IDs on same channel | ⚠️ | `CanIfRxPduIdCanIdType` field | CanIf_ConfigTypes.h:250 | Type field defined but NOT checked during filtering |
| SWS_CANIF_00026 | Accept received L-PDU if received DLC >= configured DLC | ✅ | `CanIf_RxIndication()` | 823–828 | `if (CanDlc < entry->CanIfCanRxPduDlc)` rejects undersized frames |
| SWS_CANIF_00390 | DLC check comes after software filtering | ✅ | `CanIf_RxIndication()` | 798–828 | Correct order maintained |
| SWS_CANIF_00902 | DLC check enabled globally via flag AND can be disabled per PDU | ⚠️ | `CanIf_RxIndication()` | 823 | Global `#if (CANIF_DLC_CHECK == STD_ON)` implemented; no per-PDU disable flag |
| SWS_CANIF_00168 | DLC check fails → report `CANIF_E_INVALID_DATA_LENGTH` | ✅ | `CanIf_RxIndication()` | 826 | `VALIDATE_NO_RV(FALSE, CANIF_RXINDICATION_ID, CANIF_E_PARAM_DLC)` |
| SWS_CANIF_00829 | Pass received length to upper layer if DLC check passed | ✅ | `CanIf_RxIndication()` | 858, 872, 879 | `pduInfo.SduLength = CanDlc` passed to PduR, CanTp, J1939Tp |
| SWS_CANIF_00830 | Pass received length to upper layer if DLC check not configured | ✅ | `CanIf_RxIndication()` | 858, 872, 879 | CanDlc always passed regardless of check config |
| SWS_CANIF_00906 | Bus Mirroring active → call `Mirror_ReportCanFrame()` on RxIndication | 🔧 | — | — | Bus Mirroring not implemented |

---

## Group I — Rx Indication Callback Routing

*Requirements about routing received frames to the correct upper layer module.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00056 | After DLC check → identify configured upper layer for this Rx PDU | ✅ | `CanIf_RxIndication()` | 831 | `switch(entry->CanIfRxUserType)` selects upper layer |
| SWS_CANIF_00135 | Call the configured `<User_RxIndication>()` callback | ✅ | `CanIf_RxIndication()` | 833–890 | All supported user types call their respective callback |
| SWS_CANIF_00415 | `RxIndication()` routes indication to configured upper layer(s) | ✅ | `CanIf_RxIndication()` | 831–890 | Full routing switch-case block |
| SWS_CANIF_00392 | If `CanIfPublicReadRxPduNotifyStatusApi` TRUE → store Rx notification status | 🔧 | — | — | `CANIF_READRXPDU_NOTIFY_STATUS_API = STD_OFF` |
| SWS_CANIF_00416 | Invalid HOH in `RxIndication()` → report `CANIF_E_PARAM_HOH` | ✅ | `CanIf_Arc_FindHrhChannel()` | 123 | `DET_REPORTERROR(... CANIF_E_PARAM_HRH)` if HRH not found |
| SWS_CANIF_00417 | Invalid CanId in `RxIndication()` → report `CANIF_E_PARAM_CANID` | ❌ | `CanIf_RxIndication()` | 763–898 | CanId is not validated before use in filtering |
| SWS_CANIF_00419 | Null `PduInfoPtr` or `Mailbox` in `RxIndication()` → `CANIF_E_PARAM_POINTER` | ⚠️ | `CanIf_RxIndication()` | 767 | `CanSduPtr != NULL` checked; no Mailbox parameter in this older API signature |
| SWS_CANIF_00421 | Not initialized when `RxIndication()` called → don't process | ✅ | `CanIf_RxIndication()` | 766 | `VALIDATE_NO_RV(CanIf_Global.initRun, ...)` |
| SWS_CANIF_00423 | Config: each Rx PDU must have a configured `<User_RxIndication>()` | ✅ | `CanIfRxUserType` + routing; CanIf_Cfg.c | 831–890; CanIf_Cfg.c:236,255,273 | All 3 Rx PDUs have user type configured |
| SWS_CANIF_00441 | Config: upper layer module configured via `CanIfRxPduUserRxIndicationUL` | ✅ | `CanIfRxUserType` enum field | CanIf_ConfigTypes.h:253 | PDUR, CanTp, CanNm, J1939TP, SPECIAL supported |
| SWS_CANIF_00552 | Config: name of `<User_RxIndication>()` configured via parameter | ✅ | Hardcoded in `CanIf_RxIndication()` switch-case | 846–889 | Function names resolved at compile time via `#if defined(USE_...)` |
| SWS_CANIF_00442 | PduR RxIndication → must be `PduR_CanIfRxIndication` | ✅ | `CanIf_RxIndication()` | 860 | `PduR_CanIfRxIndication(entry->CanIfCanRxPduId, &pduInfo)` |
| SWS_CANIF_00445 | CanNm RxIndication → must be `CanNm_RxIndication` | ✅ | `CanIf_RxIndication()` | 848 | `CanNm_RxIndication(entry->CanIfCanRxPduId, CanSduPtr)` |
| SWS_CANIF_00448 | CanTp RxIndication → must be `CanTp_RxIndication` | ✅ | `CanIf_RxIndication()` | 873 | `CanTp_RxIndication(entry->CanIfCanRxPduId, &CanTpRxPdu)` |
| SWS_CANIF_00554 | J1939TP RxIndication → must be `J1939Tp_RxIndication` | ✅ | `CanIf_RxIndication()` | 885 | `J1939Tp_RxIndication(entry->CanIfCanRxPduId, &J1939TpRxPdu)` |
| SWS_CANIF_00555 | XCP RxIndication → `Xcp_CanIfRxIndication` | N/A | — | — | XCP not used in this config |
| SWS_CANIF_00557 | CDD RxIndication → configurable name | ✅ | `CANIF_USER_TYPE_CAN_SPECIAL` case | 833–843 | Custom function pointer with extended signature |
| SWS_CANIF_00859 | J1939NM RxIndication → `J1939Nm_RxIndication` | N/A | — | — | Not used |
| SWS_CANIF_00880 | CAN_TSYN RxIndication → `CanTSyn_RxIndication` | N/A | — | — | Not used |

---

## Group J — Rx Buffering & Notification Status

*All disabled by compile flags (`STD_OFF`).*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00198 | If `CanIfPublicReadRxPduDataApi` TRUE → allocate Rx L-SDU buffer | 🔧 | — | — | `CANIF_READRXPDU_DATA_API = STD_OFF` |
| SWS_CANIF_00199 | After filtering+DLC → store received L-SDU in Rx buffer | 🔧 | — | — | Same flag |
| SWS_CANIF_00297 | Copy received bytes to static receive buffer | 🔧 | — | — | Same flag |
| SWS_CANIF_00851 | Copy CanId to MetaData on reception | 🔧 | — | — | MetaData not supported |
| SWS_CANIF_00472 | If `CanIfPublicReadTxPduNotifyStatusApi` TRUE → store Tx notification status | 🔧 | — | — | `CANIF_READTXPDU_NOTIFY_STATUS_API = STD_OFF` |
| SWS_CANIF_00473 | If `CanIfPublicReadRxPduNotifyStatusApi` TRUE → store Rx notification status | 🔧 | — | — | `CANIF_READRXPDU_NOTIFY_STATUS_API = STD_OFF` |
| SWS_CANIF_00324 | `ReadRxPduData()` rejects if controller not STARTED or Rx not online | 🔧 | `CanIf_ReadRxPduData()` | 490 | `VALIDATE(FALSE, ...)` — always returns E_NOT_OK |
| SWS_CANIF_00325 | Invalid RxPduId in `ReadRxPduData()` → `CANIF_E_INVALID_RXPDUID` | 🔧 | `CanIf_ReadRxPduData()` | 490 | Stub; unreachable |
| SWS_CANIF_00326 | Null PduInfoPtr in `ReadRxPduData()` → `CANIF_E_PARAM_POINTER` | 🔧 | `CanIf_ReadRxPduData()` | 492 | Stub; unreachable |
| SWS_CANIF_00329 | `ReadRxPduData()` not for range-reception PDUs | 🔧 | — | — | Not applicable — function disabled |
| SWS_CANIF_00330 | `ReadRxPduData()` configurable at compile time | ✅ | `#if (CANIF_READRXPDU_DATA_API == STD_ON)` | 486 | Correctly guarded |
| SWS_CANIF_00393 | `ReadTxNotifStatus()` resets notification status when called | 🔧 | `CanIf_ReadTxNotifStatus()` | 506 | `VALIDATE(FALSE, ...)` — always returns CANIF_NO_NOTIFICATION |
| SWS_CANIF_00331 | Invalid TxSduId in `ReadTxNotifStatus()` → `CANIF_E_INVALID_TXPDUID` | 🔧 | `CanIf_ReadTxNotifStatus()` | 506 | Stub |
| SWS_CANIF_00335 | `ReadTxNotifyStatus()` configurable at compile time | ✅ | `#if (CANIF_READTXPDU_NOTIFY_STATUS_API == STD_ON)` | 502 | Correctly guarded |
| SWS_CANIF_00394 | `ReadRxNotifStatus()` resets notification status when called | 🔧 | `CanIf_ReadRxNotifStatus()` | 535 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00336 | Invalid RxSduId in `ReadRxNotifStatus()` → `CANIF_E_INVALID_RXPDUID` | 🔧 | `CanIf_ReadRxNotifStatus()` | 535 | Stub |
| SWS_CANIF_00340 | `ReadRxNotifStatus()` configurable at compile time | ✅ | `#if (CANIF_READRXPDU_NOTIFY_STATUS_API == STD_ON)` | 532 | Correctly guarded |

---

## Group K — Dynamic PDU (Runtime CAN ID)

*Disabled by `CANIF_ARC_RUNTIME_PDU_CONFIGURATION = STD_OFF`.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00844 | Support dynamic L-PDUs (CanId in MetaData) | 🔧 | — | — | `CANIF_ARC_RUNTIME_PDU_CONFIGURATION = STD_OFF` |
| SWS_CANIF_00188 | Process MSBits of CanId for dynamic Tx L-PDU type determination | ⚠️ | `CanIf_SetDynamicTxId()` | 669–673 | Present in code but only compiles when RUNTIME config is ON |
| SWS_CANIF_00673 | Data consistency of CanId during concurrent `SetDynamicTxId()` and `Transmit()` | ❌ | `CanIf_SetDynamicTxId()` | 647–680 | No mutex/atomic operation; concurrent access not protected |
| SWS_CANIF_00855 | CanId from MetaData if mask/CanId fields omitted | N/A | — | — | MetaData not supported |
| SWS_CANIF_00856 | Ignore mask if CAN_ID_32 not in MetaData | N/A | — | — | MetaData not supported |
| SWS_CANIF_00854 | MetaData mask defines which bits go into final CanId | N/A | — | — | MetaData not supported |
| SWS_CANIF_00857 | `Init()` sets dynamic Tx PDU CanIds to configured default | 🔧 | — | — | Dynamic PDUs disabled |
| SWS_CANIF_00847 | Dynamic Rx PDUs must use ID range or mask + CAN_ID_32 MetaData | N/A | — | — | Not applicable |
| SWS_CANIF_00848 | On Rx of dynamic L-SDU → place CanId in MetaDataItem CAN_ID_32 | N/A | — | — | Not applicable |
| SWS_CANIF_00352 | Invalid TxPduId in `SetDynamicTxId()` → `CANIF_E_INVALID_TXPDUID` | 🔧 | `CanIf_SetDynamicTxId()` | 657 | Code exists; guarded by `#if (CANIF_ARC_RUNTIME_PDU_CONFIGURATION == STD_ON)` |
| SWS_CANIF_00353 | Invalid CanId in `SetDynamicTxId()` → `CANIF_E_PARAM_CANID` | 🔧 | `CanIf_SetDynamicTxId()` | 678 | Same guard |
| SWS_CANIF_00355 | Not initialized → `SetDynamicTxId()` does nothing | 🔧 | `CanIf_SetDynamicTxId()` | 650 | Same guard |
| SWS_CANIF_00357 | `SetDynamicTxId()` configurable at compile time | ✅ | `#if (CANIF_ARC_RUNTIME_PDU_CONFIGURATION == STD_ON)` | 646 | Correctly guarded |

---

## Group L — BusOff Handling

*Requirements about `CanIf_ControllerBusOff()` and the BusOff notification chain.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00724 | `ControllerBusOff()` → call `CanSM_ControllerBusOff()` or CDD | ⚠️ | `CanIf_ControllerBusOff()` | 937–940 | Mechanism correct (`CanIfBusOffNotification` called) BUT config sets it to NULL — no upper layer actually notified |
| SWS_CANIF_00429 | Invalid ControllerId in `ControllerBusOff()` → `CANIF_E_PARAM_CONTROLLERID` | ✅ | `CanIf_ControllerBusOff()` | 931 | `VALIDATE_NO_RV(Controller < CANIF_CHANNEL_CNT, ...)` |
| SWS_CANIF_00431 | Not initialized → don't execute BusOff notification | ✅ | `CanIf_ControllerBusOff()` | 921 | `VALIDATE_NO_RV(CanIf_Global.initRun, ...)` |
| SWS_CANIF_00433 | Config: ControllerId published in CanIf config | ✅ | `Arc_ChannelToControllerMap[]` | CanIf_Cfg.c:37–41 | Mapping from CAN driver controller IDs to CanIf channel IDs |
| SWS_CANIF_00866 | `SetControllerMode(STOPPED)` or `ControllerBusOff()` → set PDU to `TX_OFFLINE` | ⚠️ | `CanIf_ControllerBusOff()` → `CanIf_SetControllerMode(STOPPED)` | 935 | Sets full `CANIF_OFFLINE` (via STOPPED path); spec wants `TX_OFFLINE` (Rx still active) |
| SWS_CANIF_00524 | At least one `<User_ControllerBusOff>()` MUST be configured | ❌ | CanIf_Cfg.c | 74 | `CanIfBusOffNotification = NULL` — **violates this mandatory requirement** |
| SWS_CANIF_00450 | Config: upper layer for BusOff callback configured | ✅ | `CanIfBusOffNotification` field in `CanIf_DispatchConfigType` | CanIf_ConfigTypes.h:331 | Field exists; currently NULL in this project |
| SWS_CANIF_00558 | Config: name of `<User_ControllerBusOff>()` configured | ✅ | `CanIfBusOffNotification` function pointer | CanIf_ConfigTypes.h:331 | Function pointer mechanism correct |
| SWS_CANIF_00559 | CanSM → callback must be `CanSM_ControllerBusOff` | N/A | — | — | CanSM not configured in this project |
| SWS_CANIF_00560 | CDD → configurable name | ✅ | Function pointer mechanism | CanIf_ConfigTypes.h:331 | Can point to any function |
| SWS_CANIF_00918 | Report security event `CANIF_SEV_ERRORSTATE_BUSOFF` on BusOff | 🆕 | — | — | Security event reporting not implemented; `CanIf_ControllerBusOff()` doesn't call IdsM |

---

## Group M — Controller & Transceiver Mode Indications

*Callbacks from CAN driver that CanIf should forward to CanSM — entirely absent from code.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00711 | `CanIf_ControllerModeIndication()` → call `CanSM_ControllerModeIndication()` | 🆕 | — | — | Function does NOT exist in CanIf.c |
| SWS_CANIF_00700 | Invalid ControllerId in `ControllerModeIndication()` → error | 🆕 | — | — | Function missing |
| SWS_CANIF_00702 | Not initialized → don't execute `ControllerModeIndication()` | 🆕 | — | — | Function missing |
| SWS_CANIF_00689 | Config: upper layer for ControllerModeIndication | 🆕 | — | — | Function missing |
| SWS_CANIF_00690 | Config: name of `ControllerModeIndication` callback | 🆕 | — | — | Function missing |
| SWS_CANIF_00691 | CanSM → `CanSM_ControllerModeIndication` | 🆕 | — | — | Function missing |
| SWS_CANIF_00692 | CDD → configurable name | 🆕 | — | — | Function missing |
| SWS_CANIF_00712 | `CanIf_TrcvModeIndication()` → call `CanSM_TransceiverModeIndication()` | 🆕 | — | — | Function does NOT exist in CanIf.c |
| SWS_CANIF_00706 | Invalid TransceiverId in `TrcvModeIndication()` → error | 🆕 | — | — | Function missing |
| SWS_CANIF_00708 | Not initialized → don't execute `TrcvModeIndication()` | 🆕 | — | — | Function missing |
| SWS_CANIF_00710 | Config: TransceiverId for TrcvModeIndication | 🆕 | — | — | Function missing |
| SWS_CANIF_00730 | `TrcvModeIndication()` not provided if no transceivers | ✅ | — | — | Consistent — no transceivers configured; function correctly absent |
| SWS_CANIF_00694 | Caveats of `TrcvModeIndication()` (task-level, re-entrant per Trcv) | N/A | — | — | Not applicable; no transceivers |
| SWS_CANIF_00695 | Config: upper layer for TrcvModeIndication | N/A | — | — | Not applicable |
| SWS_CANIF_00696 | Config: name of `TrcvModeIndication` callback | N/A | — | — | Not applicable |
| SWS_CANIF_00697 | CanSM → `CanSM_TransceiverModeIndication` | N/A | — | — | Not applicable |

---

## Group N — Wakeup

*All disabled by `CANIF_WAKEUP_EVENT_API = STD_OFF`.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00395 | `CheckWakeup()` queries Can drivers/transceivers for wakeup source | 🔧 | `CanIf_CheckWakeup()` | 722–728 | Stub — `VALIDATE(FALSE, ... CANIF_E_NOK_NOSUPPORT)` |
| SWS_CANIF_00720 | If any `Can_CheckWakeup()` returns E_OK → `CheckWakeup()` returns E_OK | 🔧 | — | — | Not implemented |
| SWS_CANIF_00678 | If all return E_NOT_OK → `CheckWakeup()` returns E_NOT_OK | 🔧 | `CanIf_CheckWakeup()` | 727 | Stub returns E_NOT_OK; technically correct result but not from actual hardware query |
| SWS_CANIF_00286 | If wakeup validation enabled → store first RxIndication event per controller | 🔧 | — | — | `CANIF_WAKEUP_EVENT_API = STD_OFF` |
| SWS_CANIF_00179 | `CheckValidation()` calls `<User_ValidateWakeupEvent>()` if event stored | 🔧 | `CanIf_CheckValidation()` | 730–736 | Stub |
| SWS_CANIF_00756 | Clear wakeup event when entering `CAN_CS_SLEEP` | ❌ | `CanIf_SetControllerMode()` SLEEP case | 271–289 | No wakeup event storage; nothing to clear |
| SWS_CANIF_00398 | Invalid WakeupSource in `CheckWakeup()` → error | 🔧 | `CanIf_CheckWakeup()` | 724 | Stub; `CANIF_WAKEUP_EVENT_API = STD_OFF` |
| SWS_CANIF_00404 | Invalid WakeupSource in `CheckValidation()` → error | 🔧 | `CanIf_CheckValidation()` | 732 | Stub |
| SWS_CANIF_00408 | `CheckValidation()` configurable | ✅ | `#if (CANIF_WAKEUP_EVENT_API == STD_ON)` | 721 | Correctly guarded |
| SWS_CANIF_00659 | `<User_ValidateWakeupEvent>` callback configurable | 🔧 | — | — | Wakeup disabled |
| SWS_CANIF_00456 | Config: upper layer for wakeup validation | N/A | — | — | Wakeup disabled |
| SWS_CANIF_00563 | EcuM → `EcuM_ValidateWakeupEvent` | N/A | — | — | Wakeup disabled |
| SWS_CANIF_00564 | CDD → configurable wakeup validation name | N/A | — | — | Wakeup disabled |

---

## Group O — Transceiver Management

*All disabled by `CANIF_TRANSCEIVER_API = STD_OFF`.*

| Req ID | Short Description | Status | Function / File | Lines | Notes |
|--------|-------------------|--------|-----------------|-------|-------|
| SWS_CANIF_00358 | `SetTrcvMode()` → call `CanTrcv_SetOpMode()` | 🔧 | `CanIf_SetTransceiverMode()` | 684–691 | Stub — always E_NOT_OK |
| SWS_CANIF_00538 | Invalid TransceiverId in `SetTrcvMode()` → error | 🔧 | Same stub | 687 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00648 | Invalid TransceiverMode in `SetTrcvMode()` → error | 🔧 | Same stub | 687 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00362 | `SetTrcvMode()` configurable; E_NOT_OK if no transceiver | ✅ | `#if (CANIF_TRANSCEIVER_API == STD_ON)` + E_NOT_OK return | 683, 691 | Correctly returns E_NOT_OK |
| SWS_CANIF_00363 | `GetTrcvMode()` → call `CanTrcv_GetOpMode()` | 🔧 | `CanIf_GetTransceiverMode()` | 693–700 | Stub |
| SWS_CANIF_00364 | Invalid TransceiverId in `GetTrcvMode()` → error | 🔧 | Same stub | 696 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00650 | Null TransceiverModePtr in `GetTrcvMode()` → error | 🔧 | Same stub | 696 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00367 | `GetTrcvMode()` configurable; E_NOT_OK if no transceiver | ✅ | `#if (CANIF_TRANSCEIVER_API == STD_ON)` + E_NOT_OK | 683, 700 | Correctly handled |
| SWS_CANIF_00368 | `GetTrcvWakeupReason()` → call `CanTrcv_GetBusWuReason()` | 🔧 | `CanIf_GetTrcvWakeupReason()` | 702–709 | Stub |
| SWS_CANIF_00537 | Invalid TransceiverId in `GetTrcvWakeupReason()` → error | 🔧 | Same stub | 705 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00649 | Null TrcvWuReasonPtr in `GetTrcvWakeupReason()` → error | 🔧 | Same stub | 705 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00371 | `GetTrcvWakeupReason()` configurable | ✅ | `#if (CANIF_TRANSCEIVER_API == STD_ON)` | 683 | Correctly guarded |
| SWS_CANIF_00372 | `SetTrcvWakeupMode()` → call `CanTrcv_SetWakeupMode()` | 🔧 | `CanIf_SetTransceiverWakeupMode()` | 711–718 | Stub |
| SWS_CANIF_00535 | Invalid TransceiverId in `SetTrcvWakeupMode()` → error | 🔧 | Same stub | 714 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00536 | Invalid TrcvWakeupMode in `SetTrcvWakeupMode()` → error | 🔧 | Same stub | 714 | `VALIDATE(FALSE, ...)` |
| SWS_CANIF_00373 | `SetTrcvWakeupMode()` configurable | ✅ | `#if (CANIF_TRANSCEIVER_API == STD_ON)` | 683 | Correctly guarded |
| SWS_CANIF_00766 | `ClearTrcvWufFlag()` → `CanTrcv_ClearTrcvWufFlag()` | 🆕 | — | — | Function does NOT exist in CanIf.c (PN feature) |
| SWS_CANIF_00769 | Invalid TransceiverId in `ClearTrcvWufFlag()` → error | 🆕 | — | — | Function missing |
| SWS_CANIF_00771 | `ClearTrcvWufFlag()` configurable via `CanIfPublicPnSupport` | N/A | — | — | PN not supported |
| SWS_CANIF_00765 | `CheckTrcvWakeFlag()` → `CanTrcv_CheckWakeFlag()` | 🆕 | — | — | Function missing |
| SWS_CANIF_00770 | Invalid TransceiverId in `CheckTrcvWakeFlag()` → error | 🆕 | — | — | Function missing |
| SWS_CANIF_00813 | `CheckTrcvWakeFlag()` configurable via `CanIfPublicPnSupport` | N/A | — | — | PN not supported |

---

## Group P — Partial Networking (PN)

*Completely absent from this implementation.*

| Req ID | Short Description | Status | Notes |
|--------|-------------------|--------|-------|
| SWS_CANIF_00747 | Support PnTxFilter per CAN Controller | ❌ | No PN data structures in code |
| SWS_CANIF_00748 | PnTxFilter only effective if PN PDUs configured | ❌ | No PN support |
| SWS_CANIF_00863 | PnTxFilter enabled during init | ❌ | No PN support |
| SWS_CANIF_00749 | `SetControllerMode(SLEEP)` enables PnTxFilter | ❌ | No PN support |
| SWS_CANIF_00750 | PnTxFilter enabled → block all Tx except PN PDUs | ❌ | No PN support |
| SWS_CANIF_00751 | `TxConfirmation()` → disable PnTxFilter | ❌ | No PN support |
| SWS_CANIF_00896 | `RxIndication()` called with PnTxFilter enabled → disable it | ❌ | No PN support |
| SWS_CANIF_00752 | PnTxFilter disabled → behave as per `SetPduMode()` | ❌ | No PN support |
| SWS_CANIF_00878 | `SetPduMode(TX_OFFLINE)` with PN enabled → enable PnTxFilter | ❌ | No PN support |
| SWS_CANIF_00753 | `CanIf_ConfirmPnAvailability()` → call `<User_ConfirmPnAvailability>()` | 🆕 | Function does not exist in CanIf.c |
| SWS_CANIF_00816 | Invalid TransceiverId in `ConfirmPnAvailability()` → error | 🆕 | Function missing |
| SWS_CANIF_00817 | Not initialized → don't execute `ConfirmPnAvailability()` | 🆕 | Function missing |
| SWS_CANIF_00754 | `ConfirmPnAvailability()` configurable via `CanIfPublicPnSupport` | N/A | PN not supported |
| SWS_CANIF_00757 | `CanIf_ClearTrcvWufFlagIndication()` → call user callback | 🆕 | Function missing |
| SWS_CANIF_00805 | Invalid TransceiverId in `ClearTrcvWufFlagIndication()` → error | 🆕 | Function missing |
| SWS_CANIF_00806 | Not initialized → don't execute | 🆕 | Function missing |
| SWS_CANIF_00808 | `ClearTrcvWufFlagIndication()` configurable | N/A | PN not supported |
| SWS_CANIF_00759 | `CanIf_CheckTrcvWakeFlagIndication()` → call user callback | 🆕 | Function missing |
| SWS_CANIF_00809 | Invalid TransceiverId → error | 🆕 | Function missing |
| SWS_CANIF_00810 | Not initialized → don't execute | 🆕 | Function missing |
| SWS_CANIF_00812 | `CheckTrcvWakeFlagIndication()` configurable | N/A | PN not supported |
| SWS_CANIF_00823 | Config: upper layer for `ConfirmPnAvailability` | N/A | PN not supported |
| SWS_CANIF_00824 | Config: name of `ConfirmPnAvailability` | N/A | PN not supported |
| SWS_CANIF_00825 | `ConfirmPnAvailability` configurable via `CanIfPublicPnSupport` | N/A | PN not supported |
| SWS_CANIF_00826 | CanSM → `CanSM_ConfirmPnAvailability` | N/A | PN not supported |
| SWS_CANIF_00827 | CDD → configurable name | N/A | PN not supported |
| SWS_CANIF_00794 | Config: upper layer for `ClearTrcvWufFlagIndication` | N/A | PN not supported |
| SWS_CANIF_00795 | Config: name of `ClearTrcvWufFlagIndication` | N/A | PN not supported |
| SWS_CANIF_00796 | Configurable via `CanIfPublicPnSupport` | N/A | PN not supported |
| SWS_CANIF_00797 | CanSM → `CanSM_ClearTrcvWufFlagIndication` | N/A | PN not supported |
| SWS_CANIF_00798 | CDD → configurable name | N/A | PN not supported |
| SWS_CANIF_00800 | Config: upper layer for `CheckTrcvWakeFlagIndication` | N/A | PN not supported |
| SWS_CANIF_00801 | Config: name of `CheckTrcvWakeFlagIndication` | N/A | PN not supported |
| SWS_CANIF_00802 | Configurable via `CanIfPublicPnSupport` | N/A | PN not supported |
| SWS_CANIF_00803 | CanSM → `CanSM_CheckTransceiverWakeFlagIndication` | N/A | PN not supported |
| SWS_CANIF_00804 | CDD → configurable name | N/A | PN not supported |

---

## Group Q — Security Events

*Not implemented — no IdsM integration.*

| Req ID | Short Description | Status | Notes |
|--------|-------------------|--------|-------|
| SWS_CANIF_00903 | Include `Mirror.h` if Bus Mirroring enabled | 🔧 | Bus Mirroring disabled |
| SWS_CANIF_00913 | Security event reporting enabled via `CanIfEnableSecurityEventReporting` | ❌ | No IdsM integration |
| SWS_CANIF_00915 | `ErrorNotification()`: Tx error → report `CANIF_SEV_TX_ERROR_DETECTED` | 🆕 | `CanIf_ErrorNotification()` (standard) missing; ArcCore has `CanIf_Arc_Error()` instead |
| SWS_CANIF_00916 | `ErrorNotification()`: Rx error → report `CANIF_SEV_RX_ERROR_DETECTED` | 🆕 | Same — function missing |
| SWS_CANIF_00917 | `ControllerErrorStatePassive()` → report `CANIF_SEV_ERRORSTATE_PASSIVE` | 🆕 | `CanIf_ControllerErrorStatePassive()` does not exist in CanIf.c |
| SWS_CANIF_00918 | `ControllerBusOff()` → report `CANIF_SEV_ERRORSTATE_BUSOFF` | ❌ | `CanIf_ControllerBusOff()` exists but does not call IdsM |
| SWS_CANIF_00919 | Invalid ControllerId in `ControllerErrorStatePassive()` → error | 🆕 | Function missing |
| SWS_CANIF_00920 | Invalid ControllerId in `ErrorNotification()` → error | ⚠️ | `CanIf_Arc_Error()` validates controller but uses ArcCore signature, not AUTOSAR `CanIf_ErrorNotification()` |
| SWS_CANIF_00921 | Invalid CanError in `ErrorNotification()` → error | ⚠️ | `CanIf_Arc_Error()` takes `Can_Arc_ErrorType` — ArcCore-specific |

---

## Group R — Advanced APIs

*Functions that should exist per the spec but are entirely absent from `CanIf.c`.*

| Req ID | Short Description | Status | Notes |
|--------|-------------------|--------|-------|
| SWS_CANIF_00868 | `CanIf_SetBaudrate()` → call `Can_SetBaudrate()` | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00869 | Invalid ControllerId in `SetBaudrate()` → error | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00871 | `SetBaudrate()` configurable via `CanIfSetBaudrateApi` | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00907 | Invalid ControllerId in `GetControllerRxErrorCounter()` → error | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00908 | Null RxErrorCounterPtr in `GetControllerRxErrorCounter()` → error | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00909 | Invalid ControllerId in `GetControllerTxErrorCounter()` → error | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00910 | Null TxErrorCounterPtr in `GetControllerTxErrorCounter()` → error | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00911 | `EnableBusMirroring()` can be omitted if mirroring not needed | ✅ | Bus Mirroring disabled; API correctly omitted |
| SWS_CANIF_00912 | Invalid ControllerId in `EnableBusMirroring()` → error | 🔧 | Bus Mirroring disabled |
| SWS_CANIF_00884 | `CanIf_TriggerTransmit()` only if `CanIfTriggerTransmitSupport = TRUE` | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00885 | `TriggerTransmit()` → call `<User_TriggerTransmit>()` | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00888 | Config: upper layer for TriggerTransmit | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00889 | Config: name of `<User_TriggerTransmit>()` | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00890 | PduR → `PduR_CanIfTriggerTransmit` | N/A | Function missing |
| SWS_CANIF_00891 | CDD → configurable TriggerTransmit name | N/A | Function missing |
| SWS_CANIF_00736 | Invalid ControllerId in `GetTxConfirmationState()` → error | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00738 | `GetTxConfirmationState()` configurable | 🆕 | Function not in CanIf.c |
| SWS_CANIF_00904 | Bus Mirroring active → store frame content before `Can_Write()` | 🔧 | Bus Mirroring disabled |
| SWS_CANIF_00905 | Bus Mirroring active → call `Mirror_ReportCanFrame()` on TxConfirmation | 🔧 | Bus Mirroring disabled |
| SWS_CANIF_00906 | Bus Mirroring active → call `Mirror_ReportCanFrame()` on RxIndication | 🔧 | Bus Mirroring disabled |

---

## Requirement → CanIf.c Function Mapping

Based on `Requirments/CanIf_SWS_AR403.csv` and the current `CanIf.c` implementation. Requirements that do not map to any `CanIf.c` function are omitted.

| Req ID | CanIf.c function(s) |
| --- | --- |
| SWS_CANIF_00665 | CanIf_RxIndication |
| SWS_CANIF_00663 | CanIf_RxIndication |
| SWS_CANIF_00666 | CanIf_Transmit, CanIf_TxConfirmation |
| SWS_CANIF_00115 | CanIf_Arc_FindHrhChannel |
| SWS_CANIF_00469 | CanIf_RxIndication |
| SWS_CANIF_00211 | CanIf_RxIndication |
| SWS_CANIF_00877 | CanIf_RxIndication |
| SWS_CANIF_00382 | CanIf_Transmit |
| SWS_CANIF_00085 | CanIf_Init |
| SWS_CANIF_00864 | CanIf_Init |
| SWS_CANIF_00387 | CanIf_Init |
| SWS_CANIF_00308 | CanIf_SetControllerMode |
| SWS_CANIF_00311 | CanIf_SetControllerMode |
| SWS_CANIF_00774 | CanIf_SetControllerMode |
| SWS_CANIF_00313 | CanIf_GetControllerMode |
| SWS_CANIF_00656 | CanIf_GetControllerMode |
| SWS_CANIF_00677 | CanIf_Transmit |
| SWS_CANIF_00865 | CanIf_SetControllerMode |
| SWS_CANIF_00866 | CanIf_SetControllerMode, CanIf_ControllerBusOff |
| SWS_CANIF_00073 | CanIf_Transmit, CanIf_TxConfirmation, CanIf_RxIndication |
| SWS_CANIF_00489 | CanIf_Transmit, CanIf_RxIndication |
| SWS_CANIF_00075 | CanIf_SetControllerMode |
| SWS_CANIF_00072 | CanIf_TxConfirmation |
| SWS_CANIF_00118 | CanIf_ControllerBusOff |
| SWS_CANIF_00341 | CanIf_SetPduMode |
| SWS_CANIF_00860 | CanIf_SetPduMode |
| SWS_CANIF_00874 | CanIf_SetPduMode |
| SWS_CANIF_00346 | CanIf_GetPduMode |
| SWS_CANIF_00657 | CanIf_GetPduMode |
| SWS_CANIF_00317 | CanIf_Transmit |
| SWS_CANIF_00318 | CanIf_Transmit |
| SWS_CANIF_00243 | CanIf_Transmit |
| SWS_CANIF_00162 | CanIf_Transmit |
| SWS_CANIF_00319 | CanIf_Transmit |
| SWS_CANIF_00320 | CanIf_Transmit |
| SWS_CANIF_00882 | CanIf_Transmit |
| SWS_CANIF_00893 | CanIf_Transmit |
| SWS_CANIF_00894 | CanIf_Transmit |
| SWS_CANIF_00900 | CanIf_Transmit |
| SWS_CANIF_00381 | CanIf_Transmit |
| SWS_CANIF_00881 | CanIf_Transmit |
| SWS_CANIF_00386 | CanIf_TxConfirmation |
| SWS_CANIF_00485 | CanIf_SetControllerMode |
| SWS_CANIF_00739 | CanIf_SetControllerMode |
| SWS_CANIF_00383 | CanIf_TxConfirmation |
| SWS_CANIF_00412 | CanIf_TxConfirmation |
| SWS_CANIF_00410 | CanIf_TxConfirmation |
| SWS_CANIF_00551 | CanIf_RxIndication |
| SWS_CANIF_00389 | CanIf_RxIndication |
| SWS_CANIF_00390 | CanIf_RxIndication |
| SWS_CANIF_00030 | CanIf_RxIndication |
| SWS_CANIF_00852 | CanIf_RxIndication |
| SWS_CANIF_00026 | CanIf_RxIndication |
| SWS_CANIF_00902 | CanIf_RxIndication |
| SWS_CANIF_00168 | CanIf_RxIndication |
| SWS_CANIF_00829 | CanIf_RxIndication |
| SWS_CANIF_00830 | CanIf_RxIndication |
| SWS_CANIF_00056 | CanIf_RxIndication |
| SWS_CANIF_00135 | CanIf_RxIndication |
| SWS_CANIF_00415 | CanIf_RxIndication |
| SWS_CANIF_00416 | CanIf_Arc_FindHrhChannel |
| SWS_CANIF_00417 | CanIf_RxIndication |
| SWS_CANIF_00419 | CanIf_RxIndication |
| SWS_CANIF_00421 | CanIf_RxIndication |
| SWS_CANIF_00423 | CanIf_RxIndication |
| SWS_CANIF_00552 | CanIf_RxIndication |
| SWS_CANIF_00442 | CanIf_RxIndication |
| SWS_CANIF_00445 | CanIf_RxIndication |
| SWS_CANIF_00448 | CanIf_RxIndication |
| SWS_CANIF_00554 | CanIf_RxIndication |
| SWS_CANIF_00557 | CanIf_RxIndication |
| SWS_CANIF_00324 | CanIf_ReadRxPduData |
| SWS_CANIF_00325 | CanIf_ReadRxPduData |
| SWS_CANIF_00326 | CanIf_ReadRxPduData |
| SWS_CANIF_00393 | CanIf_ReadTxNotifStatus |
| SWS_CANIF_00331 | CanIf_ReadTxNotifStatus |
| SWS_CANIF_00394 | CanIf_ReadRxNotifStatus |
| SWS_CANIF_00336 | CanIf_ReadRxNotifStatus |
| SWS_CANIF_00188 | CanIf_SetDynamicTxId |
| SWS_CANIF_00673 | CanIf_SetDynamicTxId |
| SWS_CANIF_00352 | CanIf_SetDynamicTxId |
| SWS_CANIF_00353 | CanIf_SetDynamicTxId |
| SWS_CANIF_00355 | CanIf_SetDynamicTxId |
| SWS_CANIF_00724 | CanIf_ControllerBusOff |
| SWS_CANIF_00429 | CanIf_ControllerBusOff |
| SWS_CANIF_00431 | CanIf_ControllerBusOff |
| SWS_CANIF_00918 | CanIf_ControllerBusOff |
| SWS_CANIF_00395 | CanIf_CheckWakeup |
| SWS_CANIF_00678 | CanIf_CheckWakeup |
| SWS_CANIF_00179 | CanIf_CheckValidation |
| SWS_CANIF_00756 | CanIf_SetControllerMode |
| SWS_CANIF_00398 | CanIf_CheckWakeup |
| SWS_CANIF_00404 | CanIf_CheckValidation |
| SWS_CANIF_00358 | CanIf_SetTransceiverMode |
| SWS_CANIF_00538 | CanIf_SetTransceiverMode |
| SWS_CANIF_00648 | CanIf_SetTransceiverMode |
| SWS_CANIF_00363 | CanIf_GetTransceiverMode |
| SWS_CANIF_00364 | CanIf_GetTransceiverMode |
| SWS_CANIF_00650 | CanIf_GetTransceiverMode |
| SWS_CANIF_00368 | CanIf_GetTrcvWakeupReason |
| SWS_CANIF_00537 | CanIf_GetTrcvWakeupReason |
| SWS_CANIF_00649 | CanIf_GetTrcvWakeupReason |
| SWS_CANIF_00372 | CanIf_SetTransceiverWakeupMode |
| SWS_CANIF_00535 | CanIf_SetTransceiverWakeupMode |
| SWS_CANIF_00536 | CanIf_SetTransceiverWakeupMode |
| SWS_CANIF_00920 | CanIf_Arc_Error |
| SWS_CANIF_00921 | CanIf_Arc_Error |

## Requirements × Functions Matrix

Only requirements that reference a function in `CanIf.c` are listed below; requirements that map exclusively to configuration/header files or missing APIs have no `CanIf.c` function mapping and are omitted here.

| Req ID | CanIf_Arc_FindHrhChannel | CanIf_Init | CanIf_InitController | CanIf_PreInit_InitController | CanIf_SetControllerMode | CanIf_GetControllerMode | CanIf_FindTxPduEntry | CanIf_FindRxPduEntry | CanIf_Arc_GetReceiveHandler | CanIf_Arc_GetTransmitHandler | CanIf_Transmit | CanIf_ReadRxPduData | CanIf_ReadTxNotifStatus | CanIf_ReadRxNotifStatus | CanIf_SetPduMode | CanIf_GetPduMode | CanIf_SetDynamicTxId | CanIf_SetTransceiverMode | CanIf_GetTransceiverMode | CanIf_GetTrcvWakeupReason | CanIf_SetTransceiverWakeupMode | CanIf_CheckWakeup | CanIf_CheckValidation | CanIf_TxConfirmation | CanIf_RxIndication | CanIf_CancelTxConfirmation | CanIf_ControllerBusOff | CanIf_SetWakeupEvent | CanIf_Arc_Error | CanIf_Arc_GetChannelDefaultConfIndex |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SWS_CANIF_00665 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00663 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00666 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |
| SWS_CANIF_00115 | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00469 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00211 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00877 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00382 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00085 |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00864 |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00387 |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00308 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00311 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00774 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00313 |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00656 |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00677 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00865 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00866 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |
| SWS_CANIF_00073 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  | X | X |  |  |  |  |  |
| SWS_CANIF_00489 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00075 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00072 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |
| SWS_CANIF_00118 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |
| SWS_CANIF_00341 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00860 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00874 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00346 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00657 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00317 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00318 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00243 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00162 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00319 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00320 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00882 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00893 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00894 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00900 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00381 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00881 |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00386 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |
| SWS_CANIF_00485 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00739 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00383 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |
| SWS_CANIF_00412 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |
| SWS_CANIF_00410 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |
| SWS_CANIF_00551 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00389 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00390 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00030 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00852 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00026 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00902 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00168 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00829 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00830 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00056 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00135 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00415 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00416 | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00417 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00419 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00421 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00423 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00552 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00442 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00445 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00448 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00554 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00557 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |
| SWS_CANIF_00324 |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00325 |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00326 |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00393 |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00331 |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00394 |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00336 |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00188 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00673 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00352 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00353 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00355 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00724 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |
| SWS_CANIF_00429 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |
| SWS_CANIF_00431 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |
| SWS_CANIF_00918 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |
| SWS_CANIF_00395 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |
| SWS_CANIF_00678 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |
| SWS_CANIF_00179 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |
| SWS_CANIF_00756 |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00398 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |
| SWS_CANIF_00404 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |
| SWS_CANIF_00358 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00538 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00648 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00363 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00364 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00650 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00368 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00537 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00649 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00372 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00535 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00536 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |  |  |  |  |  |  |  |  |
| SWS_CANIF_00920 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |
| SWS_CANIF_00921 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | X |  |

## Reverse Traceability — Code to Requirements

*Every function in `CanIf.c` mapped back to its requirement(s). Confirms no orphan code.*

| Function in CanIf.c | Lines | Backed by Requirement(s) |
|--------------------|-------|--------------------------|
| `CanIf_Arc_FindHrhChannel()` | 100–126 | *ArcCore extension* — no AUTOSAR req; supports SWS_CANIF_00116 |
| `CanIf_Init()` | 131–146 | SWS_CANIF_00085, 00661, 00864, 00523 |
| `CanIf_InitController()` | 156–204 | SWS_CANIF_00308 (calls `Can_InitController`) |
| `CanIf_PreInit_InitController()` | 206–222 | *ArcCore extension* — no AUTOSAR req; called from `CanIf_Init()` |
| `CanIf_SetControllerMode()` | 226–318 | SWS_CANIF_00308, 00311, 00865, 00866, 00073, 00075, 00774 |
| `CanIf_GetControllerMode()` | 322–335 | SWS_CANIF_00313, 00656 |
| `CanIf_FindTxPduEntry()` | 344–354 | Internal helper for SWS_CANIF_00318, 00319 |
| `CanIf_FindRxPduEntry()` | 358–364 | *Runtime config only* |
| `CanIf_Arc_GetReceiveHandler()` | 366–391 | *Runtime config only* |
| `CanIf_Arc_GetTransmitHandler()` | 393–418 | *Runtime config only* |
| `CanIf_Transmit()` | 423–482 | SWS_CANIF_00317, 00318, 00162, 00319, 00320, 00677, 00073, 00382 |
| `CanIf_ReadRxPduData()` | 487–497 | SWS_CANIF_00324, 00325, 00326, 00330 (disabled) |
| `CanIf_ReadTxNotifStatus()` | 503–527 | SWS_CANIF_00393, 00331, 00335 (disabled) |
| `CanIf_ReadRxNotifStatus()` | 533–539 | SWS_CANIF_00394, 00336, 00340 (disabled) |
| `CanIf_SetPduMode()` | 544–628 | SWS_CANIF_00341, 00073, 00489, 00075, 00072, 00860, 00874 |
| `CanIf_GetPduMode()` | 632–644 | SWS_CANIF_00346, 00657 |
| `CanIf_SetDynamicTxId()` | 647–680 | SWS_CANIF_00352, 00353, 00355, 00357, 00188 (disabled) |
| `CanIf_SetTransceiverMode()` | 684–691 | SWS_CANIF_00358, 00538, 00362 (disabled) |
| `CanIf_GetTransceiverMode()` | 693–700 | SWS_CANIF_00363, 00364, 00367 (disabled) |
| `CanIf_GetTrcvWakeupReason()` | 702–709 | SWS_CANIF_00368, 00537, 00371 (disabled) |
| `CanIf_SetTransceiverWakeupMode()` | 711–718 | SWS_CANIF_00372, 00535, 00373 (disabled) |
| `CanIf_CheckWakeup()` | 722–728 | SWS_CANIF_00395, 00398, 00408 (disabled) |
| `CanIf_CheckValidation()` | 730–736 | SWS_CANIF_00179, 00404, 00408 (disabled) |
| `CanIf_TxConfirmation()` | 742–761 | SWS_CANIF_00383, 00410, 00412, 00414 |
| `CanIf_RxIndication()` | 763–898 | SWS_CANIF_00389, 00211, 00026, 00390, 00168, 00056, 00135, 00415, 00416, 00419, 00421, 00442, 00445, 00448, 00554 |
| `CanIf_CancelTxConfirmation()` | 901–914 | SWS_CANIF_00901 (disabled) |
| `CanIf_ControllerBusOff()` | 917–941 | SWS_CANIF_00724, 00429, 00431, 00433, 00866 |
| `CanIf_SetWakeupEvent()` | 943–961 | *ArcCore extension stub* |
| `CanIf_Arc_Error()` | 963–989 | *ArcCore extension*; related to SWS_CANIF_00920, 00921 |
| `CanIf_Arc_GetChannelDefaultConfIndex()` | 991–994 | *ArcCore extension* |

---

## Coverage Summary

| Status | Count | % of ~164 mapped req IDs |
|--------|-------|--------------------------|
| ✅ IMPLEMENTED | 63 | 38% |
| ⚠️ PARTIAL | 15 | 9% |
| ❌ NOT DONE | 24 | 15% |
| 🔧 DISABLED (intentional) | 41 | 25% |
| 🆕 MISSING API | 22 | 13% |
| N/A (not applicable) | ~35 | — |

> **Active coverage** (implemented + partial out of all non-N/A requirements): **~47%**  
> **Core path coverage** (Groups A–I, L only): **~71%** — the primary Tx/Rx/Init/Mode path is well-covered  
> **Feature completeness** (all groups including PN, security, transceiver): **~38%**
