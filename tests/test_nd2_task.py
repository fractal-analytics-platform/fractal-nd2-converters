from pathlib import Path

import pytest

from fractal_nd2_converters.init_task_convert_nd2_plate import (
    init_task_convert_nd2_plate,
)
from fractal_nd2_converters.init_task_convert_nd2_single_image import (
    init_task_convert_nd2_single_image,
)

from .utils import DATA_DIR, run_converter_test

TESTS_DIR = Path(__file__).parent
SNAPSHOT_DIR = TESTS_DIR / "snapshots"
ND2_DATA_DIR = DATA_DIR / "WellPlate_Jobs_3w6p2c0z0t_overlap"


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": f"{ND2_DATA_DIR}/20250506_124144_018",
                        "acquisition_id": 0,
                    }
                ]
            },
            "nd2_plate_3w6p2c",
        ),
    ],
)
def test_convert_nd2_plate(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
):
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=init_task_convert_nd2_plate,
        init_task_kwargs=init_task_kwargs,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
    )


def test_convert_nd2_single(
    tmp_path: Path,
    update_snapshots: bool,
):
    nd2_file = (
        f"{ND2_DATA_DIR}/20250506_124144_018/"
        "WellB02_ChannelSD DAPI- EM,SD GFP - EM_Seq0000.nd2"
    )
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=init_task_convert_nd2_single_image,
        init_task_kwargs={
            "acquisitions": [
                {
                    "path": nd2_file,
                    "image_name": "single_wellB02",
                }
            ]
        },
        snapshot_path=SNAPSHOT_DIR / "nd2_single_1i2c.yaml",
        update_snapshots=update_snapshots,
    )
