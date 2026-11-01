import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

md_path = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain\docchain_presentation_slides.md"
pdf_path = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain\docchain_presentation_slides.pdf"
img_path = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain\docchain_architecture_diagram.jpg"

def md_to_pdf():
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0e7490'),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        leftIndent=15,
        spaceAfter=3
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_table = False
    table_rows = []

    for line in lines:
        raw = line.rstrip('\r\n')
        stripped = raw.strip()

        # Handle tables
        if stripped.startswith('|') and stripped.endswith('|'):
            if re.match(r'^\|[\s:-]+\|', stripped) and set(stripped.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                continue
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            if table_rows:
                # Build Flowable Table
                num_cols = len(table_rows[0])
                col_widths = [140] + [380 // (num_cols - 1)] * (num_cols - 1) if num_cols > 1 else [520]
                t_data = []
                for r_idx, r in enumerate(table_rows):
                    row_cells = []
                    for c_idx, cell_text in enumerate(r):
                        clean_text = cell_text.replace('**', '')
                        if r_idx == 0:
                            p = Paragraph(clean_text, table_header)
                        else:
                            p = Paragraph(clean_text, table_cell)
                        row_cells.append(p)
                    t_data.append(row_cells)

                t = Table(t_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
            in_table = False
            table_rows = []

        if not stripped:
            continue

        if stripped.startswith('# '):
            story.append(Paragraph(stripped[2:], title_style))
        elif stripped.startswith('## '):
            story.append(Paragraph(stripped[3:], h2_style))
        elif stripped.startswith('![') and 'docchain_architecture_diagram' in stripped:
            if os.path.exists(img_path):
                img = RLImage(img_path, width=480, height=270)
                story.append(Spacer(1, 4))
                story.append(img)
                story.append(Spacer(1, 4))
        elif stripped.startswith('* ') or stripped.startswith('- '):
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', stripped[2:])
            p = Paragraph(f"• {clean}", bullet_style)
            story.append(p)
        elif stripped == '---':
            story.append(Spacer(1, 6))
        else:
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', stripped)
            story.append(Paragraph(clean, body_style))

    doc.build(story)
    print(f"[OK] PDF generated successfully at: {pdf_path}")

if __name__ == '__main__':
    md_to_pdf()
