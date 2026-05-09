##  Test Cases

---

### TC-CANIF-F-01 — Functional: SetControllerMode Uses Wrong CAN Transition Constant

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-01 |
| **Title** | Functional change — `CanIf_SetControllerMode()` passes `CAN_T_STOP` instead of `CAN_T_START` when transitioning to `CANIF_CS_STARTED` |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308 |
| **Requirement — Original** | *"The service CanIf_SetControllerMode() shall call Can_SetControllerMode(Controller, Transition) for the requested CAN controller."* For the `CANIF_CS_STARTED` transition the correct Transition argument is `CAN_T_START` per the AUTOSAR state machine (Figure 32 of the CanIf SWS). |
| **Requirement — Modified** | *"When transitioning the controller to `CANIF_CS_STARTED`, CanIf_SetControllerMode() shall call Can_SetControllerMode(Controller, CAN_T_STOP) before activating the channel."* |
| **Affected Function(s)** | `CanIf_SetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 264 — transition argument inside the `case CANIF_CS_STARTED:` block.<br><br>`OLD:` `if (Can_SetControllerMode(canControllerId, CAN_T_START) == CAN_NOT_OK)`<br>`NEW:` `if (Can_SetControllerMode(canControllerId, CAN_T_STOP) == CAN_NOT_OK)`<br><br>One constant changed on one line. The function name `Can_SetControllerMode()`, the ControllerId argument, and the return-value check are all preserved. |
| **Expected Behavior** | When `CanIf_SetControllerMode(x, CANIF_CS_STARTED)` is called: (1) `Can_SetControllerMode(canControllerId, CAN_T_STOP)` is sent to the CAN Driver — a STOP command instead of a START command. (2) If the driver returns `CAN_NOT_OK` the function returns `E_NOT_OK`. (3) If the driver returns `CAN_OK`, the CanIf internal state is updated to `CANIF_CS_STARTED` (line 267) — so CanIf believes the controller is running while the hardware remains in STOPPED state. (4) `CanIf_Transmit()` reads the CanIf state as `CANIF_CS_STARTED` and forwards frames to `Can_Write()`, but the CAN hardware transmit mailboxes are not active — frames are lost silently at the driver level without any error code. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` returns `E_OK`. 2. `CanIf_GetControllerMode(0, &m)` returns `m == CANIF_CS_STARTED` (CanIf internal state updated). 3. A CAN bus monitor shows **no frame transmitted** after `CanIf_Transmit()` — the hardware was never started. 4. The CAN Driver's internal channel state remains STOPPED, not STARTED. 5. Restoring `CAN_T_START` realigns both CanIf state and hardware state, and frames appear on the bus. |
| **AUTOSAR Rationale** | The AUTOSAR CanIf SWS state machine (Figure 32) defines the exact mapping from each requested CanIf mode to its CAN Driver transition constant: `CANIF_CS_STARTED` requires `CAN_T_START`. Using `CAN_T_STOP` is a realistic copy-paste defect — both the `CANIF_CS_STOPPED` case (line 306) and the inner SLEEP→STOPPED sub-case (line 253) use `CAN_T_STOP`, making it easy to accidentally carry the wrong constant when copying code. The defect creates a silent hardware/software state split: CanIf reports the controller as STARTED while the CAN hardware stays stopped, so all subsequent `CanIf_Transmit()` calls silently discard frames without returning an error. |

---

### TC-CANIF-F-02 — Functional: Wrong DET Error Code for Invalid ControllerId

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-02 |
| **Title** | Functional change — Incorrect DET development error code reported for invalid ControllerId |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00311 |
| **Requirement — Original** | *"If parameter ControllerId of CanIf_SetControllerMode() has an invalid value, the CanIf shall report development error code CANIF_E_PARAM_CONTROLLERID to the Det_ReportError service of the DET module."* |
| **Requirement — Modified** | *"If parameter ControllerId of CanIf_SetControllerMode() has an invalid value, the CanIf shall report development error code CANIF_E_PARAM_POINTER to the Det_ReportError service of the DET module."* |
| **Affected Function(s)** | `CanIf_SetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 236 — ControllerId validation macro.<br><br>`OLD:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`NEW:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );` |
| **Expected Behavior** | When `CanIf_SetControllerMode()` is called with a `ControllerId` value that exceeds `CANIF_CHANNEL_CNT - 1`, the function must invoke `Det_ReportError()` with the error code `CANIF_E_PARAM_POINTER` (per the modified requirement) and return `E_NOT_OK`. The function must not execute any further logic after reporting the error. |
| **Verification Criteria** | 1. Calling `CanIf_SetControllerMode(255, CANIF_CS_STARTED)` (out-of-range ControllerId) triggers a DET call with `CANIF_E_PARAM_POINTER`. 2. No DET call is made for a valid ControllerId. 3. Return value is `E_NOT_OK` for the invalid case. 4. No other change exists in the function — only the error code constant is updated. |
| **AUTOSAR Rationale** | AUTOSAR CanIf SWS Table 8-2 defines a strict mapping between parameter types and their corresponding error codes. `CANIF_E_PARAM_POINTER` is reserved for null-pointer parameters. Using it for a ControllerId range violation makes diagnostic classification impossible in DET-based development tools and violates the AUTOSAR BSW error classification scheme. |

---

### TC-CANIF-F-03 — Functional: Wrong Initial PDU Channel Mode at Startup

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-03 |
| **Title** | Functional change — Channels initialized to wrong PDU mode in `CanIf_Init()` |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00864 |
| **Requirement — Original** | *"During initialization CanIf shall switch every channel to CANIF_OFFLINE."* |
| **Requirement — Modified** | *"During initialization CanIf shall switch every channel to CANIF_ONLINE to eliminate startup latency for time-critical networks."* |
| **Affected Function(s)** | `CanIf_Init` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 140 — PDU mode initialization inside the channel-init loop.<br><br>`OLD:` `CanIf_Global.channelData[i].PduMode = CANIF_GET_OFFLINE;`<br>`NEW:` `CanIf_Global.channelData[i].PduMode = CANIF_GET_ONLINE;` |
| **Expected Behavior** | After `CanIf_Init()` returns, every channel's `PduMode` field must be `CANIF_GET_ONLINE`. Any subsequent call to `CanIf_GetPduMode()` on any channel must return `CANIF_GET_ONLINE` before any explicit `CanIf_SetPduMode()` has been called. |
| **Verification Criteria** | 1. After `CanIf_Init()`, `CanIf_GetPduMode(channelId, &mode)` returns `E_OK` and `mode == CANIF_GET_ONLINE` for every valid channel. 2. `CanIf_Transmit()` succeeds immediately after `CanIf_Init()` without requiring an explicit mode set. 3. No other initialization path sets the PduMode — the change is localized to the loop in `CanIf_Init()`. |
| **AUTOSAR Rationale** | SWS_CANIF_00864 is a hard startup-safety requirement. Starting in `CANIF_OFFLINE` guarantees that no frames are transmitted or received until CanSM has completed the full network startup sequence. Starting in `CANIF_ONLINE` immediately enables CAN frame traffic before the communication stack is ready, which can cause uncontrolled bus flooding, missed startup diagnostics, and violation of the AUTOSAR communication startup procedure defined in the CanSM SWS. |

---

### TC-CANIF-F-04 — Functional: CanIf_Transmit() Returns Wrong Value on Success

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-04 |
| **Title** | Functional change — `CanIf_Transmit()` returns incorrect value when `Can_Write()` succeeds |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00162 |
| **Requirement — Original** | *"If the call of Can_Write() returns E_OK the transmit request service CanIf_Transmit() shall return E_OK."* |
| **Requirement — Modified** | *"CanIf_Transmit() shall always return E_NOT_OK and rely on CanIf_TxConfirmation() as the sole success acknowledgment to the upper layer."* |
| **Affected Function(s)** | `CanIf_Transmit` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 481 — the success return path at the end of `CanIf_Transmit()`.<br><br>`OLD:` `return E_OK;`<br>`NEW:` `return E_NOT_OK;` |
| **Expected Behavior** | `CanIf_Transmit()` must return `E_NOT_OK` in all cases, even when `Can_Write()` returns `CAN_OK`. The function must still call `Can_Write()` and pass the frame to the CAN Driver. The return value change affects only the feedback contract to the calling upper layer module. |
| **Verification Criteria** | 1. `CanIf_Transmit()` returns `E_NOT_OK` even when `Can_Write()` returns `CAN_OK`. 2. `Can_Write()` is still called with the correct parameters — the frame is not silently dropped. 3. `CanIf_TxConfirmation()` is still triggered by the CAN Driver after physical transmission. 4. No other return site in `CanIf_Transmit()` is affected — only the final success-path return is changed. |
| **AUTOSAR Rationale** | AUTOSAR COM and PduR use the `E_OK` return from `CanIf_Transmit()` to confirm frame hand-off to the CAN layer before the `TxConfirmation` callback arrives. Returning `E_NOT_OK` unconditionally causes COM/PduR to trigger immediate retransmission logic, producing duplicate frames on the bus and corrupting the PDU transmission state machine. |

---

