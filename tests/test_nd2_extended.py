from pathlib import Path

import pytest
from ome_zarr_converters_tools.testing import run_converter_test

from fractal_nd2_converters import convert_nd2_plate, convert_nd2_single_image

from .utils import DATA_EXTENDED_DIR

RAW_DIR = DATA_EXTENDED_DIR / "raw"
SNAPSHOT_DIR = DATA_EXTENDED_DIR / "snapshots"

_PLATE_DATASETS = [
    ("hcs_3w2p2c1z1t", "", "hcs_3w2p2c1z1t"),
    ("hcs_3w2p2c1z6t", "", "hcs_3w2p2c1z6t"),
    ("hcs_3w2p2c3z1t", "", "hcs_3w2p2c3z1t"),
    ("hcs_3w2p2c1z1t_SplitP", "", "hcs_3w2p2c1z1t_SplitP"),
    ("hcs_3w6p2c1z1t_10overlap", "", "hcs_3w6p2c1z1t_10overlap"),
]
_SINGLE_IMAGE_DATASETS = [
    ("img_1p1c1z1t_noND", "img_1p1c1z1t_noND.nd2", "img_1p1c1z1t_noND"),
    ("img_1p1c1z1t", "img_1p1c1z1t.nd2", "img_1p1c1z1t"),
    ("img_1p1c1z1t_LI1x1", "img_1p1c1z1t_LI1x1.nd2", "img_1p1c1z1t_LI1x1"),
    ("img_1p2c1z1t", "img_1p2c1z1t.nd2", "img_1p2c1z1t"),
    ("img_1p2c3z1t", "img_1p2c3z1t.nd2", "img_1p2c3z1t"),
    ("img_1p2c3z1t_zlambda", "img_1p2c3z1t_zlambda.nd2", "img_1p2c3z1t_zlambda"),
    ("img_1p2c1z1t_LI2x3", "img_1p2c1z1t_LI2x3.nd2", "img_1p2c1z1t_LI2x3"),
    ("img_1p2c3z1t_LI2x3", "img_1p2c3z1t_LI2x3.nd2", "img_1p2c3z1t_LI2x3"),
    ("img_6p2c1z1t", "img_6p2c1z1t.nd2", "img_6p2c1z1t"),
    ("img_6p2c3z1t", "img_6p2c3z1t.nd2", "img_6p2c3z1t"),
    ("img_2p2c1z1t_LI2x3", "img_2p2c1z1t_LI2x3.nd2", "img_2p2c1z1t_LI2x3"),
    ("img_2p2c1z4t_2sint", "img_2p2c1z4t_2sint.nd2", "img_2p2c1z4t_2sint"),
    ("img_2p2c1z4t_5sint", "img_2p2c1z4t_5sint.nd2", "img_2p2c1z4t_5sint"),
]


@pytest.mark.extended
@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(RAW_DIR / dataset / acq_folder),
                        "acquisition_id": 0,
                    }
                ]
            },
            snapshot_name,
        )
        for dataset, acq_folder, snapshot_name in _PLATE_DATASETS
    ],
)
def test_nd2_plate_extended(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
    converter_options,
):
    run_converter_test(
        tmp_path=tmp_path,
        api_fn=convert_nd2_plate,
        api_kwargs=init_task_kwargs,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.json",
        update_snapshots=update_snapshots,
        converter_options=converter_options,
    )


@pytest.mark.extended
@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(RAW_DIR / dataset / acq_folder),
                        "acquisition_id": 0,
                    }
                ]
            },
            snapshot_name,
        )
        for dataset, acq_folder, snapshot_name in _SINGLE_IMAGE_DATASETS
    ],
)
def test_nd2_single_image_extended(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
    converter_options,
):
    run_converter_test(
        tmp_path=tmp_path,
        api_fn=convert_nd2_single_image,
        api_kwargs=init_task_kwargs,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.json",
        update_snapshots=update_snapshots,
        converter_options=converter_options,
        output_type="single_image",
    )
