"""
NetVision - Formal BTech Academic Project Report Builder (.docx)
Generates NetVision_Project_Report.docx formatted to university A4 academic standards:
- A4 page size, 1-inch margins, Times New Roman
- 16 pt bold Chapter headings, 14 pt bold subheadings, 12 pt justified body (1.5 line spacing)
- Cover Page, Certificate Template, Declaration Template, Acknowledgement Template,
  Abstract, Automatic Word Table of Contents, List of Figures, List of Tables, Abbreviations
- Chapters 1 through 12 + Verified References
- 4 high-DPI engineering diagrams + 12 genuine live application screenshots
"""

import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from report_content import (
    ROOT_DIR, PROJECT_TITLE, PROJECT_SUBTITLE, APP_VERSION,
    TEAM_MEMBERS, ABBREVIATIONS, FIGURES_LIST, TABLES_LIST,
    REFERENCES, ABSTRACT_TEXT, get_chapters
)

OUT_DOCX = ROOT_DIR / "NetVision_Project_Report.docx"

NAVY_HEX = "14243A"
LIGHT_HEX = "F2F5F8"
BORDER_HEX = "B8C4D0"
C_NAVY = RGBColor(0x14, 0x24, 0x3A)
C_DARK = RGBColor(0x1A, 0x1A, 0x1A)
C_MUTED = RGBColor(0x4A, 0x55, 0x68)


def set_cell_shading(cell, fill_hex: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_table_borders(table, border_color=BORDER_HEX):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="{NAVY_HEX}"/>'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{NAVY_HEX}"/>'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))


def prevent_row_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def add_field(paragraph, field_text: str, font_size=10, italic=False, color=C_MUTED):
    """Inserts a dynamic Word XML field (e.g., PAGE, NUMPAGES, TOC)."""
    run_begin = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run_begin._r.append(fld_begin)

    run_instr = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {field_text} "
    run_instr._r.append(instr)

    run_sep = paragraph.add_run()
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    run_sep._r.append(fld_sep)

    run_val = paragraph.add_run("1")
    run_val.font.name = "Times New Roman"
    run_val.font.size = Pt(font_size)
    run_val.font.italic = italic
    run_val.font.color.rgb = color

    run_end = paragraph.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run_end._r.append(fld_end)


def set_update_fields_on_open(doc):
    """Instructs Microsoft Word to auto-refresh TOC and page fields on open."""
    settings = doc.settings.element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)


def configure_styles(doc: Document):
    # A4 page with 1-inch margins
    for sec in doc.sections:
        sec.page_width = Mm(210)
        sec.page_height = Mm(297)
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)
        sec.different_first_page_header_footer = True

        # Header (pages 2+)
        hdr = sec.header
        hp = hdr.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hr = hp.add_run(f"{PROJECT_TITLE} — {PROJECT_SUBTITLE}")
        hr.font.name = "Times New Roman"
        hr.font.size = Pt(9.5)
        hr.font.italic = True
        hr.font.color.rgb = C_MUTED

        # Footer (pages 2+) with dynamic Page X of Y
        ftr = sec.footer
        fp = ftr.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = fp.add_run("Page ")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10)
        r1.font.color.rgb = C_MUTED
        add_field(fp, "PAGE", font_size=10)
        r2 = fp.add_run(" of ")
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(10)
        r2.font.color.rgb = C_MUTED
        add_field(fp, "NUMPAGES", font_size=10)

    # Normal body style: Times New Roman, 12 pt, 1.5 spacing, justified
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.font.color.rgb = C_DARK
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Heading 1: 16 pt bold, Times New Roman
    h1 = doc.styles["Heading 1"]
    h1.font.name = "Times New Roman"
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = C_NAVY
    h1.paragraph_format.space_before = Pt(6)
    h1.paragraph_format.space_after = Pt(12)
    h1.paragraph_format.keep_with_next = True

    # Heading 2: 14 pt bold, Times New Roman
    h2 = doc.styles["Heading 2"]
    h2.font.name = "Times New Roman"
    h2.font.size = Pt(14)
    h2.font.bold = True
    h2.font.color.rgb = C_NAVY
    h2.paragraph_format.space_before = Pt(12)
    h2.paragraph_format.space_after = Pt(6)
    h2.paragraph_format.keep_with_next = True

    set_update_fields_on_open(doc)


def add_body_p(doc, text: str, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, space_after=6):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = C_DARK
    return p