### TC-CANIF-F-05 — Functional: Invalid Identifier Replaces CANIF_GET_OFFLINE Enum Constant

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-05 |
| **Title** | Functional change — Valid AUTOSAR enum constant `CANIF_GET_OFFLINE` replaced with undefined identifier `CANIF_OFFLINE` (missing `GET_` prefix) |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00864 |
| **Requirement — Original** | *"During initialization CanIf shall switch every channel to CANIF_OFFLINE."* |
| **Requirement — Modified** | *(Erroneous change)* The correct enum constant `CANIF_GET_OFFLINE` is replaced by `CANIF_OFFLINE` — the developer omitted the mandatory `GET_` prefix used in all CanIf PDU mode read-side enum values. `CANIF_OFFLINE` is not declared anywhere in the AUTOSAR CanIf headers or the OpenSAR codebase. |
| **Affected Function(s)** | `CanIf_Init` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 140 — PDU mode initialization inside the channel-init loop.<br><br>`OLD:` `CanIf_Global.channelData[i].PduMode = CANIF_GET_OFFLINE;`<br>`NEW:` `CanIf_Global.channelData[i].PduMode = CANIF_OFFLINE;` |
| **Expected Behavior** | **The translation unit must not compile.** The C compiler treats `CANIF_OFFLINE` as an undeclared identifier and halts with a hard error at line 140. No object file is produced. No runtime behavior exists to evaluate — the defect is caught entirely at build time, before any linking or execution stage. |
| **Expected Compiler Output** | `CanIf.c:140:55: error: 'CANIF_OFFLINE' undeclared (first use in this function)`<br>`CanIf.c:140:55: note: each undeclared identifier is reported only once`<br>`make: *** [CanIf.o] Error 1` |
| **Verification Criteria** | 1. The build system reports a compilation error at `CanIf.c` line 140. 2. The error message names `CANIF_OFFLINE` as the undeclared identifier. 3. No `CanIf.o` object file is generated. 4. No other source file is affected — the error is isolated to `CanIf.c`. 5. Reverting the change to `CANIF_GET_OFFLINE` restores a clean build with zero errors. |
| **AUTOSAR Rationale** | AUTOSAR CanIf defines two parallel enum sets for PDU channel mode: `CanIf_PduSetModeType` (write-side: `CANIF_SET_OFFLINE`, `CANIF_SET_ONLINE`, …) and `CanIf_PduGetModeType` (read-side: `CANIF_GET_OFFLINE`, `CANIF_GET_ONLINE`, …). A developer unfamiliar with this naming convention may write `CANIF_OFFLINE` (dropping the `GET_` prefix), assuming the prefix is optional or interchangeable with the set-side names. The compiler immediately rejects the undeclared identifier — it cannot pass even the first compilation stage. Unlike TC-CANIF-F-03 (which substitutes `CANIF_GET_ONLINE` — a valid but semantically wrong read-side enum that compiles and fails at runtime), this change is rejected before any code runs. |

---

### TC-CANIF-F-06 — Functional: CanIf_GetControllerMode() Returns Wrong Mode Value

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-06 |
| **Title** | Functional change — `CanIf_GetControllerMode()` always writes `CANIF_CS_SLEEP` to the output parameter regardless of actual controller state |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Requirement — Original** | *"The service CanIf_GetControllerMode() shall return the current mode of the CAN controller requested by parameter ControllerId."* |
| **Requirement — Modified** | *"The service CanIf_GetControllerMode() shall always report the controller mode as CANIF_CS_SLEEP, regardless of the actual runtime state of the CAN controller."* |
| **Affected Function(s)** | `CanIf_GetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line ~332 — output parameter assignment inside `CanIf_GetControllerMode()`.<br><br>`OLD:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;`<br>`NEW:` `*ControllerModePtr = CANIF_CS_SLEEP;`<br><br>The stored channel state is no longer read. A hardcoded `CANIF_CS_SLEEP` constant is written to the caller's output variable on every call, for every channel, regardless of the actual state stored in `CanIf_Global`. |
| **Expected Behavior** | Every call to `CanIf_GetControllerMode(channelId, &mode)` returns `E_OK` and sets `mode = CANIF_CS_SLEEP`, even if the channel was successfully transitioned to `CANIF_CS_STARTED` by `CanIf_SetControllerMode()`. This cascades immediately to `CanIf_Transmit()` (line 446), which checks `csMode != CANIF_CS_STARTED` and returns `E_NOT_OK` — permanently blocking all CAN frame transmission regardless of the actual bus state. |
| **Verification Criteria** | 1. Call `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` → returns `E_OK`. 2. Call `CanIf_GetControllerMode(0, &mode)` → returns `E_OK` but `mode == CANIF_CS_SLEEP`, **not** `CANIF_CS_STARTED`. 3. Call `CanIf_Transmit(0, &pdu)` → returns `E_NOT_OK` (blocked at controller-mode guard, line 450). 4. The output parameter `mode` is `CANIF_CS_SLEEP` for every valid channel, including channels that are physically started. 5. Restoring `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;` re-enables transmit. |
| **AUTOSAR Rationale** | `CanIf_GetControllerMode()` is the sole read path for controller state in the CanIf layer. `CanIf_Transmit()` relies on it at line 446–451 to guard every transmit attempt. Returning a wrong hardcoded mode silently breaks all transmission without any error code — the failure is invisible at the `CanIf_Transmit()` call site because `E_NOT_OK` appears to originate from the controller mode, not from a code defect. This test case covers the critical "wrong output value from getter" class of defects. |

---

### TC-CANIF-F-07 — Functional: CanIf_GetPduMode() Returns Wrong PDU Mode Value

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-07 |
| **Title** | Functional change — `CanIf_GetPduMode()` always writes `CANIF_GET_OFFLINE` to the output parameter regardless of actual channel PDU mode |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00346 |
| **Requirement — Original** | *"The service CanIf_GetPduMode() shall return the current PDU channel mode of the requested controller."* |
| **Requirement — Modified** | *"The service CanIf_GetPduMode() shall always report the PDU channel mode as CANIF_GET_OFFLINE, regardless of the mode set by CanIf_SetPduMode()."* |
| **Affected Function(s)** | `CanIf_GetPduMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 641 — output parameter assignment inside `CanIf_GetPduMode()`.<br><br>`OLD:` `*PduModePtr = CanIf_Global.channelData[channel].PduMode;`<br>`NEW:` `*PduModePtr = CANIF_GET_OFFLINE;`<br><br>The stored PDU mode is no longer read. A hardcoded `CANIF_GET_OFFLINE` constant is written to the caller's output variable on every call, for every channel. |
| **Expected Behavior** | Every call to `CanIf_GetPduMode(channelId, &mode)` returns `E_OK` and sets `mode = CANIF_GET_OFFLINE`, even after `CanIf_SetPduMode(channelId, CANIF_SET_ONLINE)` has been called. This cascades to:<br>• `CanIf_Transmit()` (line 455–461): `pduMode` is always `CANIF_GET_OFFLINE` → the check `(pduMode != CANIF_GET_TX_ONLINE) && (pduMode != CANIF_GET_ONLINE)` always evaluates true → every transmit returns `E_NOT_OK`.<br>• `CanIf_RxIndication()` (line 776–783): `mode` is always `CANIF_GET_OFFLINE` → the drop condition `mode == CANIF_GET_OFFLINE` is always true → every received frame is silently discarded with no upper-layer callback. |
| **Verification Criteria** | 1. Call `CanIf_SetPduMode(0, CANIF_SET_ONLINE)` → returns `E_OK`. 2. Call `CanIf_GetPduMode(0, &mode)` → returns `E_OK` but `mode == CANIF_GET_OFFLINE`, **not** `CANIF_GET_ONLINE`. 3. `CanIf_Transmit(0, &pdu)` → returns `E_NOT_OK` (blocked at PDU mode guard, line 459). 4. A received CAN frame triggers `CanIf_RxIndication()` but no upper-layer callback fires (frame dropped at line 779). 5. Both Tx and Rx paths are simultaneously broken — the channel appears permanently offline to both directions. 6. Restoring `*PduModePtr = CanIf_Global.channelData[channel].PduMode;` re-enables both paths. |
| **AUTOSAR Rationale** | `CanIf_GetPduMode()` is used as a runtime gate by both `CanIf_Transmit()` and `CanIf_RxIndication()`. Returning a hardcoded wrong value silently disables both the transmit and receive paths simultaneously, with no error code to the upper layer. CanSM, COM, and PduR interpret the silent failure as a permanent channel-offline condition. This test case covers the high-impact "getter always returns wrong enum constant" class of defects — where the function returns `E_OK` but the output value is incorrect. |

---

