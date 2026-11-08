"""
Generate HTML, LaTeX, and PDF from schedule_data.json
"""
import os
import sys
import json
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "schedule_data.json")
HTML_FILE = os.path.join(BASE_DIR, "music_teacher_schedule.html")
TEX_FILE = os.path.join(BASE_DIR, "music_teacher_schedule.tex")
PDF_FILE = os.path.join(BASE_DIR, "music_teacher_schedule.pdf")

def load_data(filepath=DATA_FILE):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot find {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_html(data):
    title = data.get("title", "Music Department Weekly Schedule")
    subtitle = data.get("subtitle", "Complete Timetable with Designated Office Hours")
    legend = data.get("legend", "")
    days = data.get("days", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"])
    rows = data.get("rows", [])
    signature_title = data.get("signatureTitle", "Music Teacher's Signature")
    footer_text = data.get("footerText", "Music Department Master Schedule")
    page_number_text = data.get("pageNumberText", "Page 1 of 1")

    # Build table rows HTML
    rows_html = []
    num_days = len(days)

    for row in rows:
        row_type = row.get("type", "period")
        time_text = row.get("time", "")
        if row_type == "break":
            label = row.get("label", "BREAK")
            row_markup = f"""
            <tr class="break-row">
                <td class="time-col"><strong>{time_text}</strong></td>
                <td colspan="{num_days}" class="break-cell"><strong>{label}</strong></td>
            </tr>
            """
            rows_html.append(row_markup)
        else:
            label = row.get("label", "")
            cells = row.get("cells", {})
            cell_tds = []
            for day in days:
                c = cells.get(day, {"type": "empty", "text": "---", "subtext": ""})
                c_type = c.get("type", "empty")
                c_text = c.get("text", "---")
                c_subtext = c.get("subtext", "")
                c_bg = c.get("bgColor", "")
                c_color = c.get("textColor", "")

                custom_style = ""
                if c_bg:
                    custom_style += f"background-color: {c_bg} !important; "
                if c_color:
                    custom_style += f"color: {c_color} !important; "

                if c_type == "empty" or c_text == "---":
                    cell_tds.append(f'<td class="cell empty-cell" style="{custom_style}"><span class="dash">---</span></td>')
                elif c_type == "office_hour_best":
                    cell_tds.append(f"""<td class="cell office-best" style="{custom_style}">
                        <div class="cell-title">{c_text}</div>
                        <div class="cell-sub best">{c_subtext or 'Best Option'}</div>
                    </td>""")
                elif c_type == "office_hour":
                    cell_tds.append(f"""<td class="cell office-opt" style="{custom_style}">
                        <div class="cell-title">{c_text}</div>
                        <div class="cell-sub">{c_subtext or 'Option'}</div>
                    </td>""")
                else: # custom or class
                    sub_div = f'<div class="cell-sub">{c_subtext}</div>' if c_subtext else ''
                    cell_tds.append(f"""<td class="cell class-cell" style="{custom_style}">
                        <div class="cell-title">{c_text}</div>
                        {sub_div}
                    </td>""")

                row_markup = f"""
            <tr>
                <td class="time-col">
                    <div class="time-main">{time_text}</div>
                    <div class="time-sub">{label}</div>
                </td>
                {''.join(cell_tds)}
            </tr>
            """
            rows_html.append(row_markup)

    days_headers = "".join([f"<th>{d}</th>" for d in days])
    legend_html = f"""
    <div class="legend-box">
        <strong>Schedule Legend:</strong> {legend.replace("Schedule Legend:", "").strip()}
    </div>
    """ if legend else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 20mm 18mm 18mm 18mm;
        }}
        * {{
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
        body {{
            margin: 0;
            padding: 0;
            background-color: #f8fafc;
            color: #111827;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.35;
        }}
        .page-container {{
            width: 210mm;
            min-height: 297mm;
            margin: 0 auto;
            background: #ffffff;
            padding: 20mm 18mm 18mm 18mm;
            display: flex;
            flex-direction: column;
            position: relative;
        }}
        @media print {{
            body {{
                background: none;
            }}
            .page-container {{
                width: 100% !important;
                min-height: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                box-shadow: none !important;
            }}
            .no-print {{
                display: none !important;
            }}
        }}

        /* Header */
        .doc-header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .doc-title {{
            font-size: 20pt;
            font-weight: 800;
            color: #0f172a;
            margin: 0 0 6px 0;
            letter-spacing: -0.3px;
        }}
        .doc-subtitle {{
            font-size: 13pt;
            color: #4b5563;
            margin: 0;
            font-weight: 500;
        }}

        /* Legend */
        .legend-box {{
            background-color: #f9fafb;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            padding: 9px 14px;
            font-size: 9.5pt;
            line-height: 1.45;
            color: #374151;
            margin-bottom: 22px;
        }}

        /* Table */
        .schedule-table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            margin-bottom: 24px;
        }}
        .schedule-table th, .schedule-table td {{
            border-top: 1px solid #e5e7eb;
            border-bottom: 1px solid #e5e7eb;
            padding: 10px 6px;
            text-align: center;
            vertical-align: middle;
        }}
        .schedule-table thead th {{
            background-color: #2563eb !important;
            color: #ffffff !important;
            font-weight: 700;
            font-size: 10.5pt;
            border-top: 2.5px solid #1e3a8a;
            border-bottom: 2px solid #1e3a8a;
            padding: 11px 6px;
        }}
        .schedule-table thead th:first-child {{
            text-align: left;
            padding-left: 10px;
            width: 125px;
        }}
        .time-col {{
            text-align: left !important;
            padding-left: 10px !important;
            width: 125px;
            border-right: 1px solid #e5e7eb;
        }}
        .time-main {{
            font-weight: 700;
            font-size: 9.5pt;
            color: #0f172a;
            white-space: nowrap;
        }}
        .time-sub {{
            font-size: 8.5pt;
            color: #64748b;
            margin-top: 2px;
        }}
        .break-row {{
            background-color: #f3f4f6 !important;
        }}
        .break-cell {{
            font-size: 10pt;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #1f2937;
            text-transform: uppercase;
            padding: 9px !important;
        }}
        .cell {{
            height: 52px;
        }}
        .cell-title {{
            font-weight: 700;
            font-size: 9.5pt;
            line-height: 1.25;
        }}
        .cell-sub {{
            font-size: 8.5pt;
            margin-top: 2px;
        }}
        .dash {{
            color: #9ca3af;
            font-size: 14pt;
            font-weight: 700;
        }}

        /* Office Hour Highlights */
        .office-opt {{
            background-color: #e0f2fe !important;
            color: #0369a1;
        }}
        .office-opt .cell-title {{
            color: #0284c7;
        }}
        .office-opt .cell-sub {{
            color: #0369a1;
        }}
        .office-best {{
            background-color: #bfdbfe !important;
            color: #1e40af;
        }}
        .office-best .cell-title {{
            color: #1d4ed8;
            font-weight: 800;
        }}
        .office-best .cell-sub.best {{
            color: #1e3a8a;
            font-weight: 700;
        }}
        .class-cell {{
            background-color: #ecfdf5 !important;
            color: #065f46;
        }}

        /* Table Bottom Border */
        .schedule-table tr:last-child td {{
            border-bottom: 2.5px solid #0f172a;
        }}

        /* Signature Section */
        .signature-section {{
            margin-top: 28px;
            display: flex;
            justify-content: flex-end;
        }}
        .signature-box {{
            text-align: center;
            width: 220px;
        }}
        .signature-line {{
            border-bottom: 1px solid #4b5563;
            margin-bottom: 6px;
            height: 30px;
        }}
        .signature-text {{
            font-size: 9pt;
            color: #6b7280;
        }}

        /* Footer */
        .footer-section {{
            margin-top: auto;
            padding-top: 25px;
            display: flex;
            justify-content: space-between;
            font-size: 8.5pt;
            color: #9ca3af;
            border-top: 0.5px solid #f1f5f9;
        }}
    </style>
