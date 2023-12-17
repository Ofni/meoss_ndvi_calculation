#!/usr/bin/python

import argparse
import logging
import os
from sys import path

import otbApplication

# meoss_libs can be set to git submodule
# and therefore be pull/push for other people/script independently of NVDI calculations
from meoss_libs.file_management import search_B4_B8, generate_output_file_name, list_files
from meoss_libs.otb import bandmath_otb, superimpose_otb, managenodata_otb, extract_ROI_otb, radiometric_indices_otb

# Not sure to understand well the purpose of this part, really usefully ?
# Path to personal libraries
scripts_folder = os.path.dirname(os.path.realpath(__file__))
scripts_folder = os.path.normcase(scripts_folder)
path.append(scripts_folder)

# create logger
logger = logging.getLogger('NDVI calculation')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s (%(levelname)s) %(name)s(l%(lineno)d): %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

# set logger level
logging.getLogger('NDVI calculation').setLevel(logging.INFO)
logging.getLogger('FILE MANAGEMENT').setLevel(logging.INFO)


def ndvi_calculation_band(img_format, nir_band_img, red_band_img, cloud_mask_img, output_directory, shape_file):
    """
    Function to produce very high resolution vegetation maps (NDVI) from satellite images, in urban areas.
    Computation done with OTB and use B4 and B8 bands

    Args:
        img_format: Images formats. It can be: S2-2A-ESA, S2-2A, S2-3A.
        nir_band_img: Absolute path to the near infrared band image.
        red_band_img: Absolute path to the red band image.
        cloud_mask_img: Absolute path to the cloud mask image.
        output_directory: Absolute path to the output directory.
        shape_file: Absolute path to the shape file to clip the output computed index.

    Returns:
        None. The NDVI image is written in the output directory
    """
    try:
        logger.info(f"generate ndvi image with B4 B8 band images")
        logger.debug(f"files used : format: {img_format}, nir image: {nir_band_img}, red image: {red_band_img}, cloud image: {cloud_mask_img}, output dir: {output_directory}, shape file : {shape_file}")

        outfile = generate_output_file_name(red_band_img, img_format, prefix='NDVI')
        outfile_with_path = os.path.join(output_directory, outfile)

        if os.path.exists(outfile_with_path):
            logger.warning(f'File {outfile_with_path} already exists, it has not been created again')

        else:
            cloud_free_mask_value = "0"            # cloud free value in S2-2A and S2-SEN2COR masks = 0
            if img_format == 'S2-3A':
                cloud_free_mask_value = "4"        # cloud free value in S2-3A  = 4

            # the sentinel-2 from ESA (S2-SEN2COR) only provides 20 m cloud mask, this why it's necessary to do superimpose.
            app0 = superimpose_otb(cloud_mask_img, nir_band_img, "temp0.tif" )

            app1 = bandmath_otb(il=[nir_band_img, red_band_img], output_file="temp1.tif", exp="(im1b1-im2b1)/(im1b1+im2b1+1.E-6)*1000")
            app2 = bandmath_otb(il_object=[app1.GetParameterOutputImage("out"), app0.GetParameterOutputImage("out")], output_file="temp2.tif", exp=f"(im2b1=={cloud_free_mask_value})?im1b1:0")

            # if shapefile is provided, it will be used to clip spectral index to the output image, else image is directly written
            if shape_file:
                logger.info(f"shape file used: {shape_file}")
                app3 = managenodata_otb(input_image=app2.GetParameterOutputImage("out"), output_image="temp3.tif", action='exe')
                extract_ROI_otb(input_file= app3.GetParameterOutputImage("out"), shape_file=shape_file, output_file=f"{outfile_with_path}?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")

            else:
                managenodata_otb(input_image=app2.GetParameterOutputImage("out"), output_image=f"{outfile_with_path}?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES", action='write&exe')

            logger.info(f'NDVI File created: {outfile_with_path}')

    except Exception as e:
        logger.error(f"error while generating NDVI image: {e}")


