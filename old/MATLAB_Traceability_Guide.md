# MATLAB for CanIf Traceability — What It Can Actually Do

---

## Honest Assessment First

| Use Case | MATLAB Useful? | Why |
|----------|---------------|-----|
| Auto-extract CANIF tags from CanIf.c | YES — best option | MATLAB regex is powerful and scriptable |
| Generate coverage charts and visualizations | YES — excellent | MATLAB plots are publication-quality |
| Generate a formatted PDF report | YES — built-in | Report Generator toolbox (included in most licenses) |
| Requirements management with trace links | PARTIAL | Simulink Requirements toolbox works, but it's designed for Simulink models, not raw C |
| Replace Excel/StrictDoc for the matrix itself | NO | Overkill — use the CSV you already have |

**Bottom line:** MATLAB is most useful here as a **parser + visualizer + report generator**, not as a traceability management tool for pure C code.

---

## What You Need

- MATLAB R2020a or later (any edition, including student)
- No extra toolboxes required for scripts below
- Optional: Report Generator toolbox (usually included in student licenses)

---

# Part 1 — Auto-Extract Requirements Tags from CanIf.c

This script reads `CanIf.c`, finds every `CANIF` tag, and builds a table automatically. Run this before manually filling the matrix to verify nothing was missed.

Save as `extract_canif_tags.m`:

```matlab
% extract_canif_tags.m
% Scans CanIf.c and extracts all CANIF requirement tags with line numbers

canif_path = 'OpenSAR\communication\CanIf\CanIf.c';

fid = fopen(canif_path, 'r');
if fid == -1
    error('Cannot open file: %s', canif_path);
end

lines = {};
while ~feof(fid)
    lines{end+1} = fgetl(fid); %#ok<AGROW>
end
fclose(fid);

% Regex: match CANIF followed by digits OR CANIF_ followed by word chars
pattern = 'CANIF[0-9]+|CANIF_[A-Z_]+';

results = {};  % {line_number, tag, context}

for i = 1:numel(lines)
    line = lines{i};
    [tokens, matches] = regexp(line, pattern, 'tokens', 'match');
    if ~isempty(matches)
        for j = 1:numel(matches)
            tag = matches{j};
            % Skip DET error macros (they are validators, not req tags)
            if ~startsWith(tag, 'CANIF_E_') && ...
               ~strcmp(tag, 'CANIF_INIT_ID') && ...
               ~contains(tag, '_ID')
                results(end+1, :) = {i, tag, strtrim(line)}; %#ok<AGROW>
            end
        end
    end
end

% Convert to table
if isempty(results)
    disp('No CANIF tags found.');
else
    T = cell2table(results, 'VariableNames', {'Line', 'Tag', 'Context'});
    % Remove duplicate tag entries (keep first occurrence)
    [~, idx] = unique(T.Tag, 'stable');
    T_unique = T(idx, :);
    
    disp('=== CANIF Requirement Tags Found in CanIf.c ===');
    disp(T_unique);
    
    % Save to CSV
    writetable(T_unique, 'canif_tags_extracted.csv');
    fprintf('\nSaved to canif_tags_extracted.csv\n');
    fprintf('Total unique tags: %d\n', height(T_unique));
end
```

**Run it:**
```matlab
>> cd('D:\ASU\GradProject\CANIF_NEEK')
>> extract_canif_tags
```

---

# Part 2 — Coverage Visualization (Charts)

This script reads `CanIf_Traceability_Matrix.csv` and generates 3 publication-quality charts.

Save as `plot_traceability_coverage.m`:

