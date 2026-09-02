import subprocess
import os
from datetime import datetime

VENV_PYTHON = r"c:\p14venv\Scripts\python.exe"
REPO_DIR = r"C:\Projects\charts"  # The directory of your git repository

SCRIPT1 = r"c:\Projects\tracker\product_metadata.py"
SCRIPT2 = r"c:\Projects\tracker\product_metadata_360.py"
SCRIPT3 = r"C:\Projects\new_psn_app - Copy\resolve_concepts.py"
SCRIPT4 = r"C:\Projects\new_psn_app - Copy\get_metadata.py"
SCRIPT5 = r"C:\Projects\new_psn_app - Copy\get_missing_dates.py"
SCRIPT6 = r"C:\Projects\analytics2\export_metadata.py"
SCRIPT7 = r"C:\Projects\analytics2\compile_xbox.py"
SCRIPT8 = r"C:\Projects\analytics2\compile_ps.py"

# 1. Execute all metadata and chart compilation scripts sequentially
print("Starting database extraction and chart compilation pipeline...")
for script in [SCRIPT1, SCRIPT2, SCRIPT3, SCRIPT4, SCRIPT5, SCRIPT6, SCRIPT7, SCRIPT8]:
    print(f"Running: {os.path.basename(script)}...")
    subprocess.run([VENV_PYTHON, script], check=True)

print("Compilation pipeline completed. Initializing Git deployment...")

# 2. Check if any files are modified or untracked in the repository
status_check = subprocess.run(
    ["git", "status", "--porcelain"],
    cwd=REPO_DIR,
    capture_output=True,
    text=True,
    check=True,
)

if not status_check.stdout.strip():
    print("No changes detected in the charts repository. Pipeline finished.")
else:
    print("Modifications detected. Preparing commit...")

    # 3. Stage the modified and new files (the clean CSVs and metadata.json files)
    subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)

    # 4. Generate the commit message with a timestamp
    commit_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_message = f"Auto-update: {commit_time_str}"

    # 5. Commit the staged changes
    subprocess.run(["git", "commit", "-m", commit_message], cwd=REPO_DIR, check=True)

    # 6. Push the updates to your remote repository
    # Adjust "main" to your default branch name (e.g., "master") if necessary
    print("Pushing updates to GitHub...")
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)

    print("Pipeline executed and repository updated successfully.")
