# Requirement Change Testing — Deep Research Report

---

## Overview

This report documents the findings of a deep search for publicly available test cases, test suites,
or testing methodologies that specifically test **changes in software requirements** — i.e., verifying
that when a requirement changes, the corresponding code change is correctly implemented, has the right
impact, and does not regress anything else.

**Context:** AUTOSAR CanIf (CAN Interface BSW module, AR 4.0.3), OpenSAR implementation.
The project uses a requirement-to-code traceability matrix (104 mapped + 169 unmapped = 273 total
requirements) and classifies requirement changes as:

| Code | Category | Meaning |
|:---:|:---|:---|
| **F** | Functional | Changes runtime behavior |
| **NF** | Non-Functional | Structural change, identical observable behavior |
| **C** | Cosmetic | Wording only, no code change required |
| **XD-1N** | Cross-Depend 1→N | One requirement change propagates to multiple functions |
| **XD-N1** | Cross-Depend N→1 | Multiple requirement changes converge on one function |
| **CB** | Combined | Multiple categories simultaneously |
| **SY** | Syntax | Syntactic defects (missing `;`, wrong constants, undefined symbols, etc.) |

---

---

## Part 1 — What AUTOSAR Officially Provides

### 1.1 AUTOSAR Conformance Test Spec (CTSpec) — TTCN-3

**URL:** https://www.autosar.org/fileadmin/standards/R3.0.7/CP/AUTOSAR_CTSpec_Creation_Validation.pdf

Official TTCN-3 tests where each `SWS_CANIF_XXXXX` requirement maps to one or more test cases
(identified as `[ModuleName]_TC_XXXXX`). Tests verify that a BSW implementation conforms to the
requirement at its API boundary.

**What it does NOT do:**
- No change-type classification (F/NF/C/XD/CB/SY)
- No mechanism for testing what happens when a requirement changes
- Tests a static implementation against a fixed standard version; when a new AUTOSAR release is
  issued the CTSpec is updated wholesale — no delta-test methodology

**Relevance:** HIGH for structural context. The CTSpec is the closest thing AUTOSAR has to a
formal requirement-to-test mapping. Your traceability matrix is the same logical structure applied
to change analysis rather than conformance verification.

---

### 1.2 AUTOSAR Acceptance Test Spec — CAN Communication (ATS_CommunicationCAN v1.2)

**URL:** https://www.autosar.org/fileadmin/standards/tests/1-2/AUTOSAR_ATS_CommunicationCAN.pdf

The most directly relevant official AUTOSAR document. 78-page specification covering:
- CanIf transmit and receive flows
- PDU routing
- CanSM interaction
- CAN bus-level behavior

Behavioral pass/fail test sequences for the entire CAN communication stack.

**What it does NOT do:** No change-type classification. Tests are written against a fixed version
of the specification, not against requirement changes.

**Relevance:** VERY HIGH — same module layer as the CanIf project. The behavioral tests in this
document map to the **F (Functional)** change category in the project taxonomy.

---

### 1.3 AUTOSAR Acceptance Tests Overview

**URL:** https://www.autosar.org/fileadmin/standards/tests/1-2/AUTOSAR_EXP_AcceptanceTestsOverview.pdf

Overview document for the entire AUTOSAR acceptance test ecosystem. First release covered:
Runtime Environment (RTE), BSW services (NVRAM Manager, DEM, DCM, ECU State Manager, ComM),
bus behavior (CAN, LIN, FlexRay, generic ComStack), and transport protocols.

**Stated goal:** "Save considerable cost and effort in testing activities through standardization
of test cases."

**Relevance:** HIGH for scope context. Shows which BSW modules have formally standardized test cases.

---

### 1.4 Conformance Testing for AUTOSAR (ERTS 2010 / HAL paper)

**URL:** https://hal.science/hal-02264390v1/document

Academic paper from ERTS 2010 describing the AUTOSAR TTCN-3 conformance testing framework.
Explains ICC1/ICC2/ICC3 (Implementation Conformance Classes) and how test case selection depends
on configuration parameters.

**Key insight:** "The majority of functional requirements relevant to conformance relate to dynamic
behavior" — which maps directly to the **F (Functional)** category.

---

