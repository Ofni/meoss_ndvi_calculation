#!/usr/bin/python

"""
This code was created by Ghaith AMIN, PhD at CESBIO/MEOSS
Calculating Normalized Difference Vegetation Index (NDVI) using Sentinel-2
"""
import argparse
import os
from sys import path

import otbApplication

#  meoss_libs can be set to git submodule
# and therefore be pull/push for other people/script independently of NVDI calculations
from meoss_libs.libs_file_management import search_B4_B8, generate_output_file_name, list_files

# Not sure to understand well the purpose of this part, really usefully ?
# Path to personal libraries
scripts_folder = os.path.dirname(os.path.realpath(__file__))
scripts_folder = os.path.normcase(scripts_folder)
path.append(scripts_folder)


def ndvi_calculation_band(img_format, nir_band_img, red_band_img, cloud_mask_img, output_directory, shape_file):
    try:
        outfile = generate_output_file_name(red_band_img, img_format, prefix='NDVI')
        outfile_with_path = os.path.join(output_directory, outfile)

        if os.path.exists(outfile_with_path):
            print(f'File {outfile_with_path} already exists, it has not been created again')

        else:
            cloud_free_mask_value = "0"            # cloud free value in S2-2A and S2-SEN2COR masks = 0
            if img_format == 'S2-3A':
                cloud_free_mask_value = "4"        # cloud free value in S2-3A  = 4

            # the sentinel-2 from ESA (S2-SEN2COR) only provides 20 m cloud mask, this why it's necessary to do superimpose.
            app0 = otbApplication.Registry.CreateApplication("Superimpose")
            app0.SetParameterString("inm", cloud_mask_img)                             # image to reproject
            app0.SetParameterString("inr", nir_band_img)                              # image to reference
            app0.SetParameterString("out", "temp0.tif")
            app0.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
            app0.SetParameterString("interpolator", "nn")
            app0.SetParameterInt("ram", 4000)
            app0.Execute()

            app1 = otbApplication.Registry.CreateApplication("BandMath")
            app1.AddParameterStringList("il", nir_band_img)
            app1.AddParameterStringList("il", red_band_img)
            app1.SetParameterString("out", "temp1.tif")
            app1.SetParameterString("exp", "(im1b1-im2b1)/(im1b1+im2b1+1.E-6)*1000")
            app1.SetParameterInt("ram", 4000)
            app1.Execute()

            app2 = otbApplication.Registry.CreateApplication("BandMath")
            app2.AddImageToParameterInputImageList("il", app1.GetParameterOutputImage("out"))
            app2.AddImageToParameterInputImageList("il", app0.GetParameterOutputImage("out"))
            app2.SetParameterString("out", "temp2.tif")
            app2.SetParameterString("exp", "(im2b1=="+cloud_free_mask_value+")?im1b1:0")
            app2.SetParameterInt("ram", 4000)
            app2.Execute()

            app3 = otbApplication.Registry.CreateApplication("ManageNoData")
            app3.SetParameterInputImage("in", app2.GetParameterOutputImage("out"))
            app3.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
            app3.SetParameterString("mode", "changevalue")

            # if shapefile is provided, it will be used to clip spectral index to the output image, else image is directly written
            if shape_file:
                app3.SetParameterString("out", "temp3.tif")
                app3.Execute()

                # Todo replace by logger
                print(f"shape file used: {shape_file}")
                app4 = otbApplication.Registry.CreateApplication("ExtractROI")
                app4.SetParameterInputImage("in", app3.GetParameterOutputImage("out"))
                app4.SetParameterString("mode", "fit")
                app4.SetParameterString("mode.fit.vect", shape_file)
                app4.SetParameterString("out", outfile_with_path+"?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")
                app4.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
                app4.SetParameterInt("ram", 1000)
                app4.ExecuteAndWriteOutput()

            else:
                app3.SetParameterString("out", outfile_with_path+"?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")
                app3.SetParameterInt("ram", 1000)
                app3.ExecuteAndWriteOutput()

            print(f'NDVI File created: {outfile_with_path}')

    except Exception as e:
        print(f"error while generating NDVi image: {e}")


def ndvi_calculation_concatened(file, nir_band_nb, red_band_nb, output_directory):
    """
    Function to produce very high resolution vegetation maps (NDVI) from satellite images, in urban areas.
    Computation done with OTB

    :param file: files to analyse
    :param nir_band_nb: position of the near infrared bands in the images (1 for the first band)
    :param red_band_nb: position of the red bands in the images (1 for the first band)
    :param output_directory: working folder
    :return:
    """
    try:
        outfile = generate_output_file_name(file, format='S2-2A', prefix='NDVI', prefix2='concatBGRPIP')
        outfile_with_path = os.path.join(output_directory, outfile)

        if os.path.exists(os.path.join(output_directory, outfile)):
            print(f'File {outfile} already exists, it has not been created again\n')

        else:
            app = otbApplication.Registry.CreateApplication("RadiometricIndices")

            app.SetParameterString("in", file)
            app.SetParameterInt("channels.nir", nir_band_nb)
            app.SetParameterInt("channels.red", red_band_nb)
            app.SetParameterStringList("list", ['Vegetation:NDVI'])
            app.SetParameterString("out", outfile_with_path)

            app.ExecuteAndWriteOutput()

            print(f'NDVI File created: {outfile_with_path}')

    except Exception as e:
        print(f"error while generating NDVi image: {e}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='NDVI calculation', description='Generate ndvi tif')
    subparsers = parser.add_subparsers(help='sub-command help', dest='mode')

    parser.add_argument('--input-directory', '-i',  dest='input_dir', default=os.path.join(os.getcwd(), '01_DATA'), help='Input images file directory')
    parser.add_argument('--output-directory', '-o', dest='output_dir', default=os.path.join(os.getcwd(), '02_RES'), help='Output images file directory')

    parser_concat = subparsers.add_parser('concat', help='options for concatenated mode')
    parser_concat.add_argument('--nir-band-nb', '-nb',  dest='nir_band_nb', default=4, help='Inform the position of the near infrared bands in the images (1 for the first band)')
    parser_concat.add_argument('--red-band-nb', '-rb',  dest='red_band_nb', default=3, help='Inform the position of the red bands in the images (1 for the first band)')
    parser_concat.add_argument('suffixes_name', type=str, nargs='+', help='Input images file suffixes (ex: *_FRE_ConcatenateImageBGRPIR)')

    parser_band = subparsers.add_parser('band', help='options for band mode')
    parser_band.add_argument('--format', '-f', choices=['S2-2A', 'S2-2A-ESA', 'S2-3A'], required=True, dest='format', help='Sentinel-2 level : S2-2A = image processed with MAJA, S2-3A = cloud free synthesis processed with WASP, S2-2A-ESA = image processed with SEN2COR')
    parser_band.add_argument('--shapefile-directory', '-shpdir', required=False, dest='shape_directory', help=' [Optional] shapefile (must have same CRS as input image) to clip the output computed index')

    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    if args.mode == 'band':
        band_files = search_B4_B8(args.input_dir, args.format, subfolder=True)

        for red, nir, mask in zip(band_files['B4'], band_files['B8'], band_files['cloud_masks']):
            ndvi_calculation_band(args.format, nir, red, mask, args.output_dir, args.shape_directory)

    elif args.mode == 'concat':
        for image in list_files(pattern=args.suffixes_name, directory=args.input_dir, subfolder=True):
            ndvi_calculation_concatened(image, args.nir_band_nb, args.red_band_nb, args.output_dir)
