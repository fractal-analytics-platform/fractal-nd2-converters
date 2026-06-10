# ND2 Plate

Converts a folder of Nikon `.nd2` files belonging to a multi-well plate acquisition into an OME-Zarr HCS plate.

## Expected File Structure

Each `.nd2` file in the folder must contain `Well` followed by a well name (e.g. `A1`, `A01`) in its filename:

```
{folder}/
├── {prefix1}WellA01{suffix1}.nd2   → well A1
├── {prefix2}WellC02{suffix2}.nd2   → well C2
└── ...
```

This is the layout produced by the standard plate-acquisition JOBS script at the ZMB Nikon Spinning Disk. The converter:

1. Resolves the row/column of each file from its filename.
2. Groups files by well.
3. Turns every file into one or more **fields of view** inside its well's image.

If multiple files belong to the same well, each file becomes a separate field of view (`FOV_0`, `FOV_1`, ...) within that well's image.

!!! info "Skipped files"
    `.nd2` files in the folder that do not contain a `Well` pattern are skipped and logged, so a mixed folder still converts cleanly.

## Combining Multiple Acquisitions

To merge several acquisition folders into one plate (e.g. 4i / multiplexed rounds), pass multiple acquisition objects with the **same `Plate Name`** but **distinct `Acquisition Id`** values. Each folder is added to the plate as a separate acquisition round.

## Metadata

The converter extracts the following from each ND2 file:

- Well position (row and column) from the filename
- Field-of-view stage positions (X, Y)
- Channel names, emission wavelengths, and colors
- Pixel size (XY and Z spacing in micrometers)
- Time spacing (for time-series acquisitions)

## Task Parameters

| Field | Type | Default | Description |
|---|---|---|---|
| `Path` | `str` | *required* | Path to a folder containing `.nd2` files, one or more per well. |
| `Plate Name` | `str` or `null` | `null` | Custom name for the output OME-Zarr plate. Defaults to the acquisition folder name. Use the same value across acquisitions to merge them into one plate. |
| `Acquisition Id` | `int` | `0` | Acquisition identifier for combining multiple acquisitions into a single plate. |
| `Advanced` | `AcquisitionOptions` | `{}` | Advanced options: condition table, channel/pixel-size overrides, stage corrections, and filters. See [Converters Overview](index.md). |

!!! warning "Limitations"
    - This task has been tested on a limited set of acquisitions (see [this Zenodo record](https://zenodo.org/records/15411420)). It may not work on all Nikon `.nd2` acquisitions.
    - Filenames must contain `Well` followed by the well name (e.g. `WellA01`, `WellC02`); files that don't match this pattern are skipped.

## Python API

The converter is also available as a regular Python function, for use outside Fractal:

```python
from fractal_nd2_converters import ND2PlateAcquisitionModel, convert_nd2_plate

convert_nd2_plate(
    zarr_dir="/path/to/zarr_dir",
    acquisitions=[
        ND2PlateAcquisitionModel(path="/path/to/plate_folder"),
    ],
)
```

See [How to Run the Converters](../how_to_run_the_converters.md) for the full
list of parameters and more examples, including how to merge multiple
acquisitions into a single plate.
