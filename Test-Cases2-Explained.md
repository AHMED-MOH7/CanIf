# Test Cases — Plain-English Explanations

This file walks you through each of the 14 test cases in `TestCases/Test-Cases2.md` in plain language. For each test:

1. **What the original requirement says** — the AUTOSAR rule, in normal English.
2. **What the code does today** — what `CanIf.c` actually does right now.
3. **What the requirement change is** — what's new in the modified spec.
4. **What the change means** — why we'd want this change in the real world.
5. **How the code has to change** — what gets edited and where.

---

## Section 1 — Getter Return Value (GV)

### TC-2-GV-01 — Requirement-driven: GetPduMode must refuse to answer if controller isn't STARTED

**Original requirement (SWS_CANIF_00346):** If someone calls `CanIf_GetPduMode()` with a bad ControllerId (e.g., a number bigger than the number of channels), CanIf must report a DET error code `CANIF_E_PARAM_CONTROLLERID`. That's the whole rule today — it only protects against bad input parameters.

**What the code does today:** `CanIf_GetPduMode()` validates the ControllerId, then unconditionally copies the stored PDU mode value into the output pointer and returns `E_OK`. It doesn't care whether the controller is started, stopped, sleeping, or anything else — it just hands back whatever value is in memory.

**The requirement change:** We're adding a new rule on top: even if the ControllerId is valid, if the controller is not in `CAN_CS_STARTED`, the getter must return `E_NOT_OK` and not write anything to the output pointer.

**What this means:** Upper layers (COM, PduR, CanNm) ask "what's the PDU mode of channel 3?" so they can decide whether to send frames. If channel 3's controller is stopped or sleeping, the PDU mode value is meaningless garbage — but today the getter hands it back anyway, and upper layers can make wrong decisions. The new rule says: "don't give them a number they can't use; tell them it's unavailable."

**How the code changes:** Add an early-return check inside `CanIf_GetPduMode()` before line 641. If the controller mode isn't STARTED, return `E_NOT_OK` immediately. Don't touch `*PduModePtr`.

---

### TC-2-GV-02 — Code-defect injection: GetControllerMode lies and always says STARTED

**Original requirement (SWS_CANIF_00317):** `CanIf_Transmit()` must refuse to send a frame if the controller isn't in `CAN_CS_STARTED` state. This is the runtime safety guard that stops you from transmitting on a stopped or sleeping controller.

**What the code does today:** `CanIf_Transmit()` calls `CanIf_GetControllerMode()` to find out the controller's real state, then checks `if (csMode != CANIF_CS_STARTED) return E_NOT_OK;`. This guard works as long as the getter tells the truth.

**The "change":** No requirement change. We're intentionally breaking the getter as a defect-injection test. We hardcode `*ControllerModePtr = CANIF_CS_STARTED;` so the getter always lies and says "the controller is STARTED" regardless of reality.

**What this means:** Once the getter lies, the transmit guard is permanently bypassed. Every transmit attempt passes the check, calls `Can_Write()`, and the frame gets silently lost when the hardware isn't actually started. This test exists to confirm that end-to-end testing catches this kind of hidden getter corruption — it's a defect that would be invisible to anyone who only unit-tests the getter in isolation.

**How the code changes:** One line in `CanIf_GetControllerMode()` at line 332. Replace the real assignment with a hardcoded `CANIF_CS_STARTED`.

---

## Section 2 — Undefined Function Call (UD)

### TC-2-UD-01 — SetControllerMode must call a timeout-bounded driver API

**Original requirement (SWS_CANIF_00308):** When you change controller mode, CanIf must call `Can_SetControllerMode(Controller, Transition)` on the CAN driver. The driver doesn't have to respond within any specific time.

**What the code does today:** Every controller mode change inside `CanIf_SetControllerMode()` calls `Can_SetControllerMode(...)`. If the driver is slow or non-responsive, CanIf has no protection — it just waits for `Can_SetControllerMode()` to return.

**The requirement change:** Spec now demands a new function: `Can_SetControllerModeExt(Controller, Transition, Timeout_us)`. The extended API guarantees the driver will return `CAN_NOT_OK` if the mode change doesn't complete within the given microsecond budget. This is mandatory for safety-critical applications that need bounded response time.

