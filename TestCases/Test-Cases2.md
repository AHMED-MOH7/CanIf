## Test Cases — Refined Set

---

## Section 1 — Getter Return Value (GV)

*All three tests target `CanIf_GetControllerMode(uint8 Controller, CanIf_ControllerModeType *ControllerModePtr)`.
The "return value" is the value written to the output pointer `*ControllerModePtr` — the state the function reports to every caller.*

---

### TC-2-GV-01 — Getter Value: `CanIf_GetControllerMode()` Always Reports `CANIF_CS_STARTED` — All Safety Guards Bypassed

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-GV-01 |
| **Title** | Getter value change — `CanIf_GetControllerMode()` hardcodes `CANIF_CS_STARTED`; every transmit-path controller-mode guard is permanently bypassed |
| **Category** | Getter Value (GV) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Requirement — Original** | *"The service CanIf_GetControllerMode() shall return the current mode of the CAN controller requested by parameter ControllerId."* |
| **Requirement — Modified** | *"The service CanIf_GetControllerMode() shall always report the controller mode as CANIF_CS_STARTED so that the transmit path appears permanently active to all callers."* |
| **Affected Function(s)** | `CanIf_GetControllerMode` (primary) · `CanIf_Transmit` (cascading) · `CanIf_InitController` (cascading) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 332 — output parameter assignment.<br><br>`OLD:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;`<br>`NEW:` `*ControllerModePtr = CANIF_CS_STARTED;`<br><br>The actual stored state is no longer read. A hardcoded `CANIF_CS_STARTED` (integer value **2**) is written to the caller's output variable on every valid call, for every channel. |
| **Expected Behavior — Transmit path** | `CanIf_Transmit()` (lines 446–451) reads `csMode` via `CanIf_GetControllerMode()` → always receives `CANIF_CS_STARTED` (2). Guard check:<br>`csMode != CANIF_CS_STARTED` = `2 != 2` = **FALSE** → guard **never** blocks → `CanIf_Transmit()` proceeds past the controller-mode check for every channel regardless of actual hardware state. A channel in SLEEP or STOPPED state will have its frames forwarded to `Can_Write()`, which returns `CAN_NOT_OK` from the driver (hardware not active) — frames lost silently, no error propagated. |
| **Expected Behavior — Init path** | `CanIf_InitController()` (line 166–170) reads the mode via `CanIf_GetControllerMode()` → always receives `CANIF_CS_STARTED`. The check `if (mode == CANIF_CS_STARTED)` is always TRUE → `CanIf_SetControllerMode(channel, CANIF_CS_STOPPED)` is always called before re-initialization, even for a channel already STOPPED or SLEEPING. This causes unnecessary STOP commands to the CAN driver on every init call. |
| **Verification Criteria** | 1. Call `CanIf_SetControllerMode(0, CANIF_CS_STOPPED)` → returns `E_OK`. 2. Call `CanIf_GetControllerMode(0, &m)` → returns `E_OK` but `m == CANIF_CS_STARTED`, **not** `CANIF_CS_STOPPED`. 3. Call `CanIf_Transmit(0, &pdu)` → the controller-mode guard at line 450 does **not** block → `Can_Write()` is called with the frame. 4. CAN bus monitor shows no frame transmitted (hardware is STOPPED). 5. `CanIf_InitController(0, 0)` calls `CanIf_SetControllerMode(0, CANIF_CS_STOPPED)` even though controller was already STOPPED. 6. Restoring `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;` re-enables correct guard behavior. |
| **AUTOSAR Rationale** | `CANIF_CS_STARTED` (2) is the only value for which `CanIf_Transmit()`'s guard `csMode != CANIF_CS_STARTED` evaluates FALSE, allowing the call to pass. Hardcoding it permanently disables the only controller-mode safety barrier in `CanIf_Transmit()`. Unlike hardcoding SLEEP or STOPPED (which visibly block all transmission), this defect makes the system *appear* operational — `CanIf_Transmit()` returns `E_NOT_OK` only after `Can_Write()` fails, making the root cause invisible at the CanIf layer. |

---

### TC-2-GV-02 — Getter Value: `CanIf_GetControllerMode()` Always Reports `CANIF_CS_STOPPED` — All Transmissions Silently Blocked

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-GV-02 |
| **Title** | Getter value change — `CanIf_GetControllerMode()` hardcodes `CANIF_CS_STOPPED`; every transmit attempt returns `E_NOT_OK` regardless of actual controller state |
| **Category** | Getter Value (GV) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Requirement — Original** | *"The service CanIf_GetControllerMode() shall return the current mode of the CAN controller requested by parameter ControllerId."* |
| **Requirement — Modified** | *"The service CanIf_GetControllerMode() shall always report the controller mode as CANIF_CS_STOPPED to prevent accidental transmission before explicit start commands."* |
| **Affected Function(s)** | `CanIf_GetControllerMode` (primary) · `CanIf_Transmit` (cascading) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 332.<br><br>`OLD:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;`<br>`NEW:` `*ControllerModePtr = CANIF_CS_STOPPED;`<br><br>The stored state is no longer read. A hardcoded `CANIF_CS_STOPPED` (integer value **1**) is written on every call. |
| **Expected Behavior** | Every call to `CanIf_GetControllerMode(channelId, &m)` returns `E_OK` but sets `m = CANIF_CS_STOPPED`, even after a successful `CanIf_SetControllerMode(channelId, CANIF_CS_STARTED)`. This cascades to `CanIf_Transmit()` (lines 450–451): `csMode (1) != CANIF_CS_STARTED (2)` → TRUE → `return E_NOT_OK`. All CAN frame transmission from this ECU is permanently blocked. The system boots, CanSM completes startup, COM attempts transmission — every `CanIf_Transmit()` call silently returns `E_NOT_OK`. No DET error is raised; the failure appears as a communication timeout at higher layers. |
| **Verification Criteria** | 1. Call `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` → returns `E_OK`. 2. Call `CanIf_GetControllerMode(0, &m)` → `m == CANIF_CS_STOPPED`, **not** `CANIF_CS_STARTED`. 3. `CanIf_Transmit(0, &pdu)` → returns `E_NOT_OK` at line 451; `Can_Write()` is **never called**. 4. No DET error is reported — the controller-mode guard fails silently. 5. Restoring the correct field read re-enables transmission. |
| **Contrast with TC-2-GV-01** | TC-2-GV-01 hardcodes `CANIF_CS_STARTED` → guard **always passes**, frames reach a stopped driver. TC-2-GV-02 hardcodes `CANIF_CS_STOPPED` → guard **always blocks**, no frames ever reach the driver. GV-01 produces silent hardware-level drops; GV-02 produces silent CanIf-level drops with no error code in either case. |
| **AUTOSAR Rationale** | `CANIF_CS_STOPPED` (1) causes `csMode != CANIF_CS_STARTED` to always be TRUE, permanently blocking the transmit path. The failure mode is distinct from GV-01: `Can_Write()` is never called, so no hardware-side failure indication is produced. COM and PduR see `E_NOT_OK` from every `CanIf_Transmit()` call and begin retransmission queuing, eventually exhausting their buffers. No DET log points to the getter defect. |

---