def add_bullet_list(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.4
        p.paragraph_format.space_after = Pt(4)
        if ":" in item:
            lead, rest = item.split(":", 1)
            r1 = p.add_run(lead + ":")
            r1.font.name = "Times New Roman"
            r1.font.size = Pt(12)
            r1.font.bold = True
            r1.font.color.rgb = C_DARK
            r2 = p.add_run(rest)
            r2.font.name = "Times New Roman"
            r2.font.size = Pt(12)
            r2.font.color.rgb = C_DARK
        else:
            r = p.add_run(item)
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
            r.font.color.rgb = C_DARK


def add_formula_box(doc, text: str):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.1)
    set_cell_shading(cell, LIGHT_HEX)
    set_table_borders(tbl, BORDER_HEX)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.2
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = C_NAVY
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def add_code_box(doc, code: str):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.2)
    set_cell_shading(cell, LIGHT_HEX)
    set_table_borders(tbl, BORDER_HEX)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(code)
    r.font.name = "Courier New"
    r.font.size = Pt(9.5)
    r.font.color.rgb = C_NAVY
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def add_academic_table(doc, caption: str, headers, rows):
    # Table caption above table (standard IEEE/university convention)
    pc = doc.add_paragraph()
    pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pc.paragraph_format.space_before = Pt(8)
    pc.paragraph_format.space_after = Pt(4)
    pc.paragraph_format.keep_with_next = True
    rc = pc.add_run(caption)
    rc.font.name = "Times New Roman"
    rc.font.size = Pt(10.5)
    rc.font.bold = True
    rc.font.color.rgb = C_NAVY

    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    # Header row
    hdr_row = tbl.rows[0]
    set_repeat_table_header(hdr_row)
    prevent_row_split(hdr_row)
    for ci, htext in enumerate(headers):
        cell = hdr_row.cells[ci]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_shading(cell, NAVY_HEX)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(htext)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Data rows
    for ri, row_vals in enumerate(rows):
        row = tbl.rows[ri + 1]
        prevent_row_split(row)
        fill = "FFFFFF" if ri % 2 == 0 else LIGHT_HEX
        for ci, val in enumerate(row_vals):
            cell = row.cells[ci]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_shading(cell, fill)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(2.5)
            p.paragraph_format.space_after = Pt(2.5)
            r = p.add_run(str(val))
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.8)
            if ci == 0:
                r.font.bold = True
            r.font.color.rgb = C_DARK

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)


def add_academic_figure(doc, fig_no: str, caption: str, img_path: Path, desc: str = ""):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(4)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(str(img_path), width=Inches(6.15))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(6)
    p_cap.paragraph_format.line_spacing = 1.2
    rc1 = p_cap.add_run(f"{fig_no}: ")
    rc1.font.name = "Times New Roman"
    rc1.font.size = Pt(10.5)
    rc1.font.bold = True
    rc1.font.color.rgb = C_NAVY
    rc2 = p_cap.add_run(caption)
    rc2.font.name = "Times New Roman"
    rc2.font.size = Pt(10.5)
    rc2.font.italic = True
    rc2.font.color.rgb = C_DARK

    if desc:
        add_body_p(doc, desc)