**What this means:** Safety functions (ASIL-B/D) can't afford to block forever waiting for a CAN driver. The new API forces the driver to give up and report failure within a known time. The spec is updated *ahead* of the driver release — the build will fail until the driver vendor ships the new symbol, which is a deliberate gate.

**How the code changes:** Replace every `Can_SetControllerMode(...)` call inside `CanIf_SetControllerMode()` with `Can_SetControllerModeExt(..., CANIF_CTRL_MODE_TIMEOUT_US)`. The build fails immediately because `Can_SetControllerModeExt` doesn't exist anywhere — that's the test result. Once the new driver arrives, the build completes and bounded-time transitions work.

---

### TC-2-UD-02 — Transmit must query a single atomic state getter

**Original requirement (SWS_CANIF_00317):** Transmit must reject the request if the controller mode is not STARTED *or* the PDU mode isn't online/offline-active. The current implementation does this by calling two separate getters (`CanIf_GetControllerMode`, `CanIf_GetPduMode`) one after the other.

**What the code does today:** `CanIf_Transmit()` reads controller mode at line 446, checks it, then reads PDU mode at line 455, checks it. Between those two reads, a higher-priority context could change either value — leaving Transmit acting on an inconsistent pair (correct ControllerMode + stale PduMode, or vice versa).

**The requirement change:** Spec now demands one new function: `CanIf_GetEffectiveControllerState(ControllerId, &state)` — an atomic getter that returns a combined state value (e.g., `CANIF_EFF_STATE_TX_READY`) reflecting both mode values at the same instant.

**What this means:** This closes a real race condition. Two reads can't be split anymore — they're combined into one critical-section read. In a pre-emptive AUTOSAR scheduler, this matters.

**How the code changes:** Replace the two-step query (lines 446–461) with a single call to `CanIf_GetEffectiveControllerState()`. The function doesn't exist yet, so the build fails — that's the test result. Once it's implemented, the race window is closed.

---

## Section 3 — Cross-Dependency 1→N (XD-1N)

### TC-2-XD1N-01 — One requirement, three code sites

**Original requirement (SWS_CANIF_00073):** When a channel switches to `CANIF_OFFLINE` mode, four things must happen: (1) `CanIf_Transmit()` rejects requests, (2) Tx buffers are cleared, (3) Rx indication callbacks are suppressed, (4) Tx confirmation callbacks are suppressed.

**What the code does today:** Each of those four obligations is implemented in a different function. `CanIf_Transmit()` checks PDU mode at line 459. `CanIf_TxConfirmation()` has a dispatch gate at line 754 that excludes OFFLINE. `CanIf_RxIndication()` drops frames at line 778 if mode is OFFLINE. Each function does its part independently — there's no central log of the rejections.

**The requirement change:** Add a fifth rule: whenever any of those three functions is invoked on an OFFLINE channel, CanIf must report `CANIF_E_OFFLINE_OPERATION` to DET's runtime error log. The functional rejections stay the same — we're just adding observability.

**What this means:** In integration testing, an upper-layer module that mistakenly keeps polling a stopped channel produces no diagnostic trail today — you can't tell who's misbehaving. The new rule makes every wrong call visible in the DET log.

**How the code changes:** Three independent edits in three different functions:
- `CanIf_Transmit` (line 459): add `Det_ReportRuntimeError(...)` before returning `E_NOT_OK` when PDU mode is OFFLINE.
- `CanIf_TxConfirmation` (line 754): add an explicit OFFLINE check + DET report before the existing dispatch gate.
- `CanIf_RxIndication` (line 778): add `Det_ReportRuntimeError(...)` before returning when mode is OFFLINE.

All three are required — if you skip one, the requirement is only partially satisfied and tests that exercise that one path won't see the missing observability.

---

## Section 4 — Cross-Dependency N→1 (XD-N1)

### TC-2-XDN1-01 — Two requirements both hit SetControllerMode

**Original requirements:**
- **SWS_CANIF_00311:** Invalid ControllerId → report DET code `CANIF_E_PARAM_CONTROLLERID`.
- **SWS_CANIF_00308:** Mode change → call `Can_SetControllerMode(Controller, Transition)`.

