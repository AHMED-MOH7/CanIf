# CanIf.c — Complete Code Explanation

> **Step 1 of 3** — Full code understanding before traceability mapping.

---

## Table of Contents

1. [What is CanIf? (Big Picture)](#1-what-is-canif-big-picture)
2. [Where Does CanIf Live? (AUTOSAR Layer)](#2-where-does-canif-live-autosar-layer)
3. [Key Data Structures](#3-key-data-structures)
4. [All Functions — Quick Reference Table](#4-all-functions--quick-reference-table)
5. [Detailed Function Explanations](#5-detailed-function-explanations)
6. [Function Call Relationships](#6-function-call-relationships)
7. [Controller State Machine](#7-controller-state-machine)
8. [PDU Channel Mode State Machine](#8-pdu-channel-mode-state-machine)
9. [Configuration Overview (CanIf_Cfg.c / CanIf_Cfg.h)](#9-configuration-overview)
10. [What Is Implemented vs. Stubbed Out](#10-what-is-implemented-vs-stubbed-out)
11. [Files & Their Roles](#11-files--their-roles)

---

## 1. What is CanIf? (Big Picture)

**CanIf = CAN Interface**

Think of CanIf as a **middleman / translator** between the upper software layers (like PduR, CanTp, CanNm) and the actual CAN hardware driver (Can driver).

```
Upper Layers (PduR, CanNm, CanTp, CDD)
              ↕  (abstract API)
           [  CanIf  ]           ← YOU ARE HERE
              ↕  (hardware API)
       CAN Driver (Can.h/Can.c)
              ↕
        CAN Hardware (physical bus)
```

**What problems does CanIf solve?**

| Problem | CanIf Solution |
|---------|---------------|
| Upper layers don't know which CAN controller to use | CanIf maps logical PDU IDs → hardware handles (HTH/HRH) |
| Multiple CAN hardware drivers may exist | CanIf provides one unified API regardless of driver |
| CAN frames need routing to the correct upper layer | CanIf uses Rx PDU table + software filtering to route frames |
| Need to control CAN bus ON/OFF | CanIf manages controller modes and PDU channel modes |

---

## 2. Where Does CanIf Live? (AUTOSAR Layer)

```
┌──────────────────────────────────────┐
│  Application / RTE                   │
├──────────────────────────────────────┤
│  COM / DCM / NM (network management) │
├──────────────────────────────────────┤
│  PduR  │  CanNm  │  CanTp  │  CDD   │  ← upper layers that CALL CanIf
├──────────────────────────────────────┤
│           CanIf  (this file)         │  ← THE MODULE WE ARE STUDYING
├──────────────────────────────────────┤
│           Can Driver                 │  ← hardware abstraction layer
├──────────────────────────────────────┤
│           CAN Hardware               │
└──────────────────────────────────────┘
```

**Key AUTOSAR terms used in the code:**

| Term | Meaning |
|------|---------|
| **L-PDU** | Link Layer Protocol Data Unit — a CAN frame (ID + DLC + data) |
| **L-SDU** | Link Layer Service Data Unit — just the data payload part |
| **HTH** | Hardware Transmit Handle — reference to a CAN transmit mailbox |
| **HRH** | Hardware Receive Handle — reference to a CAN receive mailbox |
| **HOH** | Hardware Object Handle — collective term for HTH + HRH |
| **PduId** | Numeric ID used to identify a PDU within the software stack |
| **DLC** | Data Length Code — number of bytes in a CAN frame (0–8) |
| **BasicCAN** | A hardware receive object that can receive multiple CAN IDs |
| **FullCAN** | A hardware receive object fixed to one specific CAN ID |

---

## 3. Key Data Structures

### 3.1 Global State — `CanIf_GlobalType` (CanIf.c line 93)

```c
typedef struct {
  boolean initRun;                                   // Has CanIf_Init() been called?
  CanIf_ChannelPrivateType channelData[CANIF_CHANNEL_CNT]; // Per-channel state
} CanIf_GlobalType;
```

This is the **runtime memory** of CanIf. One global instance: `CanIf_Global`.

### 3.2 Per-Channel Runtime Data — `CanIf_ChannelPrivateType` (CanIf.c line 86)

```c
typedef struct {
  CanIf_ControllerModeType  ControllerMode;  // UNINIT / STOPPED / STARTED / SLEEP
  CanIf_ChannelGetModeType  PduMode;         // OFFLINE / ONLINE / TX_ONLINE / RX_ONLINE / etc.
} CanIf_ChannelPrivateType;
```

### 3.3 Top-Level Configuration — `CanIf_ConfigType` (CanIf_ConfigTypes.h line 381)

```
CanIf_ConfigType
├── ControllerConfig[]      → maps CanIf channels to CAN controllers
├── DispatchConfig          → callback pointers (BusOff, Wakeup, Error)
├── InitConfig
│   ├── CanIfHohConfigPtr[] → list of HOH (HTH + HRH) entries
│   ├── CanIfTxPduConfigPtr[] → Tx PDU table
│   └── CanIfRxPduConfigPtr[] → Rx PDU table
├── Arc_ChannelToControllerMap  → CanIf channel number → CAN driver controller number
└── Arc_ChannelDefaultConfIndex → default config index per channel
```

### 3.4 Tx PDU Entry — `CanIf_TxPduConfigType`

| Field | Type | Meaning |
|-------|------|---------|
| `CanIfTxPduId` | PduIdType | Unique ID for this Tx PDU |
| `CanIfCanTxPduIdCanId` | uint32 | The CAN ID to put in the frame header |
| `CanIfCanTxPduIdDlc` | uint8 | Expected data length (0–8 bytes) |
| `CanIfCanTxPduType` | enum | STATIC (fixed ID) or DYNAMIC (runtime ID) |
| `CanIfTxPduIdCanIdType` | enum | 11-bit standard or 29-bit extended |
| `CanIfUserTxConfirmation` | function ptr | Callback to call after successful Tx |
| `CanIfCanTxPduHthRef` | ptr to HTH | Which hardware transmit object to use |

### 3.5 Rx PDU Entry — `CanIf_RxPduConfigType`

| Field | Type | Meaning |
|-------|------|---------|
| `CanIfCanRxPduId` | PduIdType | Unique ID for this Rx PDU |
| `CanIfCanRxPduCanId` | uint32 | Expected CAN ID to match against |
| `CanIfCanRxPduDlc` | uint8 | Minimum expected data length |
| `CanIfRxUserType` | enum | Which upper layer to route to (PduR/CanTp/CanNm/CAN_SPECIAL) |
| `CanIfUserRxIndication` | void* | Callback function pointer |
| `CanIfCanRxPduHrhRef` | ptr to HRH | Which receive hardware object this belongs to |
| `CanIfSoftwareFilterType` | enum | Filter algorithm (only MASK supported) |
| `CanIfCanRxPduCanIdMask` | uint32 | Bit mask for software filtering |

---

## 4. All Functions — Quick Reference Table

| # | Function Name | Lines | Type | Purpose | Status |
|---|--------------|-------|------|---------|--------|
| 1 | `CanIf_Arc_FindHrhChannel` | 100–126 | Internal static | Finds which channel owns a given HRH number | ✅ Implemented |
| 2 | `CanIf_Init` | 131–146 | Public API | Initializes entire CanIf module | ✅ Implemented |
| 3 | `CanIf_InitController` | 156–204 | Public API | Initializes one specific CAN controller | ✅ Implemented |
| 4 | `CanIf_PreInit_InitController` | 206–222 | Internal helper | Initializes controller without mode checks (called from CanIf_Init) | ✅ Implemented |
| 5 | `CanIf_SetControllerMode` | 226–318 | Public API | Transitions controller between STOPPED/STARTED/SLEEP | ✅ Implemented |
| 6 | `CanIf_GetControllerMode` | 322–335 | Public API | Returns current controller mode | ✅ Implemented |
| 7 | `CanIf_FindTxPduEntry` | 344–354 | Internal helper | Looks up Tx PDU config by ID | ✅ Implemented |
| 8 | `CanIf_FindRxPduEntry` | 358–364 | Internal helper (runtime only) | Looks up Rx PDU config by ID | ✅ (runtime cfg) |
| 9 | `CanIf_Arc_GetReceiveHandler` | 366–391 | Internal (runtime only) | Finds HRH config for a channel | ✅ (runtime cfg) |
| 10 | `CanIf_Arc_GetTransmitHandler` | 393–418 | Internal (runtime only) | Finds HTH config for a channel | ✅ (runtime cfg) |
| 11 | `CanIf_Transmit` | 423–482 | Public API | Sends a CAN frame via the CAN driver | ✅ Implemented |
| 12 | `CanIf_ReadRxPduData` | 487–497 | Public API (optional) | Read buffered Rx data — **NOT SUPPORTED** | ❌ Stub |
| 13 | `CanIf_ReadTxNotifStatus` | 503–527 | Public API (optional) | Read Tx notification flag — **NOT SUPPORTED** | ❌ Stub |
| 14 | `CanIf_ReadRxNotifStatus` | 533–539 | Public API (optional) | Read Rx notification flag — **NOT SUPPORTED** | ❌ Stub |
| 15 | `CanIf_SetPduMode` | 544–628 | Public API | Sets PDU channel mode (Tx/Rx on or off) | ✅ Implemented |
| 16 | `CanIf_GetPduMode` | 632–644 | Public API | Returns current PDU channel mode | ✅ Implemented |
| 17 | `CanIf_SetDynamicTxId` | 647–680 | Public API (runtime only) | Changes CAN ID of a dynamic Tx PDU at runtime | ✅ (runtime cfg) |
| 18 | `CanIf_SetTransceiverMode` | 684–691 | Public API | Set transceiver mode — **NOT SUPPORTED** | ❌ Stub |
| 19 | `CanIf_GetTransceiverMode` | 693–700 | Public API | Get transceiver mode — **NOT SUPPORTED** | ❌ Stub |
| 20 | `CanIf_GetTrcvWakeupReason` | 702–709 | Public API | Get wakeup reason — **NOT SUPPORTED** | ❌ Stub |
| 21 | `CanIf_SetTransceiverWakeupMode` | 711–718 | Public API | Set transceiver wakeup mode — **NOT SUPPORTED** | ❌ Stub |
| 22 | `CanIf_CheckWakeup` | 722–728 | Public API | Check wakeup event — **NOT SUPPORTED** | ❌ Stub |
| 23 | `CanIf_CheckValidation` | 730–736 | Public API | Validate wakeup — **NOT SUPPORTED** | ❌ Stub |
| 24 | `CanIf_TxConfirmation` | 742–761 | Callback (from CAN driver) | CAN driver calls this to confirm successful Tx | ✅ Implemented |
| 25 | `CanIf_RxIndication` | 763–898 | Callback (from CAN driver) | CAN driver calls this when a frame is received | ✅ Implemented |
| 26 | `CanIf_CancelTxConfirmation` | 901–914 | Callback (optional) | Cancel pending Tx — **NOT SUPPORTED** | ❌ Stub |
| 27 | `CanIf_ControllerBusOff` | 917–941 | Callback (from CAN driver) | CAN driver calls this on BusOff event | ✅ Implemented |
| 28 | `CanIf_SetWakeupEvent` | 943–961 | Callback (from CAN driver) | CAN driver calls this on wakeup — **NOT SUPPORTED** | ❌ Stub |
| 29 | `CanIf_Arc_Error` | 963–989 | Callback (ArcCore extension) | CAN driver calls this on any CAN error | ✅ Implemented |
| 30 | `CanIf_Arc_GetChannelDefaultConfIndex` | 991–994 | ArcCore extension | Returns default config index for a channel | ✅ Implemented |

---

## 5. Detailed Function Explanations

### 5.1 `CanIf_Arc_FindHrhChannel` — Line 100

**What it does:** Given a raw HRH number (a hardware receive object number from the CAN driver), it searches all configured HOH entries to find which CanIf **channel** (logical controller) that HRH belongs to.

**Why it exists:** The CAN driver callback `CanIf_RxIndication()` only gives you an HRH number. CanIf needs to know the channel to check the PDU mode (is RX enabled on this channel?).

**Algorithm:**
```
For each HOH (Hardware Object Handle) group:
  For each HRH in that group:
    If HRH matches the one we're looking for → return its channel ID
Report error and return -1 if not found
```

**Returns:** `CanIf_Arc_ChannelIdType` — the channel index, or -1 if not found.

---

### 5.2 `CanIf_Init` — Line 131

**What it does:** The very first function that must be called. It:
1. Saves the config pointer globally (`CanIf_ConfigPtr`)
2. For every configured channel:
   - Sets `ControllerMode = CANIF_CS_STOPPED`
   - Sets `PduMode = CANIF_GET_OFFLINE`
   - Calls `CanIf_PreInit_InitController()` to initialize the CAN hardware controller
3. Sets `initRun = TRUE` to allow other functions to run

**Requirement reference in code:** `VALIDATE_NO_RV(ConfigPtr != 0, ...)` — rejects NULL config.

**Think of it as:** "Plug in all the hardware, put everything in safe/stopped state."

---

### 5.3 `CanIf_InitController` — Line 156

**What it does:** Re-initializes a single CAN controller during runtime. Steps:
1. Validates: module initialized, channel valid, config index valid
2. Checks current mode — if STARTED, stops it first
3. Looks up the CAN driver config for this controller
4. Calls `Can_InitController()` (the actual hardware driver)
5. Sets mode back to STOPPED

**Difference from `CanIf_PreInit_InitController`:** This function checks the current mode first (safe for runtime use). `PreInit` skips that check and is only used during cold startup from `CanIf_Init`.

---

### 5.4 `CanIf_SetControllerMode` — Line 226

**What it does:** Transitions a CAN controller between its three operational modes.

**Mode transitions allowed:**

```
STOPPED  ──────→  STARTED   (enables Tx, sets PDU mode ONLINE)
SLEEP    ──→ STOPPED ──→ STARTED

STARTED  ──────→  SLEEP     (stops first, then sleeps)
STOPPED  ──────→  SLEEP

STARTED  ──────→  STOPPED   (PDU mode → OFFLINE)
SLEEP    ──→ wakeup ──→ STOPPED
```

**For each target mode:**
- **STARTED**: wakes from SLEEP if needed → sets PDU mode ONLINE → calls `Can_SetControllerMode(CAN_T_START)`
- **SLEEP**: stops if STARTED → calls `Can_SetControllerMode(CAN_T_SLEEP)`
- **STOPPED**: wakes from SLEEP if needed → sets PDU mode OFFLINE → calls `Can_SetControllerMode(CAN_T_STOP)`

**Important:** When transitioning to STARTED, the PDU mode is automatically set to ONLINE (both Tx and Rx enabled). When transitioning to STOPPED, PDU mode is set to OFFLINE.

---

### 5.5 `CanIf_GetControllerMode` — Line 322

**What it does:** Simply reads back the current controller mode from `CanIf_Global.channelData[channel].ControllerMode`.

**No hardware call** — just reads the software state variable.

---

### 5.6 `CanIf_FindTxPduEntry` — Line 344

**What it does:** Given a `PduIdType` (a simple index number), returns a pointer to that PDU's configuration row in the `CanIfTxPduConfigPtr[]` table.

**Boundary check:** If `id >= CanIfNumberOfCanTXPduIds`, returns NULL (invalid PDU).

**Think of it as:** "Look up row number X in the Tx PDU table."

---

### 5.7 `CanIf_Transmit` — Line 423

**What it does:** The main Tx path. Called by upper layers (PduR, CanNm, CanTp) to send a CAN frame.

**Step-by-step flow:**
```
1. Validate module initialized, PduInfoPtr not NULL
2. Find Tx PDU config entry via CanIf_FindTxPduEntry()
3. Get the channel from the PDU's HTH reference
4. Check controller mode == STARTED (reject otherwise)
5. Check PDU mode == TX_ONLINE or ONLINE (reject otherwise)
6. Fill Can_PduType structure:
   - id     = configured CAN ID
   - length = PduInfoPtr->SduLength
   - sdu    = PduInfoPtr->SduDataPtr
   - swPduHandle = CanTxPduId
7. Call Can_Write() → sends to CAN hardware
8. If CAN_BUSY → return E_NOT_OK (no Tx buffering in this implementation)
9. If CAN_NOT_OK → return E_NOT_OK
10. Return E_OK
```

**Note on buffering:** The spec defines Tx buffering (`SWS_CANIF_00063`), but this implementation does NOT buffer — if the hardware is busy, the frame is simply dropped.

---

### 5.8 `CanIf_SetPduMode` — Line 544

**What it does:** Controls whether Tx and/or Rx paths are enabled on a given channel. This is independent of the hardware controller mode — it's a software gate.

**Available modes to SET:**

| Request | Result |
|---------|--------|
| `CANIF_SET_OFFLINE` | Both Tx and Rx disabled |
| `CANIF_SET_ONLINE` | Both Tx and Rx enabled |
| `CANIF_SET_TX_ONLINE` | Enable Tx (keeps current Rx state) |
| `CANIF_SET_TX_OFFLINE` | Disable Tx (keeps current Rx state) |
| `CANIF_SET_RX_ONLINE` | Enable Rx (keeps current Tx state) |
| `CANIF_SET_RX_OFFLINE` | Disable Rx (keeps current Tx state) |
| `CANIF_SET_TX_OFFLINE_ACTIVE` | Special: Tx calls still get confirmation callbacks immediately (simulated Tx) without actually sending to bus |

**The state transitions are complex** — the code has many `if (oldMode == X) newMode = Y` chains that implement the mode transition matrix from the AUTOSAR spec.

---

### 5.9 `CanIf_GetPduMode` — Line 632

**What it does:** Reads back the current PDU channel mode from the runtime data structure.

---

### 5.10 `CanIf_SetDynamicTxId` — Line 647

**What it does:** Allows changing the CAN ID of a **DYNAMIC** Tx PDU at runtime (only active when `CANIF_ARC_RUNTIME_PDU_CONFIGURATION == STD_ON`).

**Validation:**
- PDU must exist
- PDU must have type `CANIF_PDU_TYPE_DYNAMIC`
- New CanId must match the configured ID type (11-bit or 29-bit) using the MSB flag

---

### 5.11 `CanIf_TxConfirmation` — Line 742

**What it does:** Called by the CAN driver (bottom-up callback) after a frame has been **successfully placed on the bus**.

**Flow:**
```
1. Validate initialized, PDU ID valid
2. Look up the Tx PDU config entry
3. Check if a confirmation callback is configured
4. Check current PDU mode — only call callback if Tx path is active:
   (CANIF_GET_TX_ONLINE, CANIF_GET_ONLINE, CANIF_GET_OFFLINE_ACTIVE, CANIF_GET_OFFLINE_ACTIVE_RX_ONLINE)
5. Call entry->CanIfUserTxConfirmation(entry->CanIfTxPduId)
   → This calls into PduR_CanIfTxConfirmation() or CanTp_TxConfirmation() etc.
```

**Why check PDU mode here?** If the PDU mode changed between when the frame was submitted and when it was actually sent, the upper layer should not be told about it if Tx notifications are disabled.

---

### 5.12 `CanIf_RxIndication` — Line 763

**What it does:** The most complex function. Called by the CAN driver when a frame **arrives** on the bus.

**Detailed step-by-step:**

```
1. Validate: initialized, SduPtr not NULL
2. Find which channel owns the HRH (via CanIf_Arc_FindHrhChannel)
3. Check PDU mode — if Rx is disabled, DROP the frame:
   (OFFLINE, TX_ONLINE, OFFLINE_ACTIVE → all mean Rx is not running)
4. Loop through ALL configured Rx PDUs:
   a. Match: Does this PDU's HRH match the received HRH?
   b. Software filtering (if BasicCAN and filter enabled):
      - Only MASK filter supported: (received_CanId & mask) == (config_CanId & mask)
      - If filter fails → skip to next entry
   c. DLC check (if CANIF_DLC_CHECK == STD_ON):
      - Received DLC must be >= configured DLC
      - If too short → VALIDATE error + return
   d. Route to upper layer based on CanIfRxUserType:
      - CANIF_USER_TYPE_CAN_NM  → CanNm_RxIndication()
      - CANIF_USER_TYPE_CAN_PDUR → PduR_CanIfRxIndication()
      - CANIF_USER_TYPE_CAN_TP   → CanTp_RxIndication()
      - CANIF_USER_TYPE_J1939TP  → J1939Tp_RxIndication()
      - CANIF_USER_TYPE_CAN_SPECIAL → custom function pointer with extra parameters
5. If no PDU matched → report CANIF_E_PARAM_LPDU error
```

**This is the heart of CanIf** — it's the routing table for all incoming CAN messages.

---

### 5.13 `CanIf_ControllerBusOff` — Line 917

**What it does:** Called by the CAN driver when a **BusOff condition** is detected (too many errors on the bus causes the controller to go bus-off as per CAN standard).

**Flow:**
```
1. Find the channel associated with the controller number
2. Call CanIf_SetControllerMode(channel, CANIF_CS_STOPPED)
   → This stops the controller and sets PDU mode to OFFLINE
3. If a BusOff notification callback is configured:
   → Call CanIf_ConfigPtr->DispatchConfig->CanIfBusOffNotification(channel)
   → Typically calls CanSM_ControllerBusOff() (CAN State Manager)
```

**In this project's config:** `CanIfBusOffNotification = NULL` → no upper layer is notified.

---

### 5.14 `CanIf_Arc_Error` — Line 963

**What it does:** ArcCore-specific extension. Called by the CAN driver when a generic CAN error occurs (not just BusOff).

**Flow:**
```
1. Find channel from controller number
2. If CanIfErrorNotificaton callback configured → call it
3. Also call CanIfBusOffNotification (treat general errors similarly to BusOff)
```

**Note:** The dual call to both error and BusOff notification is an intentional ArcCore design choice for triggering bus recovery via CanSM.

---

### 5.15 `CanIf_Arc_GetChannelDefaultConfIndex` — Line 991

**What it does:** Returns the default configuration index for a channel. Used by external code (e.g., CanSM) that needs to re-initialize a channel after BusOff recovery.

---

## 6. Function Call Relationships

```
CanIf_Init()
  └──→ CanIf_PreInit_InitController()
         └──→ Can_InitController()  [CAN driver]

CanIf_InitController()
  ├──→ CanIf_GetControllerMode()
  ├──→ CanIf_SetControllerMode()
  └──→ Can_InitController()  [CAN driver]

CanIf_SetControllerMode()
  ├──→ CanIf_SetPduMode()
  └──→ Can_SetControllerMode()  [CAN driver]

CanIf_Transmit()                    ← called by PduR / CanNm / CanTp / Application
  ├──→ CanIf_FindTxPduEntry()
  ├──→ CanIf_GetControllerMode()
  ├──→ CanIf_GetPduMode()
  └──→ Can_Write()  [CAN driver]

CanIf_TxConfirmation()              ← called by CAN driver (hardware callback)
  ├──→ CanIf_GetPduMode()
  └──→ entry->CanIfUserTxConfirmation()
         ├── PduR_CanIfTxConfirmation()
         ├── CanTp_TxConfirmation()
         └── CanNm_TxConfirmation()

CanIf_RxIndication()                ← called by CAN driver (hardware callback)
  ├──→ CanIf_Arc_FindHrhChannel()
  ├──→ CanIf_GetPduMode()
  └──→ [routing based on user type]
         ├── PduR_CanIfRxIndication()
         ├── CanTp_RxIndication()
         ├── CanNm_RxIndication()
         ├── J1939Tp_RxIndication()
         └── (custom function ptr)

CanIf_ControllerBusOff()            ← called by CAN driver (hardware callback)
  ├──→ CanIf_SetControllerMode()
  └──→ DispatchConfig->CanIfBusOffNotification()

CanIf_Arc_Error()                   ← called by CAN driver (hardware callback)
  ├──→ DispatchConfig->CanIfErrorNotificaton()
  └──→ DispatchConfig->CanIfBusOffNotification()
```

---

## 7. Controller State Machine

Each CAN controller channel has one of these 4 states:

```
                  CanIf_Init()
                      │
                      ▼
              ┌──────────────┐
              │   UNINIT     │  (before CanIf_Init — no operations allowed)
              └──────────────┘
                      │ CanIf_Init() / CanIf_InitController()
                      ▼
              ┌──────────────┐◄─── CanIf_SetControllerMode(STOPPED)
              │   STOPPED    │     CanIf_ControllerBusOff()
              └──────────────┘
                 ↑        │
   Set(STOPPED)  │        │ SetControllerMode(STARTED)
                 │        ▼
              ┌──────────────┐
              │   STARTED    │  ← Normal operation: Tx and Rx active
              └──────────────┘
                 ↑        │
   Set(STARTED)  │        │ SetControllerMode(SLEEP)
   (via STOPPED) │        ▼
              ┌──────────────┐
              │    SLEEP     │  ← Low power: no Tx/Rx, waiting for wakeup
              └──────────────┘
```

**When controller is STOPPED:** PDU mode is forced to OFFLINE.
**When controller is STARTED:** PDU mode is set to ONLINE.
**When controller goes to SLEEP:** PDU mode is set to OFFLINE.

---

## 8. PDU Channel Mode State Machine

The PDU mode is a **software gate** on top of the hardware state. It has 6 possible values:

| Mode (GET) | Tx Enabled? | Rx Enabled? | Tx Confirmation? |
|-----------|------------|------------|-----------------|
| `CANIF_GET_OFFLINE` | No | No | No |
| `CANIF_GET_ONLINE` | Yes | Yes | Yes |
| `CANIF_GET_TX_ONLINE` | Yes | No | Yes |
| `CANIF_GET_RX_ONLINE` | No | Yes | No |
| `CANIF_GET_OFFLINE_ACTIVE` | No (but simulated) | No | Yes (immediately) |
| `CANIF_GET_OFFLINE_ACTIVE_RX_ONLINE` | No (but simulated) | Yes | Yes (immediately) |

**OFFLINE_ACTIVE** is a special diagnostic mode: CanIf calls the TxConfirmation callback immediately without actually sending to the bus. Useful for testing/simulation.

---

## 9. Configuration Overview

### 9.1 Compile-time flags (CanIf_Cfg.h)

| Flag | Value | Meaning |
|------|-------|---------|
| `CANIF_DEV_ERROR_DETECT` | STD_OFF | Development error checking disabled |
| `CANIF_DLC_CHECK` | STD_ON | Data Length Check is ACTIVE |
| `CANIF_READRXPDU_DATA_API` | STD_OFF | CanIf_ReadRxPduData() not compiled |
| `CANIF_READRXPDU_NOTIFY_STATUS_API` | STD_OFF | Rx notification status API not compiled |
| `CANIF_READTXPDU_NOTIFY_STATUS_API` | STD_OFF | Tx notification status API not compiled |
| `CANIF_TRANSCEIVER_API` | STD_OFF | Transceiver functions not compiled |
| `CANIF_WAKEUP_EVENT_API` | STD_OFF | Wakeup API not compiled |
| `CANIF_TRANSMIT_CANCELLATION` | STD_OFF | Tx cancel API not compiled |
| `CANIF_ARC_RUNTIME_PDU_CONFIGURATION` | STD_OFF | Dynamic PDU config not compiled |

### 9.2 Channels (CanIf_Cfg.h)

```
CANIF_CHL_LS  (index 0) → maps to CAN_CTRL_0  (Low-Speed CAN)
CANIF_CHL_HS  (index 1) → maps to CAN_CTRL_2  (High-Speed CAN)
```

### 9.3 Configured Tx PDUs (CanIf_Cfg.c)

| ID | Symbol | CAN ID | DLC | Channel | Confirmation Target |
|----|--------|--------|-----|---------|-------------------|
| 0 | TxDiagP2P | 0x732 | 8 | LS | CanTp_TxConfirmation |
| 1 | TxDiagP2A | 0x742 | 8 | LS | CanTp_TxConfirmation |
| 2 | LS_NM_TX | 0x401 | 8 | LS | CanNm_TxConfirmation |
| 3 | TxMsgTime | 0x101 | 8 | HS | PduR_CanIfTxConfirmation |
| 4 | HS_NM_TX | 0x402 | 8 | HS | CanNm_TxConfirmation |

### 9.4 Configured Rx PDUs (CanIf_Cfg.c)

| ID | Symbol | CAN ID | Mask | DLC | Channel | Route To |
|----|--------|--------|------|-----|---------|----------|
| 0 | RxDiagP2P | 0x731 | 0xFFF | 8 | LS | CanTp_RxIndication |
| 1 | RxDiagP2A | 0x741 | 0xFFF | 8 | LS | CanTp_RxIndication |
| 2 | RxMsgAbsInfo | 0x102 | 0xFFFF | 8 | HS | PduR_CanIfRxIndication |

---

## 10. What Is Implemented vs. Stubbed Out

### Fully Implemented ✅

- Module initialization (`CanIf_Init`, `CanIf_InitController`)
- Controller mode management (STARTED/STOPPED/SLEEP state machine)
- PDU channel mode management (all 6 modes + transitions)
- Tx path: `CanIf_Transmit` → `Can_Write`
- Rx path: `CanIf_RxIndication` with software filtering + DLC check + routing to upper layers
- BusOff handling: `CanIf_ControllerBusOff`
- Tx confirmation forwarding: `CanIf_TxConfirmation`
- Error handling: `CanIf_Arc_Error` (ArcCore extension)

### Compiled But Not Functional ❌ (Stubs — return `E_NOT_OK` / `CANIF_NO_NOTIFICATION`)

| Function | Why Not Supported |
|----------|------------------|
| `CanIf_ReadRxPduData` | Requires Rx buffering (not implemented) |
| `CanIf_ReadTxNotifStatus` | Requires notification status storage (not implemented) |
| `CanIf_ReadRxNotifStatus` | Requires notification status storage (not implemented) |
| `CanIf_SetTransceiverMode` | No transceiver driver configured |
| `CanIf_GetTransceiverMode` | No transceiver driver configured |
| `CanIf_GetTrcvWakeupReason` | No transceiver driver configured |
| `CanIf_SetTransceiverWakeupMode` | No transceiver driver configured |
| `CanIf_CheckWakeup` | Wakeup not supported in this hardware config |
| `CanIf_CheckValidation` | Wakeup not supported in this hardware config |
| `CanIf_CancelTxConfirmation` | Tx cancellation not supported |
| `CanIf_SetWakeupEvent` | Wakeup events not supported |

### Available Only When `CANIF_ARC_RUNTIME_PDU_CONFIGURATION == STD_ON` (Currently OFF)

- `CanIf_FindRxPduEntry`
- `CanIf_Arc_GetReceiveHandler`
- `CanIf_Arc_GetTransmitHandler`
- `CanIf_SetDynamicTxId`

---

## 11. Files & Their Roles

| File | Location | Role |
|------|----------|------|
| `CanIf.c` | `OpenSAR/communication/CanIf/` | Main implementation — ALL the functions |
| `CanIf.h` | `OpenSAR/include/` | Public API declarations + service IDs |
| `CanIf_ConfigTypes.h` | `OpenSAR/include/` | All struct/enum type definitions |
| `CanIf_Types.h` | `OpenSAR/include/` | Mode enum types (ControllerMode, PduMode) |
| `CanIf_Cbk.h` | `OpenSAR/include/` | Callback declarations (TxConfirmation, RxIndication, etc.) |
| `CanIf_Cfg.h` | `OpenSAR/app/config/GEN/` | Compile-time flags + channel/PDU ID enums |
| `CanIf_Cfg.c` | `OpenSAR/app/config/GEN/` | Static configuration tables (PDU tables, HOH tables, channel maps) |
| `CanIf_SpecialPdus.h` | `OpenSAR/app/config/` | Project-specific PDU ID definitions |

---

## Summary

CanIf.c implements **~50% of the full AUTOSAR CanIf specification**. The core functionality is complete:
- Full initialization and controller lifecycle management
- Full Tx path (Transmit → CAN driver → TxConfirmation → upper layer)
- Full Rx path (RxIndication → software filter → DLC check → upper layer routing)
- BusOff and error event handling

What is **not implemented** are optional/advanced features: Tx buffering, dynamic PDU IDs (in default config), transceiver management, wakeup handling, and notification status read-back APIs.
