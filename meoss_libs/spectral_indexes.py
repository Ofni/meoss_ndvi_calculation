# -*- coding: utf-8 -*-
"""
CALCULATION OF SPECTRAL INDEXES

This file gathers functions and/or procedures which allow to calculate
spectral indexes (NDVI, etc.)

Created on Tuesday March 16 2021.
Author : Agathe Fontaine

Modified on Thursday May 27 2021
By : Agathe Fontaine
Addition of spectral indexes NDWI, MSAVI2 and EVI

Modified on Wednesday June 02 2021
By : Agathe Fontaine
Possibility to choose the input band numbers for the calculation of the indexes

Modified on Monday June 14 2021
By : Agathe Fontaine
Addition of a function allowing an array to be scaled from one range of values
to another range

Simplified on Wednesday October 25 2023 for a recruitment test
By : Agathe Fontaine
"""
# Libraries import

import numpy as np
from osgeo import gdal
from os.path import join, normcase
from sys import path

# Path to personal libraries
scripts_folder = '/media/tech/Recrutement_test_dev/cas1_env-afo/'
scripts_folder = normcase(scripts_folder)
path.append(scripts_folder)
# Personal libraries
import TestRecrutement_read_and_write as rw # NOQA

# Rescale values


def f_rescale(in_array, range1, range2):
    """
    This function allows an array to be scaled from one range of values
    to another range (e.g. from (-1,1) to (0,255)).

    Parameters
    ----------
    in_array : numpy array
        array to rescale.
    range1 : tuple
        initial range of values.
    range2 : tuple
        final range of values.

    Returns
    -------
    rescaled array.

    """

    range1_min_array = range1[0] * np.ones((in_array.shape[0], in_array.shape[1]))
    delta1 = range1[1] - range1[0]
    delta1_array = delta1 * np.ones((in_array.shape[0], in_array.shape[1]))

    range2_min_array = range2[0] * np.ones((in_array.shape[0], in_array.shape[1]))
    delta2 = range2[1] - range2[0]
    delta2_array = delta2 * np.ones((in_array.shape[0], in_array.shape[1]))

    return (delta2_array * (in_array - range1_min_array) / delta1_array) + range2_min_array


# NDVI

# The NDVI is calculated from the near infra-red (NIR) and the red (R) bands
# as follow :
# (NIR - R) / (NIR + R)

def f_ndvi(red, nir):
    """
    This function allows to calculate NDVI from Numpy arrays.

    Input parameters
    -----------------
    red : numpy array corresponding to the red band
    nir : numpy array corresponding to the near infra-red band

    Return
    -------
    ndvi : numpy array
    """
    return (nir - red) / (nir + red)


def create_ndvi_image(image, images_folder, work_folder, ndvi_filename,
                      nir_band, red_band, in_nodata_value=None, out_nodata_value=None,
                      rescale=False, range1=None, range2=None,
                      gdal_dtype=gdal.GDT_Float32, driver_name='GTiff'):
    """
    This procedure allows to create a NDVI image from an input image.
    The created image is in .tif format.

    Input parameters
    -----------
    image : str
        Multi-spectral image in a compatible format (.tif, .jp2, etc.)
    images_folder : str
        Folder with images
    work_folder : str
        Out folder for the NDVI image
    ndvi_filename : str
        Name of the output NDVI file
    nir_band : int (0 for the first band)
        Numero of the near infrared band
    red_band : int (0 for the first band)
        Numero of the red band
    in_nodata_value : int (default = None)
        Value of the No Data of the input image
    out_nodata_value : int (default = None)
        Value of the No Data of the output image
    rescale : boolean (default = False)
        True to rescale values
    range1 / range2 : tuple (default = None
        Only if rescale = True. Ranges of values to rescale
    gdal_dtype : Pixel data type (default = gdal.GDT_Float32)
        In GDAL format (GDT_Byte, GDT_Int8, GDT_UInt16, GDT_Int16...)
    driver_name : str (default = 'GTiff')
        Any driver supported by GDAL.
    """

    # Opening with GDAL
    # dataset = gdal.Open(normcase(join(images_folder,image)))
    dataset = rw.open_image(normcase(join(images_folder, image)))

    # Read each band as an array and convert to float for calculations
    # Application of the No Data mask if necessary
    if in_nodata_value is not None:
        image_array = dataset.ReadAsArray().astype(float)
        red = image_array[red_band, :, :]
        mask_nodata = red == in_nodata_value
        nir = image_array[nir_band, :, :]
        red = np.ma.masked_equal(red, in_nodata_value)
        nir = np.ma.masked_equal(nir, in_nodata_value)
    else:
        image_array = dataset.ReadAsArray().astype(float)
        red = image_array[red_band, :, :]
        nir = image_array[nir_band, :, :]

    # Application of the f_ndvi() function
    ndvi = f_ndvi(red, nir)

    # Rescale values, if necessary
    if rescale:
        ndvi = f_rescale(ndvi, range1, range2)

    # Application of the NoData mask if necessary
    if in_nodata_value is not None:
        ndvi[mask_nodata] = out_nodata_value

    # Write image
    rw.write_image(normcase(join(work_folder, ndvi_filename)), ndvi, data_set=dataset,
                   gdal_dtype=gdal_dtype, transform=None, projection=None,
                   driver_name=None, nb_col=None, nb_ligne=None, nb_band=1,
                   nodata=out_nodata_value)

    # Delete array
    del ndvi