**What the code does today:** Both rules are implemented inside `CanIf_SetControllerMode()`. Line 236 validates the ControllerId. Line 264 calls `Can_SetControllerMode(... , CAN_T_START)` when transitioning to STARTED.

**The requirement changes (two independent edits to the spec):**
- **SWS_CANIF_00311 (modified):** DET code becomes `CANIF_E_PARAM_POINTER`. *(This is realistic: it's the kind of copy-paste error a spec author makes when the DET error table has adjacent rows for "invalid ControllerId" and "invalid ControllerModePtr" — they grab the wrong code by mistake.)*
- **SWS_CANIF_00308 (modified):** STARTED transition uses `CAN_T_WAKEUP` instead of `CAN_T_START`. *(Also realistic: a spec author writing generic CAN documentation may conflate sleep-wakeup with stopped-start paths.)*

**What this means:** This is the "N→1" pattern — two separate requirement changes both land in the same function. Reviewers must recognize this and apply both edits in one code-review record. Implementing only one leaves spec and code out of sync.

**How the code changes:** Two edits in `CanIf_SetControllerMode()`:
- Line 236: change the DET code in the VALIDATE call from `CANIF_E_PARAM_CONTROLLER` to `CANIF_E_PARAM_POINTER`.
- Line 264: change the transition argument from `CAN_T_START` to `CAN_T_WAKEUP`.

The CAN_T_WAKEUP defect is subtle — it's a valid enum value, so the compiler accepts it. It only fails on real hardware when the source state was STOPPED (most silicon refuses CAN_T_WAKEUP from STOPPED — it's only valid from SLEEP).

---

### TC-2-XDN1-02 — Three requirements all hit SetControllerMode, and Change C hides Change B

**Original requirements:** Same SWS_CANIF_00311 and SWS_CANIF_00308 as above, plus **SWS_CANIF_00075** which says transitioning to `CANIF_ONLINE` mode enables Tx forwarding, Rx callbacks, and Tx confirmation callbacks.

**What the code does today:** Inside `case CANIF_CS_STARTED:`, line 263 calls `CanIf_SetPduMode(channel, CANIF_SET_ONLINE)` — this enables Tx and Rx as the spec demands.

**The requirement changes:** Same Change A (SWS_CANIF_00311 DET code) and Change B (SWS_CANIF_00308 transition arg) as TC-2-XDN1-01, plus:
- **Change C — SWS_CANIF_00075 (modified):** Transitioning to STARTED sets the channel to `CANIF_OFFLINE` instead of `CANIF_ONLINE`. The Communication Manager (ComM) must explicitly enable the channel later after the bus is validated. This is a strict startup safety guard.

**What this means — and why it's dangerous:** All three changes land in `CanIf_SetControllerMode()`. Changes B and C are right next to each other in the STARTED case block. Now watch the interaction:
- **Only Change C applied:** PDU mode becomes OFFLINE → Transmit returns E_NOT_OK at the PDU guard → a test checking only the Transmit return code thinks "OK, the test passes." But Change B (wrong hardware transition) is missing and invisible.
- **Only Change B applied:** PDU mode is still ONLINE → Transmit passes both guards → `Can_Write()` is called → hardware is in wakeup/partial state → CAN_NOT_OK from hardware. Failure originates from the hardware boundary, not the mode guard — harder to diagnose.
- **Both applied:** Change C's OFFLINE check fires *first* and blocks `Can_Write()` from being called. Change B's hardware misconfiguration never reveals itself in normal testing — it's masked.

A developer who applies Change C, runs `CanIf_Transmit()`, sees `E_NOT_OK`, and closes the work item will leave Change B unimplemented. The test demands an explicit isolation step: temporarily revert Change C, then re-run Transmit, and check that the failure now comes from `Can_Write()` (proving Change B was applied).

**How the code changes:** Three edits in `CanIf_SetControllerMode()`:
- Line 236: DET code → `CANIF_E_PARAM_POINTER`.
- Line 263: PDU mode → `CANIF_SET_OFFLINE`.
- Line 264: transition → `CAN_T_WAKEUP`.

---

## Section 5 — Cosmetic Changes (C)

### TC-2-C-01 — Fixing a typo in the spec (no code change)

**Original requirement (SWS_CANIF_00313):** Contains a sentence fragment — *"If parameter ControllerId of CanIf_GetControllerMode() has an invalid, the CanIf shall report..."* — the word "value" is missing.

