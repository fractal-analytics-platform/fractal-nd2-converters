# Fractal ND2 Converters

[![CI (build and test)](https://github.com/fractal-analytics-platform/fractal-nd2-converters/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/fractal-analytics-platform/fractal-nd2-converters/actions/workflows/build_and_test.yml)
[![codecov](https://codecov.io/gh/fractal-analytics-platform/fractal-nd2-converters/graph/badge.svg)](https://codecov.io/gh/fractal-analytics-platform/fractal-nd2-converters)

A collection of [Fractal](https://fractal-analytics-platform.github.io/) tasks to convert Nikon ND2 files to the [OME-Zarr](https://ngff.openmicroscopy.org/) format.

## Tasks

| Task | Use case |
|---|---|
| `Convert Nikon ND2 Image to OME-Zarr` | Convert a single `.nd2` file, or a folder of `.nd2` files, into one or more standalone OME-Zarr images. |
| `Convert Nikon ND2 Plate to OME-Zarr` | Convert a folder of `.nd2` files belonging to a multi-well plate acquisition into an OME-Zarr HCS plate. |

Each task is a Fractal **compound task**: an init step parses the `.nd2`
metadata and builds the parallelization list, and a compute step writes the
image data well-by-well (or image-by-image).

## Installation

```bash
pip install fractal-nd2-converters
```

## Documentation

Full documentation — including the supported file layouts, all converter
parameters, and the condition-table format — is available at
<https://fractal-analytics-platform.github.io/fractal-nd2-converters/>.

## Python API

In addition to running these as Fractal tasks, the converters can be used directly from Python. See [How to Run the Converters](https://fractal-analytics-platform.github.io/fractal-nd2-converters/how_to_run_the_converters/) for the full reference.

```python
from fractal_nd2_converters import convert_nd2_plate, ND2PlateAcquisitionModel

images = convert_nd2_plate(
    zarr_dir="/path/to/output",
    acquisitions=[
        ND2PlateAcquisitionModel(path="/path/to/raw", acquisition_id=0)
    ],
)
```

```python
from fractal_nd2_converters import convert_nd2_single_image, ND2ImageAcquisitionModel

images = convert_nd2_single_image(
    zarr_dir="/path/to/output",
    acquisitions=[
        ND2ImageAcquisitionModel(path="/path/to/file.nd2", image_name="my_image")
    ],
)
```

`converter_options` (`ConverterOptions`), `overwrite` (`OverwriteMode`), and `runner`
(`RunnerType`) from `ome_zarr_converters_tools` can be used to customize conversion.