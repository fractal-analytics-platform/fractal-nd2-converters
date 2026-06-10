"""Initialize the Nikon ND2 image to OME-Zarr conversion task."""

import logging
import re
from pathlib import Path

from ome_zarr_converters_tools import (
    AcquisitionOptions,
    ConverterOptions,
    OverwriteMode,
)
from pydantic import Field, validate_call

from fractal_nd2_converters.common import BaseAcquisitionModel, run_convert_init
from fractal_nd2_converters.nd2_image._parser import parse_nd2_image_acquisition

logger = logging.getLogger("convert_nd2_single_image_task")


default_converter_options = ConverterOptions()


class ND2ImageAcquisitionModel(BaseAcquisitionModel):
    """Model for Nikon ND2 non-plate acquisitions.

    Accepts a single .nd2 file or a folder of .nd2 files that do not
    follow a plate layout (no well information in filenames).
    """

    image_name: str | None = None
    """
    Optional custom name for the output OME-Zarr image. If not provided,
    the name will be derived from the file or folder name.
    """
    advanced: AcquisitionOptions = Field(default_factory=AcquisitionOptions)
    """
    Advanced acquisition options.
    """

    @property
    def normalized_image_name(self) -> str:
        """Get the normalized image name."""
        if self.image_name is not None:
            return self.image_name
        return self._sanitized_name

    def get_zarr_name(self, nd2_path: Path) -> str:
        """Get the sanitized zarr name for an nd2 file.

        For folders, appends the sanitized file stem to the image name.
        For single files, returns the image name directly.
        """
        if Path(self.path).is_dir():
            sanitized_stem = re.sub(r"[^A-Za-z0-9\-_. ]", "_", nd2_path.stem)
            return self.normalized_image_name + "_" + sanitized_stem
        return self.normalized_image_name


@validate_call
def convert_nd2_image_init_task(
    *,
    # Fractal parameters
    zarr_dir: str,
    # Task parameters
    acquisitions: list[ND2ImageAcquisitionModel],
    converter_options: ConverterOptions = default_converter_options,
    overwrite: OverwriteMode = OverwriteMode.NO_OVERWRITE,
):
    """Initialize the task to convert Nikon ND2 images to OME-Zarr.

    Use this task for standalone ND2 files or folders of ND2 files that
    do not follow a plate layout.

    Args:
        zarr_dir (str): Directory to store the Zarr files.
        acquisitions (list[ND2ImageAcquisitionModel]): List of image
            acquisitions to convert to OME-Zarr.
        converter_options (ConverterOptions): Advanced converter options.
        overwrite (OverwriteMode): Overwrite mode for existing data.
            - "No Overwrite": Do not overwrite existing data.
            - "Overwrite": Remove and replace existing data.
            - "Extend": Extend existing data without removing it.
            Default is "No Overwrite".

    Returns:
        dict: ``{"parallelization_list": [...]}`` for the compute task.
    """
    return run_convert_init(
        zarr_dir=zarr_dir,
        acquisitions=acquisitions,
        parse_function=parse_nd2_image_acquisition,
        converter_options=converter_options,
        overwrite=overwrite,
        collection_type="SingleImage",
    )


if __name__ == "__main__":
    from fractal_task_tools.task_wrapper import run_fractal_task

    run_fractal_task(
        task_function=convert_nd2_image_init_task,
        logger_name=logger.name,
    )
