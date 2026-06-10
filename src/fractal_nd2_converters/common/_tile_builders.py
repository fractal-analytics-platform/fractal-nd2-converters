"""Parse ND2 metadata and build ``Tile`` objects.

Shared by the image and plate parsers: reads shapes, scales, channels and
field-of-view positions from an ND2 file and turns them into
``ome-zarr-converters-tools`` ``Tile`` models bound to an :class:`nd2Loader`.
"""

import logging
from pathlib import Path

import nd2
import numpy as np
from ome_zarr_converters_tools import (
    AcquisitionDetails,
    AttributeType,
    ChannelInfo,
    ImageInPlate,
    SingleImage,
    Tile,
    default_axes_builder,
)
from pydantic import BaseModel

from fractal_nd2_converters.common._loaders import nd2Loader

logger = logging.getLogger(__name__)


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
    """Convert nd2 Color object to hex color string (e.g., '#0000FF')."""
    return f"#{color.r:02X}{color.g:02X}{color.b:02X}"


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
        # Note: this assumes the same transform applies to all channels
        if not nd2file.metadata.channels:
            raise ValueError("No channel metadata found in ND2 file")
        transform = nd2file.metadata.channels[0].volume.cameraTransformationMatrix
        transform = np.array(transform).reshape(2, 2)

        # load channel info
        channels = [
            ChannelInfo(
                channel_label=ch.channel.name,
                wavelength_id=str(ch.channel.emissionLambdaNm),
                color=_color_to_hex(ch.channel.color),
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
            points = loops["XYPosLoop"].parameters.points  # type: ignore
            for p, pnt in enumerate(points):
                xy = np.dot(
                    transform,
                    [pnt.stagePositionUm.x, pnt.stagePositionUm.y],
                )
                positions.append((f"FOV_{p}", xy[0], -xy[1], p))
        else:
            fov_name = fov_name_override if fov_name_override is not None else "FOV_0"
            if not nd2file.metadata.channels:
                raise ValueError("No channel metadata found in ND2 file")
            channel = nd2file.metadata.channels[0]
            pnt = channel.position  # type: ignore
            xy = np.dot(
                transform,
                [pnt.stagePositionUm.x, pnt.stagePositionUm.y],
            )
            positions.append((fov_name, xy[0], -xy[1], None))

    return _ND2Metadata(
        shape_x=shape_x,
        shape_y=shape_y,
        shape_z=shape_z,
        shape_c=shape_c,
        shape_t=shape_t,
        acquisition_details=acq,
        positions=positions,
    )


def build_tiles(
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


def get_nd2_files(path: str | Path) -> list[Path]:
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
