# Extended Test Data Intake — Detailed Workflow

## Context

New extended test datasets exist but are not yet formatted to match the naming conventions used by the existing extended test suites. This document is the full, step-by-step workflow to process new raw Nikon ND2 acquisition folders into properly named, snapshotted extended test entries.

---

## Converter Reference Table

| Converter | Init Task | Compute Task | Dataset list in `test_nd2_extended.py` | Test function |
|---|---|---|---|---|
| ND2 plate | `nd2_plate/convert_nd2_plate_init_task` | `common/image_in_plate_compute_task` | `_PLATE_DATASETS` | `test_nd2_plate_extended` |
| ND2 single image | `nd2_image/convert_nd2_image_init_task` | `common/single_image_compute_task` | `_SINGLE_IMAGE_DATASETS` | `test_nd2_single_image_extended` |

Both converters live in `tests/test_nd2_extended.py`. The `data-extended` subfolder is always `Nikon-ND2/`.

---

## Naming Convention

### Plate datasets (HCS)

```
hcs_{W}w{P}p{C}c{Z}z{T}t_{Descriptor}
```

### Single-image datasets

```
img_{P}p{C}c{Z}z{T}t_{Descriptor}
```

where `{P}` is the total number of images/positions in the acquisition.

| Token | Meaning | Source in snapshot YAML |
|---|---|---|
| `{W}` | Number of wells (plate only) | `len(plates[plate].wells)` |
| `{P}` | Fields of view per well (plate) / total images (single) | `len(images[img].tables.FOV_ROI_table.rois)` — use `1` if table absent |
| `{C}` | Number of channels | `images[img].shape` at `axes.index('c')` |
| `{Z}` | Number of Z slices | `images[img].shape` at `axes.index('z')` |
| `{T}` | Number of time points | `images[img].shape` at `axes.index('t')`, or `1` if `t` not in axes |
| `{Descriptor}` | Human-readable variant | Inferred from acquisition characteristics (see below) |

**Descriptor guidance** — use PascalCase words separated by underscores to describe what makes the dataset distinctive. Examples:
- Projection type: `MIP`, `SUM`, `MIP_SUM`, `MIP_Slice`
- Tiling arrangement: `Centered`, `Grid`
- Split-file format: `SplitP`
- Acquisition mode: `dual`, `seq`
- Fov spacing variant: `nospacing`, `10overlap`, `1000spacing`
- Binning: `2bin`

---

## Step-by-Step Workflow

### Step 0 — Check if extended test infrastructure exists

The directory `tests/data-extended/Nikon-ND2/` is typically a symlink to an external data store. Verify it exists and is resolvable:

```bash
ls tests/data-extended/Nikon-ND2/
```

If the symlink is missing, create it pointing to the external data path following the pattern of existing symlinks in `tests/data-extended/`. The directory must contain `raw/`, `snapshots/`, and `output/` subdirectories.

The test file (`tests/test_nd2_extended.py`) already exists — no template is needed.

---

### Step 1 — Place the raw data with a temporary name

Copy or symlink the new acquisition folder into:

```
tests/data-extended/Nikon-ND2/raw/{tmp_name}/{acq_subfolder}/
```

- `{tmp_name}` is a temporary top-level wrapper (e.g., the original dataset name or a short description).
- `{acq_subfolder}` is the original acquisition folder name as-is (no renaming yet).

> **Zip-based datasets**: If the data is distributed as a zip file, place the zip directly in `tests/data-extended/Nikon-ND2/` and register it in `conftest.py`'s `LOCAL_ZIPS` dict:
> ```python
> LOCAL_ZIPS = {
>     ...
>     "{zip_filename}.zip": "{tmp_name}",
> }
> ```
> The conftest will auto-extract it into `raw/{tmp_name}/` on the next test run. Then proceed from Step 2 as normal.

---

### Step 2 — Add temp entry to dataset list and run converter with `--update-snapshots`

In `tests/test_nd2_extended.py`, add a 3-tuple to `_PLATE_DATASETS` (or `_SINGLE_IMAGE_DATASETS`):

```python
_PLATE_DATASETS = [
    ("{tmp_name}", "{acq_subfolder}", "{tmp_name}"),
]
```

The tuple is `(dataset, acq_folder, snapshot_name)` where `path = RAW_DIR / dataset / acq_folder`.

Then run:

```bash
pixi run -e test pytest tests/test_nd2_extended.py \
    -k "{tmp_name}" --extended --update-snapshots
```

This produces:
- `tests/data-extended/Nikon-ND2/snapshots/{tmp_name}.yaml` — the snapshot
- `tests/data-extended/Nikon-ND2/output/{tmp_name}/` — the zarr output (kept for inspection)

If the converter fails, debug the raw data format before continuing.

---

