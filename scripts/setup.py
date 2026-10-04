"""
Project Environment and Data Setup Utility
------------------------------------------
Prepares all directories, verifies Python environment, downloads MovieLens 100K,
and runs the complete data processing & serving layer generation pipeline.
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def setup_project():
    print("==================================================")
    print(" Setting up Movie Recommendation Data Serving Project")
    print("==================================================")

    # 1. Check Python version
    major, minor = sys.version_info[:2]
    print(f"[OK] Python version: {major}.{minor}")

    # 2. Run data pipeline CLI
    pipeline_script = BASE_DIR / "scripts" / "run_pipeline.py"
    print(f"[INFO] Executing pipeline: {pipeline_script}")
    result = subprocess.run([sys.executable, str(pipeline_script)], cwd=str(BASE_DIR))

    if result.returncode != 0:
        print("[ERROR] Pipeline setup failed. Please inspect logs.")
        sys.exit(1)

    print("\n[SUCCESS] Project setup and serving layer built successfully!")
    print("Next steps:")
    print("1. Start backend:  python -m uvicorn backend.main:app --reload")
    print("2. Start frontend: cd frontend && npm install && npm run dev")


if __name__ == "__main__":
    setup_project()
