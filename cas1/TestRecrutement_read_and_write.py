# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 2021
@author: Agathe Fontaine

Modified on Tue Mar 16 2021
by: Agathe Fontaine
Modifications : write_image. Adding a No Data option.

Modified on Tue Mar 30 2021
by: Agathe Fontaine
Modifications : create a new method : rasterize_multibands()

Modified on Wed Mar 31 2021
by: Agathe Fontaine
Modifications : create news functions :
    rasterize_multibands_memory() and vector_to_3d_array()

Simplified on Wednesday October 25 2023 for a recruitment test
By : Agathe Fontaine
"""

from osgeo import gdal
import numpy as np


def open_image(filename, verbose=False):
    """
    Open an image file with gdal

    Paremeters
    ----------
    filename : str
      Image path to open

    Return
    ------
    osgeo.gdal.Dataset
    """
    data_set = gdal.Open(filename, gdal.GA_ReadOnly)

    if data_set is None:
        print('Impossible to open {}'.format(filename))
        exit()
    elif data_set is not None and verbose:
        print('{} is open'.format(filename))

    return data_set


def write_image(out_filename, array, data_set=None, gdal_dtype=None, transform=None, projection=None, driver_name=None, nb_col=None, nb_ligne=None, nb_band=None, nodata=None):
    """
    Write a array into an image file.

    Parameters
    ----------
    out_filename : str
        Path of the output image.
    array : numpy.ndarray
        Array to write
    nb_col : int (optional)
        If not indicated, the function consider the `array` number of columns
    nb_ligne : int (optional)
        If not indicated, the function consider the `array` number of rows
    nb_band : int (optional)
        If not indicated, the function consider the `array` number of bands
    data_set : osgeo.gdal.Dataset
        `gdal_dtype`, `transform`, `projection` and `driver_name` values
        are infered from `data_set` in case there are not indicated.
    gdal_dtype : Pixel data type (optional)
        In GDAL format (GDT_Byte, GDT_Int8, GDT_UInt16, GDT_Int16...).
    transform : tuple (optional)
        GDAL Geotransform information same as return by
        data_set.GetGeoTransform().
    projection : str (optional)
        GDAL projetction information same as return by
        data_set.GetProjection().
    driver_name : str (optional)
        Any driver supported by GDAL. Ignored if `data_set` is indicated.
    nodata : int (optional)
        No Data value to apply.

    Returns
    -------
    None
    """
    # Get information from array if the parameter is missing
    nb_col = nb_col if nb_col is not None else array.shape[1]
    nb_ligne = nb_ligne if nb_ligne is not None else array.shape[0]
    array = np.atleast_3d(array)
    nb_band = nb_band if nb_band is not None else array.shape[2]

    # Get information from data_set if provided
    transform = transform if transform is not None else data_set.GetGeoTransform()
    projection = projection if projection is not None else data_set.GetProjection()
    gdal_dtype = gdal_dtype if gdal_dtype is not None \
        else data_set.GetRasterBand(1).DataType
    driver_name = driver_name if driver_name is not None \
        else data_set.GetDriver().ShortName

    # Create DataSet
    driver = gdal.GetDriverByName(driver_name)
    output_data_set = driver.Create(out_filename, nb_col, nb_ligne, nb_band,
                                    gdal_dtype)
    output_data_set.SetGeoTransform(transform)
    output_data_set.SetProjection(projection)

    # Fill it and write image
    for idx_band in range(nb_band):
        if nodata is not None:
            output_data_set.GetRasterBand(idx_band + 1).SetNoDataValue(nodata)
        output_band = output_data_set.GetRasterBand(idx_band + 1)
        output_band.WriteArray(array[:, :, idx_band])
        # not working with a 2d array.
        # this is what np.atleast_3d(array)
        # was for
        output_band.FlushCache()

    del output_band
    output_data_set = None


def write_data_set(array, data_set=None, gdal_dtype=None, transform=None, projection=None, nb_col=None, nb_ligne=None, nb_band=None, nodata=None):
    """
    Write a array into a dataset.

    Parameters
    ----------
    array : numpy.ndarray
        Array to write
    nb_col : int (optional)
        If not indicated, the function consider the `array` number of columns
    nb_ligne : int (optional)
        If not indicated, the function consider the `array` number of rows
    nb_band : int (optional)
        If not indicated, the function consider the `array` number of bands
    data_set : osgeo.gdal.Dataset
        `gdal_dtype`, `transform`, `projection` and `driver_name` values
        are infered from `data_set` in case there are not indicated.
    gdal_dtype : int (optional)
        Gdal data type (e.g. : gdal.GDT_Int32).
    transform : tuple (optional)
        GDAL Geotransform information same as return by
        data_set.GetGeoTransform().
    projection : str (optional)
        GDAL projetction information same as return by
        data_set.GetProjection().
    nodata : int (optional)
        No Data value to apply.

    Returns
    -------
    output_data_set : GDAL data set
    """
    # Get information from array if the parameter is missing
    nb_col = nb_col if nb_col is not None else array.shape[1]
    nb_ligne = nb_ligne if nb_ligne is not None else array.shape[0]
    array = np.atleast_3d(array)
    nb_band = nb_band if nb_band is not None else array.shape[2]

    # Get information from data_set if provided
    transform = transform if transform is not None else data_set.GetGeoTransform()
    projection = projection if projection is not None else data_set.GetProjection()
    gdal_dtype = gdal_dtype if gdal_dtype is not None \
        else data_set.GetRasterBand(1).DataType
    driver_name = 'MEM'

    # Create DataSet
    driver = gdal.GetDriverByName(driver_name)
    output_data_set = driver.Create('', nb_col, nb_ligne, nb_band, gdal_dtype)
    output_data_set.SetGeoTransform(transform)
    output_data_set.SetProjection(projection)

    # Fill it and write image
    for idx_band in range(nb_band):
        if nodata is not None:
            output_data_set.GetRasterBand(idx_band + 1).SetNoDataValue(nodata)
        output_band = output_data_set.GetRasterBand(idx_band + 1)
        output_band.WriteArray(array[:, :, idx_band])
        '''
        not working with a 2d array.
        this is what np.atleast_3d(array)
        was for
        '''
        output_band.FlushCache()

    del output_band

    return output_data_set