### TC-CANIF-F-10 — Functional: CanIf_GetPduMode() Always Returns CANIF_GET_ONLINE — All Guards Bypassed

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-10 |
| **Title** | Functional change — `CanIf_GetPduMode()` hardcodes `CANIF_GET_ONLINE` (integer 3); every PDU mode safety guard is permanently bypassed |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00346 |
| **Requirement — Original** | *"The service CanIf_GetPduMode() shall return the current PDU channel mode of the requested controller."* |
| **Requirement — Modified** | *"The service CanIf_GetPduMode() shall always report the PDU channel mode as CANIF_GET_ONLINE so that the channel always appears fully operational to all callers."* |
| **Affected Function(s)** | `CanIf_GetPduMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 641 — output parameter assignment inside `CanIf_GetPduMode()`.<br><br>`OLD:` `*PduModePtr = CanIf_Global.channelData[channel].PduMode;`<br>`NEW:` `*PduModePtr = CANIF_GET_ONLINE;`<br><br>The stored PDU mode is no longer read. A hardcoded `CANIF_GET_ONLINE` (integer value **3**) is written to the caller's output variable on every call, for every channel, regardless of the actual mode stored in `CanIf_Global`. |
| **Expected Behavior — Transmit path** | `CanIf_Transmit()` (lines 455–461) reads `pduMode` via `CanIf_GetPduMode()` → always receives `CANIF_GET_ONLINE` (3). Guard check:<br>`(pduMode != CANIF_GET_TX_ONLINE) && (pduMode != CANIF_GET_ONLINE)`<br>= `(3 != 2) && (3 != 3)`<br>= `TRUE && FALSE`<br>= **FALSE** → guard never triggers → `CanIf_Transmit()` always proceeds to `Can_Write()` regardless of actual channel state. A channel set to `CANIF_SET_OFFLINE` still transmits frames. |
| **Expected Behavior — Receive path** | `CanIf_RxIndication()` (lines 776–783) reads `mode` via `CanIf_GetPduMode()` → always receives `CANIF_GET_ONLINE` (3). Drop condition:<br>`(mode == CANIF_GET_OFFLINE(0)) \|\| (mode == CANIF_GET_TX_ONLINE(2)) \|\| (mode == CANIF_GET_OFFLINE_ACTIVE(4))`<br>None of these match 3 → drop condition **never** triggers → every received frame is forwarded to the upper-layer callback, even on channels that are in OFFLINE state. |
| **Verification Criteria** | 1. Call `CanIf_SetPduMode(0, CANIF_SET_OFFLINE)` → channel should be offline. 2. Call `CanIf_GetPduMode(0, &mode)` → returns `E_OK` but `mode == CANIF_GET_ONLINE` (3), **not** `CANIF_GET_OFFLINE` (0). 3. `CanIf_Transmit(0, &pdu)` → returns `E_OK` and `Can_Write()` is called — frame transmitted despite the channel being OFFLINE. 4. A received frame on channel 0 triggers the upper-layer `<User_RxIndication>()` callback — frame not dropped despite OFFLINE state. 5. Both Tx and Rx safety barriers are simultaneously broken for every channel. 6. Restoring `*PduModePtr = CanIf_Global.channelData[channel].PduMode;` re-enables correct guard behavior. |
| **Contrast with TC-CANIF-F-07** | TC-CANIF-F-07 hardcodes `CANIF_GET_OFFLINE` (0) → both paths **blocked**; channel appears permanently dead. TC-CANIF-F-10 hardcodes `CANIF_GET_ONLINE` (3) → both paths **always open**; all safety guards bypassed. These two test cases demonstrate the two failure extremes of a getter returning a hardcoded wrong value: F-07 freezes the network, F-10 makes it uncontrollably active. |
| **AUTOSAR Rationale** | `CANIF_GET_ONLINE` is the only PDU mode that simultaneously satisfies both the Tx acceptance condition (`!= CANIF_GET_TX_ONLINE && != CANIF_GET_ONLINE` evaluates to FALSE) and the Rx forward condition (not in any of the drop-mode values). Hardcoding it makes the channel appear permanently online to every guard in the module. Unlike F-07 (which produces visible system silence), this defect causes the system to transmit and receive without restrictions — undetectable until a CAN bus overload or protocol violation occurs. |

---

### TC-CANIF-F-11 — Functional: CanIf_GetControllerMode() Reads Wrong Struct Field

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-11 |
| **Title** | Functional change — `CanIf_GetControllerMode()` reads `PduMode` field instead of `ControllerMode` field; integer values accidentally coincide for one mode causing intermittent spurious transmission |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Requirement — Original** | *"The service CanIf_GetControllerMode() shall return the current mode of the CAN controller requested by parameter ControllerId."* |
| **Requirement — Modified** | *(Erroneous change)* The developer accidentally types `PduMode` instead of `ControllerMode` when accessing the `channelData` struct. Both fields are adjacent members of the same `CanIf_ChannelPrivateType` struct (line 88–90 of `CanIf.c`), making the typo visually subtle. |
| **Affected Function(s)** | `CanIf_GetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 332 — struct field access inside `CanIf_GetControllerMode()`.<br><br>`OLD:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;`<br>`NEW:` `*ControllerModePtr = (CanIf_ControllerModeType)CanIf_Global.channelData[channel].PduMode;`<br><br>The `ControllerMode` field name is replaced by `PduMode`. A cast to `CanIf_ControllerModeType` silences the type-mismatch warning. |
| **Expected Behavior — Integer value analysis** | From `CanIf_Types.h` — exact integer values:<br>`CanIf_ControllerModeType`: UNINIT=0, STOPPED=1, **STARTED=2**, SLEEP=3<br>`CanIf_ChannelGetModeType`: OFFLINE=0, RX_ONLINE=1, **TX_ONLINE=2**, ONLINE=3, OFFLINE_ACTIVE=4<br><br>`CANIF_GET_TX_ONLINE` (2) and `CANIF_CS_STARTED` (2) share the **same integer value**. This creates a state-dependent behavior:<br><br>• **PduMode = CANIF_GET_OFFLINE (0)** → returns as CANIF_CS_UNINIT (0) → `csMode(0) != CANIF_CS_STARTED(2)` → Tx **blocked**.<br>• **PduMode = CANIF_GET_RX_ONLINE (1)** → returns as CANIF_CS_STOPPED (1) → `csMode(1) != 2` → Tx **blocked**.<br>• **PduMode = CANIF_GET_TX_ONLINE (2)** → returns as CANIF_CS_STARTED (2) → `csMode(2) != 2` → **FALSE** → Tx **accidentally allowed**, even if the actual controller is STOPPED or SLEEP.<br>• **PduMode = CANIF_GET_ONLINE (3)** → returns as CANIF_CS_SLEEP (3) → `csMode(3) != 2` → Tx **blocked**. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(0, CANIF_CS_STOPPED)` + `CanIf_SetPduMode(0, CANIF_SET_TX_ONLINE)` → `CanIf_GetControllerMode(0, &m)` returns `m == CANIF_CS_STARTED` (2) even though the actual mode is STOPPED. 2. `CanIf_Transmit(0, &pdu)` proceeds past the controller-mode guard (line 450) and calls `Can_Write()` even though the hardware is stopped. 3. For all other PDU modes (OFFLINE / RX_ONLINE / ONLINE), `CanIf_Transmit()` is correctly blocked — the defect only surfaces when PDU mode is exactly `CANIF_GET_TX_ONLINE`. 4. Restoring `.ControllerMode` in the field access corrects all mode reports. |
| **AUTOSAR Rationale** | This defect is both realistic (one-word typo in a long struct access expression) and non-deterministic (manifests only when `PduMode == CANIF_GET_TX_ONLINE`). In the typical system startup sequence — where CanSM sets the PDU channel to `CANIF_SET_TX_ONLINE` during the STOPPED→STARTED transition — this exact mode is briefly active, meaning the defect triggers precisely during controller startup, allowing frame transmission to reach a driver that has not yet been fully started. The cast `(CanIf_ControllerModeType)` suppresses the compiler warning, making this defect invisible to static analysis. |

---

### TC-CANIF-NF-01 — Non-Functional: Loop Variable Type Widened in `CanIf_Init()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-NF-01 |
| **Title** | Non-functional change — channel-init loop variable widened from `uint8` to `uint32`; identical behavior for all valid configurations |
| **Category** | Non-Functional (NF) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00085 (initialization) |
| **Affected Function(s)** | `CanIf_Init` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 137 — loop variable declaration in `CanIf_Init()`.<br><br>`OLD:` `for (uint8 i = 0; i < CANIF_CHANNEL_CNT; i++)`<br>`NEW:` `for (uint32 i = 0; i < CANIF_CHANNEL_CNT; i++)`<br><br>No other change anywhere in the function. |
| **Expected Behavior** | `CanIf_Init()` behaves **identically** for all valid values of `CANIF_CHANNEL_CNT`. The loop iterates the same number of times; every `channelData[i]` access produces the same address; every assignment inside the body executes in the same order with the same values. The only effect is that the local loop variable `i` occupies 4 bytes of stack instead of 1. No output, no branch, no pointer value changes. |
| **Verification Criteria** | 1. After `CanIf_Init()`, `CanIf_GetPduMode(ch, &m)` returns `CANIF_GET_OFFLINE` for all channels — identical to pre-change result. 2. After `CanIf_Init()`, `CanIf_GetControllerMode(ch, &m)` returns `CANIF_CS_STOPPED` for all channels — identical to pre-change result. 3. Full functional regression suite passes with zero behavioral differences. 4. No caller of `CanIf_Init()` is affected — the function signature is unchanged. |
| **AUTOSAR Rationale** | This is a pure implementation-internal change. `CANIF_CHANNEL_CNT` is always a small number (typically ≤ 4 in a real ECU) and fits in a `uint8`. Widening the loop variable to `uint32` never changes the iteration count, the index values, or any computed address. The classification is Non-Functional because for every possible combination of inputs and configurations, the observable outputs of `CanIf_Init()` are bit-for-bit identical before and after the change. |

---

### TC-CANIF-NF-02 — Non-Functional: Reorder Independent Validation Checks in `CanIf_Transmit()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-NF-02 |
| **Title** | Non-functional change — two independent input validation checks swapped in `CanIf_Transmit()`; normal execution path is unchanged |
| **Category** | Non-Functional (NF) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00162 |
| **Affected Function(s)** | `CanIf_Transmit` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, lines 431–432 — the two opening VALIDATE macros in `CanIf_Transmit()`.<br><br>`OLD (original order):`<br>`  VALIDATE(CanIf_Global.initRun, CANIF_TRANSMIT_ID, CANIF_E_UNINIT );`<br>`  VALIDATE((PduInfoPtr != 0), CANIF_TRANSMIT_ID, CANIF_E_PARAM_POINTER );`<br><br>`NEW (swapped order):`<br>`  VALIDATE((PduInfoPtr != 0), CANIF_TRANSMIT_ID, CANIF_E_PARAM_POINTER );`<br>`  VALIDATE(CanIf_Global.initRun, CANIF_TRANSMIT_ID, CANIF_E_UNINIT );`<br><br>No other change in the function. |
| **Expected Behavior** | For all normal inputs (`initRun == TRUE` and `PduInfoPtr != NULL`): execution proceeds identically. For any call where exactly one condition fails: the same single DET error is reported and `E_NOT_OK` returned — identical to before. The only scenario where behavior differs is the degenerate case where **both** conditions fail simultaneously: original order reports `CANIF_E_UNINIT` first; new order reports `CANIF_E_PARAM_POINTER` first. This edge case represents a simultaneous programming error and has no defined correct handling. |
| **Verification Criteria** | 1. `CanIf_Transmit(validId, validPtr)` with `initRun == TRUE`: identical result. 2. `CanIf_Transmit(validId, NULL)` with `initRun == TRUE`: reports `CANIF_E_PARAM_POINTER`, returns `E_NOT_OK` — identical to before. 3. `CanIf_Transmit(validId, validPtr)` with `initRun == FALSE`: reports `CANIF_E_UNINIT`, returns `E_NOT_OK` — identical to before. 4. Full regression suite passes with zero behavioral differences for all normal test inputs. |
| **AUTOSAR Rationale** | Both VALIDATE checks are independent — neither depends on the other's result. For every operationally meaningful call (valid or singly-invalid inputs), the outcome is identical. The change is Non-Functional because the function's contract with its callers is 100% preserved for all normal operating scenarios. Only the double-fault case reports a different first error code — a scenario that represents a fundamental caller programming error, not a defined operational path. |

---

