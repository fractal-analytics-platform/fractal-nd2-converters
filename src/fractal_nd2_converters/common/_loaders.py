"""Image loader for nd2 files."""

from typing import Any

import nd2
import numpy as np
from ome_zarr_converters_tools.models._loader import ImageLoaderInterface


class nd2Loader(ImageLoaderInterface):
    """Custom loader for nd2 files."""

    file_path: str
    p: int | None  # tile-position index (None for single-position files)

    def load_data(self, resource: Any = None) -> np.ndarray:
        """Load the tile data as a numpy array."""
        if resource is not None:
            path = f"{resource}/{self.file_path}"
        else:
            path = self.file_path

        tile_data = nd2.imread(path, xarray=True, dask=True)

        if "P" in tile_data.dims:
            tile_data = tile_data.isel(P=self.p)
        if not set(tile_data.dims).issubset(("T", "C", "Z", "Y", "X")):
            raise ValueError(
                f"Data can only have dimensions T, C, Z, Y, X. Found: {tile_data.dims}"
            )
        if "Z" not in tile_data.dims:
            tile_data = tile_data.expand_dims(Z=1, axis=0)
        if "C" not in tile_data.dims:
            tile_data = tile_data.expand_dims(C=1, axis=0)
        if "T" not in tile_data.dims:
            tile_data = tile_data.expand_dims(T=1, axis=0)
        if tile_data.dims != ("T", "C", "Z", "Y", "X"):
            tile_data = tile_data.transpose("T", "C", "Z", "Y", "X")

        arr = tile_data.data.compute()
        # Squeeze T=1 to align with default_axes_builder(is_time_series=False)
        if arr.shape[0] == 1:
            arr = arr[0]
        return arr

    def find_data_type(self, resource: Any = None) -> str:
        """Return the dtype without loading the full array."""
        path = f"{resource}/{self.file_path}" if resource else self.file_path
        with nd2.ND2File(path) as f:
            return str(f.dtype)
