import logging
import os
from fnmatch import fnmatch

import numpy as np

from osgeo import gdal

logger = logging.getLogger('FILE MANAGEMENT')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s (%(levelname)s) %(name)s(l%(lineno)d): %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)


def list_files(pattern=['*'], directory=None, extension='tif', subfolder=False):
    """
    Function to list files in a directory with a specific extension. files can be filtered with a pattern.
    without any arguments, the function will list all .tif files in the current directory.

    Args:
        pattern (list[str], optional): Pattern (unix style) of the files to search. If not provided will search all .extension files
        directory (str, optional): Directory path to search in, if not provided the current working directory is used.
        extension (str, optional): Extension of the files to search. default extension is 'tif'.
        subfolder (bool, optional): If True, search in subdirectories.

    Returns:
        list: List of found files (with theire full path).

    Exception:
        On any errors return an empty list.

    Examples:
        List all '.tif' files in the current directory and its subdirectories.
        >>> files = list_files(subfolder=True)

        List all 'FRE_B8.jpg' and 'FRE_B6.jpg' files in the current directory.
        >>> files = list_files(pattern=['FRE_B8', 'FRE_B6'], extension='jpg')

        List all '*_L2A_*_FRE_B8.tif' and '*T31TCJ_*_ATB_R?.tif' files in the current directory.
        >>> files = list_files(pattern=['*_L2A_*_FRE_B8', '*T31TCJ_*_ATB_R?'])
    """
    try:
        images = []

        if not directory:
            directory = os.getcwd()

        for dirpath, dirnames, files in os.walk(directory):
            for name in files:
                for pat in pattern:
                    if extension and name.lower().endswith(extension) and fnmatch(name, f"{pat}.{extension}"):
                        abspath = os.path.abspath(os.path.join(dirpath, name))
                        images.append(abspath)
            if not subfolder:
                break

        logger.debug(f"{len(images)} image(s) found that match {pattern} .{extension} pattern in {directory}")

        images.sort()
        return images

    except Exception as e:
        print(f'error while getting files: {e}')
        return []


def search_B4_B8(input_directory, img_format, subfolder=True):
    """
    Find the B4 and B8 bands images in the input directory and depending on the image format.

    Args:
        input_directory (str): the directory path in which looking for.
        img_format (str): Images formats. It can be: S2-2A-ESA, S2-2A, S2-3A.
        subfolder (bool, optional): If True, search in subdirectories. Default is True

    Returns:
        dict: a dictionary that contains absolute paths of files.
            - 'B4' : List of B4 band files.
            - 'B8' : List of B8 band files.
            - 'cloud_masks' : list of cloud mask.
            - 'format' : Images's format.
    """

    res = {'B4': [], 'B8': [], 'cloud_masks': [], 'format': img_format}

    logger.debug(f"searching B4 and B8 bands in {input_directory} with format {img_format}")

    if img_format == "S2-2A-ESA":
        logger.info("looking for S2-2A-ESA files")
        res['B4'] = list_files(pattern=['*10m*B04*'], directory=input_directory, extension='jp2', subfolder=subfolder)
        res['B8'] = list_files(pattern=['*10m*B08*'], directory=input_directory, extension='jp2', subfolder=subfolder)
        res['cloud_masks'] = list_files(pattern=['*20m*CLD*'], directory=input_directory, extension='jp2', subfolder=subfolder)

    # search bands in S2-Thiea folders
    elif img_format == "S2-2A":
        logger.info("looking for S2-2A files")
        res['B4'] = list_files(pattern=['SENTINEL2*_FRE_B4'], directory=input_directory, extension='tif', subfolder=subfolder)
        res['B8'] = list_files(pattern=['SENTINEL2*_FRE_B8'], directory=input_directory, extension='tif', subfolder=subfolder)
        res['cloud_masks'] = list_files(pattern=['SENTINEL2*_CLM_R1'], directory=input_directory, extension='tif', subfolder=subfolder)

    # search bands in S2-Thiea syntheses folders
    elif img_format == "S2-3A":
        logger.info("looking for S2-3A files")
        res['B4'] = list_files(pattern=['SENTINEL2*_FRC_B4'], directory=input_directory, extension='tif', subfolder=subfolder)
        res['B8'] = list_files(pattern=['SENTINEL2*_FRC_B8'], directory=input_directory, extension='tif', subfolder=subfolder)
        res['cloud_masks'] = list_files(pattern=['SENTINEL2*_FLG_R1'], directory=input_directory, extension='tif', subfolder=subfolder)

    else:
        logger.warning("S2 format not recognized!")

    logger.debug(f"B4 and B8 files found : {res}")

    return res


