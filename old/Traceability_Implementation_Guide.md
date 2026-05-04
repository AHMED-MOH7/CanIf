# CanIf Traceability Matrix — Complete Implementation Guide

## What You Already Have

Before starting, note that the work is already partially done:

| File | What It Contains |
|------|-----------------|
| `CanIf_Traceability_Matrix.csv` | 45 requirements, fully traced, ready to import |
| `CanIf_Traceability_Summary.md` | Human-readable grouped view with coverage stats |

Everything below is about **how to present, extend, or maintain** that matrix using your chosen tool.

---

## Option Comparison

| Tool | Cost | Effort | Best For |
|------|------|--------|----------|
| Excel / Google Sheets | Free | Low | Submission, quick sharing |
| Doorstop | Free (open source) | Medium | Git-based, developer-friendly |
| StrictDoc | Free (open source) | Medium | PDF/HTML export, AUTOSAR-style docs |
| OpenFastTrace (OFT) | Free (open source) | Medium | Automated coverage checking from code tags |
| ReqIF Studio | Free (Eclipse plugin) | High | AUTOSAR/DOORS-compatible format |

---

# Option A — Excel / Google Sheets (Fastest, Zero Install)

## Step 1: Open the CSV

1. Open **Microsoft Excel** or go to **sheets.google.com**
2. `File → Open → CanIf_Traceability_Matrix.csv`
3. If asked about delimiter: choose **Comma**

## Step 2: Format as a Table

1. Select all data (`Ctrl+A`)
2. `Insert → Table` → check "My table has headers" → OK
3. The columns are:

```
Req_ID | SWS_Reference | Requirement_Description | Function | File |
Start_Line | End_Line | Implementation_Status | DET_Error_ID |
Verification_Method | Notes
```

## Step 3: Add Color-Coding by Status

1. Select the `Implementation_Status` column
2. `Home → Conditional Formatting → Highlight Cell Rules → Text that contains`

| Rule Text | Fill Color |
|-----------|-----------|
| `Implemented` | Green |
| `Not Supported` | Red |
| `ArcCore extension` | Blue |
| `conditional` | Yellow |

## Step 4: Add a Coverage Dashboard (Optional)

1. Insert a new sheet named `Dashboard`
2. Add these COUNTIF formulas:

```excel
=COUNTIF(Sheet1[Implementation_Status],"Implemented")
=COUNTIF(Sheet1[Implementation_Status],"*Not Supported*")
=COUNTIF(Sheet1[Implementation_Status],"*ArcCore*")
=COUNTA(Sheet1[Req_ID])
```

3. Create a pie chart from those counts

## Step 5: Export for Submission

- `File → Export → PDF` — gives a clean printable matrix
- Or keep it as `.xlsx` and share the file

---

# Option B — Doorstop (Git-Based, Free)

Doorstop stores requirements as plain text files inside your Git repo, then checks that every requirement is linked to code. It works on the command line.

## Step 1: Install

```bash
pip install doorstop
```

Requires Python 3.8+. Check with:

```bash
python --version
pip --version
```

## Step 2: Initialize a Doorstop Document

Navigate to your project root:

```bash
cd D:\ASU\GradProject\CANIF_NEEK
doorstop create CANIF . --parent SYS
```

This creates a `CANIF/` folder where each `.yml` file is one requirement.

## Step 3: Add Requirements from the CSV

Each requirement becomes one YAML file. Example for CANIF053:

```bash
doorstop add CANIF
```

This creates `CANIF/CANIF001.yml`. Open it and fill it:

```yaml
# CANIF/CANIF053.yml
active: true
derived: false
header: ''
level: 5.1
links: []
normative: true
ref: 'CanIf.c+757'        # file+line reference
reviewed: null
text: |
  Upper layer TX confirmation callbacks shall only be called
  when the PDU channel mode allows transmission.
  SWS_Ref: SWS_CANIF_00053
  Function: CanIf_TxConfirmation
  Status: Implemented
```

