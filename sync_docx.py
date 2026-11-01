import shutil
import time

src = "DocChain_IEEE_Final_Report.docx"
dst = "DocChain_IEEE_Report.docx"

for i in range(10):
    try:
        shutil.copyfile(src, dst)
        print(f"Successfully synced {dst}!")
        break
    except PermissionError:
        print(f"Attempt {i+1}: {dst} is still open in WPS Office. Waiting 2 seconds...")
        time.sleep(2)