### TC-2-GV-03 — Getter Value: `CanIf_GetControllerMode()` Always Reports `CANIF_CS_UNINIT` — Transmit Blocked and Init Pre-Condition Check Corrupted

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-GV-03 |
| **Title** | Getter value change — `CanIf_GetControllerMode()` hardcodes `CANIF_CS_UNINIT`; transmit blocked and `CanIf_InitController()` pre-condition check always evaluates false |
| **Category** | Getter Value (GV) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Requirement — Original** | *"The service CanIf_GetControllerMode() shall return the current mode of the CAN controller requested by parameter ControllerId."* |
| **Requirement — Modified** | *"The service CanIf_GetControllerMode() shall always report the controller mode as CANIF_CS_UNINIT."* |
| **Affected Function(s)** | `CanIf_GetControllerMode` (primary) · `CanIf_Transmit` (cascading — Tx blocked) · `CanIf_InitController` (cascading — pre-check bypassed) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 332.<br><br>`OLD:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;`<br>`NEW:` `*ControllerModePtr = CANIF_CS_UNINIT;`<br><br>A hardcoded `CANIF_CS_UNINIT` (integer value **0**) is written on every valid call. |
| **Expected Behavior — Transmit path** | `CanIf_Transmit()` reads `csMode` → `CANIF_CS_UNINIT` (0). Guard `csMode (0) != CANIF_CS_STARTED (2)` → TRUE → returns `E_NOT_OK`. All transmissions blocked — identical observable effect to GV-02, but the reported mode value carries different semantic weight: UNINIT implies the module was never initialized. |
| **Expected Behavior — InitController path** | `CanIf_InitController()` (line 166–170) calls `CanIf_GetControllerMode(channel, &mode)` → `mode = CANIF_CS_UNINIT`. The check `if (mode == CANIF_CS_STARTED)` → `UNINIT (0) == STARTED (2)` → **FALSE** → the STARTED→STOPPED pre-condition stop command is **never issued**, even when the controller is actually STARTED. Re-initializing a running controller without first stopping it violates the AUTOSAR initialization sequence and may cause the CAN hardware to enter an undefined state. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` → `E_OK`. 2. `CanIf_GetControllerMode(0, &m)` → `E_OK` but `m == CANIF_CS_UNINIT`. 3. `CanIf_Transmit(0, &pdu)` → `E_NOT_OK` (guard blocks at line 451). 4. Call `CanIf_InitController(0, 0)` while controller is STARTED → `CanIf_SetControllerMode(0, CANIF_CS_STOPPED)` is **NOT** called before re-init (because mode check returns UNINIT, not STARTED). 5. Restoring the correct field read fixes both the transmit block and the init pre-condition. |
| **Contrast with TC-2-GV-01 and TC-2-GV-02** | GV-01 (STARTED): TX guard bypassed. GV-02 (STOPPED): TX blocked, InitController stop-check fires unconditionally. GV-03 (UNINIT): TX blocked AND InitController stop-check never fires. Each hardcoded value produces a qualitatively different failure mode in the same two downstream callers. |
| **AUTOSAR Rationale** | `CANIF_CS_UNINIT` is the reset state — returned only before `CanIf_Init()` is called. After module initialization, no channel should ever report UNINIT. Returning it post-init confuses the entire lifecycle management layer: CanSM, CanNm, and diagnostics modules use controller mode to gate their own transitions. All of them would stall waiting for a STARTED indication that can never come. The secondary defect in `CanIf_InitController()` (skipping the stop-before-reinit) is a safety hazard that only manifests during run-time reconfigurations and has no explicit error code. |

---

## Section 2 — Syntax Errors (SY)

---

### TC-2-SY-01 — Syntax: Missing Semicolon on Output Assignment in `CanIf_GetControllerMode()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-SY-01 |
| **Title** | Syntax defect — missing `;` on the `*ControllerModePtr` assignment at line 332 of `CanIf_GetControllerMode()` |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Affected Function(s)** | `CanIf_GetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 332.<br><br>`OLD:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;`<br>`NEW:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode`<br><br>*(Semicolon removed from end of statement.)* |
| **Expected Behavior** | **The translation unit must not compile.** The C grammar requires every expression-statement to end with `;`. Without it, the compiler attempts to parse `return E_OK;` (line 334) as a continuation of the assignment expression and fails. No object file is produced. |
| **Expected Compiler Output** | `CanIf.c:333:3: error: expected ';' before 'return'`<br>`make: *** [CanIf.o] Error 1` |
| **Verification Criteria** | 1. Compiler reports a syntax error referencing line 332 or 333 of `CanIf.c`. 2. No `CanIf.o` object file is generated. 3. No other source file is affected. 4. Restoring the `;` produces a clean build with zero errors. |
| **Rationale** | A missing semicolon on a single-line assignment is the simplest possible C syntax defect. It is caught before any linking or runtime stage. This test establishes the baseline expectation that the build pipeline surfaces single-character omissions before integration. |

---

### TC-2-SY-02 — Syntax: Missing Dereference Operator in `CanIf_GetControllerMode()` — Output Parameter Never Written

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-SY-02 |
| **Title** | Syntax defect — `*ControllerModePtr = ...` changed to `ControllerModePtr = &...`; caller's output variable is never updated, all mode reads return stale or garbage data |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313, SWS_CANIF_00229 |
| **Affected Function(s)** | `CanIf_GetControllerMode` (primary) · `CanIf_Transmit` (cascading) · `CanIf_InitController` (cascading) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 332.<br><br>`OLD:` `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;`<br>`NEW:` ` ControllerModePtr = &CanIf_Global.channelData[channel].ControllerMode;`<br><br>The `*` dereference operator is removed. The local copy of the pointer `ControllerModePtr` is re-pointed to the global field, but the **caller's variable** (the lvalue passed by address) is never touched. |
| **Expected Behavior** | **Compiles with a warning only.** At runtime, `CanIf_GetControllerMode()` returns `E_OK`, but the caller's `*ControllerModePtr` retains whatever value it held before the call — uninitialized garbage or a prior stale mode value. This causes every downstream consumer to make mode decisions based on wrong data:<br><br>• **`CanIf_Transmit()` (line 446–451):** `csMode` is never written → guard `csMode != CANIF_CS_STARTED` may randomly pass or block depending on stack content. Behavior is non-deterministic and not reproducible between builds or optimization levels.<br>• **`CanIf_InitController()` (line 166):** `mode` is never written → the STARTED pre-condition check is based on an uninitialized local → may skip the mandatory stop command or issue it spuriously. |
| **Expected Compiler Output** | `CanIf.c:332:20: warning: value computed is not used [-Wunused-value]`<br>*(Compiles successfully; only a warning. Enabling `-Werror=unused-value` promotes this to a build error.)* |
| **Verification Criteria** | 1. Build succeeds with at most one warning. 2. After calling `CanIf_SetControllerMode(0, CANIF_CS_STARTED)`, call `CanIf_GetControllerMode(0, &m)` → returns `E_OK` but `m` retains its pre-call value. 3. `CanIf_Transmit()` behavior becomes non-deterministic — on some builds it passes the guard, on others it blocks, with no code change between runs. 4. Enabling `-Werror=unused-value` converts the warning to a compile error. 5. Restoring `*ControllerModePtr =` (dereference) fixes the output write and all downstream consumers. |
| **Rationale** | `ControllerModePtr = &x` (rebind the local pointer) and `*ControllerModePtr = x` (write through the pointer) look nearly identical in source — the difference is a single `*` character. The compiler accepts the rebind because `ControllerModePtr` is an assignable local. The defect is silent at the function boundary: the return code is `E_OK`, the function completes normally, and only the output value is wrong. In AUTOSAR CanIf, this makes the entire controller-mode lifecycle — startup, shutdown, BusOff recovery — non-deterministic. |

---

### TC-2-SY-03 — Syntax: Missing `break` in `CANIF_CS_STARTED` Case of `CanIf_SetControllerMode()` — Silent Fallthrough Into SLEEP Transition

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-SY-03 |
| **Title** | Syntax defect — missing `break` after `CANIF_CS_STARTED` case block causes silent fallthrough into `CANIF_CS_SLEEP` case; controller starts then is immediately put to sleep |
| **Category** | Syntax (SY) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308, SWS_CANIF_00773 |
| **Affected Function(s)** | `CanIf_SetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 269 — the `break` terminating the `CANIF_CS_STARTED` outer case.<br><br>`OLD:`<br>`    CanIf_Global.channelData[channel].ControllerMode = CANIF_CS_STARTED;`<br>`  }`<br>`  break;   // ← line 269`<br><br>`case CANIF_CS_SLEEP:`<br><br>`NEW:`<br>`    CanIf_Global.channelData[channel].ControllerMode = CANIF_CS_STARTED;`<br>`  }`<br>`            // break removed`<br><br>`case CANIF_CS_SLEEP:` |
| **Expected Behavior** | **Compiles without error.** At runtime, after the `CANIF_CS_STARTED` transition completes (PDU mode set ONLINE, `Can_SetControllerMode(CAN_T_START)` called, internal state updated to `CANIF_CS_STARTED`), execution **falls through** into `case CANIF_CS_SLEEP:` (line 271). The SLEEP block then executes unconditionally: since `oldMode` at the time of fallthrough is `CANIF_CS_STARTED` (just updated at line 267), the `case CANIF_CS_STARTED:` inner branch at line 274–278 fires: `Can_SetControllerMode(canControllerId, CAN_T_STOP)` is called and `ControllerMode` is overwritten to `CANIF_CS_STOPPED`. Then `Can_SetControllerMode(CAN_T_SLEEP)` is called at line 285 and `ControllerMode` is set to `CANIF_CS_SLEEP`.<br><br>Net observable result: every call to `CanIf_SetControllerMode(x, CANIF_CS_STARTED)` returns `E_OK` but leaves the controller in `CANIF_CS_SLEEP` state. The CAN hardware transitions START → STOP → SLEEP in one call. |
| **Verification Criteria** | 1. Build succeeds (possibly one `-Wimplicit-fallthrough` warning). 2. After `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` returns `E_OK`: `CanIf_GetControllerMode(0, &m)` → `m == CANIF_CS_SLEEP`, **not** `CANIF_CS_STARTED`. 3. `CanIf_Transmit(0, &pdu)` → returns `E_NOT_OK` (controller in SLEEP, csMode != STARTED). 4. Enabling `-Wimplicit-fallthrough` compiler flag surfaces the defect at compile time. 5. Restoring `break;` at line 269 fixes both the warning and the runtime state failure. |
| **Rationale** | Missing `break` in a `switch-case` compiles silently and the runtime failure is non-obvious because the function returns `E_OK`. The AUTOSAR state machine (CanIf SWS Figure 32) defines START as a terminal transition — execution must stop there. Fallthrough into SLEEP immediately undoes the START transition. A developer testing `CanIf_SetControllerMode()` for return value only (`E_OK`) would not detect this defect; only querying the resulting mode via `CanIf_GetControllerMode()` reveals the failure. |

