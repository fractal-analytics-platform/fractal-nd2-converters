from pathlib import Path

import pytest
from ome_zarr_converters_tools.testing import run_converter_test

from fractal_nd2_converters import convert_nd2_single_image

from .utils import DATA_DIR, SNAPSHOT_DIR

RAW_DIR = DATA_DIR / "raw"
_SINGLE_FILE = RAW_DIR / "img_1p2c1z1t.nd2"
_FOLDER_DATA = RAW_DIR / "hcs_3w2p2c1z1t_SplitP"


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(_SINGLE_FILE),
                        "image_name": "img_1p2c1z1t",
                    }
                ]
            },
            "img_1p2c1z1t",
        ),
    ],
)
def test_nd2_single_image(
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


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(_FOLDER_DATA),
                    }
                ]
            },
            "img_3w2p2c1z1t_SplitP",
        ),
    ],
)
def test_nd2_folder(
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
