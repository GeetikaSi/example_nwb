import os, sys
import collections
from datetime import datetime
from dateutil.tz import tzlocal
import pytz
import re
import numpy as np
import json
import pandas as pd
import pathlib
import pynwb
from pynwb import NWBFile, NWBHDF5IO
from pynwb import NWBFile, TimeSeries, NWBHDF5IO
from pynwb.image import ImageSeries
from pynwb.ophys import TwoPhotonSeries, OpticalChannel, ImageSegmentation, \
    Fluorescence, CorrectedImageStack, MotionCorrection, RoiResponseSeries, DfOverF
import scanreader

# ============================== SET CONSTANTS ==========================================
zero_zero_time = datetime.strptime('00:00:00', '%H:%M:%S').time()  # no precise time available
institution = 'DataJoint - testing CorrectedImageStack'

single_tiff_file = scanreader.read_scan('./k53_20160530_RSM_125um_41mW_zoom2p2_00001_00001.tif')
add_tiff_file = scanreader.read_scan('./k53_20160530_RSM_125um_41mW_zoom2p2_00001_00001.tif')
tiff_files = [single_tiff_file, add_tiff_file]

def get_nwb_subject(session_key):
    subj_key = {'animal_id': 'abc123', 'datasource_id': 0}
    subj = {'animal_id': 'abc123',
            'datasource_id': 0,
            'animal_species': 'mouse',
            'animal_name': '123',
            'animal_sex': 'M',
            'animal_dob': datetime.date(datetime(2022, 3, 1)),
            'color': 'Unknown',
            'animal_notes': 'Sample animal'}
    strain = 'C +/- x GC+/-'

    return pynwb.file.Subject(
        subject_id=f'{subj_key["animal_id"]}-{subj_key["datasource_id"]}-{session_key}',
        description=f'animal_name: {subj["animal_name"]}; color: {subj["color"]}; strain: {strain}; animal_notes: {subj["animal_notes"]}',
        genotype=' x ',
        sex=subj['animal_sex'],
        species=subj['animal_species'],
        date_of_birth=datetime.combine(subj['animal_dob'], zero_zero_time) if subj['animal_dob'] else None)


