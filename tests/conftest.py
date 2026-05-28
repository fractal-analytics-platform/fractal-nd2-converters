"""Test configuration for fractal-nd2-converters."""

import hashlib
import logging
import os
import urllib.request
import zipfile
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
LOCAL_DATA_DIR = DATA_DIR / "local"

ZENODO_RECORD_URL = "https://zenodo.org/api/records/15411420/files"
ZENODO_FILES = {
    "WellPlate_Jobs_3w6p2c0z0t_overlap.zip": {
        "md5": "cef8298f9722532cc47e962b674b127c",
    },
}

# Local test datasets (not on Zenodo). Checked out from env var or a known
# developer path. Tests that require these are skipped when the source isn't
# found.
_DEFAULT_LOCAL_TBH = Path("~/data/Converters_Test_Data_TODO/Nikon-nd2-TBH").expanduser()
LOCAL_TBH_DIR = Path(os.environ.get("ND2_LOCAL_TEST_DATA", str(_DEFAULT_LOCAL_TBH)))

LOCAL_ZIPS = [
    "WellPlate_Jobs_3w2p2c0z0t.zip",
    "WellPlate_Jobs_3w2p2c0z0t_splitP.zip",
    "WellPlate_Jobs_3w2p2c0z6t.zip",
    "WellPlate_Jobs_3w2p2c3z0t.zip",
    "ND_Acquisitions_nd2.zip",
]


def _download_zenodo_data() -> None:
    """Download and extract test data from Zenodo if not already present."""
    for filename, meta in ZENODO_FILES.items():
        extracted_dir = DATA_DIR / filename.replace(".zip", "")
        if extracted_dir.exists():
            return

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = DATA_DIR / filename
        url = f"{ZENODO_RECORD_URL}/{filename}/content"

        logger.info(f"Downloading {filename} from Zenodo...")
        urllib.request.urlretrieve(url, zip_path)

        # Verify MD5
        md5 = hashlib.md5(zip_path.read_bytes()).hexdigest()
        if md5 != meta["md5"]:
            zip_path.unlink()
            raise RuntimeError(
                f"MD5 mismatch for {filename}: "
                f"expected {meta['md5']}, got {md5}"
            )

        # Extract and remove zip
        logger.info(f"Extracting {filename}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(DATA_DIR)
        zip_path.unlink()


def _extract_local_data() -> None:
    """Extract local TBH test zips to tests/data/local/ if present."""
    if not LOCAL_TBH_DIR.exists():
        return
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename in LOCAL_ZIPS:
        zip_path = LOCAL_TBH_DIR / filename
        extracted_dir = LOCAL_DATA_DIR / filename.replace(".zip", "")
        if not zip_path.exists() or extracted_dir.exists():
            continue
        logger.info(f"Extracting local test data: {filename}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(LOCAL_DATA_DIR)


def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Regenerate assertion snapshot YAMLs",
    )


def pytest_configure(config):
    """Prepare test data before test collection."""
    _download_zenodo_data()
    _extract_local_data()


@pytest.fixture
def update_snapshots(request):
    return request.config.getoption("--update-snapshots")


@pytest.fixture
def local_data_available():
    """True when local TBH test datasets have been extracted."""
    return LOCAL_TBH_DIR.exists() and any(
        (LOCAL_DATA_DIR / z.replace(".zip", "")).exists() for z in LOCAL_ZIPS
    )
