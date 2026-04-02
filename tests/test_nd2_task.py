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

from .utils import DATA_DIR, SNAPSHOT_DIR, run_converter_test

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
    )
