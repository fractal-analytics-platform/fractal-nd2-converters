# Changelog

## [v0.1.0]

### Features
- Add Python API functions (`convert_nd2_plate`, `convert_nd2_single_image`) for programmatic
  use outside Fractal.
- Update tests to call the high-level API functions end-to-end.

### Docs
- Add "Python API" section to README with usage examples.

### Fix
- Fix typos in the plate task docs (`within`) and the conversion log message (`Successfully`);
  regenerate `__FRACTAL_MANIFEST__.json`.

### Chores
- Remove `_setup_single_image.py` and its import: `ome-zarr-converters-tools>=0.10.0` now ships
  a built-in `setup_singleimage` handler for `SingleImage` collections, making the local copy
  redundant.
- Bump to `ome-zarr-converters-tools>=0.10.4,<0.11.0`.
- Migrate to the centralized snapshot-testing harness from
  `ome_zarr_converters_tools.testing`: drop the local `tests/utils.py` snapshot engine in favour
  of the shared `run_converter_test`, load the shared pytest plugin via `pytest_plugins` in
  `conftest.py`, and store snapshots as JSON instead of YAML. Drop the now-unused `devtools` and
  `pyyaml` test dependencies.
- Rename `nd2_utils.py` to `_nd2_utils.py` to signal private implementation.
- Align repository tooling with `ome-zarr-converters-tools`: adopt its `.pre-commit-config.yaml`
  (`validate-pyproject` v0.25, `crate-ci/typos`, `astral-sh/ruff-pre-commit` v0.15.17,
  `nbstripout`) with a per-repo `_typos.toml`, add a `chores` pixi task, bump GitHub Actions pins
  (`checkout` v7, `codecov-action` v7, `action-gh-release` v3, `setup-python` v6), and add a terse
  `CLAUDE.md`.