```matlab
% plot_traceability_coverage.m
% Reads the traceability matrix CSV and generates coverage charts

csv_path = 'CanIf_Traceability_Matrix.csv';
T = readtable(csv_path, 'TextType', 'string');

% ---------------------------------------------------------------
% Chart 1: Pie chart — Implementation Status Distribution
% ---------------------------------------------------------------
statuses = T.Implementation_Status;

% Normalize status labels into 3 groups
groups = strings(height(T), 1);
for i = 1:height(T)
    s = statuses(i);
    if contains(s, "Not Supported")
        groups(i) = "Not Supported";
    elseif contains(s, "ArcCore") || contains(s, "internal") || contains(s, "Extension")
        groups(i) = "ArcCore Extension";
    else
        groups(i) = "Implemented";
    end
end

cats     = ["Implemented", "Not Supported", "ArcCore Extension"];
counts   = [sum(groups == "Implemented"), ...
            sum(groups == "Not Supported"), ...
            sum(groups == "ArcCore Extension")];

figure('Name', 'Coverage Pie Chart', 'Position', [100 100 600 500]);
explode = [0, 1, 0];  % explode "Not Supported" slice
p = pie(counts, explode);

% Color the slices
colors = [0.18 0.63 0.27;   % green  - Implemented
          0.85 0.20 0.20;   % red    - Not Supported
          0.20 0.45 0.75];  % blue   - ArcCore Extension
for k = 1:3
    p(2*k-1).FaceColor = colors(k, :);
end

labels = compose('%s\n(%d)', cats, counts);
legend(labels, 'Location', 'southoutside', 'FontSize', 10);
title('CanIf.c — Requirement Implementation Status', 'FontSize', 13, 'FontWeight', 'bold');
saveas(gcf, 'chart_pie_coverage.png');
fprintf('Saved: chart_pie_coverage.png\n');

% ---------------------------------------------------------------
% Chart 2: Horizontal bar chart — Requirements per Function
% ---------------------------------------------------------------
funcs        = T.Function;
unique_funcs = unique(funcs, 'stable');
func_counts  = arrayfun(@(f) sum(funcs == f), unique_funcs);

% Sort by count
[func_counts_sorted, idx] = sort(func_counts, 'ascend');
funcs_sorted = unique_funcs(idx);

figure('Name', 'Requirements per Function', 'Position', [100 100 750 600]);
barh(func_counts_sorted, 'FaceColor', [0.20 0.45 0.75], 'EdgeColor', 'none');
yticks(1:numel(funcs_sorted));
yticklabels(funcs_sorted);
xlabel('Number of Requirements Traced', 'FontSize', 11);
title('CanIf.c — Requirements Traced per Function', 'FontSize', 13, 'FontWeight', 'bold');
grid on;
ax = gca;
ax.XMinorGrid = 'on';
saveas(gcf, 'chart_bar_per_function.png');
fprintf('Saved: chart_bar_per_function.png\n');

% ---------------------------------------------------------------
% Chart 3: Grouped bar chart — Implemented vs Not Supported by Section
% ---------------------------------------------------------------
sections = {
    'Initialization',   {'CANIF001','CANIF007','CANIF008','CANIF066','CANIF092','CANIF293'};
    'Controller Mode',  {'CANIF017','CANIF021','CANIF022','CANIF023'};
    'PDU Mode',         {'CANIF072','CANIF075'};
    'Transmission',     {'CANIF005','CANIF011','CANIF161','CANIF082','CANIF189','CANIF209'};
    'Reception',        {'CANIF020','CANIF025','CANIF060','CANIF026','CANIF208','CANIF233'};
    'Notifications',    {'CANIF013','CANIF053','CANIF019','CANIF037'};
    'Transceiver/Other',{'CANIF034','CANIF038','CANIF039','CANIF040','CANIF041','CANIF042','CANIF194','CANIF202','CANIF207'};
};

sec_names = {};
sec_impl  = [];
sec_nosup = [];

for s = 1:size(sections, 1)
    sec_name = sections{s, 1};
    req_ids  = sections{s, 2};
    impl  = 0;
    nosup = 0;
    for r = 1:numel(req_ids)
        row = T(T.Req_ID == string(req_ids{r}), :);
        if ~isempty(row)
            st = row.Implementation_Status(1);
            if contains(st, "Not Supported")
                nosup = nosup + 1;
            else
                impl = impl + 1;
            end
        end
    end
    sec_names{end+1} = sec_name; %#ok<AGROW>
    sec_impl(end+1)  = impl;     %#ok<AGROW>
    sec_nosup(end+1) = nosup;    %#ok<AGROW>
end

figure('Name', 'Coverage by Section', 'Position', [100 100 800 500]);
b = bar([sec_impl; sec_nosup]', 'grouped');
b(1).FaceColor = [0.18 0.63 0.27];
b(2).FaceColor = [0.85 0.20 0.20];
b(1).EdgeColor = 'none';
b(2).EdgeColor = 'none';
xticks(1:numel(sec_names));
xticklabels(sec_names);
xtickangle(25);
ylabel('Number of Requirements', 'FontSize', 11);
title('CanIf.c — Coverage by Functional Section', 'FontSize', 13, 'FontWeight', 'bold');
legend({'Implemented', 'Not Supported'}, 'Location', 'northeast');
grid on;
saveas(gcf, 'chart_bar_by_section.png');
fprintf('Saved: chart_bar_by_section.png\n');

% ---------------------------------------------------------------
% Print summary to console
% ---------------------------------------------------------------
total      = height(T);
n_impl     = sum(groups == "Implemented");
n_nosup    = sum(groups == "Not Supported");
n_arc      = sum(groups == "ArcCore Extension");
pct_impl   = round(100 * n_impl / total);

fprintf('\n========== COVERAGE SUMMARY ==========\n');
fprintf('Total requirements traced : %d\n', total);
fprintf('Implemented               : %d  (%d%%)\n', n_impl,  pct_impl);
fprintf('Not Supported             : %d  (%d%%)\n', n_nosup, round(100*n_nosup/total));
fprintf('ArcCore Extensions        : %d  (%d%%)\n', n_arc,   round(100*n_arc/total));
fprintf('=======================================\n');
```

