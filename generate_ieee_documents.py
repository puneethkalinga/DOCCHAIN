import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

base_dir = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain"
md_path = os.path.join(base_dir, "DocChain_IEEE_Report.md")
docx_path = os.path.join(base_dir, "DocChain_IEEE_Report.docx")
pdf_path = os.path.join(base_dir, "DocChain_IEEE_Report.pdf")
img_path = os.path.join(base_dir, "docchain_architecture_diagram.jpg")

# ==============================================================================
# 1. BUILD IEEE DOCX DOCUMENT
# ==============================================================================
def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def generate_docx():
    doc = Document()
    
    # 0.75-inch standard margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    in_table = False
    table_rows = []

    for idx, raw in enumerate(lines):
        line = raw.strip()

        # Handle tables
        if line.startswith('|') and line.endswith('|'):
            if re.match(r'^\|[\s:-]+\|', line) and set(line.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                continue
            cells = [c.strip() for c in line[1:-1].split('|')]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            if table_rows:
                t = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                for r_idx, row_data in enumerate(table_rows):
                    row = t.rows[r_idx]
                    for c_idx, cell_data in enumerate(row_data):
                        if c_idx < len(row.cells):
                            cell = row.cells[c_idx]
                            cell.text = cell_data.replace('**', '')
                            p = cell.paragraphs[0]
                            p.paragraph_format.space_after = Pt(2)
                            p.paragraph_format.space_before = Pt(2)
                            for run in p.runs:
                                run.font.name = 'Times New Roman'
                                if r_idx == 0:
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(255, 255, 255)
                                    run.font.size = Pt(9.5)
                                else:
                                    run.font.size = Pt(9)
                            if r_idx == 0:
                                set_cell_background(cell, "1E3A8A")
                            elif r_idx % 2 == 1:
                                set_cell_background(cell, "F8FAFC")
                doc.add_paragraph()
            in_table = False
            table_rows = []

        if not line:
            continue

        # Title
        if line.startswith('# '):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(line[2:].strip())
            run.font.name = 'Times New Roman'
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = RGBColor(17, 24, 39)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.space_before = Pt(0)

        # Author / Affiliation
        elif idx == 2 and line.startswith('**Puneeth'):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(line.replace('**', ''))
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)
            run.font.bold = True
            p.paragraph_format.space_after = Pt(3)

        elif line.startswith('*Department of Artificial Intelligence*') or line.startswith('*Amrita Vishwa Vidyapeetham'):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(line.replace('*', ''))
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.font.italic = True
            run.font.color.rgb = RGBColor(55, 65, 81)
            p.paragraph_format.space_after = Pt(4)

        # Headings (I. II. III.)
        elif line.startswith('## '):
            h_text = line[3:].strip()
            p = doc.add_paragraph()
            run = p.add_run(h_text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(17, 24, 39)
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(5)

        # Subheadings (A. B. C.)
        elif line.startswith('### '):
            sub_text = line[4:].strip()
            p = doc.add_paragraph()
            run = p.add_run(sub_text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10.5)
            run.font.bold = True
            run.font.italic = True
            run.font.color.rgb = RGBColor(31, 41, 55)
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)

        # Horizontal line
        elif line == '---':
            continue

        # Code block representation for architecture / tables
        elif line.startswith('```') or line.startswith('+---') or line.startswith('| Table'):
            continue

        # Bullets
        elif line.startswith('* ') or line.startswith('- '):
            p = doc.add_paragraph(style='List Bullet')
            clean_text = line[2:]
            parts = re.split(r'(\*\*.*?\*\*)', clean_text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r = p.add_run(part[2:-2])
                    r.font.name = 'Times New Roman'
                    r.font.bold = True
                    r.font.size = Pt(10)
                else:
                    r = p.add_run(part)
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(2.5)

        # Standard Paragraphs
        else:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r = p.add_run(part[2:-2])
                    r.font.name = 'Times New Roman'
                    r.font.bold = True
                    r.font.size = Pt(10)
                elif part.startswith('*') and part.endswith('*'):
                    r = p.add_run(part[1:-1])
                    r.font.name = 'Times New Roman'
                    r.font.italic = True
                    r.font.size = Pt(10)
                else:
                    r = p.add_run(part)
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(5)

    # Insert Architecture Diagram before section IV
    if os.path.exists(img_path):
        # We can add an appendix / architecture figure paragraph
        for idx_p, p in enumerate(doc.paragraphs):
            if 'III. System Architecture and Design' in p.text:
                fig_p = doc.paragraphs[idx_p + 1].insert_paragraph_before()
                fig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = fig_p.add_run()
                r.add_picture(img_path, width=Inches(6.2))
                cap_p = doc.paragraphs[idx_p + 2].insert_paragraph_before()
                cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = cap_p.add_run("Fig. 1. End-to-End Decoupled Cloud Architecture of DocChain Platform.")
                r_cap.font.name = 'Times New Roman'
                r_cap.font.size = Pt(9)
                r_cap.font.bold = True
                break

    doc.save(docx_path)
    print(f"[OK] IEEE Word Document created at: {docx_path}")

# ==============================================================================
# 2. BUILD IEEE PDF DOCUMENT
# ==============================================================================
def generate_pdf():
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_s = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#111827'),
        spaceAfter=12
    )
    author_s = ParagraphStyle(
        'AuthorStyle',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=3
    )
    affil_s = ParagraphStyle(
        'AffilStyle',
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=14
    )
    h1_s = ParagraphStyle(
        'IEEEH1',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#111827'),
        spaceBefore=14,
        spaceAfter=5,
        keepWithNext=True
    )
    h2_s = ParagraphStyle(
        'IEEEH2',
        fontName='Helvetica-BoldOblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1f2937'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_s = ParagraphStyle(
        'IEEEBody',
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        alignment=4, # Justify
        spaceAfter=5
    )
    bullet_s = ParagraphStyle(
        'IEEEBullet',
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        leftIndent=15,
        alignment=4,
        spaceAfter=3
    )
    caption_s = ParagraphStyle(
        'CaptionStyle',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=colors.HexColor('#374151'),
        spaceBefore=4,
        spaceAfter=10
    )
    tbl_cell = ParagraphStyle(
        'TblCell',
        fontName='Helvetica',
        fontSize=8,
        leading=11
    )
    tbl_hdr = ParagraphStyle(
        'TblHdr',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    in_table = False
    table_rows = []

    for idx, raw in enumerate(lines):
        line = raw.strip()

        # Handle tables
        if line.startswith('|') and line.endswith('|'):
            if re.match(r'^\|[\s:-]+\|', line) and set(line.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                continue
            cells = [c.strip() for c in line[1:-1].split('|')]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            if table_rows:
                num_cols = len(table_rows[0])
                if num_cols == 3:
                    col_widths = [130, 210, 190]
                elif num_cols <= 1:
                    col_widths = [530]
                else:
                    col_widths = [150] + [380 // (num_cols - 1)] * (num_cols - 1)
                t_data = []
                for r_idx, r in enumerate(table_rows):
                    row_cells = []
                    for c_idx, cell_text in enumerate(r):
                        clean_text = cell_text.replace('**', '')
                        if r_idx == 0:
                            p = Paragraph(clean_text, tbl_hdr)
                        else:
                            p = Paragraph(clean_text, tbl_cell)
                        row_cells.append(p)
                    t_data.append(row_cells)

                t = Table(t_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
            in_table = False
            table_rows = []

        if not line:
            continue

        if line.startswith('# '):
            story.append(Paragraph(line[2:].strip(), title_s))
        elif idx == 2 and line.startswith('**Puneeth'):
            story.append(Paragraph(line.replace('**', ''), author_s))
        elif line.startswith('*Department of Artificial Intelligence*'):
            story.append(Paragraph(line.replace('*', ''), affil_s))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94a3b8'), spaceAfter=10))
        elif line.startswith('*Amrita Vishwa'):
            continue
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].strip(), h1_s))
            if 'III. System Architecture and Design' in line and os.path.exists(img_path):
                img = RLImage(img_path, width=520, height=292)
                story.append(Spacer(1, 6))
                story.append(img)
                story.append(Paragraph("Fig. 1. End-to-End Decoupled Cloud Architecture of DocChain Platform.", caption_s))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:].strip(), h2_s))
        elif line.startswith('```') or line.startswith('+---') or line.startswith('| Table'):
            continue
        elif line == '---':
            story.append(Spacer(1, 6))
        elif line.startswith('* ') or line.startswith('- '):
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line[2:])
            clean = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean)
            story.append(Paragraph(f"• {clean}", bullet_s))
        else:
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            clean = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean)
            story.append(Paragraph(clean, body_s))

    doc.build(story)
    print(f"[OK] IEEE PDF Document created at: {pdf_path}")

if __name__ == '__main__':
    generate_docx()
    generate_pdf()
