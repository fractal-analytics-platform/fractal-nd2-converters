"""Tools to convert nd2 files to ome-zarr."""

import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import nd2
import numpy as np
import polars
from ome_zarr_converters_tools import (
    AcquisitionDetails,
    AcquisitionOptions,
    AttributeType,
    ChannelInfo,
    ConverterOptions,
    ImageInPlate,
    SingleImage,
    Tile,
    TiledImage,
    default_axes_builder,
    tiles_aggregation_pipeline,
)
from ome_zarr_converters_tools.models._loader import ImageLoaderInterface
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class _BaseND2AcquisitionModel(BaseModel):
    """Shared base for ND2 acquisition models."""

    @property
    def _sanitized_name(self) -> str:
        """Get the sanitized name from the path."""
        name = self.path.rstrip("/").split("/")[-1].split(".nd2")[0]
        return re.sub(r"[^A-Za-z0-9\-_. ]", "_", name)


class ND2ImageAcquisitionModel(_BaseND2AcquisitionModel):
    """Model for Nikon ND2 non-plate acquisitions.

    Accepts a single .nd2 file or a folder of .nd2 files that do not
    follow a plate layout (no well information in filenames).
    """

    path: str
    """
    Path to the nd2 file, or a folder containing nd2 files.
    """
    image_name: str | None = None
    """
    Optional custom name for the output OME-Zarr image. If not provided,
    the name will be derived from the file or folder name.
    """
    advanced: AcquisitionOptions = Field(default_factory=AcquisitionOptions)
    """
    Advanced acquisition options.
    """

    @property
    def normalized_image_name(self) -> str:
        """Get the normalized image name."""
        if self.image_name is not None:
            return self.image_name
        return self._sanitized_name

    def get_zarr_name(self, nd2_path: Path) -> str:
        """Get the sanitized zarr name for an nd2 file.

        For folders, appends the sanitized file stem to the image name.
        For single files, returns the image name directly.
        """
        if Path(self.path).is_dir():
            sanitized_stem = re.sub(r"[^A-Za-z0-9\-_. ]", "_", nd2_path.stem)
            return self.normalized_image_name + "_" + sanitized_stem
        return self.normalized_image_name


class ND2PlateAcquisitionModel(_BaseND2AcquisitionModel):
    """Model for Nikon ND2 plate acquisitions.

    Accepts a folder of .nd2 files where each file corresponds to a well
    (e.g. WellB02_..., WellC03_...).
    """

    path: str
    """
    Path to a folder containing nd2 files for each well. Each file must have
    well information in its filename (e.g. WellB02_..., WellC03_...).
    """
    plate_name: str | None = None
    """
    Optional custom name for the plate. If not provided, the name will be the
    acquisition directory name.
    """
    acquisition_id: int = Field(default=0, ge=0)
    """
    Acquisition ID, used to identify the acquisition in case of multiple acquisitions.
    """
    advanced: AcquisitionOptions = Field(default_factory=AcquisitionOptions)
    """
    Advanced acquisition options.
    """

    @property
    def normalized_plate_name(self) -> str:
        """Get the normalized plate name."""
        if self.plate_name is not None:
            return self.plate_name
        return self._sanitized_name

    def get_condition_table(self) -> polars.DataFrame | None:
        """Get the path to the condition table if it exists."""
        if self.advanced.condition_table_path is not None:
            try:
                return polars.read_csv(self.advanced.condition_table_path)
            except Exception as e:
                raise ValueError(
                    "Failed to read condition table at "
                    f"{self.advanced.condition_table_path}: {e}"
                ) from e
        return None


