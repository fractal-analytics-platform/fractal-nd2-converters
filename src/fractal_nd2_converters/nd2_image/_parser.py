"""Parse ND2 image (non-plate) metadata into ``TiledImage`` objects.

Handles single .nd2 files and folders of .nd2 files that do not follow a plate
layout. Each file (or each position within it) becomes a positioned field of
view inside a single OME-Zarr image.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ome_zarr_converters_tools import (
    ConverterOptions,
    SingleImage,
    TiledImage,
    tiles_aggregation_pipeline,
)

from fractal_nd2_converters.common._tile_builders import build_tiles, get_nd2_files

if TYPE_CHECKING:
    from fractal_nd2_converters.nd2_image.convert_nd2_image_init_task import (
        ND2ImageAcquisitionModel,
    )

logger = logging.getLogger(__name__)


def parse_nd2_image_acquisition(
    *,
    acquisition_model: ND2ImageAcquisitionModel,
    converter_options: ConverterOptions,
) -> list[TiledImage]:
    """Parse nd2 image acquisition and return list of tiled images.

    Handles single .nd2 files and folders of .nd2 files (non-plate).

    Args:
        acquisition_model: Acquisition input model containing path and options.
        converter_options: Converter options for tile processing.

    Returns:
        List of TiledImage objects ready for conversion.
    """
    nd2_list = get_nd2_files(acquisition_model.path)

    all_tiles = []
    for nd2_path in nd2_list:
        zarr_name = acquisition_model.get_zarr_name(nd2_path)
        collection = SingleImage(image_path=zarr_name)

        tiles = build_tiles(
            nd2_path=nd2_path,
            collection=collection,
            attributes={},
        )
        all_tiles.extend(tiles)

    logger.info(f"Built {len(all_tiles)} tiles")

    tiled_images = tiles_aggregation_pipeline(
        tiles=all_tiles,
        converter_options=converter_options,
        filters=acquisition_model.advanced.filters,
    )

    return tiled_images
