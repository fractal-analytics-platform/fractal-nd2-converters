from pathlib import Path

import pytest

from fractal_nd2_converters.compute_task_single_image import (
    compute_task_single_image,
)
from fractal_nd2_converters.init_task_convert_nd2_single_image import (
    init_task_convert_nd2_single_image,
)

from .utils import DATA_DIR, SNAPSHOT_DIR, run_converter_test

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
        init_task_fn=init_task_convert_nd2_single_image,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_single_image,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
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
        init_task_fn=init_task_convert_nd2_single_image,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_single_image,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
        converter_options=converter_options,
        output_type="single_image",
    )
