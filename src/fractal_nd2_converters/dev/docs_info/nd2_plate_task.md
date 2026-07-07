### Purpose
- Convert a folder of Nikon .nd2 files belonging to a plate acquisition to an OME-Zarr plate.

### Outputs
- An OME-Zarr plate.

### Limitations
- This task has been tested on a limited set of acquisitions (see https://zenodo.org/records/15411420). It may not work on all Nikon .nd2 acquisitions.
- See below for more detailed input expectations.

### Expected inputs
The following input layout is supported. (The names in curly braces `{}` can be freely chosen by the user.)

- Folder of nd2 files belonging to a plate acquisition
	- acquisition path input:
		```text
		.../{folder}
		----/{prefix1}WellA01{suffix1}.nd2
		----/{prefix2}WellC02{suffix2}.nd2
		...
		```
	- output: OME-Zarr plate
	- Note:
		- This works for files generated with the standard plate acquisition JOBS script at the ZMB Nikon Spinning Disk
		- The filenames MUST contain `Well` followed by the well name. Valid options for well names are e.g. `A1`, `A01`
		- If there are multiple files corresponding to the same well, they will be treated as separate positions within the well
		- If there are other .nd2 files in the folder that do not adhere to this naming convention, they will be ignored