def generate_output_file_name(file, format, prefix='', prefix2='', suffix=''):
    """
    Generates the output file name based on : the input file name, provided format, prefixes, and suffix.

    Args:
        file (str): The input file name from which is generated the output name (with path or not).
        format (str): The format of the input file. Can be "S2-2A-ESA", "S2-2A" or "S2-3A".
        prefix (str, optional): The prefix to add to the output file name. Defaults to ''.
        prefix2 (str, optional): A second prefix to add to the output file name. Defaults to ''.
        suffix (str, optional): The suffix to add to the output file name. Defaults to ''.

    Returns:
        str: The output file name. If format is not found return filename with .no_format extension.

    Exception:
        On any errors, the function returns the input file name with ".error" extension.

    Examples:
        >>> generate_output_file_name('/var/data/SENTINEL2A_20231012-105856-398_L2A_T31TCJ_D_V3-1.tif', format='S2-A2', prefix='NDVI')
        will return NDVI_T31TCJ_20231012T105856.tif

        >>> generate_output_file_name('/var/data/SENTINEL2A_20231012-105856-398_L2A_T31TCJ_D_V3-1.tif', format='S2-A2', prefix='NDVI', prefix2='prefix2', suffix='suffix')
        will return NDVI_prefix2_T31TCJ_20231012T105856_suffix.tif

        >>> generate_output_file_name('/var/data/SENTINEL2A_20231012-105856-398_L2A_T31TCJ_D_V3-1.tif', format='unknown', prefix='NDVI')
        will return SENTINEL2A_20231012-105856-398_L2A_T31TCJ_D_V3-1.tif.no_format
    """
    try:
        file = os.path.basename(file)
        extension = os.path.splitext(file)[1]
        splitname = file.split('_')

        if prefix:
            prefix = f"{prefix}_"
        if prefix2:
            prefix2 = f"{prefix2}_"
        if suffix:
            suffix = f"_{suffix}"

        if format in ["S2-2A-ESA"]:
            outfile = prefix + prefix2 + splitname[0] + '_' + splitname[1] + suffix + extension  # index name if format esa
        elif format in ["S2-2A", "S2-3A"]:
            outfile = prefix + prefix2 + splitname[3] + '_' + splitname[1].split('-')[0] + 'T' + splitname[1].split('-')[1] + suffix + extension  # index name if format thiea
        else:
            outfile = f"{os.path.splitext(file)[0]}.no_format{os.path.splitext(file)[1]}"
            logger.warning(f"format not found, generated output file as {outfile}")

    except Exception as e:
        outfile = f"{os.path.splitext(file)[0]}.error{os.path.splitext(file)[1]}"
        logger.error(f"error while formatting output filename : {e}")
        logger.error(f"generated output file as {outfile}")

    return outfile




####################################################################
####   LEGACY CODE TO BE DELETED IF NO lONGER BE USED    ###########
####################################################################
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


def search_files_legacy(directory='.', extension='jp2', resolution='10m', band='B04'):
    images = []
    extension = extension.lower()
    resolution = resolution.lower()
    band = band.upper()

    for dirpath, dirnames, files in os.walk(directory):

        for name in files:
            if extension and name.lower().endswith(extension) and name.lower().find(
                    resolution) >= 0 and name.upper().find(band) >= 0:
                abspath = os.path.abspath(os.path.join(dirpath, name))
                images.append(abspath)

    print(str(len(images)) + " image(s) found")
    return images


def list_files_legacy(si_folder, suffix_in_si):

    lst_si = []
    for f in os.listdir(si_folder):
        for i in range(len(suffix_in_si)):
            if fnmatch(f, "*{}".format(suffix_in_si[i])):
                lst_si.append(f)
    lst_si.sort()
    print(len(lst_si))
    return lst_si