---

## Section 3 — Undefined Function Call (UD)

---

### TC-2-UD-01 — Undefined Call: `CanIf_GetAHMED()` Substituted for `CanIf_GetControllerMode()` in `CanIf_Transmit()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-UD-01 |
| **Title** | Undefined function call — `CanIf_GetControllerMode()` replaced by `CanIf_GetAHMED()` at the controller-mode check inside `CanIf_Transmit()` |
| **Category** | Undefined Function (UD) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00162, SWS_CANIF_00313 |
| **Affected Function(s)** | `CanIf_Transmit` (call site) · `CanIf_GetControllerMode` (intended callee — no longer called) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 446.<br><br>`OLD:` `if (CanIf_GetControllerMode(channel, &csMode) == E_NOT_OK){`<br>`NEW:` `if (CanIf_GetAHMED(channel, &csMode) == E_NOT_OK){`<br><br>`CanIf_GetAHMED` has no declaration in any header file and no definition in any translation unit of the OpenSAR codebase. |
| **Expected Behavior** | **Fails at compile time (C99/C11) or link time (C89).** In C99 and later (which OpenSAR targets with GCC `-std=c99` or `-std=c11`), calling an undeclared function is a compile-time error: `implicit declaration of function 'CanIf_GetAHMED'`. No object file is produced. In C89 mode the compiler emits a warning and emits a call; the linker then fails because the symbol `CanIf_GetAHMED` is undefined in all object files. Either way, no executable is generated. |
| **Expected Build Output** | *C99 compiler:*<br>`CanIf.c:446:7: error: implicit declaration of function 'CanIf_GetAHMED' [-Werror=implicit-function-declaration]`<br>`make: *** [CanIf.o] Error 1`<br><br>*Linker (C89 dialect):*<br>`CanIf.o: undefined reference to 'CanIf_GetAHMED'`<br>`collect2: error: ld returned 1 exit status` |
| **Verification Criteria** | 1. Build fails at compile stage (C99) or link stage (C89). 2. Error message names `CanIf_GetAHMED` as the undefined symbol. 3. No `.elf` or executable image is produced. 4. Reverting to `CanIf_GetControllerMode` restores a clean build. 5. No other source file is affected — the error is isolated to `CanIf.c`. |
| **Rationale** | Replacing a getter function call with a non-existent variant (e.g., a developer typo or a wrong branch merge) is a realistic defect in multi-module AUTOSAR projects. Unlike a wrong-but-defined function call (which compiles and fails at runtime), an undefined symbol is caught at the build stage — the earliest possible detection point. This test validates that the build pipeline correctly surfaces both compile-time and link-time symbol resolution failures. |

---