class nd2Loader(ImageLoaderInterface):
    """Custom loader for nd2 files."""

    file_path: str
    p: int | None  # tile-position index (None for single-position files)

    def load_data(self, resource: Any = None) -> np.ndarray:
        """Load the tile data as a numpy array."""
        if resource is not None:
            path = f"{resource}/{self.file_path}"
        else:
            path = self.file_path

        tile_data = nd2.imread(path, xarray=True, dask=True)

        if "P" in tile_data.dims:
            tile_data = tile_data.isel(P=self.p)
        if not set(tile_data.dims).issubset(("T", "C", "Z", "Y", "X")):
            raise ValueError(
                f"Data can only have dimensions T, C, Z, Y, X. Found: {tile_data.dims}"
            )
        if "Z" not in tile_data.dims:
            tile_data = tile_data.expand_dims(Z=1, axis=0)
        if "C" not in tile_data.dims:
            tile_data = tile_data.expand_dims(C=1, axis=0)
        if "T" not in tile_data.dims:
            tile_data = tile_data.expand_dims(T=1, axis=0)
        if tile_data.dims != ("T", "C", "Z", "Y", "X"):
            tile_data = tile_data.transpose("T", "C", "Z", "Y", "X")

        return tile_data.data.compute()

    def find_data_type(self, resource: Any = None) -> str:
        """Return the dtype without loading the full array."""
        path = f"{resource}/{self.file_path}" if resource else self.file_path
        with nd2.ND2File(path) as f:
            return str(f.dtype)


class _ND2Metadata(BaseModel):
    """Parsed metadata from an ND2 file."""

    shape_x: int
    shape_y: int
    shape_z: int
    shape_c: int
    shape_t: int
    acquisition_details: AcquisitionDetails
    positions: list[tuple[str, float, float, int | None]]


def _color_to_hex(color) -> str:
    """Convert nd2 Color object to 6-character hex string (e.g., '0000FF')."""
    return f"{color.r:02X}{color.g:02X}{color.b:02X}"


def _parse_nd2_metadata(
    nd2_path: str | Path,
    fov_name_override: str | None = None,
) -> _ND2Metadata:
    """Parse metadata from an ND2 file.

    Args:
        nd2_path: Path to the .nd2 file.
        fov_name_override: When provided and the file has no P dimension,
            use this name instead of the default "FOV_0". Used when multiple
            single-position files contribute to the same well.

    Returns:
        Parsed ND2 metadata including shapes, acquisition details,
        and FOV positions.
    """
    with nd2.ND2File(str(nd2_path)) as nd2file:
        shape_x = nd2file.sizes.get("X", 1)
        shape_y = nd2file.sizes.get("Y", 1)
        shape_z = nd2file.sizes.get("Z", 1)
        shape_c = nd2file.sizes.get("C", 1)
        shape_t = nd2file.sizes.get("T", 1)

        # scale factors [um]/[px]
        scale_x = nd2file.voxel_size().x
        scale_z = nd2file.voxel_size().z

        # t_spacing in seconds; read from TimeLoop when available
        scale_t = 1.0
        if shape_t > 1:
            time_loops = [e for e in nd2file.experiment if e.type == "TimeLoop"]
            if time_loops:
                params = time_loops[0].parameters
                if params.periodMs > 0:
                    scale_t = params.periodMs / 1000.0
                elif params.periodDiff.avg > 0:
                    scale_t = params.periodDiff.avg / 1000.0

        # camera transformation matrix
        transform = nd2file.metadata.channels[0].volume.cameraTransformationMatrix
        transform = np.array(transform).reshape(2, 2)

        # load channel info
        channels = [
            ChannelInfo(
                channel_label=ch.channel.name,
                wavelength_id=str(ch.channel.emissionLambdaNm),
                colors=_color_to_hex(ch.channel.color),
            )
            for ch in nd2file.metadata.channels
        ]

        acq = AcquisitionDetails(
            channels=channels,
            pixelsize=scale_x,
            z_spacing=scale_z,
            t_spacing=scale_t,
            axes=default_axes_builder(is_time_series=shape_t > 1),
        )

        # Build per-position list
        positions: list[tuple[str, float, float, int | None]] = []
        if "P" in nd2file.sizes:
            loops = {experiment.type: experiment for experiment in nd2file.experiment}
            if "XYPosLoop" not in loops:
                raise ValueError(
                    f"The nd2 file {nd2_path} contains multiple positions, "
                    "but no XYPosLoop was found in metadata."
                )
            for p, pnt in enumerate(loops["XYPosLoop"].parameters.points):
                xy = np.dot(
                    transform,
                    [pnt.stagePositionUm.x, pnt.stagePositionUm.y],
                )
                positions.append((f"FOV_{p}", xy[0], -xy[1], p))
        else:
            fov_name = fov_name_override if fov_name_override is not None else "FOV_0"
            pnt = nd2file.frame_metadata(0).channels[0].position
            positions.append(
                (fov_name, pnt.stagePositionUm.x, pnt.stagePositionUm.y, None)
            )

    return _ND2Metadata(
        shape_x=shape_x,
        shape_y=shape_y,
        shape_z=shape_z,
        shape_c=shape_c,
        shape_t=shape_t,
        acquisition_details=acq,
        positions=positions,
    )