### 1.5 Conformance Test of AUTOSAR Network Management (Springer 2018)

**URL:** https://link.springer.com/article/10.1007/s10776-018-0385-4
**Also on ResearchGate:** https://www.researchgate.net/publication/322627419_Conformance_Test_of_AUTOSAR_Network_Management

Journal paper proposing a conformance test approach for AUTOSAR NM using virtual network simulation.
State-machine-driven tests. Same communication stack layer as CanIf.

**Relevance:** MEDIUM-HIGH. State-machine test coverage is directly applicable to the XD-1N and
XD-N1 cross-dependency test cases where a single requirement drives transitions through the
controller state machine.

---

### 1.6 AUTOSAR CAN Acceptance Test Thesis (Linköping University)

**URL:** http://liu.diva-portal.org/smash/record.jsf?pid=diva2:1162038

Master's thesis building a test framework following the AUTOSAR ATS_CommunicationCAN specification,
targeting Arctic Core / Arctic Studio. 11 test cases, 82.7% pass rate.

**Relevance:** MEDIUM-HIGH. Real-world academic attempt at implementing the AUTOSAR CAN test spec.
The 11-test scope validates that a 25-test suite (this project) is appropriately ambitious for a
graduate project in this domain.

---

---

## Part 2 — Industry Tools

### 2.1 VectorCAST — Change-Based Testing (CBT) + Reqs2x

**URL:** https://www.vector.com/int/en/products/products-a-z/software/vectorcast/
**CBT whitepaper:** https://cdn.vector.com/cms/content/products/VectorCAST/Docs/Whitepapers/English/Change_Based_Testing_For_Efficient_Software_Development.pdf
**AUTOSAR webinar:** https://www.vector.com/at/en/events/global-de-en/webinar-recordings/2020/vectorcast-how-to-unit-test-autosar-software-components/

**What it does:**

- **Change-Based Testing (CBT):** Analyzes each code change against all existing test cases and
  selects the subset of tests actually impacted by that change. Reduces total re-run time.
- **Requirement Traceability:** Bidirectional link between requirements (DOORS, codebeamer, Polarion)
  and test cases.
- **Reqs2x (VectorCAST 2026, March 2026):** AI-powered feature that generates executable unit tests
  directly from requirement text.

**What it does NOT do:**
VectorCAST CBT operates at the **code-change level** — it detects which source lines changed and
selects tests that cover those lines. It does **not** classify the requirement change as F/NF/C/XD/CB.
It cannot determine whether a requirement change is cosmetic (no code needed) or cross-dependent
(multiple functions affected). This is the gap the project taxonomy fills.

**Relevance:** VERY HIGH. VectorCAST CBT is the industrial equivalent of what the project proposes
at the conceptual level. The distinction: CBT answers "which tests cover the changed lines?",
while the project taxonomy answers "what kind of requirement change is this, and how many functions
does it touch?"

---

### 2.2 TESSY (Razorcat)

**URL:** https://www.razorcat.com/en/product-tessy.html

Automated unit and integration test tool for embedded C/C++.

**What it does:**
- Bidirectional traceability between requirements and test cases
- Regression test automation on change
- AUTOSAR SWC support: generates stubs for RTE interfaces (Rte_Read, Rte_Write), supports ARXML
- ISO 26262 certified

**What it does NOT do:**
TESSY does not classify requirement changes by type. The engineer manually decides whether a
requirement change is functional, cosmetic, or structural; TESSY executes the tests the engineer
selects.

**Relevance:** HIGH. TESSY is the most widely used tool for AUTOSAR BSW unit testing in industry.
The combination of TESSY + this project's change-type taxonomy is the practical workflow the
project implicitly proposes.

---

### 2.3 TPT (Test Procedure Tool — PikeTec / Synopsys)

**URL:** https://piketec.com/tpt/requirements-coverage/ (now Synopsys)

Model-based dynamic testing tool; MiL/SiL/PiL/HiL/ViL support, ASPICE-compliant.

**What it does:**
- **Requirement change flagging:** When a linked requirement changes, TPT highlights all test cases
  linked to that requirement, making it immediately visible which tests need review.
- ISO 26262 certified ASIL A–D

