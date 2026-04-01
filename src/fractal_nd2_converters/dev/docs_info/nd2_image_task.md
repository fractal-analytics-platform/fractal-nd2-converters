### Purpose
- Convert a Nikon .nd2 file, or a folder of .nd2 files to OME-Zarr image(s).

### Outputs
- One or more OME-Zarr images.

### Limitations
- This task has been tested on a limited set of acquisitions (see https://zenodo.org/records/15411420). It may not work on all Nikon .nd2 acquisitions.
- If the positions are split into different files with e.g. the 'Split Multipoints' option, they will be converted to individual images.
- See below for more detailed input expectations.

### Expected inputs
The following input layouts are supported. (The names in curly braces `{}` can be freely chosen by the user.)

- Single file acquisition
	- acquisition path input:
		```text
		.../{filename}.nd2
		```
	- output: single OME-Zarr image

- Folder of single file acquisitions
	- acquisition path input:
		```text
		.../{folder}
		----/{filename1}.nd2
		----/{filename2}.nd2
		...
		```
	- output: multiple OME-Zarr images
	- Note:
		- For plate acquisitions where filenames contain `Well` (e.g. `WellA01{filename}.nd2`), use the "Convert Nikon ND2 Plate to OME-Zarr" task instead