def _build_tiles(
    nd2_path: str | Path,
    collection: ImageInPlate | SingleImage,
    attributes: dict[str, AttributeType],
    fov_name_override: str | None = None,
) -> list[Tile]:
    """Build tiles from nd2 file."""
    meta = _parse_nd2_metadata(nd2_path, fov_name_override=fov_name_override)

    return [
        Tile(
            fov_name=fov_name,
            start_x=start_x,
            start_y=start_y,
            start_z=0,
            length_x=meta.shape_x,
            length_y=meta.shape_y,
            length_z=meta.shape_z,
            length_c=meta.shape_c,
            length_t=meta.shape_t,
            attributes=attributes,
            collection=collection,
            image_loader=nd2Loader(file_path=str(nd2_path), p=p_idx),
            acquisition_details=meta.acquisition_details,
        )
        for fov_name, start_x, start_y, p_idx in meta.positions
    ]


def _parse_well_info(fn) -> tuple[str, int] | None:
    """Get well info from filename.

    Returns:
        Tuple of (row, column) if well pattern is found, None otherwise.
    """
    pattern = r"Well([A-Z])(\d+)"
    match = re.search(pattern, Path(fn).stem)
    if match:
        row = match.group(1)
        col = int(match.group(2))
        return row, col
    else:
        return None


def _get_nd2_files(path: str | Path) -> list[Path]:
    """Get list of nd2 files from a path.

    Args:
        path: Path to a single .nd2 file or a directory containing .nd2 files.

    Returns:
        Sorted list of nd2 file paths.
    """
    path = Path(path)
    if path.is_dir():
        paths = sorted(path.glob("*.nd2"))
        if not paths:
            raise ValueError(f"No nd2 files found in directory {path}")
        return paths
    elif path.is_file():
        if path.suffix != ".nd2":
            raise ValueError(f"File {path} is not an nd2 file")
        return [path]
    else:
        raise ValueError(f"Path {path} is neither a file nor a directory")


def get_attributes_from_condition_table(
    condition_table: polars.DataFrame | None,
    row: str,
    column: int,
    acquisition: int = 0,
) -> dict[str, AttributeType]:
    """Get the attributes from the condition table."""
    if condition_table is None:
        return {}
    columns = condition_table.columns
    columns_lower = [col.lower() for col in columns]
    if "row" not in columns_lower:
        raise ValueError("Condition table must contain a 'row' column.")
    row_col_name = columns[columns_lower.index("row")]

    if "column" in columns_lower:
        column_col_name = columns[columns_lower.index("column")]
    elif "col" in columns_lower:
        column_col_name = columns[columns_lower.index("col")]
    else:
        raise ValueError("Condition table must contain a 'column' or 'col' column.")

    filtered = condition_table.filter(
        (polars.col(row_col_name) == row) & (polars.col(column_col_name) == column)
    )
    if "acquisition" in columns_lower:
        acquisition_col_name = columns[columns_lower.index("acquisition")]
        filtered = filtered.filter(polars.col(acquisition_col_name) == acquisition)
    if filtered.is_empty():
        logger.warning(
            f"No matching entry found in condition table "
            f"for row:{row} / column:{column} / acquisition:{acquisition}"
        )
        return {}
    filtered_dict = filtered.to_dict(as_series=False)
    attributes = {}
    for key, value in filtered_dict.items():
        if key in ["row", "column", "acquisition"]:
            continue
        if all(isinstance(v, str | type(None)) for v in value):
            formatted_value = [v if v is None else v.strip() for v in value]
            # Replace common placeholder values with None
            formatted_value = [
                None if v in ["", "Na", "NA", "N/A"] else v for v in formatted_value
            ]
            attributes[key] = formatted_value
        elif all(isinstance(v, int | float | bool | type(None)) for v in value):
            attributes[key] = value
        else:
            types_found = {type(v).__name__ for v in value}
            raise ValueError(
                f"Condition table column '{key}' must contain either all strings"
                f", bools, or all numbers, but found types: {types_found}"
            )

    return attributes