## Step 4: Add All Requirements by Script

Instead of manual editing, run this Python script to bulk-convert the CSV:

```python
# convert_csv_to_doorstop.py
import csv
import os
import yaml

csv_file = "CanIf_Traceability_Matrix.csv"
output_dir = "CANIF"
os.makedirs(output_dir, exist_ok=True)

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        doc = {
            'active': True,
            'derived': False,
            'level': i,
            'normative': True,
            'ref': f"{row['File']}+{row['Start_Line']}",
            'links': [],
            'text': (
                f"{row['Requirement_Description']}\n"
                f"SWS_Ref: {row['SWS_Reference']}\n"
                f"Function: {row['Function']}\n"
                f"Status: {row['Implementation_Status']}\n"
                f"DET_Error: {row['DET_Error_ID']}\n"
                f"Verification: {row['Verification_Method']}"
            )
        }
        filename = os.path.join(output_dir, f"{row['Req_ID']}.yml")
        with open(filename, 'w') as out:
            yaml.dump(doc, out, default_flow_style=False, allow_unicode=True)

print("Done. Run: doorstop publish all ./traceability_report")
```

Run it:

```bash
python convert_csv_to_doorstop.py
```

## Step 5: Publish HTML Report

```bash
doorstop publish all ./traceability_report
```

Open `./traceability_report/index.html` in a browser — this is your full traceability report.

## Step 6: Check Coverage

```bash
doorstop check
```

This validates that all requirement references point to real files and lines.

---

# Option C — StrictDoc (AUTOSAR-Style PDF/HTML Export, Free)

StrictDoc is an open-source tool specifically designed for requirements traceability. It produces professional AUTOSAR-style documents.

## Step 1: Install

```bash
pip install strictdoc
```

## Step 2: Create the Project Config

Create a file `strictdoc.toml` in your project root:

```toml
[project]
title = "CanIf Traceability Matrix — OpenSAR"

[[project.source_files]]
glob = "OpenSAR/communication/CanIf/**"
```

## Step 3: Create a Requirements Document

Create `canif_requirements.sdoc`:

```
[DOCUMENT]
TITLE: CanIf Requirements Traceability

[GRAMMAR]
ELEMENTS:
- TAG: REQUIREMENT
  FIELDS:
  - TITLE: UID
    TYPE: String
    REQUIRED: True
  - TITLE: SWS_REF
    TYPE: String
    REQUIRED: False
  - TITLE: STATUS
    TYPE: SingleChoice(Implemented, Not_Supported, ArcCore_Extension, Partial)
    REQUIRED: True
  - TITLE: FUNCTION
    TYPE: String
    REQUIRED: True
  - TITLE: LINES
    TYPE: String
    REQUIRED: False
  - TITLE: STATEMENT
    TYPE: String
    REQUIRED: True
  - TITLE: VERIFICATION
    TYPE: String
    REQUIRED: False

[SECTION]
TITLE: Initialization

[REQUIREMENT]
UID: CANIF001
SWS_REF: SWS_CANIF_00001
STATUS: Implemented
FUNCTION: CanIf_Init
LINES: 131-146
STATEMENT: CanIf_Init shall initialize all CanIf-internal variables and set module state to initialized.
VERIFICATION: Code Review / Unit Test

[REQUIREMENT]
UID: CANIF007
SWS_REF: SWS_CANIF_00007
STATUS: Implemented
FUNCTION: CanIf_Init
LINES: 139
STATEMENT: CanIf_Init shall set all CAN controller modes to CANIF_CS_STOPPED.
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF008
SWS_REF: SWS_CANIF_00008
STATUS: Implemented
FUNCTION: CanIf_Init
LINES: 140
STATEMENT: CanIf_Init shall set all PDU channel modes to CANIF_GET_OFFLINE.
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF066
SWS_REF: SWS_CANIF_00066
STATUS: Implemented
FUNCTION: CanIf_InitController
LINES: 185-199
STATEMENT: CanIf shall have access to CAN Driver configuration data.
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF092
SWS_REF: SWS_CANIF_00092
STATUS: Implemented
FUNCTION: CanIf_InitController
LINES: 168-175
STATEMENT: If controller is STARTED during CanIf_InitController it shall be set to STOPPED first.
VERIFICATION: Code Review / Unit Test

[REQUIREMENT]
UID: CANIF293
SWS_REF: SWS_CANIF_00293
STATUS: Implemented
FUNCTION: CanIf_InitController
LINES: 200
STATEMENT: CanIf_InitController shall subsequently call Can_InitController.
VERIFICATION: Code Review

[SECTION]
TITLE: Controller Mode Management

[REQUIREMENT]
UID: CANIF017
SWS_REF: SWS_CANIF_00017
STATUS: Implemented
FUNCTION: CanIf_SetControllerMode
LINES: 248-268
STATEMENT: Transition to CS_STARTED; set PDU mode ONLINE; call CAN_T_START.
VERIFICATION: Code Review / State Machine Test

[REQUIREMENT]
UID: CANIF021
SWS_REF: SWS_CANIF_00021
STATUS: Implemented
FUNCTION: CanIf_SetControllerMode
LINES: 271-289
STATEMENT: Transition to CS_SLEEP via STOPPED state; call CAN_T_SLEEP.
VERIFICATION: Code Review / State Machine Test

[REQUIREMENT]
UID: CANIF022
SWS_REF: SWS_CANIF_00022
STATUS: Implemented
FUNCTION: CanIf_SetControllerMode
LINES: 291-311
STATEMENT: Transition to CS_STOPPED; set PDU mode OFFLINE; call CAN_T_STOP.
VERIFICATION: Code Review / State Machine Test

[REQUIREMENT]
UID: CANIF023
SWS_REF: SWS_CANIF_00023
STATUS: Implemented
FUNCTION: CanIf_GetControllerMode
LINES: 322-335
STATEMENT: Return the current CAN controller mode via output pointer.
VERIFICATION: Code Review / Unit Test

[SECTION]
TITLE: PDU Mode Management

[REQUIREMENT]
UID: CANIF072
SWS_REF: SWS_CANIF_00072
STATUS: Implemented
FUNCTION: CanIf_SetPduMode
LINES: 544-630
STATEMENT: SetPduMode transitions channel between all 7 PDU channel modes.
VERIFICATION: Code Review / State Machine Test

[REQUIREMENT]
UID: CANIF075
SWS_REF: SWS_CANIF_00075
STATUS: Implemented
FUNCTION: CanIf_GetPduMode
LINES: 632-646
STATEMENT: GetPduMode returns current channel PDU mode via output pointer.
VERIFICATION: Code Review / Unit Test

[SECTION]
TITLE: Transmission

[REQUIREMENT]
UID: CANIF005
SWS_REF: SWS_CANIF_00005
STATUS: Implemented
FUNCTION: CanIf_Transmit
LINES: 423-482
STATEMENT: CanIf_Transmit requests L-PDU transmission via the CAN Driver.
VERIFICATION: Code Review / Integration Test

[REQUIREMENT]
UID: CANIF011
SWS_REF: SWS_CANIF_00011
STATUS: Implemented
FUNCTION: CanIf_Transmit
LINES: 469
STATEMENT: CanIf_Transmit shall call Can_Write with HTH and PDU data.
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF161
SWS_REF: SWS_CANIF_00161
STATUS: Implemented
FUNCTION: CanIf_Transmit
LINES: 450-479
STATEMENT: Check CS_STARTED before transmitting; handle CAN_BUSY without buffering.
VERIFICATION: Code Review / Unit Test

[REQUIREMENT]
UID: CANIF082
SWS_REF: SWS_CANIF_00082
STATUS: Implemented
FUNCTION: CanIf_Transmit
LINES: 475-479
STATEMENT: Handle CAN_BUSY return from Can_Write (Tx buffering not supported).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF189
SWS_REF: SWS_CANIF_00189
STATUS: Implemented
FUNCTION: CanIf_SetDynamicTxId
LINES: 647-683
STATEMENT: SetDynamicTxId updates the CAN ID of a dynamic L-PDU at runtime.
VERIFICATION: Code Review / Unit Test

[REQUIREMENT]
UID: CANIF209
SWS_REF: SWS_CANIF_00209
STATUS: Not_Supported
FUNCTION: CanIf_CancelTxConfirmation
LINES: 901-914
STATEMENT: CancelTxConfirmation shall confirm cancellation of a pending Tx PDU.
VERIFICATION: Code Review

[SECTION]
TITLE: Reception

[REQUIREMENT]
UID: CANIF020
SWS_REF: SWS_CANIF_00020
STATUS: Implemented
FUNCTION: CanIf_RxIndication
LINES: 763-898
STATEMENT: RxIndication distributes received CAN frame to configured upper layer.
VERIFICATION: Code Review / Integration Test

[REQUIREMENT]
UID: CANIF025
SWS_REF: SWS_CANIF_00025
STATUS: Implemented
FUNCTION: CanIf_RxIndication
LINES: 776-788
STATEMENT: Discard received frame if PDU channel mode disables receiver path.
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF060
SWS_REF: SWS_CANIF_00060
STATUS: Implemented
FUNCTION: CanIf_RxIndication
LINES: 796-820
STATEMENT: Perform software filtering on BASIC CAN HRH using mask/ID filter.
VERIFICATION: Code Review / Unit Test

[REQUIREMENT]
UID: CANIF026
SWS_REF: SWS_CANIF_00026
STATUS: Implemented
FUNCTION: CanIf_RxIndication
LINES: 823-829
STATEMENT: Check received L-PDU DLC when DLC check is enabled (compile-time flag).
VERIFICATION: Code Review / Unit Test

[REQUIREMENT]
UID: CANIF208
SWS_REF: SWS_CANIF_00208
STATUS: Implemented
FUNCTION: CanIf_RxIndication
LINES: 853-864
STATEMENT: Call PduR_CanIfRxIndication for PDUs routed through the PDU Router.
VERIFICATION: Code Review / Integration Test

[REQUIREMENT]
UID: CANIF233
SWS_REF: SWS_CANIF_00233
STATUS: Implemented
FUNCTION: CanIf_RxIndication
LINES: 846-851
STATEMENT: Call CanNm_RxIndication for CAN Network Management PDUs.
VERIFICATION: Code Review / Integration Test

[SECTION]
TITLE: Notifications

[REQUIREMENT]
UID: CANIF013
SWS_REF: SWS_CANIF_00013
STATUS: Implemented
FUNCTION: CanIf_TxConfirmation
LINES: 742-761
STATEMENT: TxConfirmation notifies upper layer of successful L-PDU transmission.
VERIFICATION: Code Review / Integration Test

[REQUIREMENT]
UID: CANIF053
SWS_REF: SWS_CANIF_00053
STATUS: Implemented
FUNCTION: CanIf_TxConfirmation
LINES: 754-758
STATEMENT: Upper layer TX callback shall only be called when PDU channel mode allows TX.
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF019
SWS_REF: SWS_CANIF_00019
STATUS: Implemented
FUNCTION: CanIf_ControllerBusOff
LINES: 917-942
STATEMENT: ControllerBusOff sets controller to STOPPED and notifies upper layer.
VERIFICATION: Code Review / Integration Test

[REQUIREMENT]
UID: CANIF037
SWS_REF: SWS_CANIF_00037
STATUS: Implemented
FUNCTION: CanIf_SetWakeupEvent
LINES: 943-962
STATEMENT: SetWakeupEvent propagates a wakeup event to the EcuM.
VERIFICATION: Code Review

[SECTION]
TITLE: Not Supported APIs

[REQUIREMENT]
UID: CANIF194
SWS_REF: SWS_CANIF_00194
STATUS: Not_Supported
FUNCTION: CanIf_ReadRxPduData
LINES: 487-497
STATEMENT: ReadRxPduData copies received Rx data to a buffer (not implemented).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF202
SWS_REF: SWS_CANIF_00202
STATUS: Not_Supported
FUNCTION: CanIf_ReadTxNotifStatus
LINES: 503-527
STATEMENT: ReadTxNotifStatus returns TX notification status (not implemented).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF207
SWS_REF: SWS_CANIF_00207
STATUS: Not_Supported
FUNCTION: CanIf_ReadRxNotifStatus
LINES: 533-539
STATEMENT: ReadRxNotifStatus returns RX notification status (not implemented).
VERIFICATION: Code Review

[SECTION]
TITLE: Transceiver APIs

[REQUIREMENT]
UID: CANIF034
SWS_REF: SWS_CANIF_00034
STATUS: Not_Supported
FUNCTION: CanIf_SetTransceiverMode
LINES: 684-692
STATEMENT: SetTransceiverMode (not implemented).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF038
SWS_REF: SWS_CANIF_00038
STATUS: Not_Supported
FUNCTION: CanIf_GetTransceiverMode
LINES: 693-701
STATEMENT: GetTransceiverMode (not implemented).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF039
SWS_REF: SWS_CANIF_00039
STATUS: Not_Supported
FUNCTION: CanIf_GetTrcvWakeupReason
LINES: 702-710
STATEMENT: GetTrcvWakeupReason (not implemented).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF040
SWS_REF: SWS_CANIF_00040
STATUS: Not_Supported
FUNCTION: CanIf_SetTransceiverWakeupMode
LINES: 711-720
STATEMENT: SetTransceiverWakeupMode (not implemented).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF041
SWS_REF: SWS_CANIF_00041
STATUS: Not_Supported
FUNCTION: CanIf_CheckWakeup
LINES: 722-729
STATEMENT: CheckWakeup (not implemented).
VERIFICATION: Code Review

[REQUIREMENT]
UID: CANIF042
SWS_REF: SWS_CANIF_00042
STATUS: Not_Supported
FUNCTION: CanIf_CheckValidation
LINES: 730-739
STATEMENT: CheckValidation (not implemented).
VERIFICATION: Code Review
```

