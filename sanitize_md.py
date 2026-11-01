import os
import re

md_path = "DocChain_IEEE_Report.md"
if os.path.exists(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Strip display equations
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: m.group(1).replace(r'\text{', '').replace('}', '').replace(r'\sum_{i=1}^{k}', 'Σ').replace(r'\leftarrow', '←').replace(r'\tau', 'tag').replace(r'\_', '_'), text, flags=re.DOTALL)
    
    # Strip inline equations
    text = re.sub(r'\$(.*?)\$', lambda m: m.group(1).replace(r'\text{', '').replace('}', '').replace(r'\leftarrow', '←').replace(r'\rightarrow', '→').replace(r'\_', '_').replace(r'\neq', '≠'), text)

    # Clean backticks from table / headings if any
    text = text.replace(r'\_', '_')

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Sanitized DocChain_IEEE_Report.md successfully!")
