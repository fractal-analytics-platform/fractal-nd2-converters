"""A collection of fractal tasks to convert Nikon ND2 files to OME-Zarr"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fractal-nd2-converters")
except PackageNotFoundError:
    __version__ = "uninstalled"

from fractal_nd2_converters.nd2_image import (
    ND2ImageAcquisitionModel,
    convert_nd2_single_image,
)
from fractal_nd2_converters.nd2_plate import (
    ND2PlateAcquisitionModel,
    convert_nd2_plate,
)

__all__ = [
    "ND2ImageAcquisitionModel",
    "ND2PlateAcquisitionModel",
    "convert_nd2_plate",
    "convert_nd2_single_image",
]
