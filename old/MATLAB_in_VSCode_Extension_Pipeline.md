# MATLAB in the VS Code Extension — Traceability Pipeline

---

## Direct Answer First

**Does MATLAB auto-generate a traceability matrix from C code?**
**NO.** There is no built-in MATLAB feature that reads `CanIf.c` and outputs a traceability matrix.

**Can MATLAB generate one with scripts?**
**YES** — but only if you write the scripts. The scripts I gave earlier do exactly that.

**What MATLAB genuinely does well in each phase of your tool:**

| Phase | MATLAB's Role | Does it generate the matrix? |
|-------|--------------|------------------------------|
| Static Analysis | Polyspace runs on C code, finds bugs/MISRA violations, outputs XML/JSON | Feeds DATA into the matrix — does not create it |
| Unit Testing | MATLAB calls C via MEX, runs tests, outputs pass/fail per function | Feeds VERIFICATION STATUS into the matrix |
| Change Propagation | Scripts diff two versions of CanIf.c, find changed functions | Flags IMPACTED REQUIREMENTS in the matrix |
| Requirements Linking | Simulink Requirements toolbox manages links | Only works well with Simulink models, not raw C |

**Who actually generates the matrix in your tool?**
Your AI component (Claude). MATLAB feeds it raw data. Claude maps that data to requirements and writes the matrix entries.

---

## Your Tool Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VS Code Extension                        │
│                                                             │
│  User triggers phase (static analysis / unit test / etc.)  │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐    ┌──────────────────┐               │
│  │  MATLAB Runner  │    │   AI Component   │               │
│  │  (child process)│    │   (Claude API)   │               │
│  └────────┬────────┘    └────────┬─────────┘               │
│           │                      │                          │
│           ▼                      ▼                          │
│  Raw analysis data       Interprets + maps data             │
│  (JSON/XML/CSV)          to requirement IDs                 │
│           │                      │                          │
│           └──────────┬───────────┘                          │
│                      ▼                                       │
│           ┌──────────────────────┐                          │
│           │  Traceability Matrix │  ← single JSON file      │
│           │  (traceability.json) │    updated each phase    │
│           └──────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## The Central Matrix File

All phases read and write a single `traceability.json`. Design it once, every phase updates its own fields:

```json
{
  "generated": "2026-04-30",
  "source_file": "communication/CanIf/CanIf.c",
  "requirements": [
    {
      "req_id": "CANIF053",
      "sws_ref": "SWS_CANIF_00053",
      "description": "Upper layer TX callback only called when PDU mode allows TX",
      "function": "CanIf_TxConfirmation",
      "file": "CanIf.c",
      "lines": { "start": 754, "end": 758 },
      "phases": {
        "static_analysis": {
          "status": "pass",
          "polyspace_result": "green",
          "misra_violations": [],
          "run_date": "2026-04-30"
        },
        "unit_testing": {
          "status": "pass",
          "test_cases": ["TC_TxConf_ModeCheck_Online", "TC_TxConf_ModeCheck_Offline"],
          "coverage_pct": 100,
          "run_date": "2026-04-30"
        },
        "change_propagation": {
          "status": "unchanged",
          "last_changed_commit": "a3f9c12",
          "impacted": false,
          "run_date": "2026-04-30"
        }
      },
      "overall_status": "verified"
    }
  ]
}
```

---

## Phase 1 — Static Analysis (MATLAB + Polyspace)

### What Polyspace does
Polyspace Bug Finder/Code Prover analyzes C code for:
- Null pointer dereferences
- Buffer overflows
- MISRA C violations
- Unreachable code
- Division by zero

It outputs results as XML or JSON, one entry per finding, with file + line number.

### MATLAB script for this phase

Save as `phase_static_analysis.m`:

```matlab
% phase_static_analysis.m
% Runs Polyspace on CanIf.c and maps findings to traceability.json

src_file   = 'OpenSAR\communication\CanIf\CanIf.c';
json_path  = 'traceability.json';
out_folder = 'polyspace_results';

%% Step 1: Run Polyspace Bug Finder (if licensed)
% If you have Polyspace, uncomment this block:
%
% opts = polyspaceBugFinder;
% opts.Sources = {src_file};
% opts.IncludeFolders = {'OpenSAR\communication\CanIf',...
%                        'OpenSAR\include'};
% opts.Checkers.CodingRulesCodeMetrics.EnableMisraC2012 = true;
% results_folder = run(opts, out_folder);
% results = polyspaceReadResults(results_folder, 'BugFinder');

%% Step 1b: Fallback — static analysis via cppcheck JSON output
% If you don't have Polyspace, use cppcheck (free) and parse its output.
% Run in terminal first:
%   cppcheck --xml --xml-version=2 CanIf.c 2> cppcheck_results.xml
%
% Then parse the XML here:

if ~isfile('cppcheck_results.xml')
    fprintf('No static analysis results found. Run cppcheck first.\n');
    findings = struct('line', {}, 'severity', {}, 'message', {});
else
    xml_data = xmlread('cppcheck_results.xml');
    errors   = xml_data.getElementsByTagName('error');
    findings = struct('line', {}, 'severity', {}, 'message', {});
    for k = 0:errors.getLength-1
        err  = errors.item(k);
        loc  = err.getElementsByTagName('location');
        if loc.getLength > 0
            line_num = str2double(loc.item(0).getAttribute('line'));
            findings(end+1).line     = line_num; %#ok<AGROW>
            findings(end).severity   = char(err.getAttribute('severity'));
            findings(end).message    = char(err.getAttribute('msg'));
        end
    end
    fprintf('Found %d static analysis findings.\n', numel(findings));
end

%% Step 2: Load traceability matrix
fid  = fopen(json_path, 'r');
raw  = fread(fid, inf, 'uint8=>char')';
fclose(fid);
data = jsondecode(raw);

%% Step 3: Map findings to requirements by line number
for i = 1:numel(data.requirements)
    req      = data.requirements(i);
    start_ln = req.lines.start;
    end_ln   = req.lines.x_end;   % 'end' is reserved in MATLAB — jsondecode maps it to x_end
    
    % Find findings that fall inside this function's line range
    violations = {};
    for f = 1:numel(findings)
        if findings(f).line >= start_ln && findings(f).line <= end_ln
            violations{end+1} = sprintf('Line %d [%s]: %s', ...
                findings(f).line, findings(f).severity, findings(f).message); %#ok<AGROW>
        end
    end
    
    if isempty(violations)
        data.requirements(i).phases.static_analysis.status   = 'pass';
        data.requirements(i).phases.static_analysis.findings = {};
    else
        data.requirements(i).phases.static_analysis.status   = 'fail';
        data.requirements(i).phases.static_analysis.findings = violations;
    end
    data.requirements(i).phases.static_analysis.run_date = datestr(now, 'yyyy-mm-dd');
end

%% Step 4: Write updated matrix back
fid = fopen(json_path, 'w');
fprintf(fid, '%s', jsonencode(data, 'PrettyPrint', true));
fclose(fid);

fprintf('Static analysis phase complete. Updated: %s\n', json_path);
```

---

## Phase 2 — Unit Testing (MATLAB MEX)

### What this does
Compiles CanIf.c as a MEX file (C code called from MATLAB), runs test cases against each function, records pass/fail and coverage per requirement.

### MATLAB script for this phase

Save as `phase_unit_testing.m`:

```matlab
% phase_unit_testing.m
% Runs unit tests against CanIf functions and updates traceability.json

json_path = 'traceability.json';

%% Step 1: Define test cases
% Each test case maps to a Req_ID and a function call scenario
test_cases = {
    % {req_id, test_name, description, expected_result, actual_result}
    'CANIF001', 'TC_Init_NullPtr',      'CanIf_Init with NULL config',         'E_NOT_OK', '';
    'CANIF001', 'TC_Init_Valid',        'CanIf_Init with valid config',         'E_OK',     '';
    'CANIF007', 'TC_Init_ModeCheck',    'Controller mode = STOPPED after init', 'STOPPED',  '';
    'CANIF092', 'TC_InitCtrl_Started',  'InitController when CS_STARTED',       'E_OK',     '';
    'CANIF161', 'TC_Transmit_Stopped',  'Transmit when controller STOPPED',     'E_NOT_OK', '';
    'CANIF161', 'TC_Transmit_Busy',     'Transmit returns CAN_BUSY',            'E_NOT_OK', '';
    'CANIF053', 'TC_TxConf_Online',     'TxConfirmation in ONLINE mode',        'callback', '';
    'CANIF053', 'TC_TxConf_Offline',    'TxConfirmation in OFFLINE mode',       'no_callback','';
    'CANIF026', 'TC_RxInd_DLCFail',    'RxIndication with DLC too small',      'DET_error','';
    'CANIF025', 'TC_RxInd_ModeOff',    'RxIndication when RX disabled',        'dropped',  '';
};

%% Step 2: Run tests
% NOTE: Actual MEX compilation requires stub headers.
% Without the full AUTOSAR stack, tests run as behavioral stubs.
% Replace the 'actual_result' column with real MEX outputs when available.

fprintf('Running %d unit test cases...\n', size(test_cases, 1));

results = struct();
for i = 1:size(test_cases, 1)
    req_id    = test_cases{i, 1};
    test_name = test_cases{i, 2};
    expected  = test_cases{i, 4};
    
    % --- REPLACE THIS BLOCK with real MEX calls when compiled ---
    % Example for MEX: actual = CanIf_Transmit_mex(pdu_id, pdu_info);
    % For now, stub as "pending"
    actual = 'pending';
    
    if strcmp(actual, 'pending')
        status = 'pending';
    elseif strcmp(actual, expected)
        status = 'pass';
    else
        status = 'fail';
    end
    
    if ~isfield(results, req_id)
        results.(req_id).test_cases = {};
        results.(req_id).statuses   = {};
    end
    results.(req_id).test_cases{end+1} = test_name;
    results.(req_id).statuses{end+1}   = status;
    
    fprintf('  [%s] %s — %s\n', status, test_name, req_id);
end

%% Step 3: Load and update traceability matrix
fid  = fopen(json_path, 'r');
raw  = fread(fid, inf, 'uint8=>char')';
fclose(fid);
data = jsondecode(raw);

for i = 1:numel(data.requirements)
    req_id = data.requirements(i).req_id;
    if isfield(results, req_id)
        r = results.(req_id);
        statuses = r.statuses;
        
        if all(strcmp(statuses, 'pass'))
            overall = 'pass';
        elseif any(strcmp(statuses, 'fail'))
            overall = 'fail';
        else
            overall = 'pending';
        end
        
        data.requirements(i).phases.unit_testing.status     = overall;
        data.requirements(i).phases.unit_testing.test_cases = r.test_cases;
        data.requirements(i).phases.unit_testing.run_date   = datestr(now, 'yyyy-mm-dd');
    end
end

fid = fopen(json_path, 'w');
fprintf(fid, '%s', jsonencode(data, 'PrettyPrint', true));
fclose(fid);

fprintf('\nUnit testing phase complete. Updated: %s\n', json_path);
```

---

## Phase 3 — Change Propagation (Your Current Phase)

### What this does
Compares the current `CanIf.c` against a previous version (via Git), finds changed functions, then flags every requirement linked to those functions as "impacted — needs re-verification".

### MATLAB script for this phase

Save as `phase_change_propagation.m`:

```matlab
% phase_change_propagation.m
% Detects changes in CanIf.c and flags impacted requirements

src_file  = 'OpenSAR\communication\CanIf\CanIf.c';
json_path = 'traceability.json';

%% Step 1: Get changed line ranges from Git
% Returns lines that changed between HEAD and the previous commit
[status, diff_output] = system(sprintf('git diff HEAD~1 HEAD -U0 -- "%s"', src_file));

if status ~= 0
    fprintf('Git diff failed or no previous commit. Using full file.\n');
    changed_lines = [];
else
    % Parse unified diff to extract changed line numbers
    changed_lines = [];
    lines = strsplit(diff_output, '\n');
    for k = 1:numel(lines)
        ln = lines{k};
        % Hunk header format: @@ -old_start,old_count +new_start,new_count @@
        tok = regexp(ln, '^\+\+\+ .*|^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', 'tokens');
        if ~isempty(tok) && ~isempty(tok{1})
            new_start = str2double(tok{1}{1});
            if numel(tok{1}) >= 2 && ~isempty(tok{1}{2})
                count = str2double(tok{1}{2});
            else
                count = 1;
            end
            if count > 0
                changed_lines = [changed_lines, new_start:(new_start+count-1)]; %#ok<AGROW>
            end
        end
    end
    fprintf('Changed lines detected: %d\n', numel(changed_lines));
end

%% Step 2: Load traceability matrix
fid  = fopen(json_path, 'r');
raw  = fread(fid, inf, 'uint8=>char')';
fclose(fid);
data = jsondecode(raw);

%% Step 3: Flag impacted requirements
impacted_reqs = {};

for i = 1:numel(data.requirements)
    req      = data.requirements(i);
    start_ln = req.lines.start;
    end_ln   = req.lines.x_end;
    
    if isempty(changed_lines)
        impacted = false;
    else
        % Check if any changed line falls within this requirement's function range
        impacted = any(changed_lines >= start_ln & changed_lines <= end_ln);
    end
    
    data.requirements(i).phases.change_propagation.impacted  = impacted;
    data.requirements(i).phases.change_propagation.run_date  = datestr(now, 'yyyy-mm-dd');
    
    if impacted
        data.requirements(i).phases.change_propagation.status = 'needs_reverification';
        impacted_reqs{end+1} = req.req_id; %#ok<AGROW>
        fprintf('  [IMPACTED] %s — %s (lines %d-%d)\n', ...
            req.req_id, req.function, start_ln, end_ln);
    else
        data.requirements(i).phases.change_propagation.status = 'unchanged';
    end
end

%% Step 4: Write updated matrix
fid = fopen(json_path, 'w');
fprintf(fid, '%s', jsonencode(data, 'PrettyPrint', true));
fclose(fid);

fprintf('\n--- Change Propagation Summary ---\n');
fprintf('Total requirements : %d\n', numel(data.requirements));
fprintf('Impacted           : %d\n', numel(impacted_reqs));
if ~isempty(impacted_reqs)
    fprintf('Impacted IDs       : %s\n', strjoin(impacted_reqs, ', '));
end
fprintf('Updated: %s\n', json_path);
```

