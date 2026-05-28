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

from .utils import DATA_EXTENDED_DIR, run_converter_test

RAW_DIR = DATA_EXTENDED_DIR / "raw"
SNAPSHOT_DIR = DATA_EXTENDED_DIR / "snapshots"

_PLATE_DATASETS = []
_SINGLE_IMAGE_DATASETS = []


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
        init_task_fn=init_task_convert_nd2_plate,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_image_in_plate,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
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
        init_task_fn=init_task_convert_nd2_single_image,
        init_task_kwargs=init_task_kwargs,
        compute_task_fn=compute_task_single_image,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
        converter_options=converter_options,
        output_type="single_image",
    )
