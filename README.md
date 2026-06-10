# Fractal ND2 Converters

A collection of [Fractal](https://fractal-analytics-platform.github.io/) tasks to convert Nikon ND2 files to the [OME-Zarr](https://ngff.openmicroscopy.org/) format.

## Python API

In addition to running these as Fractal tasks, the converters can be used directly from Python:

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