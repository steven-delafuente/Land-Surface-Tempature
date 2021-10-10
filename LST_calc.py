import pandas as pd
import os
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
from rasterio.plot import show
import numpy as np
import math


file_directory = 'Insert appropriate directory containing all Landsat8 Images'

#Use vector layer to clip syudy area from larger Landsat image.
shape = gpd.read_file('Insert Location of approriate mask layer (Vector)')
#study_area = shape[shape['facility']=='study_area']


def calc_BT(TOA,K1_CONSTANT,K2_CONSTANT):
    '''Calculate Brightness Tempature'''
    TOA = TOA
    BT = (K2_CONSTANT/(np.log(K1_CONSTANT/TOA+1)))-273.15
    return BT


dirs = [i for i in os.walk(file_directory)]
dirs = dirs[0][1]


#pre-cliped study area refrence layer. Extract metadata for clipped LST TIFF output. Lat operation in this file.
#There is a cleaner way to do this. 
#Needs revision soon. 
ref_layer = rasterio.open('ref_layer.tif')



for i in dirs:
    with open(os.join(file_directory + '/{}/{}_MTL.txt'.format(i,i))) as f:
        lines = f.readlines()

    with rasterio.open(os.join(file_directory + '/{}/{}_B10.TIF'.format(i,i))) as src:
        Band10, Band10_transform = rasterio.mask.mask(src, study_area.geometry, crop=True)
        Band10_meta = src.meta

    with rasterio.open(os.join(file_directory + '/{}/{}_B4.TIF'.format(i,i))) as src:
        Band04, Band04_transform = rasterio.mask.mask(src, study_area.geometry, crop=True)
        Band04_meta = src.meta
    
    with rasterio.open(os.join(file_directory + '/{}/{}_B5.TIF'.format(i,i))) as src:
        Band05, Band05_transform = rasterio.mask.mask(src, study_area.geometry, crop=True)
        Band05_meta = src.meta

    TOA = 0.0003342 * Band10 + 0.1
    BT = calc_BT(TOA, 774.8853, 1321.0789)
    NDVI = ((Band05 - Band04 )/ ( Band05 + Band04 ))
    PV = ((NDVI - NDVI.min())/(NDVI.max()-NDVI.min()))**2
    E = 0.004 * PV + 0.986
    LST = (BT/(1+(0.00115 * BT/1.4388)*np.log(E)))


    kwargs = ref_layer.meta
    kwargs.update(
        dtype=rasterio.float32,
        count = 1)

    # Output clipped Land Surface Temp TIFF
    with rasterio.open(os.join(file_directory + '/{}/{}_LST.TIF'.format(i,i), 'w', **kwargs)) as dst:
        dst.write(LST.astype(rasterio.float32))
