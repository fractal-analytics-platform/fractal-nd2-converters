# Fractal ND2 Converters

[![CI (build and test)](https://github.com/fractal-analytics-platform/fractal-nd2-converters/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/fractal-analytics-platform/fractal-nd2-converters/actions/workflows/build_and_test.yml)
[![codecov](https://codecov.io/gh/fractal-analytics-platform/fractal-nd2-converters/graph/badge.svg)](https://codecov.io/gh/fractal-analytics-platform/fractal-nd2-converters)

A collection of [Fractal](https://fractal-analytics-platform.github.io/) tasks to convert Nikon `.nd2` files into the [OME-Zarr](https://ngff.openmicroscopy.org/) format.

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

## Part of the OME-Zarr converters ecosystem

This converter is a thin, format-specific layer built on
[`ome-zarr-converters-tools`](https://github.com/BioVisionCenter/ome-zarr-converters-tools),
the shared engine that handles tiling, image registration, and OME-Zarr writing for
the whole Fractal converter family. Because they all share that engine, every
converter offers the same options, behavior, and development workflow.

Sibling converters built on the same tooling:

- [`fractal-czi-converters`](https://github.com/fractal-analytics-platform/fractal-czi-converters) — Zeiss `.czi`
- [`fractal-lif-converters`](https://github.com/fractal-analytics-platform/fractal-lif-converters) — Leica `.lif`
- [`fractal-uzh-converters`](https://github.com/fractal-analytics-platform/fractal-uzh-converters) — HCS plates (Operetta, ScanR, CQ3K, CellVoyager, ImageXpress, custom TIFF)

## Documentation

Full documentation — including the supported file layouts, all converter
parameters, and the condition-table format — is available at
<https://fractal-analytics-platform.github.io/fractal-nd2-converters/>.
