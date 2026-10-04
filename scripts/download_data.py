"""
MovieLens 100K Dataset Downloader
---------------------------------
Automated utility to fetch, verify, and unpack the MovieLens 100K dataset
from GroupLens research repository into the raw data directory.
"""

import os
import sys
import zipfile
import logging
from pathlib import Path
import requests

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("download_data")

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
TARGET_DIR = RAW_DIR / "ml-100k"
ZIP_PATH = RAW_DIR / "ml-100k.zip"


def verify_dataset(target_dir: Path) -> bool:
    """Check if the required MovieLens 100K files exist in the target directory."""
    required_files = ["u.item", "u.data", "u.genre", "u.user"]
    return all((target_dir / f).exists() for f in required_files)


def download_and_extract(force: bool = False) -> bool:
    """Download MovieLens 100K zip file and extract to raw data folder."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if not force and verify_dataset(TARGET_DIR):
        logger.info(f"Dataset already present and verified at: {TARGET_DIR}")
        return True

    logger.info(f"Downloading MovieLens 100K from: {MOVIELENS_URL}")
    try:
        # Use requests with stream to handle large download safely
        try:
            import certifi
            verify_ssl = certifi.where()
        except ImportError:
            verify_ssl = True

        response = requests.get(MOVIELENS_URL, stream=True, timeout=30, verify=verify_ssl)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1024 * 64

        with open(ZIP_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and downloaded % (chunk_size * 8) == 0:
                        percent = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {percent:.1f}% ({downloaded / 1024 / 1024:.2f} MB)")

        logger.info(f"Download completed successfully. Saved to: {ZIP_PATH}")

        # Extract the archive
        logger.info("Extracting archive...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(RAW_DIR)

        # Cleanup zip file
        if ZIP_PATH.exists():
            ZIP_PATH.unlink()

        if verify_dataset(TARGET_DIR):
            logger.info(f"MovieLens 100K successfully extracted and verified at: {TARGET_DIR}")
            return True
        else:
            logger.error(f"Archive extracted, but required files missing in {TARGET_DIR}")
            return False

    except Exception as e:
        logger.error(f"Failed to download or extract dataset: {e}")
        logger.error(
            "\n"
            "====================================================================\n"
            "FALLBACK INSTRUCTIONS (Offline / Network Issue):\n"
            "1. Download 'ml-100k.zip' manually from:\n"
            f"   {MOVIELENS_URL}\n"
            "2. Unzip the contents so that files are placed at:\n"
            f"   {TARGET_DIR}\n"
            "   (Specifically ensuring 'u.item', 'u.data', and 'u.genre' are inside)\n"
            "3. Rerun: python scripts/run_pipeline.py\n"
            "===================================================================="
        )
        return False


if __name__ == "__main__":
    force_download = "--force" in sys.argv
    success = download_and_extract(force=force_download)
    sys.exit(0 if success else 1)
