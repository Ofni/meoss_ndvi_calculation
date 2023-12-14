#!/usr/bin/python

"""
This code was created by Ghaith AMIN, PhD at CESBIO/MEOSS 
Calculating Normalized Difference Vegetation Index (NDVI) using Sentinel-2
"""

import os
import argparse
import otbApplication



def search_files(directory='.', extension='jp2', resolution='10m', band='B04'):
    images=[]
    extension = extension.lower()      
    resolution = resolution.lower()
    band = band.upper()  
 
    for dirpath, dirnames, files in os.walk(directory): 
                                                       
        for name in files:
            if extension and name.lower().endswith(extension) and name.lower().find(resolution) >= 0 and name.upper().find(band) >= 0: 
                abspath = os.path.abspath(os.path.join(dirpath, name))  
                images.append(abspath)                                 

    print(str(len(images)) + " image(s) found")
    return images

    
def ndvi(argsformat, red, nir, mask, out, shp):  

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
    
    valuemask = "0"            # cloud free value in S2-2A and S2-SEN2COR masks = 0 
    if argsformat == 'S2-3A':
        valuemask = "4"        # cloud free value in S2-3A  = 4 

    app2 = otbApplication.Registry.CreateApplication("BandMath")
    app2.AddImageToParameterInputImageList("il",app1.GetParameterOutputImage("out"))
    app2.AddImageToParameterInputImageList("il", app0.GetParameterOutputImage("out"))
    app2.SetParameterString("out", "temp2.tif")
    app2.SetParameterString("exp", "(im2b1=="+valuemask+")?im1b1:0")
    app2.SetParameterInt("ram",4000)
    app2.Execute()
    
    app3 = otbApplication.Registry.CreateApplication("ManageNoData")
    app3.SetParameterInputImage("in", app2.GetParameterOutputImage("out"))
    app3.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
    app3.SetParameterString("mode", "changevalue")
    # if no shapefile is provided the image will be written, but if yes, then shapefile will be used to clip spectral index then write it
    if shp :
        app3.SetParameterString("out", "temp3.tif")
        app3.Execute() 
        
        print("...................................................................shp =", shp)
        app4 = otbApplication.Registry.CreateApplication("ExtractROI")
        app4.SetParameterInputImage("in", app3.GetParameterOutputImage("out"))
        app4.SetParameterString("mode","fit")
        app4.SetParameterString("mode.fit.vect", shp)
        app4.SetParameterString("out", out+"?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")
        app4.SetParameterOutputImagePixelType("out", otbApplication.ImagePixelType_int16)
        app4.SetParameterInt("ram",1000)
        app4.ExecuteAndWriteOutput()

    else : 
        app3.SetParameterString("out", out+"?gdal:co:COMPRESS=DEFLATE&gdal:co:BIGTIFF=YES")
        app3.SetParameterInt("ram",1000)
        app3.ExecuteAndWriteOutput()     
        

if __name__ == "__main__":
    # Make parser object
    parser = argparse.ArgumentParser(description= """ Compute the Spectral Index NDVI from Sentinel-2 """)
    parser.add_argument('-s2dir', action='store', required=True, help='Directory containing Sentinel-2 L2A ')
    parser.add_argument('-format', choices=['S2-2A','S2-2A-ESA','S2-3A'], required=True, help='Sentinel-2 level : S2-2A = image processed with MAJA, S2-3A = cloud free synthese processed with WASP, S2-2A-ESA = image processed with SEN2COR')
    parser.add_argument('-shpdir', action='store', required=False, help=' [Optional] shapefile (must have same CRS as input image) to clip the output computed index')
    parser.add_argument('-indexdir', action='store', required=True, help='Output directory for computed NDVIs')
    
     
    args=parser.parse_args()
    
    # search bands in S2-ESA folder
    if args.format == "S2-2A-ESA" :
 
        B4=search_files(args.s2dir)
        B8=search_files(args.s2dir,'jp2', resolution='10m', band='B08') 
        cloud_masks=search_files(args.s2dir, 'jp2', resolution='20m', band='CLD')
        print (str(cloud_masks))
        
    # search bands in S2-Thiea folders
    elif args.format == "S2-2A" :
        
        B4=search_files(args.s2dir, 'tif', resolution='SENTINEL2', band='_FRE_B4.tif')
        B8=search_files(args.s2dir, 'tif', resolution='SENTINEL2', band='_FRE_B8.tif') 
        cloud_masks=search_files(args.s2dir, 'tif', resolution='SENTINEL2', band='_CLM_R1.tif')
        print (str(cloud_masks))

    # search bands in S2-Thiea syntheses folders
    elif args.format == "S2-3A" :
        B4=search_files(args.s2dir, 'tif', resolution='SENTINEL2', band='_FRC_B4.tif')
        B8=search_files(args.s2dir, 'tif', resolution='SENTINEL2', band='_FRC_B8.tif')
        cloud_masks=search_files(args.s2dir, 'tif', resolution='SENTINEL2', band='_FLG_R1')  
        
    else:
        print("S2 format not recognized!")
        exit
    
    if not os.path.isdir(args.indexdir):   
        os.mkdir(args.indexdir)
    
    abspathout = os.path.abspath(args.indexdir)

               
    for red, nir, mask in zip (B4, B8, cloud_masks) : 
        splitname = os.path.basename(red).split('_')
        if args.format== "S2-2A-ESA" :
            outfile = "NDVI_"+splitname[0]+"_"+splitname[1]+".TIF" # index name if format esa
        elif args.format== "S2-2A" or args.format== "S2-3A" :
            splitname_2 = splitname[1].split('-')
            outfile = "NDVI_"+splitname[3]+"_"+splitname_2[0]+"T"+splitname_2[1]+".TIF" # index name if format thiea   
        else:
            print("ERROR: "+red)
            continue
      
        absoutfile = os.path.join(abspathout, outfile)
            
        if os.path.exists(absoutfile) : 
            print("######################################################"" index already exist in outdir :", str(absoutfile))
            continue
        
        
        ndvi(args.format, red, nir, mask, absoutfile, args.shpdir)




