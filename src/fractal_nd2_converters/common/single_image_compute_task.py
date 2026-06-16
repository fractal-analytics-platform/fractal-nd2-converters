"""Compute task for single-image ND2 acquisitions."""

import logging

from ome_zarr_converters_tools import (
    ConvertParallelInitArgs,
    ImageListUpdateDict,
    SingleImage,
)
from pydantic import validate_call

from fractal_nd2_converters.common._compute import run_nd2_compute_task

logger = logging.getLogger(__name__)


@validate_call
def single_image_compute_task(
    *,
    # Fractal parameters
    zarr_url: str,
    init_args: ConvertParallelInitArgs,
) -> ImageListUpdateDict:
    """Create a single standalone OME-Zarr image from an ND2 file.

    Args:
        zarr_url (str): URL to the OME-Zarr image to populate.
        init_args (ConvertParallelInitArgs): Arguments from the init task.

    Returns:
        ImageListUpdateDict: The Fractal image-list update for the new image.
    """
    return run_nd2_compute_task(
        zarr_url=zarr_url, init_args=init_args, collection_type=SingleImage
    )


if __name__ == "__main__":
    from fractal_task_tools.task_wrapper import run_fractal_task

    run_fractal_task(task_function=single_image_compute_task, logger_name=logger.name)
