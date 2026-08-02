"""Master Script to generate and sync all deliverables in root directories.
Places 01_Executive_Summary.pdf, 01_Executive_Summary.md, 02_Architecture.pdf,
02_Architecture.md, 03_Demo_Script_and_Walkthrough.md, and 05_Benchmark.xlsx
in both /Users/venkatreddy/Desktop/OCR/DataDynamos/ and /Users/venkatreddy/Desktop/OCR/
"""

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("/Users/venkatreddy/Desktop/OCR/DataDynamos")
PARENT_ROOT = Path("/Users/venkatreddy/Desktop/OCR")
SUBMISSION_DIR = PROJECT_ROOT / "backend/submission_package/Name_HealthcareAIHackathon"
PYTHON_BIN = PROJECT_ROOT / "backend/.venv/bin/python"

def run_script(script_path):
    print(f"Running script: {script_path.name}...")
    res = subprocess.run([str(PYTHON_BIN), str(script_path)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running {script_path.name}:\n{res.stderr}")
    else:
        print(f"Success: {res.stdout.strip()}")

def sync_deliverables():
    # 1. Run individual generators
    run_script(PROJECT_ROOT / "scripts/build_executive_summary.py")
    run_script(PROJECT_ROOT / "scripts/build_architecture_pdf.py")
    run_script(PROJECT_ROOT / "backend/scripts/generate_submission_deliverables.py")

    # Files to sync
    files_to_sync = [
        "01_Executive_Summary.pdf",
        "01_Executive_Summary.md",
        "02_Architecture.pdf",
        "02_Architecture.md",
        "03_Demo_Script_and_Walkthrough.md",
        "05_Benchmark.xlsx",
    ]

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

    print("\nSyncing all files across root folders...")
    for filename in files_to_sync:
        # Check source in project root or submission dir
        src = PROJECT_ROOT / filename
        if not src.exists():
            src = SUBMISSION_DIR / filename
        
        if src.exists():
            # Copy to project root
            target_proj = PROJECT_ROOT / filename
            if src != target_proj:
                shutil.copy2(src, target_proj)
            
            # Copy to parent root /Users/venkatreddy/Desktop/OCR/
            target_parent = PARENT_ROOT / filename
            shutil.copy2(src, target_parent)

            # Copy to submission package dir
            target_sub = SUBMISSION_DIR / filename
            if src != target_sub:
                shutil.copy2(src, target_sub)

            print(f"Synced {filename} -> {target_proj} & {target_parent} & {target_sub}")
        else:
            print(f"Warning: Source file {filename} not found!")

if __name__ == "__main__":
    sync_deliverables()
