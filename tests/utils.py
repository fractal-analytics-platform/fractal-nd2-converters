"""Test utilities for fractal-nd2-converters."""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
import yaml
from ngio import OmeZarrContainer, open_ome_zarr_container, open_ome_zarr_plate
from ome_zarr_converters_tools import (
    ImageInPlate,
    SingleImage,
    generic_compute_task,
)
from ome_zarr_converters_tools.fractal._models import ConvertParallelInitArgs
from pydantic import BaseModel, Field, model_validator

from fractal_nd2_converters.nd2_utils import nd2Loader

DATA_DIR = Path(__file__).parent / "data"


class FingerprintModel(BaseModel):
    mean: float
    std: float
    min: float
    max: float
    hash: str

    @classmethod
    def from_array(cls, arr: np.ndarray, decimals=6):
        return cls(
            mean=float(np.mean(arr)),
            std=float(np.std(arr)),
            min=float(np.min(arr)),
            max=float(np.max(arr)),
            hash=hashlib.sha256(
                np.round(arr, decimals).tobytes()
            ).hexdigest(),
        )


class RoiAssertionModel(BaseModel):
    slice_repr: str
    finger_print: FingerprintModel
    xy_origin: list[float] | None = None


class TableAssertionModel(BaseModel):
    rois: dict[str, RoiAssertionModel] = Field(default_factory=dict)


class ImageAssertionModel(BaseModel):
    axes: list[str]
    shape: list[int]
    pixelsize: list[float]
    channel_labels: list[str] = Field(default_factory=list)
    wavelength_ids: list[str | None] = Field(default_factory=list)
    types: dict[str, bool] = Field(default_factory=dict)
    attributes: dict[str, str | int | float] = Field(default_factory=dict)
    tables: dict[str, TableAssertionModel | None] = Field(
        default_factory=dict
    )


def deep_merge(a, b):
    result = a.copy()
    for key, value in b.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class PlateAssertionModel(BaseModel):
    wells: list[str]
    images: dict[str, ImageAssertionModel]

    @model_validator(mode="before")
    def validate_images(cls, values):
        common_assertions = values.pop("images_common", {})
        if common_assertions:
            values["images"] = {
                path: deep_merge(common_assertions, img)
                for path, img in values.get("images", {}).items()
            }
        return values


class MultiPlateAssertionModel(BaseModel):
    plates: dict[str, PlateAssertionModel]

    @property
    def expected_parallelization_list_length(self) -> int:
        return sum(len(plate.images) for plate in self.plates.values())

    def aggregated_types(self) -> dict[str, bool]:
        result = {}
        for plate_path, plate in self.plates.items():
            for image_path, img in plate.images.items():
                key = f"{plate_path}/{image_path}" if image_path else plate_path
                result[key] = img.types
        return result

    def aggregated_attributes(
        self,
    ) -> dict[str, dict[str, str | int | float]]:
        result = {}
        for plate_path, plate in self.plates.items():
            for image_path, img in plate.images.items():
                key = f"{plate_path}/{image_path}" if image_path else plate_path
                result[key] = img.attributes
        return result


def _load_snapshot(yaml_path: Path) -> MultiPlateAssertionModel:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return MultiPlateAssertionModel(**data)


def _is_plate_zarr(zarr_path: Path) -> bool:
    """Check if a .zarr path is an HCS plate."""
    zattrs = zarr_path / ".zattrs"
    if zattrs.exists():
        with open(zattrs) as f:
            return "plate" in json.load(f)
    return False


def _get_zarr_images(
    zarr_path: Path,
) -> tuple[list[str], dict[str, OmeZarrContainer]]:
    """Get wells and images from a zarr path (plate or single image)."""
    if _is_plate_zarr(zarr_path):
        plate = open_ome_zarr_plate(zarr_path)
        wells = list(plate.get_wells().keys())
        images = dict(plate.get_images().items())
    else:
        wells = []
        images = {"": open_ome_zarr_container(zarr_path)}
    return wells, images


def _plate_after_init_checks(
    *,
    init_output: dict,
    multi_plate_assertions: MultiPlateAssertionModel,
    zarr_dir: Path,
):
    parallelization_list = len(init_output["parallelization_list"])
    expected = multi_plate_assertions.expected_parallelization_list_length
    assert parallelization_list == expected
    for plate_name, plate_assert in multi_plate_assertions.plates.items():
        plate_path = zarr_dir / plate_name
        if plate_assert.wells:
            plate = open_ome_zarr_plate(plate_path)
            wells = plate.get_wells().keys()
            assert set(wells) == set(plate_assert.wells)


