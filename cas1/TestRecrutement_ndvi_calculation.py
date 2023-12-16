# -*- coding: utf-8 -*-
"""
PROGRAM TO PRODUCE VERY HIGH RESOLUTION VEGETATION MAPS FROM SATELLITE IMAGES, IN URBAN AREAS.
PART 2 : PREPARE RASTERS OF THE INPUT FEATURES TO TRAIN THE CLASSIFIER.
         ZONAL STATISTICS WILL BE THEN PERFORM ON QGIS.

PREREQUISITES :
    - Part 0 if necessary, and part 1. BE CAREFUL:
      You have to take the entire tiles to calculate ndvi and then SFS'Texture',
      and not the cut images created for the segmentation. Because the OTB
      function 'SFS'Texture' doesn't take into account the nodata values.
      So, for example, it would consider -1000 in the calculation.

Created on Tuesday November 25 2021
Author : Agathe Fontaine
Modified for SPOT images on Monday December 19 2022
By : Agathe Fontaine
Simplified on Wednesday October 25 2023 for a recruitment test
By : Agathe Fontaine

"""

import argparse
import os
import subprocess
import time
from sys import path

import otbApplication

from meoss_libs.libs_file_management import list_files, generate_output_file_name

# Path to personal libraries
scripts_folder = os.path.dirname(os.path.realpath(__file__))
scripts_folder = os.path.normcase(scripts_folder)
path.append(scripts_folder)


def ndvi_calculation_concatened(file, nir_band_nb: int, red_band_nb: int, work_folder):
    """
    Function to produce very high resolution vegetation maps (NDVI) from satellite images, in urban areas.
    Computation done with OTB

    :param file: files to analyse
    :param nir_band_nb: position of the near infrared bands in the images (1 for the first band)
    :param red_band_nb: position of the red bands in the images (1 for the first band)
    :param work_folder: working folder
    :return:
    """

    ndvi_image = os.path.splitext(image)[0] + '_NDVI_otb.tif'

    if os.path.exists(os.path.join(work_folder, ndvi_image)):
        print(f'File {ndvi_image} already exists, it has not been created again\n')
    else:
        app = otbApplication.Registry.CreateApplication("RadiometricIndices")

        app.SetParameterString("in", os.path.join(input_folder, image))
        app.SetParameterInt("channels.nir", nir_band_nb)
        app.SetParameterInt("channels.red", red_band_nb)
        app.SetParameterStringList("list", ['Vegetation:NDVI'])
        app.SetParameterString("out", os.path.normcase(os.path.join(work_folder, ndvi_image)) )

        app.ExecuteAndWriteOutput()

        if os.path.exists(os.path.join(work_folder, ndvi_image)):
            print(f'File {ndvi_image} created\n')
        else:
            print(f'ERROR :\n {ndvi_image} not created\n')


if __name__ == '__main__':

    parser = argparse.ArgumentParser( prog='NDVI calculation', description='Generate ndvi tif')

    parser.add_argument('--input-directory', '-i',  dest='input_dir',      action='store', default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'var', 'datas'), help='Input images file directory')
    parser.add_argument('--output-directory', '-o', dest='output_dir',     action='store', default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'var', 'results'), help='Output images file directory')
    parser.add_argument('--nir-band-nb', '-nb',     dest='nir_band_nb', action='store', default=4, help='Inform the position of the near infrared bands in the images (1 for the first band)')
    parser.add_argument('--red-band-nb', '-rb',     dest='red_band_nb', action='store', default=3, help='Inform the position of the red bands in the images (1 for the first band)')
    parser.add_argument('suffixes_name', type=str, nargs='+', help='Input images file suffixes (ex: _FRE_ConcatenateImageBGRPIR.tif)')

    args = parser.parse_args()

    start_time = time.time()

    # prepare input folder
    input_folder = os.path.normcase( args.input_dir)

    # prepare output folder
    output_folder = os.path.normcase(args.output_dir)
    os.makedirs(output_folder, exist_ok=True)

    # get file to analyse
    lst_si = list_files_legacy(input_folder, args.suffixes_name)

    # compute ndvi !
    for image in lst_si:
        ndvi_calculation_concatened(image, args.nir_band_nb, args.red_band_nb, output_folder)

    elapsed_time = time.time() - start_time
    m, s = divmod(elapsed_time, 60)
    h, m = divmod(m, 60)
    print(f"Elapsed time during the whole program = {round(h)}h {round(m)}min {round(s, 1)}sec.")