</head>
<body>
    <div class="page-container">
        <!-- Header -->
        <div class="doc-header">
            <h1 class="doc-title">{title}</h1>
            <p class="doc-subtitle">{subtitle}</p>
        </div>

        <!-- Legend -->
        {legend_html}

        <!-- Timetable -->
        <table class="schedule-table">
            <thead>
                <tr>
                    <th>Time / Period</th>
                    {days_headers}
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>

        <!-- Signature -->
        <div class="signature-section">
            <div class="signature-box">
                <div class="signature-line"></div>
                <div class="signature-text">{signature_title}</div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer-section">
            <div>{footer_text}</div>
            <div>{page_number_text}</div>
        </div>
    </div>
</body>
</html>
"""
    return html

def generate_tex(data):
    title = data.get("title", "Music Department Weekly Schedule")
    subtitle = data.get("subtitle", "Complete Timetable with Designated Office Hours")
    legend = data.get("legend", "")
    days = data.get("days", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"])
    rows = data.get("rows", [])
    signature_title = data.get("signatureTitle", "Music Teacher's Signature")
    footer_text = data.get("footerText", "Music Department Master Schedule")
    page_number_text = data.get("pageNumberText", "Page 1 of 1")

    num_days = len(days)

    # Format days header
    days_tex = " & \n".join([f"\\textcolor{{white}}{{\\textbf{{{d}}}}}" for d in days])

    rows_tex = []
    for row in rows:
        row_type = row.get("type", "period")
        time_text = row.get("time", "")
        if row_type == "break":
            label = row.get("label", "MORNING BREAK")
            row_tex = f"""\\rowcolor{{gray!15}} 