### TC-2-UD-02 — Undefined Call: `Can_ARC_SetMode()` Substituted for `Can_SetControllerMode()` in `CanIf_SetControllerMode()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-UD-02 |
| **Title** | Undefined function call — `Can_SetControllerMode()` replaced by `Can_ARC_SetMode()` at the CAN Driver START transition inside `CanIf_SetControllerMode()` |
| **Category** | Undefined Function (UD) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308 |
| **Affected Function(s)** | `CanIf_SetControllerMode` (call site) · `Can_SetControllerMode` (CAN Driver API — no longer called) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 264.<br><br>`OLD:` `if (Can_SetControllerMode(canControllerId, CAN_T_START) == CAN_NOT_OK){`<br>`NEW:` `if (Can_ARC_SetMode(canControllerId, CAN_T_START) == CAN_NOT_OK){`<br><br>`Can_ARC_SetMode` is not declared in `Can.h` or any CAN driver header in the OpenSAR codebase, and has no definition in any translation unit. |
| **Expected Behavior** | **Fails at compile time (C99) or link time (C89).** `Can_ARC_SetMode` is an undefined symbol. In C99 mode the compiler rejects the implicit declaration. In C89 mode the linker fails during the link stage when combining `CanIf.o` with the CAN Driver object files. No executable is produced. Unlike TC-2-UD-01 (which is caught within `CanIf.c` itself), this defect crosses a module boundary — the undefined symbol is expected to resolve to the CAN Driver module, making it a cross-module link error. |
| **Expected Build Output** | *C99 compiler:*<br>`CanIf.c:264:9: error: implicit declaration of function 'Can_ARC_SetMode' [-Werror=implicit-function-declaration]`<br>`make: *** [CanIf.o] Error 1`<br><br>*Linker (C89 dialect):*<br>`CanIf.o: undefined reference to 'Can_ARC_SetMode'`<br>`collect2: error: ld returned 1 exit status` |
| **Verification Criteria** | 1. Build fails. 2. Error references `Can_ARC_SetMode` as undefined. 3. No executable produced. 4. `Can_SetControllerMode` (the correct symbol) remains defined and callable in `Can.o`. 5. Reverting the change restores a clean build. |
| **Contrast with TC-2-UD-01** | TC-2-UD-01 replaces an intra-module CanIf getter call. TC-2-UD-02 replaces an inter-module call into the CAN Driver — a cross-BSW-module boundary error. Both are caught at build time, but the latter distinguishes compile-phase (declaration check) from link-phase (symbol resolution across modules). |
| **Rationale** | Wrong function names at BSW module boundaries are a frequent integration defect during AUTOSAR stack assembly — especially when two vendor modules use different naming conventions. This test validates that the linker correctly enforces inter-module symbol contracts and that no CAN mode transition is silently dropped if the target function name is wrong. |

---

## Section 4 — Cross-Dependency 1→N (XD-1N)

---

### TC-2-XD1N-01 — Cross-Depend 1→2: `CANIF_GET_TX_ONLINE` Removed as Valid Mode in Both `CanIf_Transmit` and `CanIf_TxConfirmation`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-XD1N-01 |
| **Title** | Cross-depend (1→2) — Single requirement change removes `CANIF_GET_TX_ONLINE` as an accepted mode from both `CanIf_Transmit()` and `CanIf_TxConfirmation()` |
| **Category** | Cross-Depend 1→N (XD-1N) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00073 (modified) |
| **Requirement — Original** | *"For a channel in CANIF_GET_TX_ONLINE mode: CanIf shall forward transmit requests (CanIf_Transmit) and invoke transmit confirmation callbacks (CanIf_TxConfirmation) for associated L-PDUs."* Both functions treat `CANIF_GET_TX_ONLINE` as an enabled-for-transmit state. |
| **Requirement — Modified** | *"CANIF_GET_TX_ONLINE mode is deprecated. CanIf shall no longer accept transmit requests or invoke transmit confirmation callbacks for channels in CANIF_GET_TX_ONLINE mode. These channels must be treated as OFFLINE for all Tx operations."* |
| **Affected Function(s)** | `CanIf_Transmit` **and** `CanIf_TxConfirmation` |
| **Mandatory Code Modification** | **File:** `CanIf.c`<br><br>**Modification 1 — `CanIf_Transmit` (line 459):**<br>`OLD:` `if ((pduMode != CANIF_GET_TX_ONLINE) && (pduMode != CANIF_GET_ONLINE))`<br>`NEW:` `if (pduMode != CANIF_GET_ONLINE)`<br>*(Removes `CANIF_GET_TX_ONLINE` from the accepted-modes condition. Now only `CANIF_GET_ONLINE` allows new transmit requests.)*<br><br>**Modification 2 — `CanIf_TxConfirmation` (line 754):**<br>`OLD:` `if ((mode == CANIF_GET_TX_ONLINE) \|\| (mode == CANIF_GET_ONLINE) \|\| (mode == CANIF_GET_OFFLINE_ACTIVE) \|\| (mode == CANIF_GET_OFFLINE_ACTIVE_RX_ONLINE))`<br>`NEW:` `if ((mode == CANIF_GET_ONLINE) \|\| (mode == CANIF_GET_OFFLINE_ACTIVE) \|\| (mode == CANIF_GET_OFFLINE_ACTIVE_RX_ONLINE))`<br>*(Removes `CANIF_GET_TX_ONLINE` from the confirmation-allowed modes. Channels in TX_ONLINE no longer invoke `<User_TxConfirmation>`.)* |
| **Expected Behavior** | When a channel PDU mode is `CANIF_GET_TX_ONLINE`:<br>• `CanIf_Transmit()`: previously returned `E_OK` and called `Can_Write()`. After change: `pduMode != CANIF_GET_ONLINE` → TRUE → returns `E_NOT_OK`. New Tx requests blocked.<br>• `CanIf_TxConfirmation()`: previously invoked `<User_TxConfirmation>()`. After change: `mode == CANIF_GET_TX_ONLINE` no longer matches → upper-layer callback is **not** invoked. Existing queued frames are silently confirmed without notifying COM/PduR. |
| **Verification Criteria** | 1. `CanIf_SetPduMode(0, CANIF_SET_TX_ONLINE)` → channel in `CANIF_GET_TX_ONLINE`. 2. `CanIf_Transmit(0, &pdu)` → returns `E_NOT_OK` (new behavior). 3. A simulated `CanIf_TxConfirmation(txPduId)` on that channel → `<User_TxConfirmation>()` is **not** invoked (new behavior). 4. Implementing only Modification 1 (Transmit) but not Modification 2 (TxConfirmation): new Tx blocked but old confirmations still fire — inconsistent Tx state machine. 5. Implementing only Modification 2 (TxConfirmation) but not Modification 1 (Transmit): confirmations suppressed but new Tx still allowed — channel silently transmits without the ability to confirm. 6. Both functions must be updated together to maintain a consistent OFFLINE-equivalent state for `CANIF_GET_TX_ONLINE`. |
| **AUTOSAR Rationale** | `CANIF_GET_TX_ONLINE` is referenced in two separate CanIf pipeline stages: the outgoing-frame acceptance check (`CanIf_Transmit`) and the transmit-completion callback (`CanIf_TxConfirmation`). A single requirement governing this mode therefore traces to both functions. Updating only one produces an asymmetric state where the entry gate (Transmit) and exit gate (TxConfirmation) disagree about whether the mode is active. This split causes COM/PduR to enter inconsistent PDU state machines: frames are not accepted for sending but old send-completions still arrive. |

---

## Section 5 — Cross-Dependency N→1 (XD-N1)

---