## Step 4: Build and Export

```bash
# Serve as a live web app
strictdoc server .

# Export to HTML
strictdoc export . --formats html

# Export to PDF (requires passthrough backend)
strictdoc export . --formats pdf
```

The HTML output at `output/html/index.html` is a full navigable document with a built-in traceability matrix view.

---

# Option D — OpenFastTrace / OFT (Automated Tag-Based Tracing, Free)

OFT is specifically designed for code where requirements are tagged inline — exactly like the `CANIF053`, `CANIF092` tags already in `CanIf.c`.

## Step 1: Install Java

OFT requires Java 11+:

```bash
java -version
```

If not installed: download from adoptium.net (free, Temurin build).

## Step 2: Download OFT

```bash
# Download the latest OFT jar
# Visit: https://github.com/itsallcode/openfasttrace/releases
# Download: openfasttrace-x.x.x.jar
```

Or using PowerShell:

```powershell
Invoke-WebRequest -Uri "https://github.com/itsallcode/openfasttrace/releases/download/3.7.0/openfasttrace-3.7.0.jar" -OutFile "oft.jar"
```

## Step 3: Create a Requirements Spec File

OFT reads requirements from a markdown file using a specific tag format. Create `canif_reqs.md`:

```markdown
# CanIf Requirements

`req~CANIF001~1`
CanIf_Init shall initialize all internal variables.
Needs: impl

`req~CANIF053~1`
Upper layer TX callback only called when PDU mode allows TX.
Needs: impl

`req~CANIF092~1`
Stop controller if STARTED before re-init.
Needs: impl

`req~CANIF161~1`
Check CS_STARTED before transmitting; handle CAN_BUSY without buffering.
Needs: impl
```

