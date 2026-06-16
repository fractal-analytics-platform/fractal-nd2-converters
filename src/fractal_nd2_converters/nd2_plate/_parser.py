"""Parse ND2 plate metadata into ``TiledImage`` objects.

Each .nd2 file in the acquisition folder must carry well information in its
filename (e.g. ``WellB02_...``). Multiple files per well are supported: each
file becomes a separate field of view within the well image.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from ome_zarr_converters_tools import (
    ConverterOptions,
    ImageInPlate,
    TiledImage,
    tiles_aggregation_pipeline,
)

from fractal_nd2_converters.common import get_attributes_from_condition_table
from fractal_nd2_converters.common._tile_builders import build_tiles, get_nd2_files

if TYPE_CHECKING:
    from fractal_nd2_converters.nd2_plate.convert_nd2_plate_init_task import (
        ND2PlateAcquisitionModel,
    )

logger = logging.getLogger(__name__)


def _parse_well_info(fn) -> tuple[str, int] | None:
    """Get well info from filename.

    Returns:
        Tuple of (row, column) if well pattern is found, None otherwise.
    """
    pattern = r"Well([A-Z])(\d+)"
    match = re.search(pattern, Path(fn).stem)
    if match:
        row = match.group(1)
        col = int(match.group(2))
        return row, col
    else:
        return None


def parse_nd2_plate_acquisition(
    *,
    acquisition_model: ND2PlateAcquisitionModel,
    converter_options: ConverterOptions,
) -> list[TiledImage]:
    """Parse nd2 plate acquisition and return list of tiled images.

    Each .nd2 file in the folder must have well information in its filename
    (e.g. WellB02_...). Multiple files per well are supported: each file
    becomes a separate FOV within the well image.

    Args:
        acquisition_model: Acquisition input model containing path and options.
        converter_options: Converter options for tile processing.

    Returns:
        List of TiledImage objects ready for conversion.
    """
    nd2_list = get_nd2_files(acquisition_model.path)
    condition_table = acquisition_model.get_condition_table()

    # Group files by well so we can detect multi-file wells.
    well_files: dict[tuple[str, int], list[Path]] = defaultdict(list)
    for nd2_path in nd2_list:
        well_info = _parse_well_info(nd2_path)
        if well_info is None:
            logger.warning(
                f"Skipping {nd2_path.name}: filename does not match "
                "Well pattern (e.g. WellA01, WellB02)"
            )
            continue
        well_files[well_info].append(nd2_path)

    all_tiles = []
    for (row, col), files in well_files.items():
        collection = ImageInPlate(
            plate_name=acquisition_model.normalized_plate_name,
            row=row,
            column=col,
            acquisition=acquisition_model.acquisition_id,
        )
        attributes = get_attributes_from_condition_table(
            condition_table=condition_table,
            row=row,
            column=col,
            acquisition=acquisition_model.acquisition_id,
        )

        multi_file_well = len(files) > 1
        for i, nd2_path in enumerate(files):
            # When multiple files share a well, single-position files would all
            # get fov_name="FOV_0". Pass an explicit override so each file gets
            # a distinct name (FOV_0, FOV_1, …).
            fov_override = f"FOV_{i}" if multi_file_well else None
            tiles = build_tiles(
                nd2_path=nd2_path,
                collection=collection,
                attributes=attributes,
                fov_name_override=fov_override,
            )
            all_tiles.extend(tiles)

    logger.info(f"Built {len(all_tiles)} tiles")

    tiled_images = tiles_aggregation_pipeline(
        tiles=all_tiles,
        converter_options=converter_options,
        filters=acquisition_model.advanced.filters,
    )

    return tiled_images