**Run it:**
```matlab
>> cd('D:\ASU\GradProject\CANIF_NEEK')
>> plot_traceability_coverage
```

Produces 3 PNG files ready to drop into your report:
- `chart_pie_coverage.png`
- `chart_bar_per_function.png`
- `chart_bar_by_section.png`

---

# Part 3 — Generate a PDF Report (Report Generator)

This uses MATLAB's built-in `mlreportgen` (included in most MATLAB licenses, including student).

Check if you have it first:
```matlab
>> ver mlreportgen
```

If it shows a version, you have it. If not, skip to Part 3B.

Save as `generate_traceability_report.m`:

```matlab
% generate_traceability_report.m
% Generates a formatted PDF traceability report

import mlreportgen.report.*
import mlreportgen.dom.*

csv_path = 'CanIf_Traceability_Matrix.csv';
T = readtable(csv_path, 'TextType', 'string');

% Create report
rpt = Report('CanIf_Traceability_Report', 'pdf');
rpt.Title = 'CanIf Traceability Matrix Report';

% --- Cover Page ---
tp = TitlePage;
tp.Title   = 'CanIf Traceability Matrix';
tp.Subtitle = 'OpenSAR — communication/CanIf/CanIf.c';
tp.Author  = 'Generated by MATLAB';
tp.PubDate = datestr(now, 'yyyy-mm-dd');
add(rpt, tp);

% --- Table of Contents ---
add(rpt, TableOfContents);

% --- Section 1: Summary ---
ch1 = Chapter('Title', 'Coverage Summary');

total  = height(T);
n_impl = sum(contains(T.Implementation_Status, "Implemented") & ...
             ~contains(T.Implementation_Status, "ArcCore") & ...
             ~contains(T.Implementation_Status, "internal"));
n_nosup = sum(contains(T.Implementation_Status, "Not Supported"));
n_arc   = total - n_impl - n_nosup;

summary_text = Paragraph(sprintf( ...
    'This document traces %d requirements from the AUTOSAR SWS_CanIf specification ' ...
    'to their implementation in CanIf.c (996 lines, 30 functions).\n\n' ...
    'Implemented: %d (%d%%)\nNot Supported: %d (%d%%)\nArcCore Extensions: %d', ...
    total, n_impl, round(100*n_impl/total), n_nosup, round(100*n_nosup/total), n_arc));
add(ch1, summary_text);

% Embed pie chart if it exists
if isfile('chart_pie_coverage.png')
    img = Image('chart_pie_coverage.png');
    img.Width  = '12cm';
    img.Height = '10cm';
    add(ch1, img);
end
add(rpt, ch1);

% --- Section 2: Full Traceability Matrix Table ---
ch2 = Chapter('Title', 'Full Traceability Matrix');

% Create table with key columns only (keep it readable)
cols = {'Req_ID', 'Function', 'Start_Line', 'End_Line', 'Implementation_Status', 'Verification_Method'};
T_display = T(:, cols);

tbl = MATLABTable(T_display);
tbl.Style = {FontSize('8pt'), FontFamily('Courier New')};

% Color header row
tbl.Header.Style = {Bold(true), ...
                    BackgroundColor(Color('4472C4')), ...
                    Color(Color('white'))};
add(ch2, tbl);
add(rpt, ch2);

% --- Section 3: Not Supported Requirements ---
ch3 = Chapter('Title', 'Not Supported Requirements');

T_nosup = T(contains(T.Implementation_Status, "Not Supported"), :);
p = Paragraph(sprintf('%d requirements are not supported in this implementation. ' ...
    'Each is flagged with CANIF_E_NOK_NOSUPPORT DET error.', height(T_nosup)));
add(ch3, p);

tbl2 = MATLABTable(T_nosup(:, {'Req_ID', 'SWS_Reference', 'Requirement_Description', 'Function'}));
tbl2.Header.Style = {Bold(true), BackgroundColor(Color('C0392B')), Color(Color('white'))};
add(ch3, tbl2);
add(rpt, ch3);

% --- Close and open ---
close(rpt);
rptview(rpt);
fprintf('Report saved as: CanIf_Traceability_Report.pdf\n');
```