**What it does NOT do:**
TPT flags *which tests are linked* to a changed requirement but does NOT classify the nature of
the change (F/NF/C/XD/CB/SY). That judgment is left to the engineer.

**Relevance:** VERY HIGH. TPT's requirement-change flagging is the most direct industrial parallel
to this project's approach. Key distinction: TPT uses model-based Simulink-style tests for SWC
(controller functions); this project works with C unit tests for BSW modules.

---

### 2.4 Parasoft C/C++test — AUTOSAR + Requirements Traceability

**URL:** https://www.parasoft.com/learning-center/requirements-traceability/

Static and dynamic testing with AUTOSAR C++14 compliance checking, RTM generation, ISO 26262
support. Integrates with ALM tools for requirement-to-test linking.

**Relevance:** MEDIUM. Good general reference for industrial requirement-traceability tooling in
the AUTOSAR context.

---

### 2.5 autosar.io — TC Auto-Generation

**URL:** https://autosar.io/en/insights/tc-auto-generation

Automated test case generation from AUTOSAR requirements. Features:
- Automatic requirement ID → test case traceability mapping
- Identifies impacted test cases when requirements change
- Three methodologies: requirements-based, model-based (ARXML/Simulink), code-based

**Relevance:** MEDIUM-HIGH. Represents the emerging AI-driven direction in AUTOSAR testing.
No change-type classification.

---

### Industry Tools — Summary

| Tool | Flags affected tests on change? | Classifies change type (F/NF/C/XD)? |
|:---|:---:|:---:|
| VectorCAST CBT | YES (code-level) | NO |
| TESSY | YES (manual selection) | NO |
| TPT | YES (requirement-linked) | NO |
| Parasoft C/C++test | YES (traceability link) | NO |
| autosar.io | YES (impact identification) | NO |

**Pattern:** Every tool flags which tests are affected. None classify what kind of change it is.

---

---

## Part 3 — Academic Papers

### 3.1 Understanding Changes in Use Cases (IEEE RE 2015)

**URL:** https://ieeexplore.ieee.org/document/7320452/
**Authors:** Eder, Broy — TU Munich / BMW affiliation

Studied real requirement changes at a major automotive OEM and classified them as:

| Academic Category | Proportion | Maps to Project Taxonomy |
|:---|:---:|:---|
| **Syntactic** | ~30% | **C (Cosmetic)** + **SY (Syntax)** |
| **Semantic** | ~50% | **F (Functional)** + **NF (Non-Functional)** |
| **Structural** | ~20% | **XD-1N** + **XD-N1** |

**Key finding:** "Practitioners found the classification of changes into semantic and syntactic
categories to have intuitive understanding" — validates the project's classification approach as
practically usable.

**Relevance:** VERY HIGH. The most academically aligned change taxonomy to the one used in this
project. Note: this paper works on use-case requirements at an OEM level, not on AUTOSAR SWS
unit-level BSW requirements. This project adapts the taxonomy to the BSW domain and adds the
Combined (CB) category.

---

### 3.2 Co-Evolution of Model-Based Tests for Industrial Automotive Software (IEEE 2015)

**URL:** https://ieeexplore.ieee.org/document/7102613

Addresses the problem of keeping test suites synchronized when automotive software (Simulink models)
change. Proposes automated test model adaptation based on evolution patterns.

**Test impact classification:**
- **(a) Directly affected** — the changed requirement maps straight to the test → **F (Functional)**
- **(b) Indirectly affected** — through inter-module dependencies → **XD cross-dependency categories**
- **(c) Unaffected** — no observable behavioral change → **NF (Non-Functional)** + **C (Cosmetic)**

**What it does NOT cover:** This paper operates on Simulink model-based tests for SWC (controller
functions), not on C unit tests for BSW modules. The BSW unit-test gap is what this project fills.

**Relevance:** VERY HIGH — the closest academic methodology paper to the project's approach.

---

### 3.3 A Taxonomy for RE–Software Test Alignment (ACM TOSEM 2014)

**URL:** https://dl.acm.org/doi/10.1145/2523088
**arXiv preprint:** https://arxiv.org/abs/2307.12477
**Authors:** Unterkalmsteiner, Feldt, Gorschek