def export_to_nwb(session_key, output_dir='./', overwrite=True):

    print(f'Exporting to NWB 2.0 for session: {session_key}...')
    # ===============================================================================
    # ============================== META INFORMATION ===============================
    # ===============================================================================

    session = {'session_name': 'abc123d4fcbb',
                'recording_order': 0,
                'recording_name': 'rrrrd24',
                'animal_id': 'abc123',
                'datasource_id': 0,
                'animal_name': '123',
                'timestamp': datetime(2022, 3, 1, 5, 30, 10),
                'combined': 'yes',
                'timeseries_name': '123_20220301_ML-100_DJ01_3Openfiled',
                'equipment_type': '2Pminiscope_A',
                'username': 'testuser'}
    file_name = '_'.join(
        [session['session_name'],
         session['timestamp'].strftime('%Y-%m-%d'),
         str(session['timeseries_name'])])
    nwbfile = NWBFile(
            identifier=file_name,
            related_publications='',
            experiment_description='',
            session_description='Imaging session',
            session_start_time=datetime.combine(session['timestamp'], zero_zero_time),
            file_create_date=datetime.now(tzlocal()),
            experimenter='Test',
            institution=institution,
            keywords=['Two-photon imaging'])

    # ==========================================================================
    # ----- Create a Device, create an OpticalChannel and an ImagingPlane ------
    # ==========================================================================
    system_names = np.array(['System v1.0'])
    scope_names = np.array(['Scope 1'])
    device_name = ["{}_{}".format(system_name_, scope_name_) for system_name_, scope_name_ in zip(system_names,scope_names)][0]
    device = nwbfile.create_device(name=device_name,
                                   description="",
                                   manufacturer=""
                                   )
    nwbfile.subject = get_nwb_subject(session_key)
    optical_channel = OpticalChannel(name="OpticalChannel",
                                     description="an optical channel",
                                     emission_lambda=500.
                                     )

    plane_keys = [{'session_name': 'abc123d4fcbb',
                    'recording_order': 0,
                    'recording_name': 'rrrrd24',
                    'dataset_name': 'dddd280d',
                    'center_plane': 0},
                    {'session_name': 'abc123d4fcbb',
                    'recording_order': 0,
                    'recording_name': 'rrrrd24',
                    'dataset_name': 'dddd280d',
                    'center_plane': 1}]

    ophys_module = nwbfile.create_processing_module(name='ophys',
                                                    description='optical physiology processed data'
                                                    )
    img_seg = ImageSegmentation()
    corrected_image_stacks = []
    roi_resp_series = []
    for plane, tiff_file in zip(plane_keys,tiff_files):
        print(plane)
        num_planes = tiff_file.num_scanning_depths
        framerate = tiff_file.fps
        imaging_plane = nwbfile.create_imaging_plane(name="ImagingPlane"+ '_' + str(plane['center_plane']),
                                                    optical_channel=optical_channel,
                                                    imaging_rate=framerate,
                                                    description="",
                                                    device=device,
                                                    excitation_lambda=600.,
                                                    indicator="GFP",
                                                    location="",
                                                    grid_spacing=(),
                                                    grid_spacing_unit="",
                                                    origin_coords=(),
                                                    origin_coords_unit=""
                                                    )

        # ==========================================================================
        # ---------------------------- Insert data file ----------------------------
        # ==========================================================================

        file_path = np.array(['./k53_20160530_RSM_125um_41mW_zoom2p2_00001_00001.tif'])
        image_series = TwoPhotonSeries(name='TwoPhotonSeries2'+'_'+str(plane['center_plane']),
                                        dimension=[100, 100],
                                        external_file=file_path,
                                        imaging_plane=imaging_plane,
                                        starting_frame=[0],
                                        format='external',
                                        starting_time=0.0,
                                        rate=1.0
                                        )
        nwbfile.add_acquisition(image_series)

        # ==========================================================================
        # --------------------- MotionCorrection information -----------------------
        # ==========================================================================

        corrected = ImageSeries(name='corrected',  
                                data=np.ones((256,265,1000)),
                                unit='na',
                                format='Average projection of motion corrected stack - contrast enhanced (unwarped)', 
                                starting_time=0.0,
                                rate=1.0
                                )
        x_mocor = np.ones((26100,))
        y_mocor = np.ones((26100,))
        xy_translation_data = zip(x_mocor, y_mocor)

        xy_translation = TimeSeries(name='xy_translation',
                                    data=list(xy_translation_data),
                                    unit='pixels',
                                    starting_time=0.0,
                                    rate=1.0,
                                    )

        corrected_image_stack = CorrectedImageStack(corrected=corrected,
                                                    original=image_series,
                                                    xy_translation=xy_translation,
                                                    )

        corrected_image_stacks.append(corrected_image_stack)

        # ==========================================================================
        # ----------------------- Segmentation information -------------------------
        # ==========================================================================

        ps = img_seg.create_plane_segmentation(name='PlaneSegmentation'+'_'+str(plane['center_plane']),
                                            description='output from segmenting the imaging plane',
                                            imaging_plane=imaging_plane,
                                            reference_images=image_series  # optional
                                            )

        # ==========================================================================
        # -------------- ROIs (Image masks, Pixel masks) information ---------------
        # ==========================================================================

        cell_ids = np.arange(1,170,1)
        pixel_masks = []
        for cell in cell_ids:
            xpix_corr = np.random.randint(321, 340, 313)
            ypix_corr = np.random.randint(268, 301, 313)
            lambda_corr = np.random.uniform(low=0.001, high=0.02, size=(313,))
            pixel_mask = list(zip(xpix_corr, ypix_corr, lambda_corr))
            pixel_masks.append(pixel_mask)
            ps.add_roi(pixel_mask=pixel_masks[0])

        # ==========================================================================
        # ----------------------- Flourescence information -------------------------
        # ==========================================================================

        raw_fluo_traces = np.random.random((26100, 170))

        timestamps = np.random.random((26100, 170))
        timestamps = np.vstack(timestamps)
        raw_fluo_traces = np.vstack(raw_fluo_traces).T
        timestamps = np.vstack(timestamps).T

        roi_region = ps.create_roi_table_region(region=list(range(len(cell_ids))),
                                                description='list of ROIs'
                                                )

        # TODO: Can timestamps be stored as an 2d array instead of just 1D
        roi_resp_series.append(RoiResponseSeries(name='RawfluorescenceResponseSeries'+'_'+str(plane['center_plane']),
                                            data=raw_fluo_traces,
                                            description='Raw fluorescence trace',
                                            rois=roi_region,
                                            unit='a.u.',
                                            timestamps=timestamps))

    motion_correction = MotionCorrection(corrected_image_stacks=corrected_image_stacks)
    ophys_module.add(motion_correction)
    ophys_module.add(img_seg)
    fl = Fluorescence(roi_response_series=roi_resp_series)
    ophys_module.add(fl)
    # ------------------------ Write to .nwb -------------------
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    save_file_name = ''.join([nwbfile.identifier, '.nwb'])
    output_fp = (output_dir / save_file_name).absolute()
    if overwrite or not output_fp.exists():
        with NWBHDF5IO(output_fp.as_posix(), mode='w') as io:
            io.write(nwbfile)
            print(f'\tWrite NWB 2.0 file: {save_file_name}')

    print('\tDone.')
    return nwbfile

def write_nwb_files(session_keys, output_dir='./', overwrite=True):
    for session_key in session_keys:
        export_to_nwb(session_key, output_dir=output_dir, overwrite=overwrite)