def _image_list_updates_checks(
    *,
    image_list_updates: list[dict],
    multi_plate_assertions: MultiPlateAssertionModel,
    zarr_dir: Path,
):
    aggregated_types = multi_plate_assertions.aggregated_types()
    aggregated_attrs = multi_plate_assertions.aggregated_attributes()
    for updates in image_list_updates:
        assert "image_list_updates" in updates
        assert len(updates["image_list_updates"]) == 1
        upd = updates["image_list_updates"][0]
        zarr_url = Path(upd["zarr_url"])
        assert zarr_url.exists()
        image_path = zarr_url.relative_to(zarr_dir).as_posix()
        assert image_path in aggregated_types
        assert upd["types"] == aggregated_types[image_path]
        assert upd["attributes"] == aggregated_attrs[image_path], (
            f"{upd['attributes']} != {aggregated_attrs[image_path]}"
        )


def _check_roi_tables(
    ome_zarr_image: OmeZarrContainer,
    image_assertions: ImageAssertionModel,
):
    assert set(ome_zarr_image.list_tables()) == set(
        image_assertions.tables.keys()
    ), set(ome_zarr_image.list_tables())
    image = ome_zarr_image.get_image()
    for table_name, table_assert in image_assertions.tables.items():
        if table_assert is None:
            continue
        roi_table = ome_zarr_image.get_roi_table(table_name)
        for roi_name, roi_assert in table_assert.rois.items():
            for roi in roi_table.rois():
                if roi.name == roi_name:
                    break
            else:
                raise AssertionError(
                    f"ROI {roi_name} not found in table {table_name}"
                )
            roi_pixel = roi.to_pixel(pixel_size=image.pixel_size)
            slices_repr = str(roi_pixel.slices)
            assert slices_repr == str(roi_assert.slice_repr), slices_repr
            roi_array = image.get_roi_as_numpy(roi)
            fingerprint = FingerprintModel.from_array(roi_array)
            assert fingerprint == roi_assert.finger_print, fingerprint
            if roi_assert.xy_origin is not None:
                y_origin = getattr(roi, "y_micrometer_original", None)
                x_origin = getattr(roi, "x_micrometer_original", None)
                assert [y_origin, x_origin] == roi_assert.xy_origin


def _post_compute_checks(
    *,
    multi_plate_assertions: MultiPlateAssertionModel,
    zarr_dir: Path,
):
    for plate_name, plate_assert in multi_plate_assertions.plates.items():
        plate_path = zarr_dir / plate_name
        _wells, images = _get_zarr_images(plate_path)
        for image_path, ome_zarr_image in images.items():
            assert image_path in plate_assert.images
            img_assert = plate_assert.images[image_path]
            image = ome_zarr_image.get_image()
            assert list(image.axes) == img_assert.axes
            assert list(image.shape) == img_assert.shape
            assert np.allclose(
                list(image.pixel_size.tzyx), img_assert.pixelsize
            )
            if img_assert.channel_labels:
                assert ome_zarr_image.channel_labels == list(
                    img_assert.channel_labels
                )
            if img_assert.wavelength_ids:
                assert ome_zarr_image.wavelength_ids == list(
                    img_assert.wavelength_ids
                )
            _check_roi_tables(
                ome_zarr_image=ome_zarr_image,
                image_assertions=img_assert,
            )


