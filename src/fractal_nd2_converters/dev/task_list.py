"""Contains the list of tasks available to fractal."""

from fractal_task_tools.task_models import ConverterCompoundTask

AUTHORS = "Flurin Sturzenegger"

TASK_LIST = [
    ConverterCompoundTask(
        name="Convert Nikon ND2 Plate to OME-Zarr",
        executable_init="init_task_convert_nd2_plate.py",
        executable="compute_task_image_in_plate.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 4000},
        category="Conversion",
        modality="HCS",
        tags=[
            "Nikon",
            "ND2",
            "Plate converter",
        ],
        docs_info="file:docs_info/nd2_plate_task.md",
    ),
    ConverterCompoundTask(
        name="Convert Nikon ND2 Image to OME-Zarr",
        executable_init="init_task_convert_nd2_single_image.py",
        executable="compute_task_single_image.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 4000},
        category="Conversion",
        modality="Other",
        tags=[
            "Nikon",
            "ND2",
            "Image converter",
        ],
        docs_info="file:docs_info/nd2_image_task.md",
    ),
]