Foundational paper proposing the REST (Requirements Engineering–Software Test) alignment taxonomy.
Introduces the "information dyad" concept — structured information exchange between RE and testing.
Validated on five industrial cases and 13 alignment methods. Includes the REST-bench assessment
framework.

**Relevance:** HIGH — theoretical foundation. The project's traceability matrix is an instantiation
of a REST alignment method under this taxonomy.

---

### 3.4 Change Impact Analysis: A Systematic Mapping Study (ScienceDirect 2020)

**URL:** https://www.sciencedirect.com/science/article/abs/pii/S016412122030282X

Mapping study analyzing 111 papers on Change Impact Analysis (CIA) methods.

**Key finding:** "A number of important software maintenance tasks require an up-to-date requirements
traceability matrix: change impact analysis, determination of test cases to execute for regression
testing."

**Relevance:** HIGH as a survey anchor. Confirms the academic consensus that RTM + CIA + regression
test selection is the correct pipeline for handling requirement changes.

---

### 3.5 Improving Efficiency of Change Impact Assessment Using Graphical Requirement Specs (Springer 2010)

**URL:** https://link.springer.com/chapter/10.1007/978-3-642-13792-1_26

Experiment by Mellegård and Staron measuring how graphical vs. textual requirement specifications
affect change impact assessment efficiency.

**Key result:** Graphical representations decreased time and increased confidence, but accuracy
decreased. Demonstrates that requirement representation format has measurable impact on change
impact analysis quality.

**Relevance:** MEDIUM. Supports the rationale for the traceability matrix (structured representation
aids change impact assessment) and validates the difficulty of manual change analysis from textual
AUTOSAR SWS documents.

---

### 3.6 Test Case Specification Techniques in Automotive Industry: A Review (arXiv 2024)

**URL:** https://arxiv.org/html/2512.23780

Systematic literature review of 50 peer-reviewed studies on test case specification techniques
in automotive software.

**Key findings:**
- Requirements often arrive late, forcing testers to design tests on "outdated previous requirements"
  — the exact scenario this project's change-classification approach addresses
- Poor traceability between requirements and specifications complicates coverage validation
- "A seamless chain of methods and tools to support the entire life cycle is lacking"

**Relevance:** HIGH for situating the contribution. This 2024 review confirms that
requirement-to-code traceability + change-type classification addresses a documented,
actively-researched gap in automotive software testing.

---

### 3.7 Automated Testing from Requirement Specification Models (IEEE 2011)

**URL:** https://ieeexplore.ieee.org/document/5985928/

Automated test case generation for automotive embedded systems from requirement specification
models (EAST-ADL architecture description language).

**Relevance:** MEDIUM. Shows the MBT pipeline from requirements to test cases — the theoretical
basis for the requirement-to-test traceability matrix.

---

---

## Part 4 — Standards

### 4.1 ISO 26262 Part 6 — Software Testing

**URL:** https://www.parasoft.com/learning-center/iso-26262/regression-testing/

**What it mandates:**
- **Requirement-based testing** is "highly recommended" for ALL ASIL levels (A–D)
- **Regression testing:** When software units are modified, previously passed tests must be
  re-executed to verify no regressions
- **Coverage criteria:** MC/DC required at ASIL C/D
- **Fault injection** testing: recommended at ASIL A/B, highly recommended at ASIL C/D

**What it does NOT provide:**
The standard mandates regression testing after changes but gives no taxonomy for classifying the
nature of the change. It does not distinguish whether a change is Functional (re-run all tests),
Cosmetic (no code change needed), or Cross-Dependent (multiple functions affected).

**Relevance:** VERY HIGH as justification. The F/NF/C/XD/CB/SY taxonomy is an operationalization
of the ISO 26262 regression testing requirement for the specific case of AUTOSAR BSW
requirement changes.

---

### 4.2 Automotive SPICE (ASPICE) — SWE.4 / SWE.5 / SWE.6

**URLs:**
- SWE.4: https://www.ul.com/sis/resources/process-swe-4
- SWE.6: https://www.ul.com/sis/resources/process-swe-6

**What ASPICE mandates:**
- **SWE.4 (Software Unit Verification):** Bidirectional traceability between software detailed design
  and unit test specification; documented regression strategy specifying which tests re-run when
  units change
