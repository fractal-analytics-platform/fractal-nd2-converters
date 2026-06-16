"""Initialize the Nikon ND2 plate to OME-Zarr conversion task."""

import logging

import polars
from ome_zarr_converters_tools import (
    AcquisitionOptions,
    ConverterOptions,
    OverwriteMode,
)
from pydantic import Field, validate_call

from fractal_nd2_converters.common import BaseAcquisitionModel, run_convert_init
from fractal_nd2_converters.nd2_plate._parser import parse_nd2_plate_acquisition

logger = logging.getLogger("convert_nd2_plate_task")


default_converter_options = ConverterOptions()


class ND2PlateAcquisitionModel(BaseAcquisitionModel):
    """Model for Nikon ND2 plate acquisitions.

    Accepts a folder of .nd2 files where each file corresponds to a well
    (e.g. WellB02_..., WellC03_...).
    """

    path: str
    """
    Path to a folder containing nd2 files for each well. Each file must have
    well information in its filename (e.g. WellB02_..., WellC03_...).
    """
    plate_name: str | None = None
    """
    Optional custom name for the plate. If not provided, the name will be the
    acquisition directory name.
    """
    acquisition_id: int = Field(default=0, ge=0)
    """
    Acquisition ID, used to identify the acquisition in case of multiple acquisitions.
    """
    advanced: AcquisitionOptions = Field(default_factory=AcquisitionOptions)
    """
    Advanced acquisition options.
    """

    @property
    def normalized_plate_name(self) -> str:
        """Get the normalized plate name."""
        if self.plate_name is not None:
            return self.plate_name
        return self._sanitized_name

    def get_condition_table(self) -> polars.DataFrame | None:
        """Get the path to the condition table if it exists."""
        if self.advanced.condition_table_path is not None:
            try:
                return polars.read_csv(self.advanced.condition_table_path)
            except Exception as e:
                raise ValueError(
                    "Failed to read condition table at "
                    f"{self.advanced.condition_table_path}: {e}"
                ) from e
        return None


@validate_call
def convert_nd2_plate_init_task(
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

    Returns:
        dict: ``{"parallelization_list": [...]}`` for the compute task.
    """
    return run_convert_init(
        zarr_dir=zarr_dir,
        acquisitions=acquisitions,
        parse_function=parse_nd2_plate_acquisition,
        converter_options=converter_options,
        overwrite=overwrite,
        collection_type="ImageInPlate",
    )


if __name__ == "__main__":
    from fractal_task_tools.task_wrapper import run_fractal_task

    run_fractal_task(task_function=convert_nd2_plate_init_task, logger_name=logger.name)