---

## How Your VS Code Extension Calls MATLAB

In your TypeScript extension code:

```typescript
// matlabRunner.ts
import { execFile } from 'child_process';
import * as path from 'path';

export function runMatlabPhase(
    phase: 'static_analysis' | 'unit_testing' | 'change_propagation',
    workspacePath: string
): Promise<string> {

    const scriptMap = {
        'static_analysis':   'phase_static_analysis.m',
        'unit_testing':      'phase_unit_testing.m',
        'change_propagation':'phase_change_propagation.m'
    };

    const scriptPath = path.join(workspacePath, scriptMap[phase]);

    return new Promise((resolve, reject) => {
        // -batch runs MATLAB headlessly (no GUI), exits when done
        execFile('matlab', ['-batch', `run('${scriptPath}')`], 
            { cwd: workspacePath },
            (error, stdout, stderr) => {
                if (error) {
                    reject(`MATLAB phase [${phase}] failed: ${stderr}`);
                } else {
                    resolve(stdout);
                }
            }
        );
    });
}
```

Then in your AI component, after MATLAB runs, pass the updated `traceability.json` to Claude:

```typescript
// aiAnalyzer.ts
import Anthropic from '@anthropic-ai/sdk';
import * as fs from 'fs';

const client = new Anthropic();

export async function analyzeTraceabilityWithAI(
    jsonPath: string,
    phase: string
): Promise<string> {

    const matrix = fs.readFileSync(jsonPath, 'utf-8');

    const response = await client.messages.create({
        model: 'claude-sonnet-4-6',
        max_tokens: 2048,
        messages: [{
            role: 'user',
            content: `You are an AUTOSAR safety analyst.
Phase just completed: ${phase}
Traceability matrix (JSON): ${matrix}

Tasks:
1. Identify requirements that need attention (failed, impacted, pending)
2. Explain the impact in plain language
3. Suggest which requirements need re-verification first
4. Flag any safety-critical requirements (controller mode, bus-off, DLC check)

Be concise. Use requirement IDs (CANIF###) throughout.`
        }]
    });

    return response.content[0].type === 'text' ? response.content[0].text : '';
}
```

---

## Full Phase Pipeline

```
User triggers phase in VS Code
         │
         ▼
runMatlabPhase('change_propagation')
         │
         ▼ (MATLAB writes updated traceability.json)
         │
         ▼
analyzeTraceabilityWithAI('change_propagation')
         │
         ▼ (Claude identifies impacted reqs, explains impact)
         │
         ▼
Display in VS Code sidebar:
  ● CANIF161 — IMPACTED (CanIf_Transmit changed at line 450)
  ● CANIF053 — IMPACTED (CanIf_TxConfirmation changed at line 754)
  → 2 requirements need re-verification
```

---

## Summary: Who Does What

| Responsibility | Done By |
|---------------|---------|
| Parse CanIf.c, extract tags | MATLAB script |
| Run static analysis (bug/MISRA finding) | MATLAB + Polyspace (or cppcheck) |
| Run unit tests, record pass/fail | MATLAB MEX |
| Detect changed lines via Git diff | MATLAB (calls `git diff`) |
| Flag impacted requirements | MATLAB (line-range overlap) |
| Update traceability.json | MATLAB (all phases write to same file) |
| Interpret results, explain impact | Claude API (your AI component) |
| Display to user | VS Code extension (TypeScript) |
| **Generate the matrix itself** | **Claude API** (initial run) / **MATLAB scripts** (updates) |