def _generate_snapshot(
    *,
    zarr_dir: Path,
    image_list_updates: list[dict],
    snapshot_path: Path,
) -> None:
    """Generate multi_plate_assertions dict from converted plates."""
    plate_names = sorted(
        p.name for p in zarr_dir.iterdir() if p.suffix == ".zarr"
    )

    updates_by_image: dict[str, dict] = {}
    for updates in image_list_updates:
        for upd in updates.get("image_list_updates", []):
            zarr_url = Path(upd["zarr_url"])
            rel = zarr_url.relative_to(zarr_dir).as_posix()
            updates_by_image[rel] = upd

    all_plates = {}
    for plate_name in plate_names:
        plate_path = zarr_dir / plate_name
        wells, images = _get_zarr_images(plate_path)
        images_dict = {}

        for img_path, ome_zarr_image in images.items():
            image = ome_zarr_image.get_image()
            entry: dict = {
                "axes": list(image.axes),
                "shape": list(image.shape),
                "pixelsize": list(image.pixel_size.tzyx),
                "channel_labels": list(ome_zarr_image.channel_labels),
                "wavelength_ids": list(ome_zarr_image.wavelength_ids),
            }

            full_path = f"{plate_name}/{img_path}" if img_path else plate_name
            if full_path in updates_by_image:
                upd = updates_by_image[full_path]
                if "types" in upd:
                    entry["types"] = upd["types"]
                if "attributes" in upd:
                    entry["attributes"] = upd["attributes"]

            table_names = ome_zarr_image.list_tables()
            if table_names:
                tables_dict = {}
                for table_name in table_names:
                    try:
                        roi_table = ome_zarr_image.get_roi_table(table_name)
                    except Exception:
                        tables_dict[table_name] = None
                        continue
                    rois_dict = {}
                    for roi in roi_table.rois():
                        roi_pixel = roi.to_pixel(pixel_size=image.pixel_size)
                        roi_array = image.get_roi_as_numpy(roi)
                        fp = FingerprintModel.from_array(roi_array)
                        y_origin = getattr(
                            roi, "y_micrometer_original", None
                        )
                        x_origin = getattr(
                            roi, "x_micrometer_original", None
                        )
                        if y_origin is not None and x_origin is not None:
                            yx_origin = [y_origin, x_origin]
                        else:
                            yx_origin = None
                        rois_dict[roi.name] = {
                            "slice_repr": str(roi_pixel.slices),
                            "finger_print": fp.model_dump(),
                            "xy_origin": yx_origin,
                        }
                    tables_dict[table_name] = {"rois": rois_dict}
                entry["tables"] = tables_dict

            images_dict[img_path] = entry

        all_plates[plate_name] = {
            "wells": wells,
            "images": images_dict,
        }

    snapshot_data = {"plates": all_plates}
    MultiPlateAssertionModel(**snapshot_data)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with open(snapshot_path, "w") as f:
        yaml.safe_dump(
            snapshot_data,
            f,
            default_flow_style=False,
            sort_keys=False,
        )


def _infer_collection_type(zarr_dir: Path):
    """Infer collection type from zarr output after init."""
    for p in zarr_dir.iterdir():
        if p.suffix == ".zarr" and _is_plate_zarr(p):
            return ImageInPlate
    return SingleImage


def _run_compute_tasks(output, collection_type):
    """Run compute tasks and return updates list."""
    updates_list = []
    for p in output["parallelization_list"]:
        init_args = p["init_args"]
        if isinstance(init_args, dict):
            init_args = ConvertParallelInitArgs(**init_args)
        update = generic_compute_task(
            zarr_url=p["zarr_url"],
            init_args=init_args,
            collection_type=collection_type,
            image_loader_type=nd2Loader,
        )
        updates_list.append(update)
    return updates_list


def run_converter_test(
    *,
    tmp_path: Path,
    init_task_fn: Callable,
    init_task_kwargs: dict,
    snapshot_path: Path,
    update_snapshots: bool,
):
    """Run a converter end-to-end and check against snapshot assertions.

    Args:
        tmp_path: Pytest tmp_path for zarr output.
        init_task_fn: The converter init task function.
        init_task_kwargs: Kwargs for the init task (e.g. acquisitions).
        snapshot_path: Path to the snapshot YAML file.
        update_snapshots: If True, regenerate the snapshot file.
    """
    zarr_dir = tmp_path / "ome_zarr_output"

    # 1. Run init task
    output = init_task_fn(zarr_dir=str(zarr_dir), **init_task_kwargs)

    # 2. Infer collection type and run compute tasks
    collection_type = _infer_collection_type(zarr_dir)
    updates_list = _run_compute_tasks(output, collection_type)

    # 3. Generate or load snapshot
    if update_snapshots:
        _generate_snapshot(
            zarr_dir=zarr_dir,
            image_list_updates=updates_list,
            snapshot_path=snapshot_path,
        )
        return

    if not snapshot_path.exists():
        raise FileNotFoundError(
            f"Snapshot file {snapshot_path} not found. "
            "Run with --update-snapshots to generate it."
        )

    # 4. Load snapshot and run all checks
    assertions = _load_snapshot(snapshot_path)
    _plate_after_init_checks(
        init_output=output,
        multi_plate_assertions=assertions,
        zarr_dir=zarr_dir,
    )
    _image_list_updates_checks(
        image_list_updates=updates_list,
        multi_plate_assertions=assertions,
        zarr_dir=zarr_dir,
    )
    _post_compute_checks(
        multi_plate_assertions=assertions,
        zarr_dir=zarr_dir,
    )
