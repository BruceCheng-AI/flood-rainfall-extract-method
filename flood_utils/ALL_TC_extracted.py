import ee,geemap,os
import Water_extract_main

#Obtain the file endwith '.shp' in the TargetDir
def find_files_EndWith_shp(TargetDir):
    """
    Find all files in the target directory that end with 'shp'.

    Args:
        TargetDir (str): The target directory to search for files.

    Returns:
        list: A list of file names that end with 'shp'.
    """
    all_files = os.listdir(TargetDir);
    TC_filesList = [file for file in all_files if file.endswith('shp')];
    return TC_filesList


if '__name__'=="__mainWater_extract_main.ee_init__":
    #Initializing GEE
    Water_extract_main.ee_init()

    TargetDir = r'E:/多年台风洪水检测/数据/temp/'
    TCs_List = find_files_EndWith_shp(TargetDir);

    # Creat a list to store the results of each typhoon in turn
    TCs_water_lst =[]
    #Process the typhoon in the list one by one
    for TC in TCs_List:
        TC_water = Water_extract_main.TC_flood(TargetDir,TC,2000000);
        TCs_water_lst.append(TC_water);
    
    print('ALL TCs have been extracted successfully')
    #将不同台风组合为一ImageCollection
    # water_collection = ee.ImageCollection.fromImages(TC_water_lst);