- **SWE.5 (Software Integration Testing):** Bidirectional traceability between software architecture
  and integration test specification
- **SWE.6 (Software Qualification Testing):** Bidirectional traceability between software
  requirements and qualification test specification

**What it does NOT provide:**
ASPICE defines that changes must be traced and regression tests must be selected, but the
classification of change type (Functional/Non-Functional/Cosmetic/Cross-Depend) is left entirely
to the project process.

**Relevance:** VERY HIGH as a framework. The project produces exactly the SWE.4 work products:
unit test specification with bidirectional requirement traceability + regression strategy +
test results. The change taxonomy adds a dimension ASPICE requires but does not specify.

---

### 4.3 DO-178C — Requirement-Based Testing (Avionics Parallel)

**URL:** https://www.do178.org/

**What it mandates:**
- Coverage of equivalence classes and boundary/singular values for all requirements
- Requirement-based test coverage as a primary verification objective
- Tests must be traceable to requirements
- Change analysis required: any change triggers re-analysis of affected requirements and tests,
  with demonstration that unchanged areas are not regressed

**What it does NOT provide:** No formal change-type taxonomy. Change analysis is process-level only.

**Relevance:** MEDIUM. DO-178C is the avionics parallel to ISO 26262. The change analysis pipeline
it mandates (identify affected requirements → identify affected tests → re-verify) is the same
logical flow the project taxonomy implements.

---

---

## Part 5 — Open-Source CanIf Test Suites

### 5.1 asusar/communication-stack (Ain Shams University)

**URL:** https://github.com/asusar/communication-stack
**Test file:** https://github.com/asusar/communication-stack/blob/master/CanIf/CanIf/CANIFRx_Test/CanIf.c

Has `CANIF_UNIT_TESTING` preprocessor flag, test configuration structures, debug print capabilities.
Tests validate configuration pointer validity and controller parameter initialization.

**Change classification:** None.
**Relevance:** HIGH for comparison. The only known open-source AUTOSAR CanIf project from an
Egyptian university with actual test infrastructure. Has basic init validation only — maps to the
**F (Functional)** and **SY (Syntax)** categories at a surface level.

---

### 5.2 autoas/as (continuation of parai/OpenSAR)

**URL:** https://github.com/autoas/as

Full AUTOSAR BSW stack including CanIf, with Python-based AsPy interface for CAN/LIN/IsoTp.
Actively maintained.

**Change classification:** None.
**Relevance:** MEDIUM. AsPy could drive integration tests for CanIf changes but has no
classification framework.

---

### 5.3 sics-sse/moped (SICS Swedish ICT)

**URL:** https://github.com/sics-sse/moped/blob/master/autosar/src/core/communication/CanIf/CanIf.c

CanIf implementation based on Arctic Core AUTOSAR stack. `VALIDATE_RV` macro checks in
`CanIf_Transmit` serve as embedded assertions and lightweight test validation points.

**Change classification:** None.
**Relevance:** MEDIUM.

---

### 5.4 Shoubra-Graduation-Project/AUTOSAR-COM-Stack

**URL:** https://github.com/Shoubra-Graduation-Project/AUTOSAR-COM-Stack

COM and CanIf modules per AUTOSAR standard, 99.1% C, comprehensive documentation.

**Change classification:** None.
**Relevance:** LOW-MEDIUM as a test source, HIGH as a parallel reference implementation.

---

---

## Part 6 — What This Project Contributes (Gap Analysis)

Based on all sources above, the following gap exists:

| What exists | What is missing |
|:---|:---|
| AUTOSAR CTSpec/ATS: tests conformance of a fixed implementation | Tests for what happens when a **requirement changes** |
| ISO 26262 / ASPICE: mandates regression testing after changes | A **taxonomy** for classifying change type to guide regression selection |
| VectorCAST CBT: selects tests based on **code-line** changes | Selection based on **requirement-change type** (F/NF/C/XD/CB/SY) |
| TPT / TESSY: flags tests linked to a changed requirement | Classification of whether the change is Functional, Cosmetic, or Cross-Dependent |
| Eder & Broy 2015: syntactic/semantic/structural taxonomy | Applied to **AUTOSAR SWS BSW** items (not OEM-level use cases) |
| Co-evolution paper 2015: direct/indirect/unaffected | Applied to **C unit tests for BSW** (not Simulink model-based SWC tests) |

