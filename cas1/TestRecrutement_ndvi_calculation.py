# -*- coding: utf-8 -*-

"""
PROGRAM TO PRODUCE VERY HIGH RESOLUTION VEGETATION MAPS
FROM SATELLITE IMAGES, IN URBAN AREAS.
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

# (0) INPUTS/OUTPUTS

# (0.1) LIBRAIRIES IMPORT

# 0.1.1. General
import os
from fnmatch import fnmatch
from sys import path
import time
import subprocess

"""
Create a command which allow to ask :
- input directory
- output directory
- type of calculation (default otb)
- number of near infrared bands in the image
- number of red bands in the image
The command give a help with the command -h
"""

parser = argparse.ArgumentParser(
    prog='NDVI calculation',
    description='Generate ndvi tif',
)
parser.add_argument('suffixes_name', type=str, nargs='+',
                    help='Input images file suffixes (ex: _FRE_ConcatenateImageBGRPIR.tif)')

parser.add_argument('--input-directory', dest='input_dir', action='store',
                    default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'var', 'datas'),
                    help='Input images file directory')

parser.add_argument('--output-directory', dest='output_dir', action='store',
                    default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'var', 'results'),
                    help='Output images file directory')

parser.add_argument('--nir-band-number', dest='nir_band_number', action='store', default=3,
                    help='Inform the position of the near infrared bands in the images (0 for the first band)')

parser.add_argument('--red-band-nb', dest='red_band_number', action='store', default=2,
                    help='Inform the position of the red bands in the images (0 for the first band)')

parser.add_argument('--numpy', dest='numpy', action='store_true',
                    help='Calculate NDVI with numpy')

args = parser.parse_args()

# Start time
start_time = time.time()

# 0.1.2. Path to personal libraries
scripts_folder = os.path.dirname(os.path.realpath(__file__))
scripts_folder = os.path.normcase(scripts_folder)
path.append(scripts_folder)

# 0.1.3. Import of the personal libraries
import TestRecrutement_spectral_indexes as si  # NOQA

# 0.2) INPUT/OUTPUT FOLDERS


# 0.2.1. Images folder
si_folder = args.input_dir
si_folder = os.path.normcase(si_folder)

# 0.2.3. Work folder
work_folder = args.output_dir
work_folder = os.path.normcase(work_folder)
os.makedirs(work_folder, exist_ok=True)


# 0.3) IMAGES AND VECTORS NAMES

# Suffix of the input images (not cut)
suffix_in_si = args.suffixes_name


# 0.4) INPUT PARAMETERS

# 0.4.1. Parameters to NDVI calculation
# Inform the position of the near infrared and red bands in the images (0 for the first band)
nir_band_nb = args.nir_band_number
red_band_nb = args.red_band_number
nodata_value = None

# (1) PREPARE OTHER INPUT FEATURES (NDVI AND SFS'TEXTURES)

# 1.0) INPUTS

# 1.0.1. List of tiles
lst_si = []
for f in os.listdir(si_folder):
    for i in range(len(suffix_in_si)):
        if fnmatch(f, "*{}".format(suffix_in_si[i])):
            print(f)
            lst_si.append(f)
lst_si.sort()
print("Length of lst_si :", len(lst_si))

os.makedirs(work_folder, exist_ok=True)

# 1.1) NDVI CALCULATION

# With numpy
if args.numpy:
    # With personal script
    # Allow to take into account nodata value
    for image in lst_si:
        ndvi_image = os.path.splitext(image)[0] + '_NDVI.tif'

        if os.path.exists(os.path.join(work_folder, ndvi_image)):
            print(f'File {ndvi_image} already exists, it has not been created again\n')

        else:
            si.create_ndvi_image(image, si_folder, work_folder, ndvi_image,
                                 nir_band=nir_band_nb, red_band=red_band_nb,
                                 in_nodata_value=nodata_value)

            if os.path.exists(os.path.join(work_folder, ndvi_image)):
                print(f'File {ndvi_image} created\n')

            else:
                print(f'ERROR :\n {ndvi_image} not created\n')
# With OTB
else:
    for image in lst_si:
        ndvi_image = os.path.splitext(image)[0] + '_NDVI_otb.tif'

        if os.path.exists(os.path.join(work_folder, ndvi_image)):
            print(f'File {ndvi_image} already exists, it has not been created again\n')

        else:
            nir_band = nir_band_nb + 1
            red_band = red_band_nb + 1
            # Define commande
            cmd_pattern = "otbcli_RadiometricIndices -in {in_raster} -channels.nir {in_nir} -channels.red {in_r} -list {index} -out {out_raster}"
            cmd = cmd_pattern.format(in_raster=os.path.join(si_folder, image),
                                     in_nir=nir_band, in_r=red_band,
                                     index='Vegetation:NDVI',
                                     out_raster=os.path.normcase(os.path.join(work_folder, ndvi_image)))
            # Execute command
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            print(cmd)
            print(result.decode())

            if os.path.exists(os.path.join(work_folder, ndvi_image)):
                print(f'File {ndvi_image} created\n')
            else:
                print(f'ERROR :\n {ndvi_image} not created\n')


# Final time
elapsed_time = time.time() - start_time
m, s = divmod(elapsed_time, 60)
h, m = divmod(m, 60)
print(f"Elapsed time during the whole program = {round(h)}h {round(m)}min {round(s, 1)}sec.")
