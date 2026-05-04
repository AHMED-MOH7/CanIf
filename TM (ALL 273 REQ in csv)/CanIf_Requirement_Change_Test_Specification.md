# CanIf Software Requirement Change — Test Case Specification

> **Standard Reference:** AUTOSAR Specification of CAN Interface (CanIf) — AR 4.0.3  
> **Source File Under Test:** `CanIf.c` — ArcCore OpenSAR Implementation  
> **Document Version:** 1.0  
> **Classification:** Technical Reference — Software Verification

---

## 1. Purpose

This document specifies a set of test cases that cover all classes of requirement
changes that can occur in an AUTOSAR CanIf software component. For each test case,
the document defines the original AUTOSAR requirement, the simulated change applied
to that requirement, the affected `CanIf.c` function(s), the mandatory code
modification that must follow, and the expected behavior and verification criteria
that confirm the change was correctly implemented.

This document is a self-contained engineering reference. It does not depend on any
external tool, system, or project context.

---

## 2. Scope

- **Module:** CanIf (CAN Interface) — AUTOSAR BSW Communication Layer  
- **Implementation:** `OpenSAR/communication/CanIf/CanIf.c`  
- **Requirement Source:** `CanIf_SWS_AR403.csv` — 273 requirements  
- **Test Coverage:** 13 test cases spanning all requirement change categories

---

## 3. Change Category Definitions

| Category | Code | Definition |
|:---|:---:|:---|
| **Functional** | F | A change in behavioral logic — algorithm, control flow, called API, error code, or return value. The function body **must** change. |
| **Non-Functional** | NF | A change in the interface contract with no behavioral logic change — data type width, parameter naming, SduLength range boundary adjustment. The function signature or data types **must** change; runtime behavior for valid inputs remains identical. |
| **Cosmetic** | C | An editorial change — wording, normative verb (shall/must), or cross-reference number update. **No code change** is required. A human engineer review is still mandatory to confirm this classification. |
| **Cross-Depend 1→N** | XD-1N | One requirement change propagates to **N ≥ 2** distinct functions. All N functions **must** be updated consistently. Updating only a subset is a defect. |
| **Cross-Depend N→1** | XD-N1 | **N ≥ 2** requirement changes all propagate to the **same single function**. The function must be updated to satisfy all N changed requirements simultaneously. |
| **Combined** | CB | A realistic scenario containing simultaneous changes of multiple categories across multiple functions. All impacted functions are updated independently per their respective change type. |

---

## 4. Test Case Template — Column Definitions

Each test case is presented as a vertical attribute table with the following fields:

| Field | Description |
|:---|:---|
| **Test Case ID** | Unique identifier following the pattern `TC-CANIF-<Category>-<NN>` |
| **Title** | Short descriptive name |
| **Category** | Change category from Section 3 |
| **AUTOSAR Requirement ID** | Official SWS requirement identifier |
| **Requirement — Original** | Verbatim text from the AUTOSAR CanIf SWS |
| **Requirement — Modified** | The new text after the simulated change |
| **Affected Function(s)** | The `CanIf.c` function(s) that implement this requirement |
| **Mandatory Code Modification** | Exact `OLD → NEW` code change that must be applied in `CanIf.c` |
| **Expected Behavior** | What the function must do after the change is correctly implemented |
| **Verification Criteria** | Conditions that confirm the change was correctly applied |
| **AUTOSAR Rationale** | Why this change matters from an AUTOSAR correctness perspective |

---

## 5. Test Cases

---

### TC-CANIF-F-01 — Functional: SetControllerMode Calls Wrong CAN Driver API

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-F-01 |
| **Title** | Functional change — `CanIf_SetControllerMode()` delegates to incorrect CAN Driver service |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308 |
| **Requirement — Original** | *"The service CanIf_SetControllerMode() shall call Can_SetControllerMode(Controller, Transition) for the requested CAN controller."* |
| **Requirement — Modified** | *"The service CanIf_SetControllerMode() shall call Can_InitController(Controller, ConfigurationIndex) for every state transition of the requested CAN controller."* |
| **Affected Function(s)** | `CanIf_SetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c` — Replace every call to `Can_SetControllerMode()` inside `CanIf_SetControllerMode()` with `Can_InitController()`. Six call sites exist, each with a different transition argument (`CAN_T_STOP`, `CAN_T_START`, `CAN_T_SLEEP`, `CAN_T_WAKEUP`). All six must be updated. <br><br>**Example (one of six):**<br>`OLD:` `if (Can_SetControllerMode(canControllerId, CAN_T_START) == CAN_NOT_OK)`<br>`NEW:` `if (Can_InitController(canControllerId, configIndex) == CAN_NOT_OK)` |
| **Expected Behavior** | Every CAN controller state transition executed inside `CanIf_SetControllerMode()` (SLEEP→STOPPED, STOPPED→STARTED, STARTED→STOPPED, STOPPED→SLEEP, SLEEP→STOPPED for wakeup) must invoke the new specified CAN Driver API. The AUTOSAR state machine diagram (Figures 32–33 of the CanIf SWS) must still be fully honored — only the delegated API changes, not the transition logic. |
| **Verification Criteria** | 1. No occurrence of `Can_SetControllerMode()` remains inside `CanIf_SetControllerMode()`. 2. All six transition paths in the switch-case block call the new API. 3. Return value checking (`CAN_NOT_OK`) is preserved on each call site. 4. Controller state variable (`CanIf_Global.channelData[channel].ControllerMode`) is updated correctly after each transition. |
| **AUTOSAR Rationale** | `Can_SetControllerMode()` is the normative CanDrv state-transition service defined in SWS_Can_00017. Replacing it with `Can_InitController()` changes the CanIf–CanDrv interface contract, violates the CAN Driver SWS, and breaks all controller state transitions at runtime. This is one of the most critical functional changes possible in the CanIf layer. |

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