**Run it:**
```matlab
>> generate_traceability_report
```

---

## Part 3B — Export to Excel with Color Formatting (No Toolbox Needed)

If you don't have Report Generator, use this instead to produce a formatted Excel file:

```matlab
% export_colored_excel.m
% Exports the traceability matrix to a formatted Excel file with color coding

csv_path  = 'CanIf_Traceability_Matrix.csv';
xlsx_path = 'CanIf_Traceability_Matrix_Formatted.xlsx';

T = readtable(csv_path, 'TextType', 'string');

% Write the table to Excel
writetable(T, xlsx_path, 'Sheet', 'Traceability Matrix');

% Open Excel via COM (Windows only) and apply formatting
try
    excel = actxserver('Excel.Application');
    excel.Visible = false;
    wb = excel.Workbooks.Open(fullfile(pwd, xlsx_path));
    ws = wb.Sheets.Item('Traceability Matrix');
    
    % Format header row
    header_range = ws.Range('A1:K1');
    header_range.Interior.Color = 4472198;  % dark blue (RGB 0x4472C4 → decimal)
    header_range.Font.Color     = 16777215; % white
    header_range.Font.Bold      = true;
    header_range.RowHeight      = 20;
    
    % Color-code rows by Implementation_Status (column 8)
    status_col = 8;
    for i = 2:height(T)+1
        cell_val = ws.Cells(i, status_col).Value;
        if contains(cell_val, 'Not Supported')
            ws.Range(sprintf('A%d:K%d', i, i)).Interior.Color = 16751052;  % light red
        elseif contains(cell_val, 'ArcCore') || contains(cell_val, 'internal')
            ws.Range(sprintf('A%d:K%d', i, i)).Interior.Color = 16763904;  % light blue
        else
            ws.Range(sprintf('A%d:K%d', i, i)).Interior.Color = 13434828;  % light green
        end
    end
    
    % Auto-fit columns
    ws.Columns.AutoFit;
    
    % Freeze top row
    ws.Range('A2').Select;
    excel.ActiveWindow.FreezePanes = true;
    
    % Add a coverage summary sheet
    sum_sheet = wb.Sheets.Add;
    sum_sheet.Name = 'Coverage Summary';
    
    n_impl  = sum(contains(T.Implementation_Status, "Implemented") & ...
                  ~contains(T.Implementation_Status, "ArcCore") & ...
                  ~contains(T.Implementation_Status, "internal"));
    n_nosup = sum(contains(T.Implementation_Status, "Not Supported"));
    n_arc   = height(T) - n_impl - n_nosup;
    
    sum_sheet.Cells(1,1).Value = 'Metric';
    sum_sheet.Cells(1,2).Value = 'Count';
    sum_sheet.Cells(1,3).Value = 'Percentage';
    sum_sheet.Cells(2,1).Value = 'Total Requirements';
    sum_sheet.Cells(2,2).Value = height(T);
    sum_sheet.Cells(3,1).Value = 'Implemented';
    sum_sheet.Cells(3,2).Value = n_impl;
    sum_sheet.Cells(3,3).Value = round(100*n_impl/height(T));
    sum_sheet.Cells(4,1).Value = 'Not Supported';
    sum_sheet.Cells(4,2).Value = n_nosup;
    sum_sheet.Cells(4,3).Value = round(100*n_nosup/height(T));
    sum_sheet.Cells(5,1).Value = 'ArcCore Extensions';
    sum_sheet.Cells(5,2).Value = n_arc;
    sum_sheet.Cells(5,3).Value = round(100*n_arc/height(T));
    
    wb.Save;
    wb.Close;
    excel.Quit;
    delete(excel);
    
    fprintf('Formatted Excel saved: %s\n', xlsx_path);
    
catch ME
    fprintf('COM Excel failed: %s\nFalling back to plain writetable.\n', ME.message);
    writetable(T, xlsx_path);
end
```