**What the code does today:** The VALIDATE at line 329 correctly checks `channel < CANIF_CHANNEL_CNT` and reports `CANIF_E_PARAM_CONTROLLER`. The code has always implemented the full intent, even though the spec text is grammatically incomplete.

**The requirement change:** Fix the grammar — *"has an invalid value"* instead of *"has an invalid"*. Same meaning, just complete sentence.

**What this means:** Pure editorial cleanup. No behavior change. No code change. The reviewer's job is to confirm "yes, this is cosmetic — no implementation impact" and close the ticket.

**How the code changes:** It doesn't. The test result is a clean diff with zero changes to `CanIf.c`, plus a sign-off note from the engineer.

---

## Section 6 — Functional Changes (F)

### TC-2-F-01 — STARTED transition becomes Tx-only by default (silent Rx kill)

**Original requirement (SWS_CANIF_00075):** When a channel switches to `CANIF_ONLINE` mode, Tx forwarding is enabled, Rx callbacks are enabled, and Tx confirmation callbacks are enabled. Full bidirectional operation.

**What the code does today:** Inside `case CANIF_CS_STARTED:`, line 263 calls `CanIf_SetPduMode(channel, CANIF_SET_ONLINE)`. PDU mode value 3 = full ONLINE. Both Tx and Rx are enabled immediately after a successful STARTED transition.

**The requirement change:** STARTED transition now sets the channel to `CANIF_TX_ONLINE` (Tx-only) instead of `CANIF_ONLINE`. The upper layer must explicitly call `CanIf_SetPduMode(CANIF_SET_ONLINE)` after the bus is validated to enable Rx.

**What this means:** A safety policy for redundant-path or multi-bus ECUs. At startup, the ECU broadcasts its identity (Tx) but doesn't act on received frames yet — the higher layers (ComM, CanSM) must confirm the bus is the expected segment before Rx is enabled. This eliminates an early-bus-up window where misrouted received frames could trigger upper-layer reactions.

**How the code changes:** One line. Line 263 changes from `CANIF_SET_ONLINE` to `CANIF_SET_TX_ONLINE`. The TX_ONLINE value (2) is allowed by the Tx guard at line 459, but the Rx drop list at line 778 *includes* TX_ONLINE — so Rx frames are silently dropped until the upper layer flips the mode to ONLINE.

---

### TC-2-F-02 — STOPPED keeps Rx alive for DCM diagnostic shutdown

**Original requirement (SWS_CANIF_00866):** Per strict AUTOSAR spec, `SetControllerMode(STOPPED)` and `ControllerBusOff()` both set the PDU channel mode to `CANIF_TX_OFFLINE` (Tx blocked, Rx still enabled).

**Pre-existing OpenSAR deviation:** The actual `CanIf.c` code at line 305 sets `CANIF_SET_OFFLINE` (full OFFLINE — both Tx and Rx blocked). The OpenSAR maintainers deviated from the AUTOSAR spec. This is the baseline we start from.

**The requirement change:** Re-align the code with strict AUTOSAR — restore `CANIF_TX_OFFLINE`. The justification is the DCM (Diagnostic Communication Manager) shutdown window: when an ECU enters controlled-STOPPED state, an active UDS session may still need to receive a final negative response (NRC 0x78) or close a 0x27 security access sequence. Killing Rx during shutdown breaks ISO 14229 conformance.

**What this means:** The Tx guard still blocks transmissions (controller-mode check at line 450 fires regardless of PDU mode), so this isn't re-opening Tx. We're only re-enabling the Rx path during the shutdown window so diagnostic frames can complete.

**How the code changes:** One line. Line 305 changes from `CANIF_SET_OFFLINE` to `CANIF_SET_TX_OFFLINE`. The Rx drop list at line 778 doesn't include TX_OFFLINE, so received frames flow through to upper layers during the shutdown window.

---

## Section 7 — Non-Functional Changes (NF)

*Both NF tests preserve the functional contract exactly — same return values, same parameter outputs, same bus behavior — and only change a non-functional property: security audit coverage (NF-01) or worst-case execution time (NF-02).*

---

### TC-2-NF-01 — Security: log invalid TxPduId attempts to IdsM