### TC-CANIF-NF-01 — Non-Functional: ControllerId Parameter Type Widened

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-NF-01 |
| **Title** | Non-functional change — `ControllerId` type widened from `uint8` to `uint16` |
| **Category** | Non-Functional (NF) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308 (parameter type definition) |
| **Requirement — Original** | ControllerId is typed as `uint8`, supporting a maximum of 255 CAN controllers per ECU. |
| **Requirement — Modified** | *"ControllerId shall be typed as uint16 to accommodate future ECU architectures with more than 255 CAN controllers."* |
| **Affected Function(s)** | `CanIf_SetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 226 — function signature.<br><br>`OLD:` `Std_ReturnType CanIf_SetControllerMode(uint8 Controller,`<br>`NEW:` `Std_ReturnType CanIf_SetControllerMode(uint16 Controller,`<br><br>The corresponding declaration in `CanIf.h` and any `CanIf_Cbk.h` must also be updated to match. |
| **Expected Behavior** | `CanIf_SetControllerMode()` accepts a `uint16` ControllerId. For any ControllerId value in the range `[0, CANIF_CHANNEL_CNT - 1]` the runtime behavior is **identical** to the previous implementation. The internal cast `(CanIf_Arc_ChannelIdType) Controller` and all range comparisons must remain logically equivalent. |
| **Verification Criteria** | 1. The function signature uses `uint16 Controller`. 2. All existing callers of `CanIf_SetControllerMode()` are updated to pass `uint16`. 3. The header declaration matches the implementation signature. 4. Functional regression tests pass without behavioral change for all valid ControllerId values (≤ 254 in the current configuration). 5. No implicit narrowing conversions are introduced. |
| **AUTOSAR Rationale** | This is an ABI-breaking interface change. Although runtime behavior is unchanged for valid inputs within the original `uint8` range, all compilation units that include `CanIf.h` must be recompiled. Mismatched signatures between caller and callee (e.g., if `CanIf.h` is not updated) cause undefined behavior per the C standard and stack corruption at runtime. |

---

### TC-CANIF-NF-02 — Non-Functional: DLC Acceptance Policy Changed to Exact Match

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-CANIF-NF-02 |
| **Title** | Non-functional change — Received frame DLC acceptance changes from ≥ configured to exact match |
| **Category** | Non-Functional (NF) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00026 |
| **Requirement — Original** | *"CanIf shall accept all received L-PDUs with a Data Length value equal or greater than the configured Data Length value."* |
| **Requirement — Modified** | *"CanIf shall accept received L-PDUs with a Data Length value equal to the configured Data Length value only. Frames with any other DLC shall be rejected."* |
| **Affected Function(s)** | `CanIf_RxIndication` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 824 — DLC comparison inside the `#if (CANIF_DLC_CHECK == STD_ON)` guard.<br><br>`OLD:` `if (CanDlc < entry->CanIfCanRxPduDlc)`<br>`NEW:` `if (CanDlc != entry->CanIfCanRxPduDlc)` |
| **Expected Behavior** | `CanIf_RxIndication()` must reject any received frame where `CanDlc` does not exactly equal the PDU's configured `CanIfCanRxPduDlc` value. Frames with `CanDlc > configured` are now rejected (previously they were accepted). Frames with `CanDlc < configured` continue to be rejected as before. The DET error `CANIF_E_PARAM_DLC` is reported and the function returns without dispatching to the upper layer. |
| **Verification Criteria** | 1. A frame with `CanDlc == configured` is accepted and dispatched to the upper layer. 2. A frame with `CanDlc > configured` (e.g., CAN FD padded frame) is rejected and `CANIF_E_PARAM_DLC` is reported via DET. 3. A frame with `CanDlc < configured` is rejected as before. 4. No other logic in `CanIf_RxIndication()` is changed — software filtering, upper-layer dispatch, and HRH lookup are unaffected. |
| **AUTOSAR Rationale** | The original requirement (≥ configured) follows the AUTOSAR default to accommodate CAN FD frames with padding. Changing to exact-match is a strict policy change that rejects all padded frames. This impacts interoperability with CAN FD networks where padding is mandatory. The change is classified as Non-functional because the dispatch logic itself does not change — only the acceptance window narrows. |

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
| SWS_CANIF_00308 | **Functional** | SetControllerMode must call `Can_InitController()` instead of `Can_SetControllerMode()` for every transition | `CanIf_SetControllerMode` | Replace all 6 call sites of `Can_SetControllerMode()` with `Can_InitController()` inside `CanIf_SetControllerMode()` | Every state transition (STOP / START / SLEEP / WAKEUP) calls the new API. Return-value checks preserved. State variable updated correctly. | Zero occurrences of `Can_SetControllerMode()` remain in `CanIf_SetControllerMode()`. All 6 transition paths verified. Functional regression tests pass. |
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

## 6. Test Coverage Matrix

| TC ID | Req ID(s) | Category | Affected Function(s) | Code Change? |
|:---|:---|:---:|:---|:---:|
| TC-CANIF-F-01 | SWS_CANIF_00308 | F | `CanIf_SetControllerMode` | YES |
| TC-CANIF-F-02 | SWS_CANIF_00311 | F | `CanIf_SetControllerMode` | YES |
| TC-CANIF-F-03 | SWS_CANIF_00864 | F | `CanIf_Init` | YES |
| TC-CANIF-F-04 | SWS_CANIF_00162 | F | `CanIf_Transmit` | YES |
| TC-CANIF-NF-01 | SWS_CANIF_00308 | NF | `CanIf_SetControllerMode` | YES (signature) |
| TC-CANIF-NF-02 | SWS_CANIF_00026 | NF | `CanIf_RxIndication` | YES |
| TC-CANIF-C-01 | SWS_CANIF_00423 | C | `CanIf_RxIndication` | NO |
| TC-CANIF-C-02 | SWS_CANIF_00552 | C | `CanIf_RxIndication` | NO |
| TC-CANIF-XD1N-01 | SWS_CANIF_00866 | XD-1N | `CanIf_SetControllerMode`, `CanIf_ControllerBusOff` | YES (both) |
| TC-CANIF-XD1N-02 | SWS_CANIF_00073 | XD-1N | `CanIf_Transmit`, `CanIf_TxConfirmation`, `CanIf_RxIndication` | YES (RxInd) + Reviewed (Tx, TxConf) |
| TC-CANIF-XDN1-01 | SWS_CANIF_00311 + 00774 | XD-N1 | `CanIf_SetControllerMode` | YES (2 sites) |
| TC-CANIF-XDN1-02 | SWS_CANIF_00389 + 00390 + 00902 | XD-N1 | `CanIf_RxIndication` | YES (3 sites) |
| TC-CANIF-CB-01 | 00308 + 00026 + 00423 + 00073 | CB | `CanIf_SetControllerMode`, `CanIf_Transmit`, `CanIf_TxConfirmation`, `CanIf_RxIndication` | YES (F+NF+XD) / NO (C) |

### Function Coverage Summary

| `CanIf.c` Function | Covered By |
|:---|:---|
| `CanIf_Init` | TC-CANIF-F-03 |
| `CanIf_SetControllerMode` | TC-CANIF-F-01, TC-CANIF-F-02, TC-CANIF-NF-01, TC-CANIF-XD1N-01, TC-CANIF-XDN1-01, TC-CANIF-CB-01 |
| `CanIf_Transmit` | TC-CANIF-F-04, TC-CANIF-XD1N-02, TC-CANIF-CB-01 |
| `CanIf_TxConfirmation` | TC-CANIF-XD1N-02, TC-CANIF-CB-01 |
| `CanIf_RxIndication` | TC-CANIF-NF-02, TC-CANIF-C-01, TC-CANIF-C-02, TC-CANIF-XD1N-02, TC-CANIF-XDN1-02, TC-CANIF-CB-01 |
| `CanIf_ControllerBusOff` | TC-CANIF-XD1N-01 |

---

## 7. Key Engineering Rules Derived from This Specification

| # | Rule |
|:---:|:---|
| 1 | A **Functional** change always requires a code modification in the function body. There are no exceptions. |
| 2 | A **Non-functional** change modifies the interface or data types. The function body logic may be identical, but the compilation unit interface changes. All callers must be updated. |
| 3 | A **Cosmetic** change requires an engineer sign-off confirming no code action is needed. Silent dismissal without a review record is a process violation. |
| 4 | A **Cross-depend 1→N** change requires all N functions to be updated **atomically**. Updating a subset and deferring the rest to a later sprint is a defect. |
| 5 | A **Cross-depend N→1** change requires all N requirement changes to be implemented in the **same function** in a single update. The implementation must be verified against all N requirements simultaneously. |
| 6 | When a function is impacted by requirements of **multiple categories** simultaneously (as in TC-CANIF-CB-01), each category's rules apply independently. Cosmetic changes do not justify skipping code changes required by Functional or Non-functional changes in the same function. |
| 7 | A change in any requirement that maps to a function must trigger a review of **all other requirements** that also map to that function, to ensure the change does not conflict with existing implementations. |

---

*End of Document*