---

# Part 4 — Simulink Requirements Toolbox (If You Have It)

Check first:
```matlab
>> license('test', 'Simulink_Requirements')
```

If it returns `1`, you have it.

## What It Does

Simulink Requirements lets you import your CSV as a formal requirements set and draw links to code — but it works best when you also have a Simulink model. For pure C code with no model, the workflow is:

```
CSV → Import as Requirements Set → Link to CanIf.c lines → Generate Report
```

## Step 1: Import the CSV

```matlab
% import_to_simulink_requirements.m

rs = slreq.import('CanIf_Traceability_Matrix.csv', ...
    'ReqsFilter',      @(x) true, ...
    'RichText',        false, ...
    'IDColumn',        'Req_ID', ...
    'SummaryColumn',   'Requirement_Description', ...
    'Keywords',        {'SWS_Reference', 'Function', 'Implementation_Status'});

slreq.editor;   % Opens the Requirements Editor GUI
```

## Step 2: View and Edit in the GUI

After running the import:
1. The **Requirements Editor** opens
2. Each row from the CSV is one requirement node
3. Right-click any requirement → **Link to Source** → browse to `CanIf.c` → select line range

## Step 3: Generate Traceability Report from GUI

In the Requirements Editor:
- `Analysis → Generate Report`
- Choose format: PDF or HTML
- It produces a document with all trace links

---

# Which MATLAB Approach to Use

| You want to... | Use |
|---------------|-----|
| Extract all CANIF tags from CanIf.c automatically | `extract_canif_tags.m` |
| Generate charts for your report/thesis | `plot_traceability_coverage.m` |
| Produce a formatted PDF automatically | `generate_traceability_report.m` (needs Report Generator) |
| Produce a color-coded Excel file | `export_colored_excel.m` |
| Full GUI with clickable trace links | Simulink Requirements import |

---

# Quick Start — Run All in One Go

```matlab
cd('D:\ASU\GradProject\CANIF_NEEK')

% Step 1: Extract tags from source
run('extract_canif_tags.m')

% Step 2: Generate all 3 charts
run('plot_traceability_coverage.m')

% Step 3: Export formatted Excel
run('export_colored_excel.m')

% Optional: PDF report (needs Report Generator toolbox)
% run('generate_traceability_report.m')
```

Total time: under 30 seconds. Output: `canif_tags_extracted.csv`, 3 PNG charts, and a formatted Excel file.
