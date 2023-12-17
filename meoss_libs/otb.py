import otbApplication


# TODO: MAYBE BETTER TO USE CLASS INSTEAD OF FUNCTION. NEED MORE USE CASES TO DECIDE.
#       following of use of "manage no data maybe" a better choice


# TODO add logger and Exception error management


def superimpose_otb(cloud_mask_img, nir_band_img, output_file, interpolator='nn', out_pixel_type=otbApplication.ImagePixelType_int16 , ram=4000):
    """
    wrap the otb Superimpose application to be  used in python as a single function

    Args:
        cloud_mask_img:
        nir_band_img:
        interpolator:
        output_file:
        out_pixel_type:
        ram:

    Returns:
        app: otbApplication object

    """
    app = otbApplication.Registry.CreateApplication("Superimpose")
    app.SetParameterString("inm", cloud_mask_img)  # image to reproject
    app.SetParameterString("inr", nir_band_img)  # image to reference
    app.SetParameterString("out", output_file)
    app.SetParameterOutputImagePixelType("out", out_pixel_type )
    app.SetParameterString("interpolator", interpolator)
    app.SetParameterInt("ram", ram)
    app.Execute()

    return app


def bandmath_otb(il=[], il_object=[] , output_file='temp1.tif', exp='', ram=4000):
    """
    wrap the otb BandMath application to be  used in python as a single function

    Args:
        il:
        il_object:
        output_file:
        exp:
        ram:

    Returns:
        app: otbApplication object

    """
    app = otbApplication.Registry.CreateApplication("BandMath")

    for img in il:
        app.AddParameterStringList("il", img)
    for img in il_object:
        app.AddImageToParameterInputImageList("il", img)

    app.SetParameterString("out", output_file)
    app.SetParameterString("exp", exp)
    app.SetParameterInt("ram", ram)
    app.Execute()

    return app


def managenodata_otb(input_image,action, output_image, out_pixel_type=otbApplication.ImagePixelType_int16,  mode='changevalue'):
    """
    wrap the otb ManageNoData application to be  used in python as a single function

    Args:
        input_image:
        action: action to be performed by the application. can be 'exe' or 'write&exe'.
        output_image:
        out_pixel_type: default to otbApplication.ImagePixelType_int16
        mode:  default to 'changevalue'

    Returns:
        app: otbApplication object

    """

    app = otbApplication.Registry.CreateApplication("ManageNoData")
    app.SetParameterInputImage("in", input_image)
    app.SetParameterString("out", output_image)
    app.SetParameterOutputImagePixelType("out", out_pixel_type)
    app.SetParameterString("mode", mode)

    if action == 'exe':
        app.Execute()
    elif action == 'write&exe':
        app.ExecuteAndWriteOutput()

    return app


def extract_ROI_otb(input_file, shape_file, output_file, out_pixel_type=otbApplication.ImagePixelType_int16, mode='fit', ram=1000):
    """
    wrap the otb ExtractROI application to be  used in python as a single function

    Args:
        input_file:
        shape_file:
        output_file:
        out_pixel_type:
        mode:
        ram:

    Returns:
        app: otbApplication object

    """
    app = otbApplication.Registry.CreateApplication("ExtractROI")
    app.SetParameterInputImage("in", input_file)
    app.SetParameterString("mode", mode)
    app.SetParameterString("mode.fit.vect", shape_file)
    app.SetParameterString("out", f"{output_file}?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")
    app.SetParameterOutputImagePixelType("out", out_pixel_type)
    app.SetParameterInt("ram", ram)
    app.ExecuteAndWriteOutput()

    return app


def radiometric_indices_otb(input_file, output_file , nir_band_nb=1, red_band_nb=1, radiometric_indices=['Vegetation:NDVI']):
    """
    wrap the otb RadiometricIndices application to be  used in python as a single function

    Args:
        input_file: Absolute path to the input image.
        output_file: Asbolute path to the output image.
        nir_band_nb:  NIR channel index.
        red_band_nb: RED channel index.
        radiometric_indices: radiometric indices (check otb documentation for all available indices)

    Returns:
        app: otbApplication object

    """
    app = otbApplication.Registry.CreateApplication("RadiometricIndices")

    app.SetParameterString("in", input_file)
    app.SetParameterInt("channels.nir", nir_band_nb)
    app.SetParameterInt("channels.red", red_band_nb)
    app.SetParameterStringList("list", radiometric_indices)
    app.SetParameterString("out", output_file)

    app.ExecuteAndWriteOutput()

    return app