**The project's specific contribution:**

> Applying a typed change-classification taxonomy (F / NF / C / XD-1N / XD-N1 / CB / SY)
> to AUTOSAR BSW requirement changes, backed by a requirement-to-code traceability matrix
> (273 SWS_CANIF requirements, 104 mapped, 169 unmapped with documented category reasons),
> for the CanIf module of OpenSAR AR 4.0.3.

This combination — typed change taxonomy + RTM + BSW unit test cases — does not appear in any
existing public source found in this research.

---

---

## All Sources

| Source | Type | URL |
|:---|:---|:---|
| AUTOSAR CTSpec Creation & Validation | Official standard | https://www.autosar.org/fileadmin/standards/R3.0.7/CP/AUTOSAR_CTSpec_Creation_Validation.pdf |
| AUTOSAR ATS CommunicationCAN v1.2 | Official test spec | https://www.autosar.org/fileadmin/standards/tests/1-2/AUTOSAR_ATS_CommunicationCAN.pdf |
| AUTOSAR Acceptance Tests Overview | Official overview | https://www.autosar.org/fileadmin/standards/tests/1-2/AUTOSAR_EXP_AcceptanceTestsOverview.pdf |
| Conformance Testing for AUTOSAR (ERTS 2010) | Academic / HAL | https://hal.science/hal-02264390v1/document |
| Conformance Test of AUTOSAR NM (Springer 2018) | Academic journal | https://link.springer.com/article/10.1007/s10776-018-0385-4 |
| AUTOSAR CAN Acceptance Test Thesis (LiU) | Academic thesis | http://liu.diva-portal.org/smash/record.jsf?pid=diva2:1162038 |
| asusar/communication-stack | Open source | https://github.com/asusar/communication-stack |
| autoas/as (OpenSAR) | Open source | https://github.com/autoas/as |
| sics-sse/moped CanIf.c | Open source | https://github.com/sics-sse/moped |
| VectorCAST CBT + Reqs2x | Industry tool | https://www.vector.com/int/en/products/products-a-z/software/vectorcast/ |
| TESSY (Razorcat) | Industry tool | https://www.razorcat.com/en/product-tessy.html |
| TPT / PikeTec (Synopsys) | Industry tool | https://piketec.com/tpt/requirements-coverage/ |
| Parasoft C/C++test | Industry tool | https://www.parasoft.com/learning-center/requirements-traceability/ |
| autosar.io TC auto-generation | Industry tool | https://autosar.io/en/insights/tc-auto-generation |
| Understanding Changes in Use Cases (IEEE RE 2015) | Academic IEEE | https://ieeexplore.ieee.org/document/7320452/ |
| Co-Evolution of Model-Based Tests (IEEE 2015) | Academic IEEE | https://ieeexplore.ieee.org/document/7102613 |
| REST Taxonomy (ACM TOSEM 2014) | Academic ACM | https://dl.acm.org/doi/10.1145/2523088 |
| Change Impact Analysis Mapping Study (2020) | Academic survey | https://www.sciencedirect.com/science/article/abs/pii/S016412122030282X |
| Improving CIA with Graphical Reqs (Springer 2010) | Academic | https://link.springer.com/chapter/10.1007/978-3-642-13792-1_26 |
| Test Spec Techniques in Automotive (arXiv 2024) | Academic survey | https://arxiv.org/html/2512.23780 |
| Automated Testing from Req Spec Models (IEEE 2011) | Academic IEEE | https://ieeexplore.ieee.org/document/5985928/ |
| ISO 26262 Regression Testing (Parasoft guide) | Standard reference | https://www.parasoft.com/learning-center/iso-26262/regression-testing/ |
| ASPICE SWE.4 Software Unit Verification | Standard reference | https://www.ul.com/sis/resources/process-swe-4 |
| ASPICE SWE.6 Software Qualification Testing | Standard reference | https://www.ul.com/sis/resources/process-swe-6 |
| DO-178C overview | Standard reference | https://www.do178.org/ |
