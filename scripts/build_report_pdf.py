"""
NetVision - Formal BTech Academic Project Report Builder (.pdf)
Generates NetVision_Project_Report.pdf using ReportLab multi-pass build with:
- A4 page size, 1-inch margins, Times-Roman academic typography
- Exact auto-computed Table of Contents with real page numbers
- Cover Page, Certificate Template, Declaration Template, Acknowledgement Template,
  Abstract, Table of Contents, List of Figures, List of Tables, List of Abbreviations
- Chapters 1 through 12 + Verified References
- 4 crisp 300-DPI engineering diagrams + 12 genuine live application screenshots
"""

import sys
import xml.sax.saxutils
from pathlib import Path
from PIL import Image as PILImage

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, Preformatted, NextPageTemplate, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from report_content import (
    ROOT_DIR, PROJECT_TITLE, PROJECT_SUBTITLE, APP_VERSION,
    TEAM_MEMBERS, ABBREVIATIONS, FIGURES_LIST, TABLES_LIST,
    REFERENCES, ABSTRACT_TEXT, get_chapters
)

OUT_PDF = ROOT_DIR / "NetVision_Project_Report.pdf"

C_NAVY = colors.HexColor("#14243A")
C_SLATE = colors.HexColor("#344B64")
C_LIGHT = colors.HexColor("#F2F5F8")
C_BORDER = colors.HexColor("#B8C4D0")
C_TEXT = colors.HexColor("#1A1A1A")
C_MUTED = colors.HexColor("#4A5568")


def esc(val: str) -> str:
    return xml.sax.saxutils.escape(str(val))