\\textbf{{{time_text}}} & 
\\multicolumn{{{num_days}}}{{c}}{{\\textbf{{\\textsf{{{label}}}}}}} \\\\
\\midrule"""
            rows_tex.append(row_tex)
        else:
            label = row.get("label", "")
            cells = row.get("cells", {})
            cell_strs = []
            for d in days:
                c = cells.get(d, {"type": "empty", "text": "---", "subtext": ""})
                c_type = c.get("type", "empty")
                c_text = c.get("text", "---")
                c_subtext = c.get("subtext", "")

                if c_type == "empty" or c_text == "---":
                    cell_strs.append("\\textcolor{gray}{\\Large ---}")
                elif c_type == "office_hour_best":
                    sub = f"\\newline \\footnotesize \\textbf{{{c_subtext or 'Best Option'}}}"
                    cell_strs.append(f"\\cellcolor{{blue!20}}\\textbf{{{c_text}}}{sub}")
                elif c_type == "office_hour":
                    sub = f"\\newline \\footnotesize {c_subtext or 'Option'}"
                    cell_strs.append(f"\\cellcolor{{blue!10}}\\textbf{{{c_text}}}{sub}")
                else: # custom
                    sub = f"\\newline \\footnotesize {c_subtext}" if c_subtext else ""
                    cell_strs.append(f"\\textbf{{{c_text}}}{sub}")

            cells_joined = " &\n".join(cell_strs)
            time_part = f"\\textbf{{{time_text}}}"
            if label:
                time_part += f"\\newline \\small \\textcolor{{darkgray}}{{{label}}}"
            
            row_tex = f"""{time_part} &
{cells_joined} \\\\
\\midrule"""
            rows_tex.append(row_tex)

    # Clean last midrule to bottomrule
    all_rows = "\n\n".join(rows_tex)
    if all_rows.endswith("\\midrule"):
        all_rows = all_rows[:-len("\\midrule")] + "\\bottomrule"

    legend_tex = ""
    if legend:
        legend_tex = f"""% --- LEGEND ---