def build_front_matter(doc: Document):
    # =========================================================================
    # 1. COVER PAGE
    # =========================================================================
    for _ in range(2):
        doc.add_paragraph()

    p_proj = doc.add_paragraph()
    p_proj.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_proj.add_run("NETVISION")
    r.font.name = "Times New Roman"
    r.font.size = Pt(28)
    r.font.bold = True
    r.font.color.rgb = C_NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(18)
    rs = p_sub.add_run(PROJECT_SUBTITLE)
    rs.font.name = "Times New Roman"
    rs.font.size = Pt(16)
    rs.font.bold = True
    rs.font.color.rgb = C_DARK

    p_type = doc.add_paragraph()
    p_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_type.paragraph_format.space_before = Pt(14)
    p_type.paragraph_format.space_after = Pt(14)
    rt = p_type.add_run("PROJECT REPORT")
    rt.font.name = "Times New Roman"
    rt.font.size = Pt(18)
    rt.font.bold = True
    rt.font.color.rgb = C_NAVY

    p_deg = doc.add_paragraph()
    p_deg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_deg.paragraph_format.space_after = Pt(24)
    rd = p_deg.add_run(
        "Submitted in partial fulfillment of the requirements for the award of the degree of\n"
        "Bachelor of Technology (B.Tech)\n"
        "in\n"
        "Computer Science & Engineering"
    )
    rd.font.name = "Times New Roman"
    rd.font.size = Pt(12.5)
    rd.font.italic = True
    rd.font.color.rgb = C_DARK

    # Submitted by block (EXACT names & roll numbers)
    p_sb = doc.add_paragraph()
    p_sb.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sb.paragraph_format.space_before = Pt(10)
    p_sb.paragraph_format.space_after = Pt(8)
    rsb = p_sb.add_run("Submitted by:")
    rsb.font.name = "Times New Roman"
    rsb.font.size = Pt(13)
    rsb.font.bold = True
    rsb.font.color.rgb = C_NAVY

    team_tbl = doc.add_table(rows=len(TEAM_MEMBERS), cols=2)
    team_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(team_tbl, BORDER_HEX)
    for idx, (_, name, roll) in enumerate(TEAM_MEMBERS):
        c0, c1 = team_tbl.rows[idx].cells
        c0.width = Inches(2.6)
        c1.width = Inches(2.2)
        set_cell_shading(c0, LIGHT_HEX if idx % 2 == 0 else "FFFFFF")
        set_cell_shading(c1, LIGHT_HEX if idx % 2 == 0 else "FFFFFF")
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p0.paragraph_format.space_before = p0.paragraph_format.space_after = Pt(4)
        r0 = p0.add_run(f"{idx + 1}.  {name}")
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(12.5)
        r0.font.bold = True

        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = p1.paragraph_format.space_after = Pt(4)
        r1 = p1.add_run(roll)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(12.5)

    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_before = Pt(28)
    p_guide.paragraph_format.space_after = Pt(24)
    rg = p_guide.add_run("Under the Guidance of:\n[Faculty Guide Name & Designation]")
    rg.font.name = "Times New Roman"
    rg.font.size = Pt(12)
    rg.font.color.rgb = C_DARK

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(24)
    ri = p_inst.add_run(
        "[Department of Computer Science & Engineering]\n"
        "[Institution / College Name]\n"
        "[University Name]\n"
        "[Academic Session]"
    )
    ri.font.name = "Times New Roman"
    ri.font.size = Pt(12.5)
    ri.font.bold = True
    ri.font.color.rgb = C_NAVY

    doc.add_page_break()

    # =========================================================================
    # 2. CERTIFICATE (EDITABLE TEMPLATE)
    # =========================================================================
    h_cert = doc.add_heading("CERTIFICATE", level=1)
    h_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_body_p(
        doc,
        "[Template — To be completed and signed by authorized faculty/institution prior to final submission]",
        align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, space_after=14
    )
    add_body_p(
        doc,
        f"This is to certify that the project report entitled \"{PROJECT_TITLE} – {PROJECT_SUBTITLE}\" "
        "submitted by Aryan Shukla (09117702724), Aaditya Rawat (07917702724), and Kushal Shedha (08817702724) "
        "in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in "
        "Computer Science & Engineering at [Institution / College Name] is a record of project work carried out "
        "under my supervision and guidance during the academic session [Academic Session]."
    )
    add_body_p(
        doc,
        "The matter embodied in this report has not been submitted elsewhere for the award of any other degree or diploma.",
        space_after=36
    )

    sig_tbl = doc.add_table(rows=2, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_cells = [
        ("_____________________________\n[Faculty Guide Name]\nProject Guide\n[Department Name]",
         "_____________________________\n[Head of Department Name]\nHead of Department\n[Department Name]"),
        ("\nDate: _____________________", "\nPlace: ____________________")
    ]
    for ri, row_pair in enumerate(sig_cells):
        for ci, txt in enumerate(row_pair):
            c = sig_tbl.rows[ri].cells[ci]
            c.width = Inches(3.1)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ri == 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(txt)
            r.font.name = "Times New Roman"
            r.font.size = Pt(11.5)

    doc.add_page_break()

    # =========================================================================
    # 3. DECLARATION (EDITABLE TEMPLATE)
    # =========================================================================
    h_decl = doc.add_heading("DECLARATION", level=1)
    h_decl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_body_p(
        doc,
        f"We hereby declare that the project work presented in this report entitled \"{PROJECT_TITLE} – {PROJECT_SUBTITLE}\" "
        "submitted to the Department of Computer Science & Engineering, [Institution / College Name], is an authentic "
        "record of our own work carried out under the guidance of [Faculty Guide Name] during [Academic Session]."
    )
    add_body_p(
        doc,
        "We further declare that all software modules, measurement tests, and screenshots reported herein reflect the "
        "actual implemented application, and all external technical standards and documentation referenced have been duly cited.",
        space_after=28
    )

    d_tbl = doc.add_table(rows=len(TEAM_MEMBERS) + 1, cols=3)
    d_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(d_tbl)
    for ci, htxt in enumerate(["Student Name", "Enrollment / Roll No.", "Signature"]):
        c = d_tbl.rows[0].cells[ci]
        set_cell_shading(c, NAVY_HEX)
        r = c.paragraphs[0].add_run(htxt)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for idx, (_, name, roll) in enumerate(TEAM_MEMBERS):
        row = d_tbl.rows[idx + 1]
        for ci, val in enumerate([name, roll, ""]):
            c = row.cells[ci]
            p = c.paragraphs[0]
            p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(10)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(11.5)

    add_body_p(doc, "\nDate: _______________________", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=6)
    doc.add_page_break()

    # =========================================================================
    # 4. ACKNOWLEDGEMENT (EDITABLE TEMPLATE)
    # =========================================================================
    h_ack = doc.add_heading("ACKNOWLEDGEMENT", level=1)
    h_ack.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_body_p(
        doc,
        "We express our sincere gratitude to our project guide, [Faculty Guide Name], Department of Computer Science "
        "& Engineering, [Institution / College Name], for their valuable guidance, constructive feedback, and continued "
        "encouragement throughout the design, development, and testing of NetVision."
    )
    add_body_p(
        doc,
        "We are grateful to [Head of Department Name], Head of the Department of Computer Science & Engineering, and "
        "the faculty and laboratory staff of [Institution / College Name] for providing the academic foundation and "
        "environment required to execute this Computer Networks engineering project."
    )
    add_body_p(
        doc,
        "Finally, we thank our classmates, families, and the open-source developer communities behind Python, Qt/PySide6, "
        "SQLite, Matplotlib, ReportLab, and pytest, whose well-engineered tools made this desktop diagnostic suite possible.",
        space_after=24
    )
    add_body_p(
        doc,
        "Aryan Shukla (09117702724)\nAaditya Rawat (07917702724)\nKushal Shedha (08817702724)",
        align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True
    )
    doc.add_page_break()

    # =========================================================================
    # 5. ABSTRACT
    # =========================================================================
    h_abs = doc.add_heading("ABSTRACT", level=1)
    h_abs.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for para in ABSTRACT_TEXT.split("\n\n"):
        add_body_p(doc, para)
    add_body_p(
        doc,
        "Keywords: Computer Networks, Wi-Fi Analyzer, IEEE 802.11, PySide6, Windows WLAN API, ICMP Latency, Jitter, "
        "Channel Congestion, SQLite WAL, Network Quality Diagnostics.",
        italic=True
    )
    doc.add_page_break()

    # =========================================================================
    # 6. TABLE OF CONTENTS (Automatic Word TOC field)
    # =========================================================================
    h_toc = doc.add_heading("TABLE OF CONTENTS", level=1)
    h_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_body_p(
        doc,
        "(Right-click the table below in Microsoft Word and choose 'Update Field' -> 'Update entire table' to refresh exact page numbers.)",
        align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, space_after=10
    )
    p_toc = doc.add_paragraph()
    add_field(p_toc, 'TOC \\o "1-2" \\h \\z \\u', font_size=11)
    doc.add_page_break()

    # =========================================================================
    # 7. LIST OF FIGURES
    # =========================================================================
    h_lof = doc.add_heading("LIST OF FIGURES", level=1)
    h_lof.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lof_rows = [[fno, cap] for fno, cap, _ in FIGURES_LIST]
    add_academic_table(doc, "Summary of Engineering Diagrams and Live Application Figures", ["Figure No.", "Figure Title"], lof_rows)
    doc.add_page_break()

    # =========================================================================
    # 8. LIST OF TABLES
    # =========================================================================
    h_lot = doc.add_heading("LIST OF TABLES", level=1)
    h_lot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lot_rows = [[tno, cap] for tno, cap in TABLES_LIST]
    add_academic_table(doc, "Summary of Specification, Schema, Testing, and Empirical Tables", ["Table No.", "Table Title"], lot_rows)
    doc.add_page_break()

    # =========================================================================
    # 9. LIST OF ABBREVIATIONS
    # =========================================================================
    h_abb = doc.add_heading("LIST OF ABBREVIATIONS", level=1)
    h_abb.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_academic_table(doc, "Technical Abbreviations Used in This Report", ["Abbreviation", "Full Form / Expansion"], ABBREVIATIONS)


def build_report_docx():
    doc = Document()
    configure_styles(doc)
    build_front_matter(doc)

    # Chapters 1 through 12
    for ch in get_chapters():
        doc.add_page_break()
        doc.add_heading(f"CHAPTER {ch['num']}: {ch['title']}", level=1)
        for kind, payload in ch["blocks"]:
            if kind == "h2":
                doc.add_heading(payload, level=2)
            elif kind == "p":
                add_body_p(doc, payload)
            elif kind == "bullet":
                add_bullet_list(doc, payload)
            elif kind == "formula":
                add_formula_box(doc, payload)
            elif kind == "code":
                add_code_box(doc, payload)
            elif kind == "table":
                cap, headers, rows = payload
                add_academic_table(doc, cap, headers, rows)
            elif kind == "figure":
                fno, cap, path, desc = payload
                add_academic_figure(doc, fno, cap, path, desc)

    # References
    doc.add_page_break()
    doc.add_heading("REFERENCES", level=1)
    for ref in REFERENCES:
        p = add_body_p(doc, ref, space_after=8)
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.first_line_indent = Inches(-0.35)

    doc.save(str(OUT_DOCX))
    print(f"DOCX Project Report generated successfully: {OUT_DOCX} ({OUT_DOCX.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    build_report_docx()
