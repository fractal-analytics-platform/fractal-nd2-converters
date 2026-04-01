"""A collection of fractal tasks to convert Nikon ND2 files to OME-Zarr"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fractal-nd2-converters")
except PackageNotFoundError:
    __version__ = "uninstalled"
