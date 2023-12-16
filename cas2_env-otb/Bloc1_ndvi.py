#!/usr/bin/python

"""
This code was created by Ghaith AMIN, PhD at CESBIO/MEOSS
Calculating Normalized Difference Vegetation Index (NDVI) using Sentinel-2
"""
import argparse
import os

import otbApplication

# meoss libs can be set to git submodule, and therefore be pull/push for other people/script independently of NVDI calculations
from meoss_libs.libs_file_management import search_B4_B8, generate_output_file_name


def ndvi_calculation_band(format, red, nir, mask, out, shp):

    outfile = generate_output_file_name(red, format, prefix='NDVI')
    outfile_with_path = os.path.join(out, outfile)

    if os.path.exists(outfile_with_path):
        print(f'File {outfile_with_path} already exists, it has not been created again')

    else:
        # the sentinel-2 from ESA (S2-SEN2COR) only provides 20 m cloud mask, this why it's necessary to do the superimpose.
        app0 = otbApplication.Registry.CreateApplication("Superimpose")
        app0.SetParameterString("inm",mask)                             # image to reproject
        app0.SetParameterString("inr",nir)                              # image to reference
        app0.SetParameterString("out", "temp0.tif")
        app0.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
        app0.SetParameterString("interpolator", "nn")
        app0.SetParameterInt("ram",4000)
        app0.Execute()

        app1 = otbApplication.Registry.CreateApplication("BandMath")
        app1.AddParameterStringList("il",nir)
        app1.AddParameterStringList("il",red)
        app1.SetParameterString("out", "temp1.tif")
        app1.SetParameterString("exp", "(im1b1-im2b1)/(im1b1+im2b1+1.E-6)*1000")
        app1.SetParameterInt("ram",4000)
        app1.Execute()

        cloud_free_mask_value = "0"            # cloud free value in S2-2A and S2-SEN2COR masks = 0
        if format == 'S2-3A':
            cloud_free_mask_value = "4"        # cloud free value in S2-3A  = 4

        app2 = otbApplication.Registry.CreateApplication("BandMath")
        app2.AddImageToParameterInputImageList("il",app1.GetParameterOutputImage("out"))
        app2.AddImageToParameterInputImageList("il", app0.GetParameterOutputImage("out"))
        app2.SetParameterString("out", "temp2.tif")
        app2.SetParameterString("exp", "(im2b1=="+cloud_free_mask_value+")?im1b1:0")
        app2.SetParameterInt("ram",4000)
        app2.Execute()

        app3 = otbApplication.Registry.CreateApplication("ManageNoData")
        app3.SetParameterInputImage("in", app2.GetParameterOutputImage("out"))
        app3.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
        app3.SetParameterString("mode", "changevalue")

        # if shapefile is provided, it will be used to clip spectral index to the output image, else image is directly written
        if shp:
            app3.SetParameterString("out", "temp3.tif")
            app3.Execute()

            print("...................................................................shp =", shp)
            app4 = otbApplication.Registry.CreateApplication("ExtractROI")
            app4.SetParameterInputImage("in", app3.GetParameterOutputImage("out"))
            app4.SetParameterString("mode","fit")
            app4.SetParameterString("mode.fit.vect", shp)
            app4.SetParameterString("out", outfile_with_path+"?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")
            app4.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
            app4.SetParameterInt("ram",1000)
            app4.ExecuteAndWriteOutput()

        else:
            app3.SetParameterString("out", outfile_with_path+"?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")
            app3.SetParameterInt("ram",1000)
            app3.ExecuteAndWriteOutput()
        

if __name__ == "__main__":

    parser = argparse.ArgumentParser( prog='NDVI calculation', description='Generate ndvi tif')
    subparsers = parser.add_subparsers(help='sub-command help', dest='mode')

    parser.add_argument('--input-directory', '-i',  dest='input_dir', default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'var', 'datas'), help='Input images file directory')
    parser.add_argument('--output-directory', '-o', dest='output_dir', default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'var', 'results'), help='Output images file directory')

    parser_concat = subparsers.add_parser('concat', help='options for concat mode')
    parser_concat.add_argument('--nir-band-nb', '-nb',  dest='nir_band_nb', default=4, help='Inform the position of the near infrared bands in the images (1 for the first band)')
    parser_concat.add_argument('--red-band-nb', '-rb',  dest='red_band_nb', default=3, help='Inform the position of the red bands in the images (1 for the first band)')
    parser_concat.add_argument('suffixes_name', type=str, nargs='+', help='Input images file suffixes (ex: _FRE_ConcatenateImageBGRPIR.tif)')

    parser_band = subparsers.add_parser('band', help='options for band mode')
    parser_band.add_argument('--format', '-f', choices=['S2-2A','S2-2A-ESA','S2-3A'], required=True, dest='format', help='Sentinel-2 level : S2-2A = image processed with MAJA, S2-3A = cloud free synthese processed with WASP, S2-2A-ESA = image processed with SEN2COR')
    parser_band.add_argument('--shapefile-directory', '-shpdir', required=False, dest='shape_directory', help=' [Optional] shapefile (must have same CRS as input image) to clip the output computed index')

    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    if args.mode == 'band':
        bande_files = search_B4_B8(args.input_dir, args.format)

        for red, nir, mask in zip (bande_files['B4'], bande_files['B8'], bande_files['cloud_masks']):
            ndvi_calculation_band(args.format, red, nir, mask, args.output_dir, args.shape_directory)

    elif args.mode == 'concat':
        pass