### TC-CANIF-F-08 — Functional: ControllerId Parameter Type Widened from `uint8` to `uint16`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-08 |
| **Title** | Functional change — `ControllerId` parameter type widened from `uint8` to `uint16`; changes valid input domain and interface contract |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308 |
| **Requirement — Original** | ControllerId is typed as `uint8`. Values `0–255` are the representable range; values `≥ CANIF_CHANNEL_CNT` are rejected by the bounds check. |
| **Requirement — Modified** | *"ControllerId shall be typed as `uint16` to support ECU configurations with more than 255 CAN controller channels."* The valid representable range is now `0–65535`. |
| **Affected Function(s)** | `CanIf_SetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 226 — function signature.<br><br>`OLD:` `Std_ReturnType CanIf_SetControllerMode(uint8 Controller,`<br>`NEW:` `Std_ReturnType CanIf_SetControllerMode(uint16 Controller,`<br><br>The corresponding declaration in `CanIf.h` must also be updated. All callers that pass a `uint8` argument must be updated to pass `uint16` to avoid implicit narrowing. |
| **Expected Behavior** | `CanIf_SetControllerMode()` now accepts a `uint16` ControllerId. Values in `[0, CANIF_CHANNEL_CNT - 1]` behave identically to before. Values in `[256, 65535]` are **new valid inputs** that were previously impossible to express — they will be checked against the bounds condition `channel < CANIF_CHANNEL_CNT` and rejected with `CANIF_E_PARAM_CONTROLLER` via DET. The function's behavior for the entire previously-valid input range is preserved. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` behaves identically to before — no regression. 2. `CanIf_SetControllerMode(256, CANIF_CS_STARTED)` is now representable; DET reports `CANIF_E_PARAM_CONTROLLER` and function returns `E_NOT_OK`. 3. Function signature in `CanIf.h` matches `CanIf.c` — mismatched signatures cause undefined behavior. 4. All compilation units that include `CanIf.h` are recompiled after the header change. 5. No implicit narrowing conversion warnings remain in any caller. |
| **AUTOSAR Rationale** | This is a Functional change — not Non-Functional — because it expands the valid input domain: values `256–65535` are now representable and must be handled by the bounds check. Any caller that previously passed a `uint8` variable now has a widened interface contract. Additionally this is an ABI-breaking change: all compilation units that include `CanIf.h` must be recompiled, and mismatched function signatures between caller and callee produce undefined behavior per the C standard. |

---

### TC-CANIF-F-09 — Functional: DLC Acceptance Policy Changed from `≥ configured` to `== configured`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-09 |
| **Title** | Functional change — received frame DLC acceptance changes from `≥ configured` to exact match `== configured`; changes which frames are accepted at runtime |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00026 |
| **Requirement — Original** | *"CanIf shall accept all received L-PDUs with a Data Length value equal or greater than the configured Data Length value."* Frames with `CanDlc >= CanIfCanRxPduDlc` are accepted. |
| **Requirement — Modified** | *"CanIf shall accept received L-PDUs with a Data Length value equal to the configured Data Length value only. Frames with any other DLC shall be rejected."* Frames with `CanDlc == CanIfCanRxPduDlc` are accepted; all others are rejected. |
| **Affected Function(s)** | `CanIf_RxIndication` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 824 — DLC comparison inside `CanIf_RxIndication()`.<br><br>`OLD:` `if (CanDlc < entry->CanIfCanRxPduDlc)`<br>`NEW:` `if (CanDlc != entry->CanIfCanRxPduDlc)`<br><br>The condition changes from "reject if less than configured" to "reject if not exactly equal to configured". |
| **Expected Behavior** | Before: frames with `CanDlc = 6` and `configured = 4` are **accepted** (6 ≥ 4). After: the same frame is **rejected** — `6 != 4` triggers `CANIF_E_PARAM_DLC` via DET and the upper-layer callback is not invoked. Frames with `CanDlc = 4` and `configured = 4` continue to be accepted in both cases. Frames with `CanDlc = 2` and `configured = 4` are rejected in both cases. The change specifically affects all frames where `CanDlc > configured` — previously accepted, now rejected. |
| **Verification Criteria** | 1. Frame `CanDlc=4`, `configured=4`: accepted and dispatched — identical to before. 2. Frame `CanDlc=2`, `configured=4`: rejected, `CANIF_E_PARAM_DLC` via DET — identical to before. 3. Frame `CanDlc=6`, `configured=4`: **rejected** (change) — `CANIF_E_PARAM_DLC` via DET, upper-layer callback NOT invoked. Previously this frame was accepted. 4. Frame `CanDlc=8`, `configured=4`: rejected — new behavior, all padded CAN FD frames dropped. 5. No other logic in `CanIf_RxIndication()` changes — HRH lookup, software filtering, and upper-layer dispatch are unaffected for accepted frames. |
| **AUTOSAR Rationale** | This is a Functional change — not Non-Functional — because it changes the runtime accept/reject decision for a real class of frames: any frame where `CanDlc > configured`. The upper-layer module no longer receives those frames. In CAN FD networks where padding is mandatory (frames are always padded to 8 or 64 bytes), this change causes **all** received frames to be rejected. This is a breaking behavioral change with direct impact on communication correctness, not merely a structural or quality improvement. |

---

### TC-CANIF-C-01 — Cosmetic: Editorial Wording Change in RxIndication Configuration Requirement

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-C-01 |
| **Title** | Cosmetic change — Normative verb and phrasing updated in SWS_CANIF_00423; no behavioral change |
| **Category** | Cosmetic (C) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00423 |
| **Requirement — Original** | *"Configuration of CanIf_RxIndication(): Each Rx L-PDU (see CanIfRxPduCfg) has to be configured with a corresponding receive indication service of an upper layer module (see [SWS_CANIF_00012]) which is called in CanIf_RxIndication()."* |
| **Requirement — Modified** | *"Configuration of CanIf_RxIndication(): Each Rx L-PDU (see CanIfRxPduCfg) MUST be configured with a corresponding receive indication service of an upper layer module (see [SWS_CANIF_00012]) that is invoked within CanIf_RxIndication()."* *(Changes: "has to" → "MUST"; "which is called" → "that is invoked within")* |
| **Affected Function(s)** | `CanIf_RxIndication` *(per requirement-to-code traceability)* |
| **Mandatory Code Modification** | **NONE.** The change is purely editorial. The normative intent — that every Rx L-PDU must have a configured upper-layer callback — is unchanged. The runtime behavior of `CanIf_RxIndication()` is identical before and after this change. |
| **Expected Behavior** | `CanIf_RxIndication()` continues to operate exactly as before. The upper-layer dispatch switch-case, software filtering, HRH lookup, and DLC check are all unaffected. A human engineer review must confirm the classification as Cosmetic and close the change request with status **"Requirements Document Updated — No Code Change Required."** |
| **Verification Criteria** | 1. `CanIf.c` source file has zero modifications after this requirement change. 2. A code diff between the pre-change and post-change versions of `CanIf.c` shows no differences. 3. The requirements document (SWS) reflects the new wording. 4. An engineer sign-off record confirms Cosmetic classification. |
| **AUTOSAR Rationale** | Cosmetic changes occur in every AUTOSAR release cycle (e.g., AR 4.0.3 → AR 4.2.2 → AR 4.4.0) as the AUTOSAR consortium standardizes normative language. The engineer review step is mandatory because the classification cannot be automated — a wording change that appears editorial may occasionally introduce a subtle behavioral shift that only a domain expert can detect. |

---

### TC-CANIF-C-02 — Cosmetic: Internal Cross-Reference Number Updated

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-C-02 |
| **Title** | Cosmetic change — Internal SWS cross-reference renumbered; no behavioral change |
| **Category** | Cosmetic (C) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00552 |
| **Requirement — Original** | *"Configuration of \<User_RxIndication\>(): The name of the API \<User_RxIndication\>() which will be called by CanIf shall be configured for CanIf by parameter CanIfRxPduUserRxIndicationName."* |
| **Requirement — Modified** | *"Configuration of \<User_RxIndication\>(): The name of the API \<User_RxIndication\>() which will be called by CanIf shall be configured for CanIf by parameter CanIfRxPduUserRxIndicationName. (see [SWS_CANIF_00056])"* *(A traceability cross-reference added for alignment with a new AUTOSAR release.)* |
| **Affected Function(s)** | `CanIf_RxIndication` *(per requirement-to-code traceability)* |
| **Mandatory Code Modification** | **NONE.** The addition of a parenthetical cross-reference carries no implementation consequence. The API name configuration mechanism and the dispatch logic within `CanIf_RxIndication()` are unchanged. |
| **Expected Behavior** | `CanIf_RxIndication()` continues to call the upper-layer receive indication service using the configured API name. No change in function behavior, no change in calling convention, and no change in the set of upper-layer modules that can be dispatched. |
| **Verification Criteria** | 1. Zero changes to `CanIf.c`. 2. Zero changes to `CanIf.h` or any configuration header. 3. Requirements document updated with the new cross-reference. 4. Engineer review record confirms Cosmetic classification. |
| **AUTOSAR Rationale** | Cross-reference updates are common during AUTOSAR version harmonization. They align requirements across different SWS documents without altering the implementation. This test case validates that the engineering process correctly distinguishes a documentation-only update from a code-impacting change. |

---

### TC-CANIF-XD1N-01 — Cross-Depend 1→2: One Requirement Change Affects Two Functions

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-XD1N-01 |
| **Title** | Cross-depend (1→2) — Single requirement change propagates to `CanIf_SetControllerMode` and `CanIf_ControllerBusOff` |
| **Category** | Cross-Depend 1→N (XD-1N) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00866 |
| **Requirement — Original** | *"If CanIf_SetControllerMode(ControllerId, CAN_CS_STOPPED) or CanIf_ControllerBusOff(ControllerId) is called, CanIf shall set the PDU channel mode of the corresponding channel to CANIF_TX_OFFLINE."* |
| **Requirement — Modified** | *"If CanIf_SetControllerMode(ControllerId, CAN_CS_STOPPED) or CanIf_ControllerBusOff(ControllerId) is called, CanIf shall set the PDU channel mode of the corresponding channel to CANIF_OFFLINE (full offline — both Tx and Rx disabled)."* |
| **Affected Function(s)** | `CanIf_SetControllerMode` **and** `CanIf_ControllerBusOff` |
| **Mandatory Code Modification** | **File:** `CanIf.c`<br><br>**Modification in `CanIf_SetControllerMode` (line 305) — `CANIF_CS_STOPPED` case:**<br>`OLD:` `CanIf_SetPduMode(channel, CANIF_SET_OFFLINE);`<br>`NEW:` *(The `CANIF_SET_OFFLINE` enum value itself corresponds to `CANIF_GET_OFFLINE`, which per the modified requirement is now the correct target. Confirm that the `CANIF_SET_OFFLINE` → `CANIF_GET_OFFLINE` mapping in `CanIf_SetPduMode()` matches the required full-offline semantics. If `CANIF_TX_OFFLINE` was previously set here by a different path, update that call site as well.)*<br><br>**Modification in `CanIf_ControllerBusOff` (line 935):**<br>`CanIf_ControllerBusOff()` calls `CanIf_SetControllerMode(channel, CANIF_CS_STOPPED)`. Because the behavior of `CanIf_SetControllerMode()` in the `CANIF_CS_STOPPED` case is updated above, `CanIf_ControllerBusOff()` is **transitively** affected. Verify that `CanIf_ControllerBusOff()` does not independently set a PDU mode that conflicts with the new requirement. If it does, update it to call `CanIf_SetPduMode(channel, CANIF_SET_OFFLINE)` directly. |
| **Expected Behavior** | After either `CanIf_SetControllerMode(x, CAN_CS_STOPPED)` or `CanIf_ControllerBusOff(x)` is called: `CanIf_GetPduMode(x, &mode)` returns `mode == CANIF_GET_OFFLINE`. Both Tx forwarding (via `CanIf_Transmit()`) and Rx indication callbacks (via `CanIf_RxIndication()`) must be suppressed for channel `x`. This behavior must be **identical** regardless of whether the OFFLINE state was triggered by a controlled stop or a BusOff event. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(ch, CAN_CS_STOPPED)` → `CanIf_GetPduMode(ch, &m)` returns `m == CANIF_GET_OFFLINE`. 2. `CanIf_ControllerBusOff(ch)` → `CanIf_GetPduMode(ch, &m)` returns `m == CANIF_GET_OFFLINE`. 3. `CanIf_Transmit()` on channel `ch` returns `E_NOT_OK` after either trigger. 4. A received frame on channel `ch` is silently dropped (no upper-layer callback) after either trigger. 5. **Both functions behave identically** — partial update (updating one but not the other) fails this test case. |
| **AUTOSAR Rationale** | SWS_CANIF_00866 explicitly names two triggering conditions (CAN_CS_STOPPED mode set and BusOff event). Both must produce the same PDU channel mode outcome. Implementing the change in only one of the two functions creates an inconsistency where a controlled stop and an emergency BusOff leave the channel in different states — a critical safety defect in any safety-relevant network. |

---

### TC-CANIF-XD1N-02 — Cross-Depend 1→3: One Requirement Change Affects Three Functions

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-XD1N-02 |
| **Title** | Cross-depend (1→3) — Single requirement change propagates to `CanIf_Transmit`, `CanIf_TxConfirmation`, and `CanIf_RxIndication` |
| **Category** | Cross-Depend 1→N (XD-1N) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00073 |
| **Requirement — Original** | *"For Physical Channels switching to CANIF_OFFLINE mode CanIf shall: prevent forwarding of transmit requests CanIf_Transmit() of associated L-PDUs to CanDrv, clear the corresponding CanIf transmit buffers, prevent invocation of receive indication callback services of the upper layer modules, prevent invocation of transmit confirmation callback services of the upper layer modules."* |
| **Requirement — Modified** | *"For Physical Channels switching to CANIF_OFFLINE mode CanIf shall: prevent forwarding of transmit requests and prevent invocation of transmit confirmation callbacks. Receive indication callbacks shall remain enabled in CANIF_OFFLINE mode to allow passive network monitoring."* |
| **Affected Function(s)** | `CanIf_Transmit` **and** `CanIf_TxConfirmation` **and** `CanIf_RxIndication` |
| **Mandatory Code Modification** | **File:** `CanIf.c`<br><br>**Modification in `CanIf_RxIndication` (line 778) — remove `CANIF_GET_OFFLINE` from the Rx-drop condition:**<br>`OLD:`<br>`if ( (mode == CANIF_GET_OFFLINE) \|\| (mode == CANIF_GET_TX_ONLINE) \|\|`<br>`     (mode == CANIF_GET_OFFLINE_ACTIVE) )`<br>`NEW:`<br>`if ( (mode == CANIF_GET_TX_ONLINE) \|\|`<br>`     (mode == CANIF_GET_OFFLINE_ACTIVE) )`<br><br>**`CanIf_Transmit` and `CanIf_TxConfirmation`** — verify that their existing mode checks correctly reject/suppress in `CANIF_GET_OFFLINE` mode. If they do, **no additional change** is needed in those functions. Document that they were reviewed and confirmed compliant. If they do not, add or correct the mode guard accordingly. |
| **Expected Behavior** | When channel PDU mode is `CANIF_GET_OFFLINE`: (a) `CanIf_Transmit()` must return `E_NOT_OK` without calling `Can_Write()`. (b) `CanIf_TxConfirmation()` must not invoke `<User_TxConfirmation>()`. (c) `CanIf_RxIndication()` must **continue** to process received frames and dispatch to the upper layer — Rx is no longer suppressed in OFFLINE mode per the modified requirement. |
| **Verification Criteria** | 1. Channel in `CANIF_GET_OFFLINE`: `CanIf_Transmit()` → `E_NOT_OK`, `Can_Write()` not called. 2. Channel in `CANIF_GET_OFFLINE`: `CanIf_TxConfirmation()` does not invoke `<User_TxConfirmation>()`. 3. Channel in `CANIF_GET_OFFLINE`: `CanIf_RxIndication()` dispatches the frame to the configured upper layer (Rx indication callback IS invoked). 4. All three functions must be reviewed and their change status (modified / confirmed-compliant) documented. Reviewing only one or two is insufficient. |
| **AUTOSAR Rationale** | SWS_CANIF_00073 is the central PDU channel mode behavioral contract. It is the highest fan-out requirement in the CanIf module — three functions share a common invariant. Any partial implementation (e.g., fixing only `CanIf_RxIndication` while forgetting `CanIf_Transmit`) creates an inconsistent OFFLINE state where Rx works differently from Tx, breaking the CanSM state machine and potentially causing unintended frame transmission on an "offline" channel. |

---

### TC-CANIF-XDN1-01 — Cross-Depend N→1: Two Requirement Changes Converge on One Function

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-XDN1-01 |
| **Title** | Cross-depend (2→1) — Two independent requirement changes both affect `CanIf_SetControllerMode` simultaneously |
| **Category** | Cross-Depend N→1 (XD-N1) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00311 **+** SWS_CANIF_00774 |
| **Requirement — Original** | *SWS_CANIF_00311:* "Invalid ControllerId → report `CANIF_E_PARAM_CONTROLLERID`."<br>*SWS_CANIF_00774:* "Invalid ControllerMode (not CAN_CS_STARTED / SLEEP / STOPPED) → report `CANIF_E_PARAM_CTRLMODE`." |
| **Requirement — Modified** | *SWS_CANIF_00311 (modified):* "Invalid ControllerId → report `CANIF_E_PARAM_POINTER`." *(error code changed)*<br>*SWS_CANIF_00774 (modified):* "ControllerMode validation is removed — all ControllerMode values are accepted without error reporting." *(validation removed entirely)* |
| **Affected Function(s)** | `CanIf_SetControllerMode` *(single function — both requirements trace here)* |
| **Mandatory Code Modification** | **File:** `CanIf.c`<br><br>**Modification 1 — SWS_CANIF_00311 (line 236):**<br>`OLD:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`NEW:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );`<br><br>**Modification 2 — SWS_CANIF_00774 (lines 313–315):**<br>`OLD:`<br>`  case CANIF_CS_UNINIT:`<br>`    // Just fall through`<br>`    break;`<br>`NEW:`<br>`  case CANIF_CS_UNINIT:`<br>`  default:`<br>`    /* All ControllerMode values accepted — validation removed per new req */`<br>`    break;` |
| **Expected Behavior** | `CanIf_SetControllerMode()` must simultaneously implement both changes: (1) ControllerId out-of-range triggers DET with `CANIF_E_PARAM_POINTER`. (2) Any ControllerMode value (including previously invalid values) is accepted without error — the function falls through to the appropriate case or a new default handler. The function must remain internally consistent — no undefined behavior for previously invalid inputs. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(255, CANIF_CS_STARTED)` → DET called with `CANIF_E_PARAM_POINTER`, returns `E_NOT_OK`. 2. `CanIf_SetControllerMode(0, CANIF_CS_UNINIT)` → no DET call, function executes the default case without error. 3. `CanIf_SetControllerMode(0, 99)` (unknown mode) → no DET call (validation removed), falls to default. 4. Both changes are applied in a **single function** — there is no second function to modify. 5. A single code-review record covers both requirement changes, confirming they are addressed in the same function. |
| **AUTOSAR Rationale** | The N→1 pattern requires the developer to recognize that multiple incoming change requests target the same implementation unit and must be resolved together. Implementing one change while leaving the other outstanding creates an inconsistency between the requirements document and the implementation. This test validates the engineering process discipline of identifying, batching, and atomically implementing all co-located requirement changes. |

---

### TC-CANIF-XDN1-02 — Cross-Depend N→1: Three Requirement Changes Converge on One Function

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-XDN1-02 |
| **Title** | Cross-depend (3→1) — Three concurrent requirement changes all affect `CanIf_RxIndication` |
| **Category** | Cross-Depend N→1 (XD-N1) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00389 **+** SWS_CANIF_00390 **+** SWS_CANIF_00902 |
| **Requirement — Original** | *SWS_CANIF_00389:* "CanIf_RxIndication() shall process software filtering; if rejected, the receive indication shall end."<br>*SWS_CANIF_00390:* "After software filtering acceptance, CanIf shall process the Data Length Check if configured."<br>*SWS_CANIF_00902:* "Data Length Check shall be processed if enabled globally (CanIfPrivateDataLengthCheck) and not disabled individually per PDU (CanIfRxPduDataLengthCheck)." |
| **Requirement — Modified** | *SWS_CANIF_00389 (modified):* "Rejected frames shall be logged to DET before being dropped."<br>*SWS_CANIF_00390 (modified):* "Data Length Check shall execute **before** software filtering, not after."<br>*SWS_CANIF_00902 (modified):* "Data Length Check shall **always** be executed, regardless of CanIfPrivateDataLengthCheck and CanIfRxPduDataLengthCheck configuration flags." |
| **Affected Function(s)** | `CanIf_RxIndication` *(single function — all three requirements trace here)* |
| **Mandatory Code Modification** | **File:** `CanIf.c` — all modifications within `CanIf_RxIndication()`<br><br>**Modification 1 — SWS_CANIF_00389 (line ~811): Add DET log before drop**<br>`OLD:` `entry++;`<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`continue; // Go to next entry`<br>`NEW:` `DET_REPORTERROR(MODULE_ID_CANIF, 0, CANIF_RXINDICATION_ID, CANIF_E_PARAM_HRH);`<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`entry++;`<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`continue;`<br><br>**Modification 2 — SWS_CANIF_00390 (structural): Move DLC check block above the software filter block.** The `#if (CANIF_DLC_CHECK == STD_ON)` block must be relocated to execute before the `if (entry->CanIfCanRxPduHrhRef->CanIfHrhType == CAN_ARC_HANDLE_TYPE_BASIC)` software filter block.<br><br>**Modification 3 — SWS_CANIF_00902 (line ~823): Remove compile-time guard**<br>`OLD:` `#if (CANIF_DLC_CHECK == STD_ON)`<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`if (CanDlc < entry->CanIfCanRxPduDlc) { ... }`<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`#endif`<br>`NEW:` `if (CanDlc < entry->CanIfCanRxPduDlc) { ... }` *(guard removed — always active)* |
| **Expected Behavior** | `CanIf_RxIndication()` must: (1) Perform DLC check first — before any software filtering. (2) DLC check is unconditional — active for every frame regardless of `CANIF_DLC_CHECK` configuration. (3) If software filtering rejects a frame, a DET error is reported before continuing to the next entry. All three behaviors must be simultaneously active — implementing two out of three is a defect. |
| **Verification Criteria** | 1. A frame with `CanDlc < configured` is rejected at the DLC stage, before software filter is reached. 2. Removing `#define CANIF_DLC_CHECK STD_ON` from the configuration does not disable the DLC check — it now runs unconditionally. 3. A frame rejected by the software mask filter triggers a `DET_REPORTERROR` call with `CANIF_E_PARAM_HRH`. 4. A frame that passes both checks is still correctly dispatched to the upper layer. 5. A single code-review record lists all three requirement IDs and confirms all three are implemented. |
| **AUTOSAR Rationale** | Three requirements govern sequential stages of the same receive processing pipeline. Changing the order of stages and removing configuration guards fundamentally changes the runtime behavior for every received frame. The atomicity of this change is critical — reordering DLC and software filtering changes which error is reported first for a non-conformant frame, affecting fault isolation capabilities in AUTOSAR diagnostic frameworks. |

---

### TC-CANIF-CB-01 — Combined: Four Simultaneous Changes Across All Categories

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-CB-01 |
| **Title** | Combined change scenario — Four concurrent requirement changes spanning Functional, Non-functional, Cosmetic, and Cross-depend categories across four functions |
| **Category** | Combined (CB) = F + NF + C + XD-1N |
| **AUTOSAR Requirement IDs** | SWS_CANIF_00308 (Functional) · SWS_CANIF_00026 (Non-Functional) · SWS_CANIF_00423 (Cosmetic) · SWS_CANIF_00073 (Cross-Depend 1→3) |
| **Changes Introduced** | See the table below |
| **Affected Function(s)** | `CanIf_SetControllerMode` · `CanIf_Transmit` · `CanIf_TxConfirmation` · `CanIf_RxIndication` |
| **Mandatory Code Modification** | See per-requirement breakdown below |
| **Expected Behavior** | See per-requirement breakdown below |
| **Verification Criteria** | See per-requirement breakdown below |
| **AUTOSAR Rationale** | This scenario represents a realistic AUTOSAR change request sprint. Multiple CRs are raised simultaneously across different requirement owners. Each function owner is responsible for implementing only the changes that trace to their function. The process must ensure no change is missed, no function is double-modified for the same reason, and cosmetic changes are correctly identified and closed without code modification. |

#### Combined Scenario — Per-Requirement Breakdown

| Req ID | Category | Change Introduced | Affected Function | Required Code Change | Expected Behavior | Verification Criteria |
|:---:|:---:|:---|:---|:---|:---|:---|
| SWS_CANIF_00308 | **Functional** | `Can_SetControllerMode()` called with `CAN_T_STOP` instead of `CAN_T_START` in the `CANIF_CS_STARTED` case | `CanIf_SetControllerMode` | Line 264: `CAN_T_START` → `CAN_T_STOP` inside the `case CANIF_CS_STARTED:` block | The CAN Driver receives a STOP command when a START is requested. CanIf internal state is updated to `CANIF_CS_STARTED` but hardware stays stopped. Frames forwarded by `CanIf_Transmit()` are silently lost at the driver level. | `CanIf_GetControllerMode()` returns `CANIF_CS_STARTED` after the call. A bus monitor shows no active CAN traffic on that channel. CAN Driver internal state remains STOPPED. |
| SWS_CANIF_00026 | **Non-Functional** | DLC acceptance changes from `≥ configured` to `== configured` only | `CanIf_RxIndication` | Line 824: `CanDlc < entry->CanIfCanRxPduDlc` → `CanDlc != entry->CanIfCanRxPduDlc` | Frames with `CanDlc > configured` are now rejected. Frames with `CanDlc == configured` accepted. `CanIf_RxIndication()` dispatch logic unchanged. | Exact-match frames pass. Under- and over-length frames trigger `CANIF_E_PARAM_DLC`. No other change in `CanIf_RxIndication()`. |
| SWS_CANIF_00423 | **Cosmetic** | Wording: "has to be configured" → "MUST be configured with ... invoked within" | `CanIf_RxIndication` | **NONE** — no code change | `CanIf_RxIndication()` behavior is identical before and after. | Zero changes to `CanIf.c`. Engineer review record confirms Cosmetic. Work item closed as "No Code Action Required". |
| SWS_CANIF_00073 | **Cross-Depend 1→3** | CANIF_OFFLINE no longer suppresses Rx indication callbacks | `CanIf_Transmit` · `CanIf_TxConfirmation` · `CanIf_RxIndication` | In `CanIf_RxIndication` line 778: remove `(mode == CANIF_GET_OFFLINE)` from Rx-drop condition. Verify `CanIf_Transmit` and `CanIf_TxConfirmation` correctly retain OFFLINE suppression. | Tx is blocked in OFFLINE mode. TxConfirmation callback suppressed in OFFLINE mode. Rx indication callbacks execute in OFFLINE mode. | All three functions reviewed. Channel in OFFLINE: Tx returns `E_NOT_OK`; TxConfirmation callback not called; RxIndication dispatches to upper layer. |

#### Combined Scenario — Aggregated Impact Summary

| CanIf.c Function | Contributing Requirement(s) | Change Type | Code Modified? |
|:---|:---|:---:|:---:|
| `CanIf_SetControllerMode` | SWS_CANIF_00308 | Functional | YES |
| `CanIf_Transmit` | SWS_CANIF_00073 | Cross-Depend | Reviewed / Confirmed |
| `CanIf_TxConfirmation` | SWS_CANIF_00073 | Cross-Depend | Reviewed / Confirmed |
| `CanIf_RxIndication` | SWS_CANIF_00026, SWS_CANIF_00423, SWS_CANIF_00073 | NF + Cosmetic + XD | YES (NF+XD) / NO (Cosmetic) |

> **Process Note:** `CanIf_RxIndication` is impacted by three requirement changes simultaneously. The NF change (SWS_CANIF_00026) and the XD change (SWS_CANIF_00073) both require code modification. The Cosmetic change (SWS_CANIF_00423) requires no modification. All three must be tracked in the same code review for `CanIf_RxIndication` to ensure nothing is missed.

---

### TC-CANIF-SY-01 — Syntax: Missing Semicolon in `CanIf_Init()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-SY-01 |
| **Title** | Syntax defect — missing `;` on assignment statement inside `CanIf_Init()` |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00085 (initialization) |
| **Affected Function(s)** | `CanIf_Init` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 145 — `initRun` flag assignment at end of `CanIf_Init()`.<br><br>`OLD:` `CanIf_Global.initRun = TRUE;`<br>`NEW:` `CanIf_Global.initRun = TRUE` *(semicolon removed)* |
| **Expected Behavior** | **The translation unit must not compile.** The C grammar requires every expression-statement to be terminated by `;`. Removing it causes the compiler to attempt to parse the next token (`}`) as a continuation of the expression and fail with a syntax error at line 145. No object file is produced. No runtime behavior exists. |
| **Expected Compiler Output** | `CanIf.c:145:3: error: expected ';' before '}' token`<br>`make: *** [CanIf.o] Error 1` |
| **Verification Criteria** | 1. Compiler reports a syntax error at `CanIf.c` line 145. 2. No `CanIf.o` is generated. 3. Restoring the `;` produces a clean build. 4. No other file is affected. |
| **Rationale** | A missing semicolon is the most common single-character syntax defect. It is caught immediately by the compiler — it can never reach the linker or runtime. This test case establishes the baseline expectation that the build pipeline surfaces even the most trivial syntax error before any integration stage. |

---

### TC-CANIF-SY-02 — Syntax: Missing Opening Brace in `for` Loop in `CanIf_Init()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-SY-02 |
| **Title** | Syntax defect — missing `{` on `for` loop body in `CanIf_Init()` produces unmatched brace and logic change |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00864, SWS_CANIF_00085 |
| **Affected Function(s)** | `CanIf_Init` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 138 — opening brace of the channel initialization `for` loop.<br><br>`OLD:`<br>```c<br>  for (uint8 i = 0; i < CANIF_CHANNEL_CNT; i++)<br>  {<br>    CanIf_Global.channelData[i].ControllerMode = CANIF_CS_STOPPED;<br>    CanIf_Global.channelData[i].PduMode = CANIF_GET_OFFLINE;<br>    CanIf_PreInit_InitController(i, CanIf_ConfigPtr->Arc_ChannelDefaultConfIndex[i]);<br>  }<br>```<br><br>`NEW:`<br>```c<br>  for (uint8 i = 0; i < CANIF_CHANNEL_CNT; i++)<br><br>    CanIf_Global.channelData[i].ControllerMode = CANIF_CS_STOPPED;<br>    CanIf_Global.channelData[i].PduMode = CANIF_GET_OFFLINE;<br>    CanIf_PreInit_InitController(i, CanIf_ConfigPtr->Arc_ChannelDefaultConfIndex[i]);<br>  }<br>```<br>*(Opening `{` on line 138 deleted; closing `}` on line 142 kept.)* |
| **Expected Behavior** | **The translation unit must not compile.** Without `{`, the `for` loop body is a single implicit statement (`CanIf_Global.channelData[i].ControllerMode = CANIF_CS_STOPPED;`). The next two statements and the remaining `}` are now at function scope with no matching opener. Additionally, the loop variable `i` (a C99 for-init declaration) is out of scope after the loop ends, causing further errors on the two statements that reference it. |
| **Expected Compiler Output** | `CanIf.c:141:5: error: 'i' undeclared (first use in this function)`<br>`CanIf.c:142:3: error: expected declaration or statement at end of input`<br>`make: *** [CanIf.o] Error 1` |
| **Verification Criteria** | 1. Compiler reports at least two errors — `i` undeclared and unmatched `}`. 2. No `CanIf.o` produced. 3. Re-inserting the `{` restores a clean build. 4. The error messages point to lines 141–142, correctly identifying the consequence of the missing brace. |
| **Rationale** | Missing braces on multi-statement loop bodies are a classic C defect. The C compiler enforces the grammar strictly — a `for` without `{` associates with exactly one statement. This test validates that the build system detects structural syntax errors, not just missing terminators. It also demonstrates how a single deleted character can generate multiple downstream error messages. |

---

### TC-CANIF-SY-03 — Syntax: Missing `break` (Fallthrough) in Switch-Case in `CanIf_SetControllerMode()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-SY-03 |
| **Title** | Syntax defect — missing `break` in `case CANIF_CS_STARTED:` causes silent fallthrough into `case CANIF_CS_SLEEP:` |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308, SWS_CANIF_00773 |
| **Affected Function(s)** | `CanIf_SetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 269 — the `break` that terminates the `case CANIF_CS_STARTED:` block.<br><br>`OLD:`<br>```c<br>    CanIf_SetPduMode(channel, CANIF_SET_ONLINE);<br>    if (Can_SetControllerMode(canControllerId, CAN_T_START) == CAN_NOT_OK){<br>      return E_NOT_OK;<br>    }<br>    CanIf_Global.channelData[channel].ControllerMode = CANIF_CS_STARTED;<br>  }<br>  break;          // ← line 269<br><br>  case CANIF_CS_SLEEP:<br>```<br><br>`NEW:`<br>```c<br>    CanIf_SetPduMode(channel, CANIF_SET_ONLINE);<br>    if (Can_SetControllerMode(canControllerId, CAN_T_START) == CAN_NOT_OK){<br>      return E_NOT_OK;<br>    }<br>    CanIf_Global.channelData[channel].ControllerMode = CANIF_CS_STARTED;<br>  }<br>              // break removed<br><br>  case CANIF_CS_SLEEP:<br>``` |
| **Expected Behavior** | **Compiles without error. Silent runtime behavioral failure.** After successfully completing the `CANIF_CS_STARTED` transition (setting PDU mode ONLINE, calling `Can_SetControllerMode(CAN_T_START)`, updating state to `CANIF_CS_STARTED`), execution falls through into `case CANIF_CS_SLEEP:` without any branch condition. The SLEEP transition code then executes immediately: `Can_SetControllerMode(CAN_T_SLEEP)` is called and `ControllerMode` is overwritten to `CANIF_CS_SLEEP`. The controller appears to have started but is then immediately put to sleep. Every call to `CanIf_SetControllerMode(x, CANIF_CS_STARTED)` silently results in a SLEEP state. |
| **Verification Criteria** | 1. Build succeeds with zero errors (possibly one warning about implicit fallthrough, depending on compiler flags). 2. After `CanIf_SetControllerMode(ch, CANIF_CS_STARTED)` returns `E_OK`: `CanIf_GetControllerMode(ch, &m)` returns `m == CANIF_CS_SLEEP`, **not** `CANIF_CS_STARTED`. 3. `CanIf_Transmit()` on that channel fails because `csMode != CANIF_CS_STARTED`. 4. Enabling `-Wimplicit-fallthrough` compiler flag surfaces the defect at compile time. 5. Restoring the `break` fixes both the warning and the runtime failure. |
| **Rationale** | Missing `break` in a `switch-case` is one of the most insidious C defects — it compiles silently and the runtime failure is non-obvious because the function returns `E_OK` (the fallthrough does not trigger any `return E_NOT_OK` path unless `CAN_T_SLEEP` fails). The AUTOSAR state machine (Figure 32 of the CanIf SWS) is violated: the transition to STARTED is immediately overwritten by SLEEP, leaving the channel permanently unable to transmit. |

---

### TC-CANIF-SY-04 — Syntax: Wrong Input Parameters to `Can_Write()` in `CanIf_Transmit()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-SY-04 |
| **Title** | Syntax defect — `Can_Write()` called with software PDU handle instead of hardware transmit handle |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00162, SWS_CANIF_00317 |
| **Affected Function(s)** | `CanIf_Transmit` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 469 — the `Can_Write()` call inside `CanIf_Transmit()`.<br><br>`OLD:` `Can_ReturnType rVal = Can_Write(txEntry->CanIfCanTxPduHthRef->CanIfHthIdSymRef, &canPdu);`<br><br>`NEW:` `Can_ReturnType rVal = Can_Write((Can_HwHandleType)CanTxPduId, &canPdu);`<br><br>The first argument changes from `txEntry->CanIfCanTxPduHthRef->CanIfHthIdSymRef` (the correct `Can_HwHandleType` HTH resolved from the PDU configuration) to `(Can_HwHandleType)CanTxPduId` (the software L-PDU identifier cast to a hardware handle type). |
| **Expected Behavior** | **Compiles with or without warning depending on compiler settings.** At runtime, `Can_Write()` receives a completely wrong first argument: the software PDU index (e.g., `0`, `1`, `2`…) is interpreted as a CAN hardware transmit mailbox number. The CAN Driver indexes into its HTH table using this wrong value. For small PDU IDs the CAN Driver may silently write to a wrong mailbox or return `CAN_NOT_OK`. For large PDU IDs (exceeding the number of physical mailboxes) the CAN Driver may access out-of-bounds memory, producing undefined behavior — random frames on the bus, corrupted CAN Driver state, or a hard fault. |
| **Verification Criteria** | 1. Build succeeds (the explicit cast suppresses the type warning). 2. `CanIf_Transmit(0, &pdu)` passes the value `0` (not the configured HTH) to `Can_Write()`. 3. The frame is transmitted on the wrong hardware mailbox OR `Can_Write()` returns `CAN_NOT_OK` for an invalid mailbox index. 4. Any PDU ID > `(number of HTHs - 1)` causes out-of-bounds HTH table access inside the CAN Driver. 5. Restoring the original argument expression restores correct mailbox selection. |
| **Rationale** | `CanIf_Transmit()` is the sole path from upper layers to the CAN bus. Passing a wrong first argument to `Can_Write()` breaks the separation-of-concerns contract between CanIf (PDU namespace) and CanDrv (hardware namespace). The explicit cast `(Can_HwHandleType)` silences the compiler, making this defect invisible to static analysis unless the cast is audited. This test case validates that function parameter correctness is verified at integration testing, not just by type-checking. |

---

### TC-CANIF-SY-05 — Syntax: Pointer Assignment Instead of Dereference in `CanIf_GetPduMode()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-SY-05 |
| **Title** | Syntax defect — output parameter written via pointer assignment instead of pointer dereference; caller's variable is never updated |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00230 |
| **Affected Function(s)** | `CanIf_GetPduMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 641 — the output write inside `CanIf_GetPduMode()`.<br><br>`OLD:` `*PduModePtr = CanIf_Global.channelData[channel].PduMode;`<br>`NEW:` ` PduModePtr = &CanIf_Global.channelData[channel].PduMode;`<br><br>The `*` (dereference operator, writing through the pointer) is replaced by making `PduModePtr` itself point to the global field. The local copy of the pointer is updated; the caller's variable is never touched. |
| **Expected Behavior** | **Compiles with a warning only (`-Wall`).** At runtime, `CanIf_GetPduMode()` returns `E_OK` as before, but the caller's `PduModePtr` variable retains whatever value it held before the call (uninitialized garbage or a previous stale value). Every function that relies on `CanIf_GetPduMode()` for a mode guard reads the wrong mode:<br>• `CanIf_Transmit()` (line 455): `pduMode` is never written → mode check may allow transmission on OFFLINE channels or block it on ONLINE ones.<br>• `CanIf_RxIndication()` (line 776): `mode` is never written → Rx frames may be incorrectly dropped or forwarded based on stale mode data.<br>The function signature and return code give no indication of the failure. |
| **Expected Compiler Output** | `CanIf.c:641:16: warning: value computed is not used [-Wunused-value]`<br>*(or `-Wunused-but-set-variable` depending on compiler version — compiles successfully)* |
| **Verification Criteria** | 1. Build succeeds (only a warning, not an error). 2. After `CanIf_SetPduMode(ch, CANIF_SET_OFFLINE)`: calling `CanIf_GetPduMode(ch, &mode)` returns `E_OK` but `mode` retains its pre-call value. 3. `CanIf_Transmit()` on a channel that was set OFFLINE no longer reliably blocks — it reads the wrong PDU mode. 4. Enabling `-Werror=unused-value` promotes the warning to an error and surfaces the defect at compile time. 5. Restoring `*PduModePtr =` (dereference) fixes the silent data corruption. |
| **Rationale** | This is one of the most subtle pointer defects in C: `PduModePtr = &x` (pointer rebind) looks almost identical to `*PduModePtr = x` (write through pointer) at a glance. The compiler allows it — `PduModePtr` is an assignable local — and only a warning is issued. The defect silently breaks every caller that relies on the output parameter. In AUTOSAR CanIf, this one-character change (`*` → space) makes the PDU channel mode control system completely unreliable without any error propagation signal. |

---

### TC-CANIF-SY-06 — Syntax: Wrong Return Value in `CanIf_GetControllerMode()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-SY-06 |
| **Title** | Syntax defect — `CanIf_GetControllerMode()` always returns `E_NOT_OK`; cascading failure blocks all transmissions |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00229 |
| **Affected Function(s)** | `CanIf_GetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 334 — the success return at the end of `CanIf_GetControllerMode()`.<br><br>`OLD:` `return E_OK;`<br>`NEW:` `return E_NOT_OK;` |
| **Expected Behavior** | **Compiles without error or warning.** At runtime, `CanIf_GetControllerMode()` always reports failure regardless of the actual controller state or validity of input parameters. This cascades to every caller:<br><br>• **`CanIf_Transmit()` (line 446):** `if (CanIf_GetControllerMode(channel, &csMode) == E_NOT_OK){ return E_NOT_OK; }` → every transmit attempt is rejected before reaching `Can_Write()`. The CAN bus receives no frames from this ECU.<br>• **`CanIf_InitController()` (line 166):** `if (CanIf_GetControllerMode(channel, &mode) == E_OK)` → the condition is always false; the controller mode validation and `CANIF_CS_STOPPED` pre-condition check are entirely bypassed at initialization time.<br><br>The function still writes `*ControllerModePtr` correctly (before the return), so the output parameter is valid — but no caller trusts it because the return code signals failure. |
| **Verification Criteria** | 1. Build succeeds with zero warnings. 2. `CanIf_GetControllerMode(0, &m)` returns `E_NOT_OK` for every valid ControllerId. 3. `CanIf_Transmit()` returns `E_NOT_OK` immediately for any PDU on any channel. 4. `CanIf_InitController()` skips its pre-condition mode check, potentially initializing a controller that is in STARTED state without stopping it first. 5. Restoring `return E_OK;` re-enables all downstream behavior. |
| **Rationale** | Returning a wrong status code is a one-token change that compiles silently and produces a complete functional failure: the entire CAN transmit path is blocked. This is more dangerous than a compile error because the ECU boots normally, passes basic startup checks, and only fails under operational load when frames should be sent. The defect is also difficult to diagnose because the symptom (`CanIf_Transmit()` returns `E_NOT_OK`) is several call-stack frames away from the root cause. |

---

### TC-CANIF-SY-07 — Syntax: Call to Non-Defined Function in `CanIf_RxIndication()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-SY-07 |
| **Title** | Syntax defect — call to non-existent function `CanIf_Arc_LogFrame()` causes linker error in `CanIf_RxIndication()` |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00389 (Rx processing pipeline) |
| **Affected Function(s)** | `CanIf_RxIndication` |
| **Mandatory Code Modification** | **File:** `CanIf.c` — insert one line immediately before line 790 (the `entry` pointer initialization at the start of the Rx PDU search loop).<br><br>`OLD:`<br>```c<br>  const CanIf_RxPduConfigType *entry = CanIf_ConfigPtr->InitConfig->CanIfRxPduConfigPtr;<br>```<br><br>`NEW:`<br>```c<br>  CanIf_Arc_LogFrame(Hrh, CanId, CanDlc);   /* log every incoming frame */<br>  const CanIf_RxPduConfigType *entry = CanIf_ConfigPtr->InitConfig->CanIfRxPduConfigPtr;<br>```<br><br>`CanIf_Arc_LogFrame()` has no declaration in any header and no definition in any translation unit in the OpenSAR codebase. |
| **Expected Behavior** | **Compiles (with implicit-function-declaration warning in C89; error in C99/C11). Fails at link time.** In C99 and later (which OpenSAR targets), calling an undeclared function is a compile-time error. In older dialects a warning is issued and a call is emitted; the linker then fails because the symbol `CanIf_Arc_LogFrame` is undefined. Either way, no executable is produced. |
| **Expected Build Output** | *C99 compiler:*<br>`CanIf.c:790:3: error: implicit declaration of function 'CanIf_Arc_LogFrame' [-Werror=implicit-function-declaration]`<br><br>*Linker (if compiler permits the call):*<br>`CanIf.o: undefined reference to 'CanIf_Arc_LogFrame'`<br>`collect2: error: ld returned 1 exit status`<br>`make: *** [CanIf.elf] Error 1` |
| **Verification Criteria** | 1. The build fails at the compile stage (C99) or link stage (C89) with a clear `CanIf_Arc_LogFrame` error. 2. No executable or `.elf` image is produced. 3. Removing the inserted line restores a clean build. 4. The error correctly identifies `CanIf_RxIndication()` as the call site. 5. Running `nm CanIf.o \| grep LogFrame` in a partial build confirms the undefined external symbol. |
| **Rationale** | Unlike TC-CANIF-F-05 (which replaced an existing enum constant with an undefined identifier — caught at compile time), this test case introduces an undefined *function symbol* — caught at link time when all object files are combined. This distinguishes two detection stages: (1) the compiler enforces scope and declaration rules within a single translation unit; (2) the linker enforces symbol resolution across all translation units. Both are required for a complete build pipeline validation. Calling a non-existent helper (e.g., a logging or tracing function added in a branch but not yet merged) is a realistic defect in multi-developer AUTOSAR projects. |

---

##  Test Coverage Matrix

| TC ID | Req ID(s) | Category | Affected Function(s) | Code Change? |
|:---|:---|:---:|:---|:---:|
| TC-CANIF-F-01 | SWS_CANIF_00308 | F | `CanIf_SetControllerMode` | YES |
| TC-CANIF-F-02 | SWS_CANIF_00311 | F | `CanIf_SetControllerMode` | YES |
| TC-CANIF-F-03 | SWS_CANIF_00864 | F | `CanIf_Init` | YES |
| TC-CANIF-F-04 | SWS_CANIF_00162 | F | `CanIf_Transmit` | YES |
| TC-CANIF-F-05 | SWS_CANIF_00864 | F | `CanIf_Init` | YES — build fails (undeclared identifier) |
| TC-CANIF-F-06 | SWS_CANIF_00313 | F | `CanIf_GetControllerMode` | YES — getter hardcodes `CANIF_CS_SLEEP` |
| TC-CANIF-F-07 | SWS_CANIF_00346 | F | `CanIf_GetPduMode` | YES — getter hardcodes `CANIF_GET_OFFLINE` |
| TC-CANIF-F-08 | SWS_CANIF_00308 | F | `CanIf_SetControllerMode` | YES — parameter type `uint8` → `uint16` |
| TC-CANIF-F-09 | SWS_CANIF_00026 | F | `CanIf_RxIndication` | YES — DLC check `>=` → `==` |
| TC-CANIF-F-10 | SWS_CANIF_00346 | F | `CanIf_GetPduMode` | YES — getter hardcodes `CANIF_GET_ONLINE` (3); all Tx/Rx guards bypassed |
| TC-CANIF-F-11 | SWS_CANIF_00313 | F | `CanIf_GetControllerMode` | YES — reads `PduMode` field instead of `ControllerMode`; spurious Tx when PduMode=TX_ONLINE(2) |
| TC-CANIF-NF-01 | SWS_CANIF_00085 | NF | `CanIf_Init` | YES — loop variable `uint8` → `uint32`, identical behavior |
| TC-CANIF-NF-02 | SWS_CANIF_00162 | NF | `CanIf_Transmit` | YES — VALIDATE check order swapped, identical behavior |
| TC-CANIF-C-01 | SWS_CANIF_00423 | C | `CanIf_RxIndication` | NO |
| TC-CANIF-C-02 | SWS_CANIF_00552 | C | `CanIf_RxIndication` | NO |
| TC-CANIF-XD1N-01 | SWS_CANIF_00866 | XD-1N | `CanIf_SetControllerMode`, `CanIf_ControllerBusOff` | YES (both) |
| TC-CANIF-XD1N-02 | SWS_CANIF_00073 | XD-1N | `CanIf_Transmit`, `CanIf_TxConfirmation`, `CanIf_RxIndication` | YES (RxInd) + Reviewed (Tx, TxConf) |
| TC-CANIF-XDN1-01 | SWS_CANIF_00311 + 00774 | XD-N1 | `CanIf_SetControllerMode` | YES (2 sites) |
| TC-CANIF-XDN1-02 | SWS_CANIF_00389 + 00390 + 00902 | XD-N1 | `CanIf_RxIndication` | YES (3 sites) |
| TC-CANIF-CB-01 | 00308 + 00026 + 00423 + 00073 | CB | `CanIf_SetControllerMode`, `CanIf_Transmit`, `CanIf_TxConfirmation`, `CanIf_RxIndication` | YES (F+NF+XD) / NO (C) |
| TC-CANIF-SY-01 | SWS_CANIF_00085 | SY | `CanIf_Init` | YES — compile error (missing `;`) |
| TC-CANIF-SY-02 | SWS_CANIF_00864 + 00085 | SY | `CanIf_Init` | YES — compile error (missing `{`, unmatched `}`) |
| TC-CANIF-SY-03 | SWS_CANIF_00308 + 00773 | SY | `CanIf_SetControllerMode` | YES — compiles, silent fallthrough into SLEEP case |
| TC-CANIF-SY-04 | SWS_CANIF_00162 + 00317 | SY | `CanIf_Transmit` | YES — compiles, wrong HTH passed to `Can_Write()` |
| TC-CANIF-SY-05 | SWS_CANIF_00230 | SY | `CanIf_GetPduMode` | YES — compiles (warning), caller's output var never written |
| TC-CANIF-SY-06 | SWS_CANIF_00229 | SY | `CanIf_GetControllerMode` | YES — compiles, all Tx permanently blocked |
| TC-CANIF-SY-07 | SWS_CANIF_00389 | SY | `CanIf_RxIndication` | YES — linker error (undefined `CanIf_Arc_LogFrame`) |