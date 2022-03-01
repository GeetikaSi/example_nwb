# Error reproduction : NWB Export using DataJoint data

Reproduce the following errors using a multiple plane ScanImage tiff file:
1. `ValueError: 'CorrectedImageStack' already exists in MotionCorrection 'MotionCorrection'`
2. `ValueError: RoiResponseSeries.__init__: incorrect shape for 'timestamps' (got '(170, 26100)', expected '(None,)')`

Jupyter notebook `motioncorrect_timestamp_errors.ipynb` calls `motioncorrect_timestamp_errors.py`
and replicates the above mentioned errors. 

+ ERROR I : `ValueError: 'CorrectedImageStack' already exists in MotionCorrection 'MotionCorrection'`

Each session has multiple planes, hence, I would like to store multiple CorrectedImageStacks in the MotionCorrection object. Currently, I’m appending the corrected_image_stack and trying to store it in the MotionCorrection object on [here](https://github.com/GeetikaSi/example_nwb/blob/9556d27499040c781299fd8f8f6d17f64cae0c1a/motioncorrect_timestamp_errors.py#L170).
This is when I receive the following error:
ValueError: 'CorrectedImageStack' already exists in MotionCorrection 'MotionCorrection'. It looks like it is not allowing me to save multiple CorrectedImageStack into the MotionCorrection object because when I tried the following it worked:
     motion_correction = MotionCorrection(corrected_image_stacks=corrected_image_stacks[0]) 

+ ERROR II : `ValueError: RoiResponseSeries.__init__: incorrect shape for 'timestamps' (got '(170, 26100)', expected '(None,)')`

Each ROI has a different timestamp, which is why I would like to store timestamps as 2D arrays (hence, the shape becomes : 26100, 170).

To run the notebook:
1. Clone the repository
2. Run the cells of `motioncorrect_timestamp_errors.ipynb`
3. You will first encounter Error II (i.e. the timestamp issue). This is because the there is no NWB MoitonCorrection object while processing the first plane.
4. To bypass the timestamp issue, you can set `timestamp = timestamp[0]` [here](https://github.com/GeetikaSi/example_nwb/blob/9556d27499040c781299fd8f8f6d17f64cae0c1a/motioncorrect_timestamp_errors.py#L222).

### About the tiff file used:

The tiff file used has a single plane but the code is setup in a way to replicate the behavior of a multiple plane tiff file processing. 

Note: This example is prepared using a different tiff file and using some random dummy data. Hence, it might not match the outputs if Suite2p is run outside. 
