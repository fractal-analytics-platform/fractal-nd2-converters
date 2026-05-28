from pathlib import Path

import pytest

from fractal_nd2_converters.compute_task_image_in_plate import (
    compute_task_image_in_plate,
)
from fractal_nd2_converters.compute_task_single_image import (
    compute_task_single_image,
)
from fractal_nd2_converters.init_task_convert_nd2_plate import (
    init_task_convert_nd2_plate,
)
from fractal_nd2_converters.init_task_convert_nd2_single_image import (
    init_task_convert_nd2_single_image,
)

from .utils import DATA_DIR, LOCAL_DATA_DIR, SNAPSHOT_DIR, run_converter_test

# ---------------------------------------------------------------------------
# Zenodo test data (auto-downloaded in conftest)
# ---------------------------------------------------------------------------

ND2_PLATE_DATA = (
    DATA_DIR / "WellPlate_Jobs_3w6p2c0z0t_overlap" / "20250506_124144_018"
)
ND2_SINGLE_FILE = (
    ND2_PLATE_DATA / "WellB02_ChannelSD DAPI- EM,SD GFP - EM_Seq0000.nd2"
)


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(ND2_PLATE_DATA),
                        "acquisition_id": 0,
                    }
                ]
            },
            "nd2_plate_3w6p2c",
        ),
    ],
)
def test_nd2_plate(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
):
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=init_task_convert_nd2_plate,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_image_in_plate,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
    )


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(ND2_SINGLE_FILE),
                        "image_name": "single_wellB02",
                    }
                ]
            },
            "nd2_single_1i2c",
        ),
    ],
)
def test_nd2_single_image(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
):
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=init_task_convert_nd2_single_image,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_single_image,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
        output_type="single_image",
    )


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(ND2_PLATE_DATA),
                    }
                ]
            },
            "nd2_folder_3i2c",
        ),
    ],
)
def test_nd2_folder(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
):
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=init_task_convert_nd2_single_image,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_single_image,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
        output_type="single_image",
    )


# ---------------------------------------------------------------------------
# Local TBH test data (skipped when not present)
# ---------------------------------------------------------------------------

_3W2P = LOCAL_DATA_DIR / "WellPlate_Jobs_3w2p2c0z0t" / "20250506_123408_112"
_3W2P_SPLITP = (
    LOCAL_DATA_DIR / "WellPlate_Jobs_3w2p2c0z0t_splitP" / "20250506_123741_693"
)
_3W2P_6T = LOCAL_DATA_DIR / "WellPlate_Jobs_3w2p2c0z6t" / "20250506_124539_026"
_3W2P_3Z = LOCAL_DATA_DIR / "WellPlate_Jobs_3w2p2c3z0t" / "20250506_124350_001"
_ND_ACQ = LOCAL_DATA_DIR / "ND_Acquisitions_nd2"


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {"acquisitions": [{"path": str(_3W2P), "acquisition_id": 0}]},
            "nd2_plate_3w2p2c",
        ),
        (
            {"acquisitions": [{"path": str(_3W2P_SPLITP), "acquisition_id": 0}]},
            "nd2_plate_3w2p2c_splitP",
        ),
        (
            {"acquisitions": [{"path": str(_3W2P_6T), "acquisition_id": 0}]},
            "nd2_plate_3w2p2c6t",
        ),
        (
            {"acquisitions": [{"path": str(_3W2P_3Z), "acquisition_id": 0}]},
            "nd2_plate_3w2p2c3z",
        ),
    ],
)
def test_nd2_plate_local(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
    local_data_available: bool,
):
    if not local_data_available:
        pytest.skip("Local TBH test data not available")
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=init_task_convert_nd2_plate,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_image_in_plate,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
    )


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(_ND_ACQ / "05_2c_3z.nd2"),
                        "image_name": "nd_acq_2c_3z",
                    }
                ]
            },
            "nd2_single_nd_acq_2c3z",
        ),
    ],
)
def test_nd2_single_nd_acq(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
    local_data_available: bool,
):
    if not local_data_available:
        pytest.skip("Local TBH test data not available")
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=init_task_convert_nd2_single_image,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_single_image,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
        output_type="single_image",
    )