### Step 3 — Parse the snapshot to derive `{W}`, `{P}`, `{C}`, `{Z}`, `{T}`

Open `tests/data-extended/Nikon-ND2/snapshots/{tmp_name}.yaml` and read:

```yaml
plates:
  {plate_name}.zarr:
    wells:              # → W = len(this list)
      - ...
    images:
      Row/Col/0:
        axes: [c, z, y, x]     # or [t, c, z, y, x]
        shape: [C, Z, Y, X]    # or [T, C, Z, Y, X]
        tables:
          FOV_ROI_table:
            rois:              # → P = len(rois); absent → P = 1
              FOV_1: ...
              FOV_2: ...
```

- **W**: `len(plates[plate].wells)` — use the first plate.
- **P**: `len(plates[plate].images[img].tables.FOV_ROI_table.rois)` for any image. If `FOV_ROI_table` is absent → `P = 1`.
- **C**: `shape[axes.index('c')]`
- **Z**: `shape[axes.index('z')]` — for projection-only datasets this will be `1`
- **T**: `shape[axes.index('t')]` if `'t'` in axes, else `1`

For single-image snapshots, read the same fields from the top-level `images:` section (no `plates:` wrapper); `{P}` is the total count of image entries.

Construct the canonical name: `hcs_{W}w{P}p{C}c{Z}z{T}t_{Descriptor}` or `img_{P}p{C}c{Z}z{T}t_{Descriptor}`.

---

### Step 4 — Rename and flatten the raw directory

- Rename `tests/data-extended/Nikon-ND2/raw/{tmp_name}/` → `tests/data-extended/Nikon-ND2/raw/{canonical_name}/`
- If the acquisition subfolder has unnecessary nesting (e.g., a single intermediate directory containing all the actual files), move the contents up one level so acquisition files live directly inside `raw/{canonical_name}/{acq_subfolder}/`.

---

### Step 5 — Update the instrument-level `README.md`

There is a single `README.md` at `tests/data-extended/Nikon-ND2/README.md`. Add a row for the new dataset:

```markdown
| {canonical_name} | HCS | {W} | {P} | {C} | {Z} | {T} | {One-sentence description} |
```

If the `README.md` does not yet exist, create it:

```markdown
# Nikon-ND2 Testing Dataset

{One paragraph describing the ND2 format and acquisition setup.}

## Details

- *Authors*: ...
- *Acquisition Date*: ...
- *Acquisition Location*: ...
- *Modality*: Fluorescence microscopy.
- *Microscope*: Nikon ...
- *Pixel size*: ...

## Overview

| Dataset Name | Type | Wells | FoV | Channels | Z-Stacks | Time Points | Extra Info |
|---|---|---|---|---|---|---|---|
| {canonical_name} | HCS | {W} | {P} | {C} | {Z} | {T} | {description} |

## Dataset Structure

- *./raw*: Contains the original microscopy data in ND2 format.
- *./snapshots*: Contains snapshot `.yaml` files used for automated testing.
```

---

### Step 6 — Update dataset list and re-generate the snapshot with canonical name

In `tests/test_nd2_extended.py`:
- Replace `"{tmp_name}"` with `"{canonical_name}"` in `_PLATE_DATASETS` or `_SINGLE_IMAGE_DATASETS`
- Delete the old snapshot: `tests/data-extended/Nikon-ND2/snapshots/{tmp_name}.yaml`
- Delete the old output dir: `tests/data-extended/Nikon-ND2/output/{tmp_name}/`

The updated tuple:
```python
("{canonical_name}", "{acq_subfolder}", "{canonical_name}"),
```

Re-run with the canonical name:

```bash
pixi run -e test pytest tests/test_nd2_extended.py \
    -k "{canonical_name}" --extended --update-snapshots
```

Verify the new snapshot:
- Plate/image name(s) reflect the canonical dataset name
- Well IDs are correct
- `axes`, `shape`, `pixelsize`, `channel_labels` look sensible

---

### Step 7 — Validation run (no `--update-snapshots`)

```bash
pixi run -e test pytest tests/test_nd2_extended.py --extended
```

All tests — including the new one — must pass.

---

## Edge Cases

**Multiple plates per dataset** (e.g., MIP + Slice):
The snapshot YAML will have multiple entries under `plates:`. W, P, C, T are read from any one plate (they match). Z may differ between plates (projections = 1, slices = N) — use the slice count for `{Z}`, or `1` if only projections exist.

**No `FOV_ROI_table`** (single-FOV wells):
`P = 1`. The `well_ROI_table` with an `image` ROI will be the only table.

**Dataset with variant kwargs** (e.g., extra acquisition options):
Keep the same raw path; use a different `snapshot_name` with a variant suffix (e.g., `{canonical_name}_seq`). Add a second tuple manually to the dataset list rather than relying on the shared list comprehension.