class AcademicReportDoc(BaseDocTemplate):
    """Multi-pass ReportLab document that populates TableOfContents automatically."""

    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=A4,
                         leftMargin=1.0 * inch, rightMargin=1.0 * inch,
                         topMargin=1.0 * inch, bottomMargin=1.0 * inch, **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="main")
        self.addPageTemplates([
            PageTemplate(id="Cover", frames=[frame], onPage=self._draw_cover_page),
            PageTemplate(id="Body", frames=[frame], onPage=self._draw_body_page),
        ])

    def _draw_cover_page(self, canvas, doc):
        # Clean academic cover border frame
        canvas.saveState()
        canvas.setStrokeColor(C_NAVY)
        canvas.setLineWidth(1.5)
        canvas.rect(0.65 * inch, 0.65 * inch, A4[0] - 1.3 * inch, A4[1] - 1.3 * inch)
        canvas.setLineWidth(0.5)
        canvas.rect(0.72 * inch, 0.72 * inch, A4[0] - 1.44 * inch, A4[1] - 1.44 * inch)
        canvas.restoreState()

    def _draw_body_page(self, canvas, doc):
        canvas.saveState()
        # Running header
        canvas.setFont("Times-Italic", 9)
        canvas.setFillColor(C_MUTED)
        canvas.drawRightString(A4[0] - 1.0 * inch, A4[1] - 0.65 * inch,
                               f"{PROJECT_TITLE} — {PROJECT_SUBTITLE}")
        canvas.setStrokeColor(C_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(1.0 * inch, A4[1] - 0.72 * inch, A4[0] - 1.0 * inch, A4[1] - 0.72 * inch)

        # Running footer with page number
        canvas.line(1.0 * inch, 0.75 * inch, A4[0] - 1.0 * inch, 0.75 * inch)
        canvas.setFont("Times-Roman", 9.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawCentredString(A4[0] / 2.0, 0.55 * inch, f"Page {doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            text = flowable.getPlainText()
            if style_name == "ChapterH1":
                self.notify("TOCEntry", (0, text, self.page))
            elif style_name == "SectionH2":
                self.notify("TOCEntry", (1, text, self.page))


def make_styles():
    base = getSampleStyleSheet()
    s = {}
    s["body"] = ParagraphStyle(
        "Body", parent=base["Normal"], fontName="Times-Roman", fontSize=11.5,
        leading=17.0, alignment=TA_JUSTIFY, textColor=C_TEXT, spaceAfter=6
    )
    s["body_center"] = ParagraphStyle(
        "BodyCenter", parent=s["body"], alignment=TA_CENTER
    )
    s["body_italic_center"] = ParagraphStyle(
        "BodyItalicCenter", parent=s["body"], fontName="Times-Italic", alignment=TA_CENTER, textColor=C_MUTED
    )
    s["body_right_bold"] = ParagraphStyle(
        "BodyRightBold", parent=s["body"], fontName="Times-Bold", alignment=TA_RIGHT
    )
    s["h1"] = ParagraphStyle(
        "ChapterH1", parent=base["Heading1"], fontName="Times-Bold", fontSize=16,
        leading=21, textColor=C_NAVY, spaceBefore=4, spaceAfter=12, keepWithNext=True
    )
    s["h1_center"] = ParagraphStyle(
        "FrontH1", parent=s["h1"], alignment=TA_CENTER
    )
    s["h2"] = ParagraphStyle(
        "SectionH2", parent=base["Heading2"], fontName="Times-Bold", fontSize=13.5,
        leading=18, textColor=C_NAVY, spaceBefore=12, spaceAfter=6, keepWithNext=True
    )
    s["bullet"] = ParagraphStyle(
        "BulletItem", parent=s["body"], leftIndent=18, firstLineIndent=-10, spaceAfter=4, leading=16
    )
    s["caption"] = ParagraphStyle(
        "Caption", parent=base["Normal"], fontName="Times-Italic", fontSize=10,
        leading=13.5, alignment=TA_CENTER, textColor=C_TEXT, spaceBefore=3, spaceAfter=8
    )
    s["tbl_caption"] = ParagraphStyle(
        "TblCaption", parent=base["Normal"], fontName="Times-Bold", fontSize=10,
        leading=13.5, alignment=TA_CENTER, textColor=C_NAVY, spaceBefore=8, spaceAfter=4, keepWithNext=True
    )
    s["formula"] = ParagraphStyle(
        "Formula", parent=base["Normal"], fontName="Times-Bold", fontSize=10.5,
        leading=15, alignment=TA_CENTER, textColor=C_NAVY
    )
    s["code"] = ParagraphStyle(
        "Code", parent=base["Code"], fontName="Courier", fontSize=8.5,
        leading=11.5, textColor=C_NAVY
    )
    s["cell"] = ParagraphStyle(
        "Cell", parent=base["Normal"], fontName="Times-Roman", fontSize=9.2,
        leading=12.2, textColor=C_TEXT, alignment=TA_LEFT
    )
    s["cell_bold"] = ParagraphStyle(
        "CellBold", parent=s["cell"], fontName="Times-Bold"
    )
    s["cell_hdr"] = ParagraphStyle(
        "CellHdr", parent=s["cell"], fontName="Times-Bold", textColor=colors.white
    )
    s["ref"] = ParagraphStyle(
        "RefItem", parent=s["body"], fontSize=10.5, leading=14.5,
        leftIndent=22, firstLineIndent=-22, spaceAfter=6
    )
    return s


def build_table(caption: str, headers, rows, styles, avail_w):
    elems = [Paragraph(esc(caption), styles["tbl_caption"])]
    ncols = len(headers)

    # Smart column proportions
    if ncols == 2:
        col_w = [avail_w * 0.28, avail_w * 0.72]
    elif ncols == 3:
        col_w = [avail_w * 0.22, avail_w * 0.28, avail_w * 0.50]
    elif ncols == 4:
        col_w = [avail_w * 0.22, avail_w * 0.22, avail_w * 0.28, avail_w * 0.28]
    elif ncols == 5:
        col_w = [avail_w * 0.26, avail_w * 0.16, avail_w * 0.18, avail_w * 0.20, avail_w * 0.20]
    elif ncols == 6:
        col_w = [avail_w * 0.09, avail_w * 0.19, avail_w * 0.20, avail_w * 0.20, avail_w * 0.21, avail_w * 0.11]
    else:
        col_w = [avail_w / ncols] * ncols

    data = [[Paragraph(esc(h), styles["cell_hdr"]) for h in headers]]
    for row in rows:
        data.append([
            Paragraph(esc(val), styles["cell_bold"] if ci == 0 else styles["cell"])
            for ci, val in enumerate(row)
        ])

    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, C_NAVY),
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, C_NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 8))
    return elems


