import docx
import PyPDF2
import os

print("--- VERIFYING DOCX ---")
for docx_name in ["DocChain_IEEE_Final_Report.docx", "DocChain_IEEE_Conference_Paper.docx"]:
    if not os.path.exists(docx_name):
        print(f"MISSING: {docx_name}")
        continue
    doc = docx.Document(docx_name)
    total_p = len(doc.paragraphs)
    total_t = len(doc.tables)
    print(f"{docx_name}: {total_p} paragraphs, {total_t} tables")
    
    # Check for raw LaTeX in paragraphs and tables
    found = []
    bad_patterns = ["$$", r"\text", r"\sum", r"\leftarrow", r"\rightarrow", "P_{\text", "H_{\text", "`"]
    for p in doc.paragraphs:
        for pat in bad_patterns:
            if pat in p.text:
                found.append((pat, p.text[:60]))
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for pat in bad_patterns:
                    if pat in cell.text:
                        found.append((pat, cell.text[:60]))
    if found:
        print(f"WARNING in {docx_name}: found {len(found)} bad patterns!")
        for f in found[:5]:
            print("  ", f)
    else:
        print(f"PERFECT! 0 raw LaTeX or markdown patterns found in {docx_name}")

print("\n--- VERIFYING PDF ---")
for pdf_name in ["DocChain_IEEE_Report.pdf", "DocChain_IEEE_Conference_Paper.pdf"]:
    if not os.path.exists(pdf_name):
        print(f"MISSING: {pdf_name}")
        continue
    reader = PyPDF2.PdfReader(pdf_name)
    print(f"{pdf_name}: {len(reader.pages)} pages")
    found = []
    bad_patterns = ["$$", r"\text", r"\sum", r"\leftarrow", r"\rightarrow", "P_{\text", "H_{\text", "`"]
    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        for pat in bad_patterns:
            if pat in text:
                found.append((pat, f"page {idx+1}"))
    if found:
        print(f"WARNING in {pdf_name}: found {len(found)} bad patterns!")
        for f in found[:5]:
            print("  ", f)
    else:
        print(f"PERFECT! 0 raw LaTeX or markdown patterns found in {pdf_name}")

print("\n--- CHECKING DocChain_IEEE_Report.docx LOCK STATUS ---")
try:
    with open("DocChain_IEEE_Report.docx", "a") as f:
        print("DocChain_IEEE_Report.docx is now UNLOCKED!")
        # Copy DocChain_IEEE_Final_Report.docx into DocChain_IEEE_Report.docx
        import shutil
        shutil.copyfile("DocChain_IEEE_Final_Report.docx", "DocChain_IEEE_Report.docx")
        print("DocChain_IEEE_Report.docx has been OVERWRITTEN with the clean version!")
except Exception as e:
    print("DocChain_IEEE_Report.docx is currently locked:", e)
