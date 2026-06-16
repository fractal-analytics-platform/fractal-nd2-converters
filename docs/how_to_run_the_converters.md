# How to Run the Converters

In addition to running them as Fractal tasks, the converters in this package
are available as plain Python functions, so you can run them from a script or
notebook without a Fractal server.

## Installation

```bash
pip install fractal-nd2-converters
```

## Importing the Converters

```python
from fractal_nd2_converters import (
    ND2ImageAcquisitionModel,
    ND2PlateAcquisitionModel,
    convert_nd2_single_image,
    convert_nd2_plate,
)
```

- `convert_nd2_single_image` — converts a `.nd2` file, or a folder of `.nd2` files, into one or more standalone OME-Zarr images. See [ND2 Image](converters/nd2_image.md).
- `convert_nd2_plate` — converts a folder of `.nd2` files into an OME-Zarr HCS plate. See [ND2 Plate](converters/nd2_plate.md).

## Common Parameters

Both functions share the same signature shape:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `zarr_dir` | `str` | *required* | Directory where the output OME-Zarr will be created. |
| `acquisitions` | `list[ND2ImageAcquisitionModel \| ND2PlateAcquisitionModel]` | *required* | List of acquisitions to convert. See [Converters Overview](converters/index.md#acquisition-parameters). |
| `converter_options` | `ConverterOptions \| None` | `None` | Advanced converter options (tiling, writer mode, OME-Zarr settings). `None` uses the defaults. See [Converters Overview](converters/index.md#converter-options). |
| `overwrite` | `OverwriteMode` | `OverwriteMode.NO_OVERWRITE` | What to do if the output already exists: `NO_OVERWRITE`, `OVERWRITE`, or `EXTEND`. |
| `runner` | `RunnerType \| None` | `None` | Execution strategy for the per-image/per-well compute step. `None` runs sequentially. |

Both functions return a list of image-list update dicts describing the
converted Zarr images, one per converted image (ND2 Image) or well (ND2
Plate).

### Runners

By default, the compute step runs sequentially. To parallelize it, pass a
runner from `ome_zarr_converters_tools`:

```python
from ome_zarr_converters_tools import ThreadedRunner, MultiprocessingRunner

# Run the compute step in 4 threads
convert_nd2_single_image(..., runner=ThreadedRunner(num_threads=4))

# Run the compute step in 4 processes
convert_nd2_plate(..., runner=MultiprocessingRunner(num_processes=4))
```

## Example: Convert an ND2 File to a Single OME-Zarr Image

```python
from fractal_nd2_converters import ND2ImageAcquisitionModel, convert_nd2_single_image

convert_nd2_single_image(
    zarr_dir="/path/to/zarr_dir",
    acquisitions=[
        ND2ImageAcquisitionModel(path="/path/to/Acquisition.nd2"),
    ],
)
```

## Example: Convert a Folder of ND2 Files to OME-Zarr Images

```python
from fractal_nd2_converters import ND2ImageAcquisitionModel, convert_nd2_single_image

convert_nd2_single_image(
    zarr_dir="/path/to/zarr_dir",
    acquisitions=[
        ND2ImageAcquisitionModel(path="/path/to/folder_of_nd2_files"),
    ],
)
```

## Example: Convert an ND2 Plate Acquisition to an OME-Zarr HCS Plate

```python
from fractal_nd2_converters import ND2PlateAcquisitionModel, convert_nd2_plate

convert_nd2_plate(
    zarr_dir="/path/to/zarr_dir",
    acquisitions=[
        ND2PlateAcquisitionModel(path="/path/to/plate_folder"),
    ],
)
```

## Example: Merge Multiple Acquisitions Into One Plate

To merge several plate acquisitions into a single OME-Zarr plate (e.g. 4i /
multiplexed rounds), pass multiple acquisition objects with the same
`plate_name` and distinct `acquisition_id` values:

```python
from fractal_nd2_converters import ND2PlateAcquisitionModel, convert_nd2_plate

convert_nd2_plate(
    zarr_dir="/path/to/zarr_dir",
    acquisitions=[
        ND2PlateAcquisitionModel(
            path="/path/to/round1_folder",
            plate_name="merged_plate",
            acquisition_id=0,
        ),
        ND2PlateAcquisitionModel(
            path="/path/to/round2_folder",
            plate_name="merged_plate",
            acquisition_id=1,
        ),
    ],
)
```
