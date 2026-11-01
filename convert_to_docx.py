import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

md_path = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain\docchain_presentation_slides.md"
docx_path = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain\docchain_presentation_slides.docx"
img_path = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain\docchain_architecture_diagram.jpg"

def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def create_docx():
    doc = Document()
    
    # Page setup - 0.75 in margins
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_table = False
    table_rows = []

    for line in lines:
        raw = line.rstrip('\r\n')
        stripped = raw.strip()

        # Handle tables
        if stripped.startswith('|') and stripped.endswith('|'):
            # Table separator line like | :--- | :--- |
            if re.match(r'^\|[\s:-]+\|', stripped) and set(stripped.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                continue
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            # End of table, write table
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
                            if r_idx == 0:
                                set_cell_background(cell, "0284C7")
                                for run in p.runs:
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(255, 255, 255)
                                    run.font.size = Pt(10)
                            else:
                                if r_idx % 2 == 1:
                                    set_cell_background(cell, "F0F9FF")
                                for run in p.runs:
                                    run.font.size = Pt(9.5)
                doc.add_paragraph() # Spacing
            in_table = False
            table_rows = []

        if not stripped:
            continue

        if stripped.startswith('# '):
            h = doc.add_heading(level=1)
            run = h.add_run(stripped[2:])
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = RGBColor(14, 116, 144)
            h.paragraph_format.space_after = Pt(8)
            h.paragraph_format.space_before = Pt(14)
        elif stripped.startswith('## '):
            h = doc.add_heading(level=2)
            run = h.add_run(stripped[3:])
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(3, 105, 161)
            h.paragraph_format.space_after = Pt(6)
            h.paragraph_format.space_before = Pt(12)
        elif stripped.startswith('![') and 'docchain_architecture_diagram' in stripped:
            if os.path.exists(img_path):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run()
                run.add_picture(img_path, width=Inches(6.2))
                caption = doc.add_paragraph("Figure: DocChain Cloud Architecture Diagram")
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                caption.runs[0].font.italic = True
                caption.runs[0].font.size = Pt(9)
                caption.runs[0].font.color.rgb = RGBColor(100, 100, 100)
        elif stripped.startswith('* ') or stripped.startswith('- '):
            p = doc.add_paragraph(style='List Bullet')
            text = stripped[2:]
            parts = re.split(r'(\*\*.*?\*\*)', text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r = p.add_run(part[2:-2])
                    r.bold = True
                    r.font.size = Pt(10)
                else:
                    r = p.add_run(part)
                    r.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(3)
        elif stripped == '---':
            continue
        else:
            p = doc.add_paragraph()
            parts = re.split(r'(\*\*.*?\*\*)', stripped)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r = p.add_run(part[2:-2])
                    r.bold = True
                    r.font.size = Pt(10)
                else:
                    r = p.add_run(part)
                    r.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(4)

    doc.save(docx_path)
    print(f"[OK] DOCX generated successfully at: {docx_path}")

if __name__ == '__main__':
    create_docx()
