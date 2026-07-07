from pathlib import Path

import pytest
from ome_zarr_converters_tools.testing import run_converter_test

from fractal_nd2_converters import convert_nd2_plate

from .utils import DATA_DIR, SNAPSHOT_DIR

RAW_DIR = DATA_DIR / "raw"
_PLATE_DATA = RAW_DIR / "hcs_3w2p2c1z1t_SplitP"


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {
                "acquisitions": [
                    {
                        "path": str(_PLATE_DATA),
                        "acquisition_id": 0,
                    }
                ]
            },
            "hcs_3w2p2c1z1t_SplitP",
        ),
    ],
)
def test_nd2_plate(
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
