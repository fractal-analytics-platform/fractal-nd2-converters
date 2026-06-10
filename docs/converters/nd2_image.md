# ND2 Image

Converts a Nikon `.nd2` file, or a folder of `.nd2` files, into one or more standalone OME-Zarr images (not a plate structure).

## Expected File Structure

| Input | Output |
|---|---|
| A single `.nd2` file | One OME-Zarr image |
| A folder of `.nd2` files | One OME-Zarr image per file |

```
Acquisition.nd2 → OME-Zarr image
```

or

```
{folder}/
├── {filename1}.nd2 → OME-Zarr image 1
├── {filename2}.nd2 → OME-Zarr image 2
└── ...
```

If a `.nd2` file contains multiple stage positions (the ND2 `P` dimension), each position becomes a positioned **field of view** inside that image. The fields of view are placed according to their stage positions and assembled into a single image by `ome-zarr-converters-tools` (see [Tiling Mode](index.md#tiling-mode)).

!!! note
    For plate acquisitions where filenames contain `Well` (e.g. `WellA01{filename}.nd2`), use the [ND2 Plate](nd2_plate.md) task instead. If positions were split into separate files (e.g. via the "Split Multipoints" option), each file is converted into its own OME-Zarr image.

## Metadata

The converter extracts the following from the ND2 file:

- Stage positions (X, Y) for each field of view
- Channel names, emission wavelengths, and colors
- Pixel size (XY and Z spacing in micrometers)
- Time spacing (for time-series acquisitions)
- Image shape (X, Y, Z, C, T)

## Task Parameters

| Field | Type | Default | Description |
|---|---|---|---|
| `Path` | `str` | *required* | Path to a `.nd2` file, or a folder containing `.nd2` files. |
| `Zarr Name` | `str` or `null` | `null` | Custom name for the output OME-Zarr image(s). Defaults to the file or folder name. For folders, the sanitized file stem is appended to form each image's name. |
| `Advanced` | `AcquisitionOptions` | `{}` | Advanced options: channel/pixel-size overrides, stage corrections, and filters. See [Converters Overview](index.md). |

!!! warning "Limitations"
    - This task has been tested on a limited set of acquisitions (see [this Zenodo record](https://zenodo.org/records/15411420)). It may not work on all Nikon `.nd2` acquisitions.
    - For files with multiple stage positions (the `P` dimension), the file metadata must contain an `XYPosLoop` entry, otherwise conversion fails.

## Python API

The converter is also available as a regular Python function, for use outside Fractal:

```python
from fractal_nd2_converters import ND2ImageAcquisitionModel, convert_nd2_single_image

convert_nd2_single_image(
    zarr_dir="/path/to/zarr_dir",
    acquisitions=[
        ND2ImageAcquisitionModel(path="/path/to/Acquisition.nd2"),
    ],
)
```

See [How to Run the Converters](../how_to_run_the_converters.md) for the full
list of parameters and more examples.