\\noindent
\\fcolorbox{{gray!30}}{{gray!5}}{{
    \\parbox{{\\dimexpr\\textwidth-2\\fboxsep-2\\fboxrule\\relax}}{{
        \\textbf{{{legend}}}
    }}
}}

\\vspace{{2em}}"""

    tex_content = f"""\\documentclass[11pt, a4paper]{{article}}

% --- UNIVERSAL PREAMBLE BLOCK ---
\\usepackage[a4paper, top=2.5cm, bottom=2.5cm, left=2cm, right=2cm]{{geometry}}
\\usepackage{{fontspec}}

\\usepackage[english, bidi=basic, provide=*]{{babel}}

\\babelprovide[import, onchar=ids fonts]{{english}}

% Set default/Latin font to Sans Serif in the main (rm) slot
\\babelfont{{rm}}{{Noto Sans}}

% --- PACKAGES FOR TABLES AND COLORS ---
\\usepackage{{booktabs}}
\\usepackage{{tabularx}}
\\usepackage{{array}}
\\usepackage[table]{{xcolor}}

\\begin{{document}}

% --- HEADER ---
\\begin{{center}}
    {{\\LARGE \\textbf{{{title}}}}}\\\\[0.5em]
    {{\\large \\textcolor{{darkgray}}{{{subtitle}}}}}
\\end{{center}}

\\vspace{{1.5em}}

{legend_tex}

% --- TABLE SCHEDULE ---
\\renewcommand{{\\arraystretch}}{{2.2}} % Gives more breathing room inside cells
\\begin{{tabularx}}{{\\textwidth}}{{ >{{\\raggedright\\arraybackslash}}p{{2.8cm}} *{{{num_days}}}{{>{{\\centering\\arraybackslash}}X}} }}
\\toprule
\\rowcolor{{blue!80}}\\textcolor{{white}}{{\\textbf{{Time / Period}}}} & 
{days_tex} \\\\
\\midrule

{all_rows}
\\end{{tabularx}}

\\vspace{{4em}}

% --- SIGNATURE ---
\\hfill
\\begin{{tabular}}{{c}}
\\rule{{5.5cm}}{{0.4pt}} \\\\
\\small \\textcolor{{gray}}{{{signature_title}}}
\\end{{tabular}}

\\vfill

% --- FOOTER ---
\\noindent\\textcolor{{gray}}{{\\small {footer_text} \\hfill {page_number_text}}}

\\end{{document}}
"""
    return tex_content

def find_browser():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge"),
        shutil.which("chrome")
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def compile_pdf(html_path=HTML_FILE, pdf_path=PDF_FILE):
    browser = find_browser()
    if not browser:
        raise RuntimeError("Neither Microsoft Edge nor Google Chrome was found for PDF printing.")

    # Convert to file URI
    file_uri = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={os.path.abspath(pdf_path)}",
        file_uri
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF generation failed: {result.stderr or result.stdout}")
    return pdf_path

def sync_all(data=None, open_pdf=False):
    if data is None:
        data = load_data(DATA_FILE)

    # 1. Write HTML
    html_content = generate_html(data)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. Write TeX
    tex_content = generate_tex(data)
    with open(TEX_FILE, "w", encoding="utf-8") as f:
        f.write(tex_content)

    # 3. Compile PDF
    pdf_path = compile_pdf(HTML_FILE, PDF_FILE)
    print(f"SUCCESS: Generated {PDF_FILE} (size: {os.path.getsize(pdf_path)} bytes)")
    print(f"Updated {HTML_FILE}")
    print(f"Updated {TEX_FILE}")

    if open_pdf:
        os.startfile(pdf_path)

    return pdf_path

if __name__ == "__main__":
    open_flag = "--open" in sys.argv
    sync_all(open_pdf=open_flag)

