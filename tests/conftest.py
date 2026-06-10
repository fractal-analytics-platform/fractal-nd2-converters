"""Test configuration for fractal-nd2-converters."""

import logging
import shutil
import zipfile
from pathlib import Path

import pytest
from ome_zarr_converters_tools import ConverterOptions, OmeZarrOptions
from ome_zarr_converters_tools.models._converter_options import BackendType

logger = logging.getLogger(__name__)

_DATA_EXTENDED_DIR = Path(__file__).parent / "data-extended" / "Nikon-ND2"

# zip filename → canonical directory name under data-extended/Nikon-ND2/raw/
LOCAL_ZIPS = {
    "WellPlate_Jobs_3w2p2c0z0t.zip": "hcs_3w2p2c1z1t",
    "WellPlate_Jobs_3w2p2c0z6t.zip": "hcs_3w2p2c1z6t",
    "WellPlate_Jobs_3w2p2c3z0t.zip": "hcs_3w2p2c3z1t",
    "WellPlate_Jobs_3w2p2c0z0t_splitP.zip": "hcs_3w2p2c1z1t_SplitP",
    "WellPlate_Jobs_3w6p2c0z0t_overlap.zip": "hcs_3w6p2c1z1t_10overlap",
}

# zip filename → {original_filename_inside_zip: canonical_dir_name}
# Each file is extracted into its own canonical directory and renamed to match it.
LOCAL_ZIPS_SPLIT = {
    "ND_Acquisitions_nd2.zip": {
        "01_0c_0z.nd2": "img_1p1c1z1t_noND",
        "02_1c_0z.nd2": "img_1p1c1z1t",
        "03_LI1x1_1c_1z.nd2": "img_1p1c1z1t_LI1x1",
        "04_2c_0z.nd2": "img_1p2c1z1t",
        "05_2c_3z.nd2": "img_1p2c3z1t",
        "06_3z_2c_z-lamda.nd2": "img_1p2c3z1t_zlambda",
        "07_LI2x3_2c_0z.nd2": "img_1p2c1z1t_LI2x3",
        "08_LI2x3_2c_3z.nd2": "img_1p2c3z1t_LI2x3",
        "09_XY2x3tiled_2c_0z.nd2": "img_6p2c1z1t",
        "10_XY2x3tiled_2c_3z.nd2": "img_6p2c3z1t",
        "11_XY2_LI2x3_2c_0z.nd2": "img_2p2c1z1t_LI2x3",
        "12_6t_XY2_2c_0z.nd2": "img_2p2c1z4t_2sint",
        "13_4t_XY2_2c_0z.nd2": "img_2p2c1z4t_5sint",
    },
}


def _extract_extended_data() -> None:
    """Extract local zips from data-extended/Nikon-ND2/ into its raw/ subdir."""
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

    for zip_name, file_map in LOCAL_ZIPS_SPLIT.items():
        zip_path = _DATA_EXTENDED_DIR / zip_name
        if not zip_path.exists():
            continue
        if all(
            (raw_dir / canonical_name).exists() for canonical_name in file_map.values()
        ):
            continue
        tmp_dir = raw_dir / zip_name.replace(".zip", "")
        if not tmp_dir.exists():
            logger.info(f"Extracting extended test data: {zip_name}...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(raw_dir)
        for src_name, canonical_name in file_map.items():
            target_dir = raw_dir / canonical_name
            if target_dir.exists():
                continue
            src = tmp_dir / src_name
            if src.exists():
                target_dir.mkdir()
                src.rename(target_dir / f"{canonical_name}.nd2")
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)


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