### TC-2-XDN1-01 — Cross-Depend 2→1: Two Independent Requirement Changes Both Affect `CanIf_SetControllerMode`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-XDN1-01 |
| **Title** | Cross-depend (2→1) — Two independent requirement changes both target `CanIf_SetControllerMode`: error code reclassification and wrong CAN transition constant |
| **Category** | Cross-Depend N→1 (XD-N1) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00311 **+** SWS_CANIF_00308 |
| **Requirement — Original** | *SWS_CANIF_00311:* "If ControllerId is invalid → report `CANIF_E_PARAM_CONTROLLER`."<br>*SWS_CANIF_00308:* "For `CANIF_CS_STARTED` transition → call `Can_SetControllerMode(Controller, CAN_T_START)`." |
| **Requirement — Modified** | *SWS_CANIF_00311 (modified):* "If ControllerId is invalid → report `CANIF_E_PARAM_POINTER`." *(wrong error code for a range check)*<br>*SWS_CANIF_00308 (modified):* "For `CANIF_CS_STARTED` transition → call `Can_SetControllerMode(Controller, CAN_T_STOP)`." *(wrong transition constant)* |
| **Affected Function(s)** | `CanIf_SetControllerMode` *(single function — both requirements trace here)* |
| **Mandatory Code Modification** | **File:** `CanIf.c`<br><br>**Modification 1 — SWS_CANIF_00311 (line 236):**<br>`OLD:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`NEW:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );`<br><br>**Modification 2 — SWS_CANIF_00308 (line 264):**<br>`OLD:` `if (Can_SetControllerMode(canControllerId, CAN_T_START) == CAN_NOT_OK){`<br>`NEW:` `if (Can_SetControllerMode(canControllerId, CAN_T_STOP) == CAN_NOT_OK){` |
| **Expected Behavior** | Both changes apply to a single function. Change 1 affects error reporting for invalid ControllerId only; Change 2 affects the hardware command sent during STARTED transition only. They are independent — neither change's effect depends on the other. A developer must apply both atomically.<br><br>• **Change 1 alone:** Invalid ControllerId reports `CANIF_E_PARAM_POINTER` instead of `CANIF_E_PARAM_CONTROLLER`. DET-based tools mismatch. Normal transitions unaffected.<br>• **Change 2 alone:** STARTED transition sends `CAN_T_STOP` to driver — hardware stays STOPPED while CanIf internal state becomes `CANIF_CS_STARTED`. Frames forwarded to a stopped driver, silently lost. Error code reporting unaffected. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(255, CANIF_CS_STARTED)` → DET reports `CANIF_E_PARAM_POINTER`, returns `E_NOT_OK`. 2. `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` → returns `E_OK`, `CanIf_GetControllerMode(0, &m)` → `m == CANIF_CS_STARTED`. 3. CAN bus monitor: **no frame transmitted** after `CanIf_Transmit()` (hardware was given STOP command, not START). 4. **Both changes must be verified in a single code-review record** — one change open and the other missed is a process failure. |
| **AUTOSAR Rationale** | The N→1 pattern requires the developer to recognize that two separate change requests (from different requirement owners) both target the same implementation unit. Implementing one without the other leaves the requirements document and implementation out of sync. This test validates that the engineering process identifies, batches, and atomically implements all co-located changes. |

---

### TC-2-XDN1-02 — Cross-Depend 3→1 (Complex): Three Requirement Changes in `CanIf_SetControllerMode` with Interacting Effects in the STARTED Transition Block

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-XDN1-02 |
| **Title** | Cross-depend (3→1, complex) — Three concurrent requirement changes all target `CanIf_SetControllerMode`; changes B and C both modify the `CANIF_CS_STARTED` case block and their effects compound — a partial implementation masks the other defect |
| **Category** | Cross-Depend N→1 (XD-N1) — Complex |
| **AUTOSAR Requirement ID** | SWS_CANIF_00311 **+** SWS_CANIF_00308 **+** SWS_CANIF_00864 |
| **Requirement — Original** | *SWS_CANIF_00311:* "Invalid ControllerId → `CANIF_E_PARAM_CONTROLLER`."<br>*SWS_CANIF_00308:* "STARTED transition → `Can_SetControllerMode(Controller, CAN_T_START)`."<br>*SWS_CANIF_00864 (applied to STARTED path):* "On STARTED transition, set PDU channel mode to `CANIF_SET_ONLINE`." |
| **Requirement — Modified** | *SWS_CANIF_00311 (modified):* "Invalid ControllerId → `CANIF_E_PARAM_POINTER`."<br>*SWS_CANIF_00308 (modified):* "STARTED transition → `Can_SetControllerMode(Controller, CAN_T_STOP)`." *(wrong command — hardware stays STOPPED)*<br>*SWS_CANIF_00864 (modified):* "On STARTED transition, set PDU channel mode to `CANIF_SET_OFFLINE`." *(wrong PDU mode — Tx blocked at CanIf level)* |
| **Affected Function(s)** | `CanIf_SetControllerMode` *(all three changes trace to this single function)* |
| **Mandatory Code Modification** | **File:** `CanIf.c`<br><br>**Change A — SWS_CANIF_00311 (line 236):**<br>`OLD:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`NEW:` `VALIDATE( channel < CANIF_CHANNEL_CNT, CANIF_SET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );`<br><br>**Change B — SWS_CANIF_00308 (line 264) — inside `case CANIF_CS_STARTED:` block:**<br>`OLD:` `if (Can_SetControllerMode(canControllerId, CAN_T_START) == CAN_NOT_OK){`<br>`NEW:` `if (Can_SetControllerMode(canControllerId, CAN_T_STOP) == CAN_NOT_OK){`<br><br>**Change C — SWS_CANIF_00864 (line 263) — inside `case CANIF_CS_STARTED:` block:**<br>`OLD:` `CanIf_SetPduMode(channel, CANIF_SET_ONLINE);`<br>`NEW:` `CanIf_SetPduMode(channel, CANIF_SET_OFFLINE);` |
| **Expected Behavior — All Three Changes Applied** | After `CanIf_SetControllerMode(ch, CANIF_CS_STARTED)` returns `E_OK`:<br>• **CanIf internal state:** `ControllerMode = CANIF_CS_STARTED` (line 267 unchanged).<br>• **PDU mode (Change C):** `CANIF_GET_OFFLINE`.<br>• **Hardware state (Change B):** CAN controller received `CAN_T_STOP` — hardware remains STOPPED.<br><br>`CanIf_Transmit()` check sequence:<br>1. Line 450: `csMode(STARTED) != CANIF_CS_STARTED` → FALSE → passes controller-mode guard.<br>2. Line 459: `pduMode(OFFLINE) != CANIF_GET_TX_ONLINE` AND `!= CANIF_GET_ONLINE` → TRUE → **returns `E_NOT_OK`**.<br><br>All transmissions blocked at the PDU-mode guard (Change C's effect). |
| **Interaction — Why Partial Testing is Dangerous** | **Only Change C applied (B not applied):** PDU mode = OFFLINE → `CanIf_Transmit()` returns `E_NOT_OK`. Hardware was started correctly (`CAN_T_START`). A test that only checks the return code of `CanIf_Transmit()` sees the expected `E_NOT_OK` and may **falsely pass** — not realizing the PDU mode is the cause, not a correct controller-mode issue. Change B's hardware misconfiguration is masked.<br><br>**Only Change B applied (C not applied):** PDU mode = `CANIF_GET_ONLINE` → `CanIf_Transmit()` passes both guards and calls `Can_Write()`. Hardware is STOPPED → `Can_Write()` returns `CAN_NOT_OK`. Frames silently lost. `CanIf_Transmit()` returns `E_NOT_OK` from the `Can_Write()` failure, not the mode guard. Test sees `E_NOT_OK` — appears to pass — but the failure origin and the actual system state are both wrong.<br><br>**Changes B+C together:** Both failure modes compound. A developer who implements only C and tests `CanIf_Transmit()` return value will observe the correct-looking `E_NOT_OK` and assume the implementation is complete — while Change B's wrong hardware command and Change A's wrong error code remain outstanding. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(255, CANIF_CS_STARTED)` → DET `CANIF_E_PARAM_POINTER`, `E_NOT_OK` (Change A). 2. `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` → `E_OK`; `CanIf_GetPduMode(0, &pm)` → `pm == CANIF_GET_OFFLINE` (Change C). 3. CAN bus monitor: hardware receives `CAN_T_STOP` command, **not** `CAN_T_START` (Change B). 4. `CanIf_Transmit(0, &pdu)` → `E_NOT_OK` (PDU mode guard, Change C). 5. **Critical:** Temporarily revert only Change C (restore `CANIF_SET_ONLINE`) and re-run `CanIf_Transmit()` — it now proceeds past PDU guard and calls `Can_Write()`, which returns `CAN_NOT_OK` (hardware stopped due to Change B). This exposes Change B as a hidden defect. 6. A single code-review record must list all three requirement IDs and confirm all three changes are implemented in `CanIf_SetControllerMode`. |
| **AUTOSAR Rationale** | When two requirement changes (B and C) both target the same code block (`case CANIF_CS_STARTED:` at lines 263–268), their individual effects can mask each other during incremental testing. Change C's OFFLINE PDU mode blocks `CanIf_Transmit()` at a higher guard, making Change B's hardware misconfiguration invisible unless the PDU mode guard is specifically bypassed in a test. This is the critical danger of N→1 changes in the same code block: partial implementations appear correct at the observable function boundary while leaving deeper defects undetected. |

---

## Section 6 — Functional Changes (F)

---

### TC-2-F-01 — Functional: Wrong PDU Mode Set During `CANIF_CS_STARTED` Transition — Rx Indication Permanently Silenced

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-F-01 |
| **Title** | Functional change — `CanIf_SetControllerMode()` sets PDU mode to `CANIF_SET_TX_ONLINE` instead of `CANIF_SET_ONLINE` during STARTED transition; CAN transmission works but all received frames are silently dropped |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00308, SWS_CANIF_00864 |
| **Requirement — Original** | *"When transitioning to `CANIF_CS_STARTED`, CanIf shall set the PDU channel mode to `CANIF_SET_ONLINE` (both Tx and Rx enabled)."* |
| **Requirement — Modified** | *"When transitioning to `CANIF_CS_STARTED`, CanIf shall set the PDU channel mode to `CANIF_SET_TX_ONLINE` to restrict the channel to transmit-only operation."* |
| **Affected Function(s)** | `CanIf_SetControllerMode` (primary) · `CanIf_RxIndication` (cascading — Rx blocked) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 263 — PDU mode set inside `case CANIF_CS_STARTED:` block.<br><br>`OLD:` `CanIf_SetPduMode(channel, CANIF_SET_ONLINE);`<br>`NEW:` `CanIf_SetPduMode(channel, CANIF_SET_TX_ONLINE);`<br><br>`CANIF_SET_TX_ONLINE` maps internally to `CANIF_GET_TX_ONLINE` (integer value **2**). `CANIF_SET_ONLINE` maps to `CANIF_GET_ONLINE` (integer value **3**). |
| **Expected Behavior — Transmit path** | `CanIf_Transmit()` (line 459): `pduMode = CANIF_GET_TX_ONLINE (2)`. Guard: `(2 != CANIF_GET_TX_ONLINE(2))` → FALSE → overall AND → FALSE → **guard does not block** → `Can_Write()` is called. Tx operates correctly. |
| **Expected Behavior — Receive path** | `CanIf_RxIndication()` (line 778): drop condition: `(mode == CANIF_GET_OFFLINE(0)) \|\| (mode == CANIF_GET_TX_ONLINE(2)) \|\| (mode == CANIF_GET_OFFLINE_ACTIVE(4))`. With `mode = CANIF_GET_TX_ONLINE(2)` → second clause is **TRUE** → `return;` — received frame is **silently discarded**. The upper-layer `<User_RxIndication>()` callback is **never invoked** for any received CAN frame on this channel. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(0, CANIF_CS_STARTED)` → `E_OK`. 2. `CanIf_GetPduMode(0, &pm)` → `pm == CANIF_GET_TX_ONLINE` (not CANIF_GET_ONLINE). 3. `CanIf_Transmit(0, &pdu)` → `E_OK`, `Can_Write()` called — Tx works. 4. Inject a received CAN frame → `CanIf_RxIndication()` fires → upper-layer callback is **NOT** invoked. The frame is dropped silently. 5. No DET error is raised for the dropped Rx frame. 6. Restoring `CANIF_SET_ONLINE` at line 263 re-enables both Tx and Rx. |
| **AUTOSAR Rationale** | `CANIF_GET_TX_ONLINE` and `CANIF_GET_ONLINE` differ by a single enum step, but their effects on the Rx indication path are opposite: TX_ONLINE is in the Rx-drop list (line 778); ONLINE is not. The defect allows the ECU to transmit while being completely blind to all incoming frames — a network-layer split-brain. CanNm, J1939, and diagnostic protocols that depend on Rx confirmation of their own transmitted frames will stall silently. The defect is invisible to any test that only verifies Tx return codes. |

---

### TC-2-F-02 — Functional: Wrong PDU Mode Set During `CANIF_CS_STOPPED` Transition — Rx Indication Continues on a Stopped Channel

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-F-02 |
| **Title** | Functional change — `CanIf_SetControllerMode()` sets PDU mode to `CANIF_SET_ONLINE` instead of `CANIF_SET_OFFLINE` during STOPPED transition; controller is stopped but received frames continue to be forwarded to upper layers |
| **Category** | Functional (F) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00866, SWS_CANIF_00308 |
| **Requirement — Original** | *"If CanIf_SetControllerMode(ControllerId, CAN_CS_STOPPED) is called, CanIf shall set the PDU channel mode of the corresponding channel to `CANIF_TX_OFFLINE` (or equivalent OFFLINE state)."* |
| **Requirement — Modified** | *"When transitioning to `CANIF_CS_STOPPED`, the PDU channel mode shall remain `CANIF_SET_ONLINE` to enable passive monitoring even after the controller is stopped."* |
| **Affected Function(s)** | `CanIf_SetControllerMode` (primary) · `CanIf_RxIndication` (cascading — Rx no longer dropped) |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 305 — PDU mode set inside `case CANIF_CS_STOPPED:` block.<br><br>`OLD:` `CanIf_SetPduMode(channel, CANIF_SET_OFFLINE);`<br>`NEW:` `CanIf_SetPduMode(channel, CANIF_SET_ONLINE);`<br><br>The stopped channel now has `CANIF_GET_ONLINE` as its PDU mode instead of `CANIF_GET_OFFLINE`. |
| **Expected Behavior — Transmit path** | `CanIf_Transmit()` (line 450): `csMode = CANIF_CS_STOPPED (1) != CANIF_CS_STARTED (2)` → TRUE → returns `E_NOT_OK`. **Tx is still correctly blocked** by the controller-mode guard. The wrong PDU mode does not affect the Tx path because the controller-mode guard fires first. |
| **Expected Behavior — Receive path** | `CanIf_RxIndication()` (line 778): `mode = CANIF_GET_ONLINE (3)`. Drop condition: `(3 == CANIF_GET_OFFLINE(0)) \|\| (3 == CANIF_GET_TX_ONLINE(2)) \|\| (3 == CANIF_GET_OFFLINE_ACTIVE(4))` → all FALSE → drop condition **does not fire** → received frame is forwarded to the upper-layer callback. A controller that has been explicitly stopped continues to deliver received CAN frames to COM/PduR/CanNm. |
| **Verification Criteria** | 1. `CanIf_SetControllerMode(0, CANIF_CS_STOPPED)` → `E_OK`. 2. `CanIf_GetPduMode(0, &pm)` → `pm == CANIF_GET_ONLINE` (not CANIF_GET_OFFLINE). 3. `CanIf_Transmit(0, &pdu)` → `E_NOT_OK` (controller-mode guard blocks at line 451 — Tx correctly blocked). 4. Inject a received CAN frame → `CanIf_RxIndication()` fires → upper-layer callback **IS invoked** despite channel being STOPPED. 5. No DET error for the spurious Rx dispatch. 6. Restoring `CANIF_SET_OFFLINE` at line 305 correctly blocks both Tx and Rx after STOPPED transition. |
| **AUTOSAR Rationale** | SWS_CANIF_00866 requires both Tx and Rx to be suppressed after a STOPPED transition. Setting PDU mode to ONLINE instead of OFFLINE correctly blocks Tx (because the controller-mode guard catches it first) but leaves Rx silently active. The defect is therefore invisible to any test that only exercises `CanIf_Transmit()` after a stop — only an Rx injection test reveals that the STOPPED channel is still forwarding frames. This split (Tx blocked, Rx active) violates the AUTOSAR communication shutdown safety model and can cause upper-layer state machines to receive frames they believe the channel is not yet delivering. |

---

## Section 7 — Non-Functional Changes (NF)

*Note: The following changes are rigorously verified as Non-Functional. For each, a complete proof is provided showing that observable outputs are bit-for-bit identical for all operationally defined inputs. The one edge case where behavior may differ (simultaneous double-fault) is explicitly characterized and shown to be outside the defined operational envelope.*

---

### TC-2-NF-01 — Non-Functional: Swap UNINIT and PARAM\_CONTROLLER VALIDATE Check Order in `CanIf_GetControllerMode()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-NF-01 |
| **Title** | Non-functional change — UNINIT check and PARAM\_CONTROLLER check swapped in `CanIf_GetControllerMode()`; behavior identical for all operational inputs |
| **Category** | Non-Functional (NF) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313, SWS_CANIF_00311 |
| **Affected Function(s)** | `CanIf_GetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, lines 328–329 — first two VALIDATE macros in `CanIf_GetControllerMode()`.<br><br>`OLD (original order):`<br>`  VALIDATE(CanIf_Global.initRun, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_UNINIT );`<br>`  VALIDATE(channel < CANIF_CHANNEL_CNT, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`  VALIDATE(ControllerModePtr != NULL, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );`<br><br>`NEW (swapped first two):`<br>`  VALIDATE(channel < CANIF_CHANNEL_CNT, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`  VALIDATE(CanIf_Global.initRun, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_UNINIT );`<br>`  VALIDATE(ControllerModePtr != NULL, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );`<br><br>Third check (`ControllerModePtr != NULL`) is unchanged in position and content. |
| **Proof of Non-Functional Classification** | The two swapped checks are **independent**: `CanIf_Global.initRun` (a module-global boolean) does not depend on the value of `channel`, and the range check `channel < CANIF_CHANNEL_CNT` does not depend on `initRun`. There is no data dependency or shared mutable state between them.<br><br>For all operationally defined input combinations:<br>**Case 1 — Both conditions true** (`initRun == TRUE` AND `channel < CANIF_CHANNEL_CNT`): Both checks pass in both orders → execution reaches line 332 → identical result.<br>**Case 2 — Only UNINIT fails** (`initRun == FALSE`, valid channel): Original reports `CANIF_E_UNINIT` and returns `E_NOT_OK`. New order: channel check passes first (channel valid), then `initRun` check fails → reports `CANIF_E_UNINIT` and returns `E_NOT_OK`. **Identical.**<br>**Case 3 — Only channel invalid** (valid `initRun`, `channel >= CANIF_CHANNEL_CNT`): Original: `initRun` check passes, channel check fails → `CANIF_E_PARAM_CONTROLLER`, `E_NOT_OK`. New order: channel check fails first → `CANIF_E_PARAM_CONTROLLER`, `E_NOT_OK`. **Identical.**<br>**Case 4 — Both fail simultaneously** (`initRun == FALSE` AND invalid channel): Original reports `CANIF_E_UNINIT` first (first check fails). New order reports `CANIF_E_PARAM_CONTROLLER` first (first check fails). **Different DET error code reported.** However, this scenario requires the caller to simultaneously provide an out-of-range ControllerId while the module is uninitialized — a double programming error with no defined correct handling in the AUTOSAR spec. It is not an operational scenario. |
| **Expected Behavior** | For all single-fault and no-fault inputs, `CanIf_GetControllerMode()` produces identical output values, identical return codes, and identical DET calls. The function's behavioral contract with all operational callers is 100% preserved. |
| **Verification Criteria** | 1. `CanIf_GetControllerMode(0, &m)` with `initRun == TRUE`, valid channel → result identical. 2. `CanIf_GetControllerMode(255, &m)` (invalid channel, module initialized) → `CANIF_E_PARAM_CONTROLLER`, `E_NOT_OK` — identical in both orders. 3. `CanIf_GetControllerMode(0, &m)` with `initRun == FALSE` → `CANIF_E_UNINIT`, `E_NOT_OK` — identical in both orders. 4. Full regression suite passes with zero behavioral differences for all operational test inputs. |
| **AUTOSAR Rationale** | This is a pure implementation-internal reordering of two independent guards. The AUTOSAR SWS does not specify the order in which multiple development-error checks must be evaluated — only that each check must trigger the correct DET code when its specific condition is violated. For all inputs where exactly one condition is false (the only operationally meaningful error scenarios), the outcome is identical. The change is Non-Functional because no caller can observe a behavioral difference under any defined operating condition. |

---

### TC-2-NF-02 — Non-Functional: Intermediate Boolean Variables for VALIDATE Conditions in `CanIf_GetControllerMode()`

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-NF-02 |
| **Title** | Non-functional change — three VALIDATE conditions extracted into named boolean variables before evaluation; logic and output are provably identical in all scenarios |
| **Category** | Non-Functional (NF) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Affected Function(s)** | `CanIf_GetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, lines 328–330 — three VALIDATE macros in `CanIf_GetControllerMode()`.<br><br>`OLD:`<br>`  VALIDATE(CanIf_Global.initRun, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_UNINIT );`<br>`  VALIDATE(channel < CANIF_CHANNEL_CNT, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`  VALIDATE(ControllerModePtr != NULL, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );`<br><br>`NEW:`<br>`  boolean moduleInitialized = CanIf_Global.initRun;`<br>`  boolean channelInRange    = (boolean)(channel < CANIF_CHANNEL_CNT);`<br>`  boolean ptrNotNull        = (boolean)(ControllerModePtr != NULL);`<br>`  VALIDATE(moduleInitialized, CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_UNINIT );`<br>`  VALIDATE(channelInRange,    CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_CONTROLLER );`<br>`  VALIDATE(ptrNotNull,        CANIF_GET_CONTROLLER_MODE_ID, CANIF_E_PARAM_POINTER );`<br><br>No other change in the function. |
| **Proof of Non-Functional Classification** | Each boolean temporary is evaluated immediately before the VALIDATE call that uses it. The evaluation order is preserved — `moduleInitialized` is read before `channelInRange`, which is read before `ptrNotNull` — matching the original sequential check order exactly.<br><br>`CanIf_Global.initRun` is a module-global boolean; reading it into a local temporary and passing the temporary to VALIDATE produces the same truth value as passing the expression directly. The same holds for the range comparison and the null pointer check. No intermediate state changes between the read and the VALIDATE call in a single-threaded execution model.<br><br>**Assumption:** AUTOSAR BSW functions are not preempted by tasks that modify `CanIf_Global.initRun` or `channel` between the boolean read and the VALIDATE call. This assumption holds within a single OS task or ISR category in the AUTOSAR OS model. In a strict single-threaded context the assumption is unconditionally valid. |
| **Expected Behavior** | For every input combination, the function reports the same DET error codes in the same order, returns the same `Std_ReturnType`, and writes the same value to `*ControllerModePtr`. The only implementation-internal difference is three additional boolean variables on the stack (3 bytes in most embedded C implementations). No caller-visible output changes. |
| **Verification Criteria** | 1. All 8 possible combinations of `{initRun, channelValid, ptrValid}` produce identical DET calls and return codes before and after the change. 2. `CanIf_GetControllerMode(0, &m)` with all conditions true: `m` receives the same controller mode value. 3. Stack usage increases by at most 3 bytes (3 `boolean` locals) — no functional impact. 4. Full regression suite passes with zero behavioral differences. |
| **AUTOSAR Rationale** | Extracting inline boolean expressions into named temporaries is a common code clarity refactoring. The AUTOSAR SWS specifies which checks must be performed and in which order they must be listed, but does not mandate whether the condition is evaluated inline or via a local copy. For a single-threaded execution model (which AUTOSAR BSW assumes for non-reentrant functions), both forms are semantically identical. The change is Non-Functional because no observable output — DET call, return code, output parameter value — differs under any defined input. |

---

## Section 8 — Cosmetic Changes (C)

---

### TC-2-C-01 — Cosmetic: Normative Verb Updated in GetControllerMode Requirement

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-C-01 |
| **Title** | Cosmetic change — Normative phrasing updated in SWS_CANIF_00313; behavioral intent unchanged, no code modification required |
| **Category** | Cosmetic (C) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 |
| **Requirement — Original** | *"The service CanIf_GetControllerMode() shall return the current mode of the CAN controller requested by parameter ControllerId."* |
| **Requirement — Modified** | *"The service CanIf_GetControllerMode() shall retrieve and provide the current operational mode of the CAN controller identified by parameter ControllerId to the caller."* *(Changes: "return" → "retrieve and provide"; "requested by" → "identified by"; "to the caller" added for clarity.)* |
| **Affected Function(s)** | `CanIf_GetControllerMode` *(per requirement-to-code traceability)* |
| **Mandatory Code Modification** | **NONE.** The normative intent — that the function reads the current controller mode and delivers it to the caller via the output parameter — is identical before and after the wording change. No implementation detail is added, removed, or altered by the rephrasing. |
| **Expected Behavior** | `CanIf_GetControllerMode()` continues to operate exactly as before. The VALIDATE checks, the field read at line 332, and the `return E_OK` at line 334 are all unaffected. A human engineer review must confirm the Cosmetic classification and close the change request with status **"Requirements Document Updated — No Code Change Required."** |
| **Verification Criteria** | 1. `CanIf.c` source file shows zero modifications after this requirement change. 2. A code diff between pre-change and post-change versions of `CanIf.c` shows no differences. 3. Requirements document (SWS) is updated with the new wording. 4. Engineer sign-off record confirms Cosmetic classification. 5. No re-testing of `CanIf_GetControllerMode()` is required (no code changed). |
| **AUTOSAR Rationale** | AUTOSAR releases (e.g., AR 4.0.3 → AR 4.2.2 → AR 4.4.0) routinely update normative phrasing to improve clarity without changing implementation semantics. The change from "return" to "retrieve and provide" is a stylistic preference — both describe the same contract: call → read → write output → return status. The mandatory engineer review is the critical process step because automated classification tools cannot reliably distinguish semantic changes from purely editorial ones; domain expertise is required to confirm no hidden behavioral shift. |

---

### TC-2-C-02 — Cosmetic: Code Comment Updated in `CanIf_GetControllerMode()` — No Behavioral Change

| Field | Details |
|:---|:---|
| **Test Case ID** | TC-2-C-02 |
| **Title** | Cosmetic change — Inline comment text updated on the channel variable declaration in `CanIf_GetControllerMode()`; no executable code is altered |
| **Category** | Cosmetic (C) |
| **AUTOSAR Requirement ID** | SWS_CANIF_00313 *(traceability reference only)* |
| **Affected Function(s)** | `CanIf_GetControllerMode` |
| **Mandatory Code Modification** | **File:** `CanIf.c`, line 325 — inline comment on the channel alias declaration.<br><br>`OLD:` `// We call this a CanIf channel. Hopefully makes it easier to follow.`<br>`NEW:` `// Map ControllerId to internal CanIf channel index for array access.`<br><br>The comment text is rewritten for clarity. The declaration and assignment on line 326 (`CanIf_Arc_ChannelIdType channel = (CanIf_Arc_ChannelIdType) Controller;`) are **unchanged**. |
| **Expected Behavior** | No change in any compiled output. Comments are stripped by the preprocessor before compilation. The object file `CanIf.o` produced from the modified source is byte-for-byte identical to the object file produced from the original source (given the same compiler flags and optimization level). All observable behaviors of `CanIf_GetControllerMode()` — DET calls, return codes, output parameter writes — remain identical. |
| **Verification Criteria** | 1. The compiled object file `CanIf.o` is binary-identical before and after the comment change (verifiable via `md5sum` or `diff` of object files compiled without debug symbols). 2. No change to `CanIf.h`, any configuration header, or any other `.c` file. 3. Engineer review record confirms Cosmetic classification. 4. No functional regression test suite re-run is required. |
| **AUTOSAR Rationale** | Comment-only changes are the most straightforward Cosmetic classification — comments have no effect on compiled output by definition. However, the mandatory engineer review step remains important: what appears to be a comment-only change might accidentally introduce or remove a `#ifdef` directive or a conditional compilation block embedded in commented text. The zero-diff object file check is the automated verification that confirms no accidental code change was introduced alongside the comment update. |

---
