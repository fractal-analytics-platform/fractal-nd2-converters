"""Convert Nikon ND2 plate datasets to OME-Zarr."""

import logging

from ome_zarr_converters_tools import (
    ConverterOptions,
    OverwriteMode,
    setup_images_for_conversion,
)
from pydantic import validate_call

from fractal_nd2_converters._nd2_utils import (
    ND2PlateAcquisitionModel,
    parse_nd2_plate_acquisition,
)

logger = logging.getLogger("convert_nd2_plate_task")

default_converter_options = ConverterOptions()


@validate_call
def init_task_convert_nd2_plate(
    *,
    # Fractal parameters
    zarr_dir: str,
    # Task parameters
    acquisitions: list[ND2PlateAcquisitionModel],
    converter_options: ConverterOptions = default_converter_options,
    overwrite: OverwriteMode = OverwriteMode.NO_OVERWRITE,
):
    """Initialize the task to convert Nikon ND2 plate datasets to OME-Zarr.

    Args:
        zarr_dir (str): Directory to store the Zarr files.
        acquisitions (list[ND2PlateAcquisitionModel]): List of plate
            acquisitions to convert to OME-Zarr.
        converter_options (ConverterOptions): Advanced converter options.
        overwrite (OverwriteMode): Overwrite mode for existing data.
            - "No Overwrite": Do not overwrite existing data.
            - "Overwrite": Remove and replace existing data.
            - "Extend": Extend existing data without removing it.
            Default is "No Overwrite".
    """
    tiled_images = []
    for acq in acquisitions:
        _tiled_images = parse_nd2_plate_acquisition(
            acquisition_model=acq,
            converter_options=converter_options,
        )
        if not _tiled_images:
            logger.warning(f"No images found in {acq.path}")
            continue
        logger.info(f"Found {len(_tiled_images)} images in acquisition {acq.path}")
        tiled_images.extend(_tiled_images)

    if not tiled_images:
        raise ValueError("No images found in any of the provided acquisitions.")

    logger.info(f"Total {len(tiled_images)} images found in all acquisitions.")

    parallelization_list = setup_images_for_conversion(
        tiled_images=tiled_images,
        zarr_dir=zarr_dir,
        converter_options=converter_options,
        collection_type="ImageInPlate",
        overwrite_mode=overwrite,
        ngff_version=converter_options.omezarr_options.ngff_version,
    )
    logger.info(
        f"Prepared parallelization list with {len(parallelization_list)} items."
    )
    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_task_tools.task_wrapper import run_fractal_task

    run_fractal_task(task_function=init_task_convert_nd2_plate, logger_name=logger.name)