## Step 4: Tag the Source Code

OFT searches for tags in comments inside the C source. The tags already exist in `CanIf.c`. OFT recognizes these patterns:

```c
// CANIF053 already at line 757 — OFT reads this as: impl~CANIF053~1
```

However OFT needs a specific format. Add these to `CanIf.c` comments where the CANIF tags already exist:

```c
entry->CanIfUserTxConfirmation(entry->CanIfTxPduId); /* impl~CANIF053~1 */
```

The format is: `impl~<REQ_ID>~<version>`

## Step 5: Run OFT

```bash
java -jar oft.jar trace canif_reqs.md OpenSAR/communication/CanIf/CanIf.c -o canif_trace_report.html -f html
```

## Step 6: Read the Report

Open `canif_trace_report.html` — OFT shows:
- Which requirements have implementation tags
- Which are uncovered
- Coverage percentage

---

# Option E — Fully Manual (No Tools, Just Markdown + Git)

If you want zero dependencies, the files already generated are your complete deliverable. Here is how to maintain them manually.

## The Workflow

```
AUTOSAR SWS_CanIf PDF
        |
        v
Read requirement number (e.g. [CANIF053])
        |
        v
Search CanIf.c for that tag:
  grep -n "CANIF053" OpenSAR/communication/CanIf/CanIf.c
        |
        v
Record in CanIf_Traceability_Matrix.csv:
  - Req_ID        = CANIF053
  - SWS_Reference = SWS_CANIF_00053
  - Function      = CanIf_TxConfirmation
  - Start_Line    = 742
  - End_Line      = 761
  - Status        = Implemented
        |
        v
Update CanIf_Traceability_Summary.md table
```