def build_figure(fig_no: str, caption: str, img_path: Path, desc: str, styles, avail_w):
    with PILImage.open(img_path) as im:
        iw, ih = im.size
    ratio = iw / ih
    w = avail_w
    h = w / ratio
    max_h = 4.35 * inch
    if h > max_h:
        h = max_h
        w = h * ratio

    elems = [
        KeepTogether([
            Spacer(1, 6),
            Image(str(img_path), width=w, height=h),
            Paragraph(f"<b>{esc(fig_no)}:</b> <i>{esc(caption)}</i>", styles["caption"]),
        ])
    ]
    if desc:
        elems.append(Paragraph(esc(desc), styles["body"]))
    return elems


def build_report_pdf():
    doc = AcademicReportDoc(str(OUT_PDF))
    styles = make_styles()
    avail_w = doc.width
    story = []

    # =========================================================================
    # 1. COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 0.55 * inch))
    story.append(Paragraph("NETVISION", ParagraphStyle(
        "CovTitle", fontName="Times-Bold", fontSize=28, leading=34, alignment=TA_CENTER, textColor=C_NAVY
    )))
    story.append(Spacer(1, 6))
    story.append(Paragraph(esc(PROJECT_SUBTITLE), ParagraphStyle(
        "CovSub", fontName="Times-Bold", fontSize=15.5, leading=20, alignment=TA_CENTER, textColor=C_SLATE
    )))
    story.append(Spacer(1, 0.45 * inch))
    story.append(Paragraph("PROJECT REPORT", ParagraphStyle(
        "CovType", fontName="Times-Bold", fontSize=18, leading=24, alignment=TA_CENTER, textColor=C_NAVY
    )))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(
        "<i>Submitted in partial fulfillment of the requirements for the award of the degree of<br/>"
        "Bachelor of Technology (B.Tech)<br/>in<br/>Computer Science &amp; Engineering</i>",
        ParagraphStyle("CovDeg", fontName="Times-Roman", fontSize=12, leading=18, alignment=TA_CENTER, textColor=C_TEXT)
    ))
    story.append(Spacer(1, 0.45 * inch))
    story.append(Paragraph("<b>Submitted by:</b>", ParagraphStyle(
        "CovSubBy", fontName="Times-Bold", fontSize=13, leading=18, alignment=TA_CENTER, textColor=C_NAVY
    )))
    story.append(Spacer(1, 8))

    team_data = [
        [Paragraph(f"<b>{num}.  {esc(name)}</b>", styles["cell_bold"]),
         Paragraph(esc(roll), ParagraphStyle("Roll", parent=styles["cell"], alignment=TA_CENTER))]
        for num, name, roll in TEAM_MEMBERS
    ]
    team_tbl = Table(team_data, colWidths=[2.8 * inch, 2.0 * inch])
    team_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_LIGHT, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(team_tbl)
    story.append(Spacer(1, 0.55 * inch))
    story.append(Paragraph(
        "Under the Guidance of:<br/><b>[Faculty Guide Name &amp; Designation]</b>",
        ParagraphStyle("CovGuide", fontName="Times-Roman", fontSize=12, leading=18, alignment=TA_CENTER, textColor=C_TEXT)
    ))
    story.append(Spacer(1, 0.65 * inch))
    story.append(Paragraph(
        "<b>[Department of Computer Science &amp; Engineering]<br/>"
        "[Institution / College Name]<br/>"
        "[University Name]<br/>"
        "[Academic Session]</b>",
        ParagraphStyle("CovInst", fontName="Times-Bold", fontSize=12.5, leading=19, alignment=TA_CENTER, textColor=C_NAVY)
    ))

    story.append(NextPageTemplate("Body"))
    story.append(PageBreak())

    # =========================================================================
    # 2. CERTIFICATE TEMPLATE
    # =========================================================================
    story.append(Paragraph("CERTIFICATE", styles["h1_center"]))
    story.append(Paragraph(
        "[Template — To be completed and signed by authorized faculty/institution prior to final submission]",
        styles["body_italic_center"]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"This is to certify that the project report entitled \"{esc(PROJECT_TITLE)} – {esc(PROJECT_SUBTITLE)}\" "
        "submitted by Aryan Shukla (09117702724), Aaditya Rawat (07917702724), and Kushal Shedha (08817702724) "
        "in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in "
        "Computer Science &amp; Engineering at [Institution / College Name] is a record of project work carried out "
        "under my supervision and guidance during the academic session [Academic Session].",
        styles["body"]
    ))
    story.append(Paragraph(
        "The matter embodied in this report has not been submitted elsewhere for the award of any other degree or diploma.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.8 * inch))
    sig_tbl = Table([
        [Paragraph("_____________________________<br/><b>[Faculty Guide Name]</b><br/>Project Guide<br/>[Department Name]", styles["body_center"]),
         Paragraph("_____________________________<br/><b>[Head of Department Name]</b><br/>Head of Department<br/>[Department Name]", styles["body_center"])],
        [Paragraph("<br/>Date: _____________________", styles["body"]),
         Paragraph("<br/>Place: ____________________", styles["body"])]
    ], colWidths=[avail_w / 2, avail_w / 2])
    story.append(sig_tbl)
    story.append(PageBreak())

    # =========================================================================
    # 3. DECLARATION TEMPLATE
    # =========================================================================
    story.append(Paragraph("DECLARATION", styles["h1_center"]))
    story.append(Paragraph(
        f"We hereby declare that the project work presented in this report entitled \"{esc(PROJECT_TITLE)} – {esc(PROJECT_SUBTITLE)}\" "
        "submitted to the Department of Computer Science &amp; Engineering, [Institution / College Name], is an authentic "
        "record of our own work carried out under the guidance of [Faculty Guide Name] during [Academic Session].",
        styles["body"]
    ))
    story.append(Paragraph(
        "We further declare that all software modules, measurement tests, and screenshots reported herein reflect the "
        "actual implemented application, and all external technical standards and documentation referenced have been duly cited.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.35 * inch))
    story.extend(build_table(
        "Student Declaration Signatures",
        ["Student Name", "Enrollment / Roll No.", "Signature"],
        [[name, roll, ""] for _, name, roll in TEAM_MEMBERS],
        styles, avail_w
    ))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("Date: _______________________", styles["body"]))
    story.append(PageBreak())

    # =========================================================================
    # 4. ACKNOWLEDGEMENT TEMPLATE
    # =========================================================================
    story.append(Paragraph("ACKNOWLEDGEMENT", styles["h1_center"]))
    story.append(Paragraph(
        "We express our sincere gratitude to our project guide, [Faculty Guide Name], Department of Computer Science "
        "&amp; Engineering, [Institution / College Name], for their valuable guidance, constructive feedback, and continued "
        "encouragement throughout the design, development, and testing of NetVision.",
        styles["body"]
    ))
    story.append(Paragraph(
        "We are grateful to [Head of Department Name], Head of the Department of Computer Science &amp; Engineering, and "
        "the faculty and laboratory staff of [Institution / College Name] for providing the academic foundation and "
        "environment required to execute this Computer Networks engineering project.",
        styles["body"]
    ))
    story.append(Paragraph(
        "Finally, we thank our classmates, families, and the open-source developer communities behind Python, Qt/PySide6, "
        "SQLite, Matplotlib, ReportLab, and pytest, whose well-engineered tools made this desktop diagnostic suite possible.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph(
        "Aryan Shukla (09117702724)<br/>Aaditya Rawat (07917702724)<br/>Kushal Shedha (08817702724)",
        styles["body_right_bold"]
    ))
    story.append(PageBreak())

    # =========================================================================
    # 5. ABSTRACT
    # =========================================================================
    story.append(Paragraph("ABSTRACT", styles["h1_center"]))
    for para in ABSTRACT_TEXT.split("\n\n"):
        story.append(Paragraph(esc(para), styles["body"]))
    story.append(Paragraph(
        "<i><b>Keywords:</b> Computer Networks, Wi-Fi Analyzer, IEEE 802.11, PySide6, Windows WLAN API, ICMP Latency, "
        "Jitter, Channel Congestion, SQLite WAL, Network Quality Diagnostics.</i>",
        styles["body"]
    ))
    story.append(PageBreak())

    # =========================================================================
    # 6. AUTOMATIC TABLE OF CONTENTS
    # =========================================================================
    story.append(Paragraph("TABLE OF CONTENTS", styles["h1_center"]))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName="Times-Bold", fontSize=11, leftIndent=0, firstLineIndent=0, spaceBefore=5, leading=14, textColor=C_NAVY),
        ParagraphStyle("TOC1", fontName="Times-Roman", fontSize=10, leftIndent=18, firstLineIndent=0, spaceBefore=1, leading=13, textColor=C_TEXT),
    ]
    story.append(toc)
    story.append(PageBreak())

    # =========================================================================
    # 7. LIST OF FIGURES, LIST OF TABLES, ABBREVIATIONS
    # =========================================================================
    story.append(Paragraph("LIST OF FIGURES", styles["h1_center"]))
    story.extend(build_table(
        "Engineering Diagrams and Live Application Screenshots",
        ["Figure No.", "Figure Title"],
        [[fno, cap] for fno, cap, _ in FIGURES_LIST],
        styles, avail_w
    ))
    story.append(PageBreak())

    story.append(Paragraph("LIST OF TABLES", styles["h1_center"]))
    story.extend(build_table(
        "Specification, Schema, Verification, and Empirical Tables",
        ["Table No.", "Table Title"],
        [[tno, cap] for tno, cap in TABLES_LIST],
        styles, avail_w
    ))
    story.append(PageBreak())

    story.append(Paragraph("LIST OF ABBREVIATIONS", styles["h1_center"]))
    story.extend(build_table(
        "Technical Abbreviations Used in This Report",
        ["Abbreviation", "Full Form / Expansion"],
        ABBREVIATIONS,
        styles, avail_w
    ))

    # =========================================================================
    # CHAPTERS 1 THROUGH 12
    # =========================================================================
    for ch in get_chapters():
        story.append(PageBreak())
        story.append(Paragraph(f"CHAPTER {ch['num']}: {esc(ch['title'])}", styles["h1"]))

        for kind, payload in ch["blocks"]:
            if kind == "h2":
                story.append(Paragraph(esc(payload), styles["h2"]))
            elif kind == "p":
                story.append(Paragraph(esc(payload), styles["body"]))
            elif kind == "bullet":
                for item in payload:
                    if ":" in item:
                        lead, rest = item.split(":", 1)
                        story.append(Paragraph(f"&bull;&nbsp;&nbsp;<b>{esc(lead)}:</b>{esc(rest)}", styles["bullet"]))
                    else:
                        story.append(Paragraph(f"&bull;&nbsp;&nbsp;{esc(item)}", styles["bullet"]))
            elif kind == "formula":
                ftbl = Table([[Paragraph(esc(payload), styles["formula"])]], colWidths=[avail_w])
                ftbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(ftbl)
                story.append(Spacer(1, 6))
            elif kind == "code":
                ctbl = Table([[Preformatted(payload, styles["code"])]], colWidths=[avail_w])
                ctbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]))
                story.append(ctbl)
                story.append(Spacer(1, 6))
            elif kind == "table":
                cap, headers, rows = payload
                story.extend(build_table(cap, headers, rows, styles, avail_w))
            elif kind == "figure":
                fno, cap, path, desc = payload
                story.extend(build_figure(fno, cap, path, desc, styles, avail_w))

    # =========================================================================
    # REFERENCES
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("REFERENCES", styles["h1"]))
    for ref in REFERENCES:
        story.append(Paragraph(esc(ref), styles["ref"]))

    doc.multiBuild(story)
    print(f"PDF Project Report generated successfully: {OUT_PDF} ({OUT_PDF.stat().st_size / (1024*1024):.2f} MB), total pages: {doc.page}")


if __name__ == "__main__":
    build_report_pdf()