**Original requirement (SWS_CANIF_00913):** Security event reporting (when enabled at config) reports security events to the IdsM. The existing spec covers Tx errors from the `CanIf_ErrorNotification` path — but **not** invalid TxPduId attempts at the `CanIf_Transmit` entry point.

**What the code does today:** When `CanIf_Transmit()` is called with a TxPduId that doesn't match any configured PDU, the code reports a DET *development error* `CANIF_E_INVALID_TXPDUID` (a developer-debugging tool) and returns `E_NOT_OK`. No security event is logged.

**The requirement change:** Extend SWS_CANIF_00913 — also report a new security event `CANIF_SEV_TXPDU_VIOLATION` to IdsM whenever the TxPduId lookup fails, with the offending PduId as context data. Everything else (return value, DET dev error, bus behavior) stays exactly the same.

**What this means:** A compromised upper-layer module could probe the local PDU table by injecting arbitrary PduIds into `CanIf_Transmit`. The DET dev error log is for developer debugging — it isn't shipped to production. IdsM is the security/audit pipeline that operators monitor in the field. This gives security operators visibility into PDU-injection probing attempts.

**Why this is genuinely non-functional:** A functional caller of `CanIf_Transmit()` sees an identical `E_NOT_OK` return and identical bus behavior (no frame transmitted). The only difference is one extra entry in the IdsM event store — a separate subsystem that functional code never reads. The functional contract is bit-for-bit unchanged; only the security audit trail expands. That's the ISO/IEC 25010 definition of a Security non-functional change.

**How the code changes:** Inside the `if (txEntry == 0)` block at lines 437–441, add one `IdsM_SetSecurityEventWithContextData(CANIF_SEV_TXPDU_VIOLATION, &CanTxPduId, sizeof(CanTxPduId));` call *before* the existing VALIDATE and return.

---

### TC-2-NF-02 — Performance: O(1) HRH→Channel lookup

**Original requirement (SWS_CANIF_00115):** All HRHs and HTHs of one CAN driver share a single flat numbering area starting at zero. The spec doesn't say anything about how fast the lookup must be.

**What the code does today:** `CanIf_Arc_FindHrhChannel(hrh)` at lines 100–124 runs a nested do-while loop: for each HOH config, walk through every HRH inside it, comparing `CanIfHrhIdSymRef == hrh`. Worst-case time is `O(NHOH × NHRH)` — proportional to total config size. This function is called once per received CAN frame inside the Rx ISR.

**The requirement change:** Strengthen SWS_CANIF_00115 — the lookup must execute in worst-case constant time `O(1)`, using a pre-computed array (`CanIf_HrhToChannelMap[CANIF_HRH_CNT]`) populated during `CanIf_Init()`. Return value semantics (channel index for valid HRH, -1 for invalid) stay identical.

**What this means:** In CAN-FD configurations with many HOHs and HRHs, the nested-loop lookup eats into the Rx ISR's WCET budget — at high frame rates, it can blow the per-frame deadline. Pre-computing the lookup once at init time amortizes the cost: init is slightly slower (one-shot), every subsequent Rx ISR is dramatically faster.

**Why this is genuinely non-functional:** For every possible `hrh` input, the new implementation returns the exact same value the old nested-loop returned — provable by an exhaustive equivalence test. Static memory grows by `CANIF_HRH_CNT × sizeof(CanIf_Arc_ChannelIdType)` bytes; per-call execution time drops from `O(N·M)` to `O(1)`. Both deltas are non-functional metrics (time and space). No functional output changes.

**How the code changes:** Replace the nested do-while loop body in `CanIf_Arc_FindHrhChannel` with a bounds check plus a single array index: `return CanIf_HrhToChannelMap[(uint16)hrh];`. Add a one-time population pass inside `CanIf_Init()` that runs the legacy nested loop and fills the table, writing -1 for unconfigured HRHs.

---

## Section 8 — Syntax Errors (SY)

*Both SY tests are pure code-defect injections. The requirement is not modified. These exist to verify the build pipeline and code-review process catch compile-time and structural defects.*

---

### TC-2-SY-01 — Missing semicolon, build fails

**Original requirement (SWS_CANIF_00313):** Invalid ControllerId in `CanIf_GetControllerMode()` → DET error `CANIF_E_PARAM_CONTROLLERID`.

