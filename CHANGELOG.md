# Changelog

## [Unreleased]

### Features
- Add Python API functions (`convert_nd2_plate`, `convert_nd2_single_image`) for programmatic
  use outside Fractal.
- Update tests to call the high-level API functions end-to-end.

### Docs
- Add "Python API" section to README with usage examples.

### Chores
- Remove `_setup_single_image.py` and its import: `ome-zarr-converters-tools>=0.10.0` now ships
  a built-in `setup_singleimage` handler for `SingleImage` collections, making the local copy
  redundant.
- Bump to `ome-zarr-converters-tools>=0.10.0,<0.11.0`.
- Rename `nd2_utils.py` to `_nd2_utils.py` to signal private implementation.