## How to Find All Tags in the Code

Run this in your terminal from the project root:

```bash
grep -n "CANIF[0-9]\+" OpenSAR/communication/CanIf/CanIf.c
```

Output maps every CANIF number to the line it appears on. Cross-reference with the AUTOSAR SWS_CanIf document (free download from autosar.org, search "SWS_CanIf").

## How to Find All DET Errors

```bash
grep -n "CANIF_E_" OpenSAR/communication/CanIf/CanIf.c
```

---

# Recommended Workflow for a Grad Project

```
Step 1 — Open CanIf_Traceability_Matrix.csv in Excel          (5 min)
Step 2 — Apply color coding by Status column                   (5 min)
Step 3 — Add the Dashboard sheet with COUNTIF charts           (10 min)
Step 4 — Export to PDF                                         (2 min)
Step 5 — Submit PDF + CSV as appendix to your report
```

If your supervisor wants a professional tool output:

```
Step 1 — pip install strictdoc                                 (2 min)
Step 2 — Copy canif_requirements.sdoc from this guide          (already written above)
Step 3 — strictdoc export . --formats html                     (1 min)
Step 4 — Submit the output/html folder or zip it
```

---

# Coverage Numbers to Include in Your Report

| Metric | Value |
|--------|-------|
| Total AUTOSAR SWS_CanIf requirements traced | 45 |
| Fully implemented | 27 (73%) |
| Not supported (flagged with DET) | 10 (27%) |
| ArcCore-specific extensions | 8 |
| Functions analyzed | 30 |
| Source lines analyzed | 996 |
| DET error types covered | 10 |

---

# AUTOSAR SWS_CanIf — Where to Get the Official Spec

1. Go to **autosar.org**
2. Navigate to: Classic Platform → Specifications → Communication → CAN Interface
3. Search for: `AUTOSAR_SWS_CANInterface`
4. Download the PDF (free, no account required)
5. Requirement IDs in the spec are formatted as `[CANIF<number>]` — they match the tags in `CanIf.c` exactly