def parse_nd2_image_acquisition(
    acquisition_model: ND2ImageAcquisitionModel,
    converter_options: ConverterOptions,
) -> list[TiledImage]:
    """Parse nd2 image acquisition and return list of tiled images.

    Handles single .nd2 files and folders of .nd2 files (non-plate).

    Args:
        acquisition_model: Acquisition input model containing path and options.
        converter_options: Converter options for tile processing.

    Returns:
        List of TiledImage objects ready for conversion.
    """
    nd2_list = _get_nd2_files(acquisition_model.path)

    all_tiles = []
    for nd2_path in nd2_list:
        zarr_name = acquisition_model.get_zarr_name(nd2_path)
        collection = SingleImage(image_path=zarr_name)

        tiles = _build_tiles(
            nd2_path=nd2_path,
            collection=collection,
            attributes={},
        )
        all_tiles.extend(tiles)

    logger.info(f"Built {len(all_tiles)} tiles")

    tiled_images = tiles_aggregation_pipeline(
        tiles=all_tiles,
        converter_options=converter_options,
        filters=acquisition_model.advanced.filters,
    )

    return tiled_images


def parse_nd2_plate_acquisition(
    acquisition_model: ND2PlateAcquisitionModel,
    converter_options: ConverterOptions,
) -> list[TiledImage]:
    """Parse nd2 plate acquisition and return list of tiled images.

    Each .nd2 file in the folder must have well information in its filename
    (e.g. WellB02_...). Multiple files per well are supported: each file
    becomes a separate FOV within the well image.

    Args:
        acquisition_model: Acquisition input model containing path and options.
        converter_options: Converter options for tile processing.

    Returns:
        List of TiledImage objects ready for conversion.
    """
    nd2_list = _get_nd2_files(acquisition_model.path)
    condition_table = acquisition_model.get_condition_table()

    # Group files by well so we can detect multi-file wells.
    well_files: dict[tuple[str, int], list[Path]] = defaultdict(list)
    for nd2_path in nd2_list:
        well_info = _parse_well_info(nd2_path)
        if well_info is None:
            logger.warning(
                f"Skipping {nd2_path.name}: filename does not match "
                "Well pattern (e.g. WellA01, WellB02)"
            )
            continue
        well_files[well_info].append(nd2_path)

    all_tiles = []
    for (row, col), files in well_files.items():
        collection = ImageInPlate(
            plate_name=acquisition_model.normalized_plate_name,
            row=row,
            column=col,
            acquisition=acquisition_model.acquisition_id,
        )
        attributes = get_attributes_from_condition_table(
            condition_table=condition_table,
            row=row,
            column=col,
            acquisition=acquisition_model.acquisition_id,
        )

        multi_file_well = len(files) > 1
        for i, nd2_path in enumerate(files):
            # When multiple files share a well, single-position files would all
            # get fov_name="FOV_0". Pass an explicit override so each file gets
            # a distinct name (FOV_0, FOV_1, …).
            fov_override = f"FOV_{i}" if multi_file_well else None
            tiles = _build_tiles(
                nd2_path=nd2_path,
                collection=collection,
                attributes=attributes,
                fov_name_override=fov_override,
            )
            all_tiles.extend(tiles)

    logger.info(f"Built {len(all_tiles)} tiles")

    tiled_images = tiles_aggregation_pipeline(
        tiles=all_tiles,
        converter_options=converter_options,
        filters=acquisition_model.advanced.filters,
    )

    return tiled_images
