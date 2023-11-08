import ee,geemap,time,os,re
from Public_methods import Route2Roi,potential_flood,parse_TC_path,to_asset,get_JRC_water
from GEE_python_Flood_extract_Li.Sentinel1_extract_method import S1_water_extract
from GEE_python_Flood_extract_Li.Sentinel2_extract_method import S2_water_extract
from GEE_python_Flood_extract_Li.modis_extract_method import modis_main 
def ee_init():
    #账户验证
    # ee.Authenticate()
    ee.Initialize();
    #设置网路代理端口
    geemap.set_proxy(port=7890);

#Combine the results extracted from different satellites
def water_extract_from_satellites(start_date,end_date,potential_flood_area):
    #依次采用不同卫星数据进行计算
    #Sentinel-1提取
    try:
        Sentinel1_water = S1_water_extract(start_date,end_date,potential_flood_area).unmask();
        time.sleep(2);
    except:
        Sentinel1_water = None;
        print('NO Sentinel-1 images')
    
    #Sentinel-2提取
    try:
        Sentinel2_water = S2_water_extract(start_date,end_date,potential_flood_area).unmask();
        time.sleep(2);
    except:
        Sentinel2_water =None;
        print('NO Sentinel-2 images')
    
    #Modis提取
    try:
        modis_water = modis_main(start_date,end_date,potential_flood_area);
        time.sleep(2);
    except:
        modis_water=None;
        print('no Modis images')

    #将所有图像组合
    if modis_water:
        satellite_water_detect = modis_water
    if Sentinel1_water:
        satellite_water_detect = satellite_water_detect.addBands([Sentinel1_water])
    if Sentinel2_water:
        satellite_water_detect = satellite_water_detect.addBands([Sentinel2_water])
    #将所有检测到的水体相加
    total_water_detect = satellite_water_detect.reduce(ee.Reducer.sum())\
                                                .select(['sum'],['All_water_detect']);


    return satellite_water_detect.addBands([total_water_detect])

def TC_flood(TargetDir,TC_file,radius):
    #load the local shpfile of TC
    TC_shp = geemap.shp_to_ee(TargetDir+'/'+TC_file);

    # parse the TC information from the name of TC_file
    TC_info=parse_TC_path(TC_file);
    start_date=ee.Date(TC_info.get('start_date'));
    end_date = ee.Date(TC_info.get('end_date'));
    year = ee.Date(start_date).get('year') 

    # Determin the TC influenece ranges based on the radius
    roi = Route2Roi(TC_shp,radius);  #radius

    #Identify potential flood areas based on the precipitation furing typhoons
    #根据中国气象局标准，单日降水超过50mm即认为暴雨
    #此处认为持续时间内日平均降雨超过暴雨量即可能发生洪水
    potential_flood_area = potential_flood(start_date,end_date,roi); 

    #根据不同卫星数据进行提取,将卫星提取的数据组合为同一image的不同波段
    #The maximum water range during the typhoon is extracted according to difference satellites
    #Return an Image with the results of different satellites for each band
    Satellit_water_detect = water_extract_from_satellites(start_date,end_date,potential_flood_area);
    
    #The JRC annual water body was used as the pre-disaster water body range
    JRC_Permanent_water = get_JRC_water(year,potential_flood_area);
    #将所有数据添加至同一image
    ALL_water_combine = ee.Image(Satellit_water_detect).addBands([JRC_Permanent_water])\
                            .set(TC_info);
    
    #Save the image to Google Earth Engine's Assets
    asset_path = 'projects/ee-mypython/assets/'  
    save_name = TC_info.get('TC_ID')+TC_info.get('TC_name');  
    save_asset = str(asset_path+save_name);    
    to_asset(save_asset,ALL_water_combine,roi,250);

    print('The ',TC_file,'has been extracted ');

    return ALL_water_combine
