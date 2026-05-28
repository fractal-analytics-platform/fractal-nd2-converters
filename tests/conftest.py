"""Test configuration for fractal-nd2-converters."""

import logging
import zipfile
from pathlib import Path

import pytest
from ome_zarr_converters_tools import ConverterOptions, OmeZarrOptions
from ome_zarr_converters_tools.models._converter_options import BackendType

logger = logging.getLogger(__name__)

_DATA_EXTENDED_DIR = Path(__file__).parent / "data-extended" / "Nikon-ND2"

# zip filename → canonical directory name under data-extended/Nikon-ND2/raw/
LOCAL_ZIPS = {
    "WellPlate_Jobs_3w2p2c0z0t.zip": "hcs_3w2p2c0z0t",
    "WellPlate_Jobs_3w2p2c0z6t.zip": "hcs_3w2p2c0z6t",
    "WellPlate_Jobs_3w2p2c3z0t.zip": "hcs_3w2p2c3z0t",
    "ND_Acquisitions_nd2.zip": "nd_acq",
}


def _extract_extended_data() -> None:
    """Extract local TBH zips from data-extended/Nikon-ND2/ into its raw/ subdir."""
    if not _DATA_EXTENDED_DIR.exists():
        return
    raw_dir = _DATA_EXTENDED_DIR / "raw"
    raw_dir.mkdir(exist_ok=True)
    for zip_name, canonical_name in LOCAL_ZIPS.items():
        zip_path = _DATA_EXTENDED_DIR / zip_name
        target_dir = raw_dir / canonical_name
        if not zip_path.exists() or target_dir.exists():
            continue
        logger.info(f"Extracting extended test data: {zip_name}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(raw_dir)
        vendor_dir = raw_dir / zip_name.replace(".zip", "")
        if vendor_dir.exists():
            vendor_dir.rename(target_dir)


def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Regenerate assertion snapshot YAMLs",
    )
    parser.addoption(
        "--extended",
        action="store_true",
        default=False,
        help="Run extended tests requiring large local test datasets",
    )


def pytest_configure(config):
    """Prepare test data and register markers before test collection."""
    config.addinivalue_line(
        "markers", "extended: mark test as requiring the extended test datasets"
    )
    _extract_extended_data()


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--extended"):
        skip_marker = pytest.mark.skip(reason="Pass --extended to run extended tests")
        for item in items:
            if "extended" in item.keywords:
                item.add_marker(skip_marker)


@pytest.fixture
def update_snapshots(request):
    return request.config.getoption("--update-snapshots")


@pytest.fixture
def converter_options():
    return ConverterOptions(
        omezarr_options=OmeZarrOptions(
            ngff_version="0.5", table_backend=BackendType.CSV
        )
    )
