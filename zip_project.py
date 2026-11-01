import os
import zipfile

project_dir = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain"
zip_path = r"C:\Users\Puneeth\Desktop\SEM5\ICC\docchain (2)\docchain\deploy.zip"

exclude_dirs = {'.venv', '.git', '.azure', '.azure_old', '.vscode', '.idea', '__pycache__'}
exclude_files = {'deploy.zip', 'verify_connections.py', 'verify_neon.py', '.env', 'docchain.db'}

print(f"Zipping {project_dir} to {zip_path}...")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(project_dir):
        # Filter out excluded directories in-place
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files:
                continue
            
            file_path = os.path.join(root, file)
            # Get relative path for the zip archive structure
            arcname = os.path.relpath(file_path, project_dir)
            zipf.write(file_path, arcname)
            # print(f"Added: {arcname}")

print("[OK] Zipping complete!")