def ndvi_calculation_concatenated(file, nir_band_nb, red_band_nb, output_directory):
    """
    Function to produce very high resolution vegetation maps (NDVI) from satellite images, in urban areas.
    Computation done with OTB and BGRPIP concatenated image

    Args:
        file: Absolute path to the concatenated image.
        nir_band_nb: Position of the near infrared bands in the images (1 for the first band).
        red_band_nb: Position of the red bands in the images (1 for the first band).
        output_directory: Absolute path to the output directory.

    Returns:
        None. The NDVI image is written in the output directory
    """
    try:
        logger.info(f"generate ndvi image with concatenated images in {file}")
        logger.debug(f"files used : file: {file}, nir nb: {nir_band_nb}, red nb: {nir_band_nb}, output dir: {output_directory}")

        outfile = generate_output_file_name(file, format='S2-2A', prefix='NDVI', prefix2='concatBGRPIP')
        outfile_with_path = os.path.join(output_directory, outfile)

        if os.path.exists(os.path.join(output_directory, outfile)):
            logger.warning(f'File {outfile_with_path} already exists, it has not been created again')

        else:
            radiometric_indices_otb(file, outfile_with_path, nir_band_nb, red_band_nb)

            logger.info(f'NDVI File created: {outfile_with_path}')

    except Exception as e:
        logger.error(f"error while generating NDVI image: {e}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='NDVI calculation', description='Generate ndvi tif', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(help='sub-command help', dest='mode')

    parser.add_argument('-i', '--input-directory',  dest='input_dir', default=os.path.join(os.getcwd(), '01_DATA'), help='Input images file directory.')
    parser.add_argument('-o', '--output-directory', dest='output_dir', default=os.path.join(os.getcwd(), '02_RES'), help='Output images file directory.')

    parser_concat = subparsers.add_parser('concat', help='options for concatenated mode')
    parser_concat.add_argument('-nb', '--nir-band-nb' ,  dest='nir_band_nb', default=4, help='Inform the position of the near infrared bands in the images (1 for the first band). default (4)')
    parser_concat.add_argument('-rb', '--red-band-nb',  dest='red_band_nb', default=3, help='Inform the position of the red bands in the images (1 for the first band). Default (3)')
    parser_concat.add_argument('suffixes_name', type=str, nargs='+', help='Input images file suffixes (ex: *_FRE_ConcatenateImageBGRPIR)')

    parser_band = subparsers.add_parser('band', help='options for band mode')
    parser_band.add_argument('-f', '--format', choices=['S2-2A', 'S2-2A-ESA', 'S2-3A'], required=True, dest='format', help='Sentinel-2 level : S2-2A = image processed with MAJA, S2-3A = cloud free synthesis processed with WASP, S2-2A-ESA = image processed with SEN2COR')
    parser_band.add_argument('-shpdir', '--shapefile-directory', required=False, dest='shape_directory', help=' [Optional] shapefile (must have same CRS as input image) to clip the output computed index')

    args = parser.parse_args()

    # TODO: depending on the needs, but all needed arguments could be moved to a configuration file instead of being passed as arguments each time

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    if args.mode == 'band':
        band_files = search_B4_B8(args.input_dir, args.format, subfolder=True)

        if len(band_files['B4']) == 0 and len(band_files['B8']) == 0:
            logger.warning("no B4 B8 files found")

        for red, nir, mask in zip(band_files['B4'], band_files['B8'], band_files['cloud_masks']):
            ndvi_calculation_band(args.format, nir, red, mask, args.output_dir, args.shape_directory)

    elif args.mode == 'concat':
        files = list_files(pattern=args.suffixes_name, directory=args.input_dir, subfolder=True)

        if len(files) == 0:
            logger.warning("no concat BGRPIP files found")

        for image in files:
            ndvi_calculation_concatenated(image, args.nir_band_nb, args.red_band_nb, args.output_dir)