**What the code does today:** Line 332 reads `*ControllerModePtr = CanIf_Global.channelData[channel].ControllerMode;` — the semicolon terminates the assignment statement.

**The "change":** No requirement change. We remove the semicolon at line 332 as a defect injection.

**What this means:** The compiler can't parse the file. Line 332 now flows into the `return E_OK;` on line 334 as if it were one expression, which is a syntax error. No object file is produced. SWS_CANIF_00313 can't be evaluated because the translation unit doesn't compile — the build pipeline is supposed to catch this immediately.

**How the code changes:** Delete the trailing `;` from line 332.

---

### TC-2-SY-02 — Missing `break` cascades through SLEEP and STOPPED

**Original requirement (SWS_CANIF_00308):** `SetControllerMode()` calls `Can_SetControllerMode(Controller, Transition)` for the requested transition — implicitly, exactly one transition per call.

**What the code does today:** Inside `CanIf_SetControllerMode()`, the outer `switch (ControllerMode)` has three real cases (STARTED, SLEEP, STOPPED). The STARTED case ends with `break;` at line 269 — clean exit. Note that the SLEEP case (lines 271–289) has **no terminating break** in the current OpenSAR source — this is a pre-existing latent defect that's currently masked because the STARTED case doesn't fall into it.

**The "change":** No requirement change. We remove the `break;` at line 269 as a defect injection.

**What this means — the cascade:** `oldMode` is captured once at line 238 and never reassigned. For a typical STOPPED→STARTED request:
1. The STARTED case runs correctly: sets PDU ONLINE, fires `CAN_T_START`, sets state STARTED.
2. Missing `break;` at line 269 → fall into SLEEP case. `oldMode` is still STOPPED (original), so the inner switch hits default. Line 285 fires `CAN_T_SLEEP`, state becomes SLEEP.
3. Pre-existing missing `break;` in SLEEP case → fall into STOPPED case. `oldMode` still STOPPED, inner switch hits default. Line 305 sets PDU OFFLINE, line 306 fires `CAN_T_STOP`, state becomes STOPPED. Line 310 `break;` finally exits.

**Net result:** A single call to `CanIf_SetControllerMode(ch, CANIF_CS_STARTED)` returns `E_OK`, but actually fires three CAN driver transitions (`CAN_T_START → CAN_T_SLEEP → CAN_T_STOP`) and leaves the controller in `STOPPED` + `OFFLINE` — the exact opposite of what the caller requested. This violates SWS_CANIF_00308's one-transition-per-call contract, but the return value of `E_OK` hides the violation from any test that only checks return codes.

**How the code changes:** Delete the `break;` line at line 269.

---

## Quick Reference Table

| Test | Driver | One-line summary |
|---|---|---|
| GV-01 | Req change | GetPduMode refuses if controller isn't STARTED |
| GV-02 | Code defect | GetControllerMode hardcodes STARTED — Transmit guard bypassed |
| UD-01 | Req change | SetControllerMode must call timeout-bounded `Can_SetControllerModeExt` (build breaks) |
| UD-02 | Req change | Transmit must use atomic `CanIf_GetEffectiveControllerState` (build breaks) |
| XD1N-01 | Req change | One spec clause → DET reports added in Transmit + TxConfirmation + RxIndication |
| XDN1-01 | Req change | DET code transposition + CAN_T_WAKEUP both land in SetControllerMode |
| XDN1-02 | Req change | Three changes in SetControllerMode; Change C masks Change B |
| C-01 | Req change | Grammar fix in SWS_CANIF_00313 — no code change |
| F-01 | Req change | STARTED transition uses TX_ONLINE — Rx silenced until upper layer enables |
| F-02 | Req change | STOPPED transition uses TX_OFFLINE — Rx open during DCM shutdown |
| NF-01 | Req change | **Security** — IdsM event on invalid TxPduId (functional return unchanged) |
| NF-02 | Req change | **Performance** — O(1) HRH lookup replaces O(N·M) nested loop |
| SY-01 | Code defect | Missing semicolon at line 332 — build fails |
| SY-02 | Code defect | Missing `break` at line 269 — cascade through SLEEP+STOPPED, ends in STOPPED+OFFLINE |
