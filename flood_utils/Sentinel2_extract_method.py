import ee
import geemap
from Public_methods import otsu,final_mask
#定义去云函数
def mask2clouds(image):
    qa = image.select('QA60')
    cloudBitMask = 1<<10
    cirrusBitMask= 1<<11
    mask =qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)
#定义NDWI指数
def cal_NDWI(image):
    NDWI = image.normalizedDifference(['B3','B11']).rename('NDWI')
    NDWI = NDWI.updateMask(NDWI.gt(-1).And(NDWI.lt(1)))
    return image.addBands(NDWI)
def S2_water_extract(start_date,end_date,roi):
    #加载哨兵2数据
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate(start_date,end_date)\
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',10)).map(mask2clouds)\
                  .select('B3','B4','B8','B11','QA60');
    #运行同一天影像
    S2_img = sentinel2.max().clip(roi);
    #计算NDWI指数
    S2_NDWI = cal_NDWI(S2_img).select(['NDWI'],['Sentinel2_water']);
    #OTSU计算阈值
    NDWI_threshold = otsu(S2_NDWI,roi);
    #根据阈值提取水体
    S2_water = S2_NDWI.gt(NDWI_threshold);
    S2_water = final_mask(S2_water);
    return S2_water.unmask()
