import ee,re

def Route2Roi(TC_shp,buffer_width):
    """
    Converts a tropical cyclone path to a region of interest (ROI) with a specified buffer width.

    Args:
        TC_shp (ee.FeatureCollection): The tropical cyclone path as a shapefile feature collection.
        buffer_width (int or float): The buffer distance to apply around the TC path.
    
    Returns:
        ee.Geometry: The buffered region of interest.
    """
    roi = TC_shp.geometry().buffer(ee.Number(buffer_width));
    return roi

def potential_flood(start_date,end_date,roi):
    """
    Extracts potential flood inundation areas based on cumulative rainfall over a specified period.

    Args:
        start_date (ee.Date): The start date for the analysis period.
        end_date (ee.Date): The end date for the analysis period.
        roi (ee.Geometry): The region of interest for flood detection.
    
    Returns:
        ee.FeatureCollection: A feature collection representing potential flood areas.
    """
    rainFall_duration = end_date.difference(start_date,'day');
    precipitation_threshold = ee.Number(rainFall_duration).multiply(ee.Number(50)); 
    # Import GPM data and accumulate total precipitation over the specified date range
    GPM = ee.ImageCollection("NASA/GPM_L3/IMERG_V06").filterDate(start_date,end_date).select('precipitationCal').filterBounds(roi)
    total_precipitation = GPM.sum()
    # Convert high precipitation areas to vectors
    potential_flood_area = total_precipitation.gt(precipitation_threshold)\
        .reduceToVectors(geometry=roi,labelProperty='label',maxPixels=10000000,crs='EPSG:4326',scale=10000)\
        .filterMetadata(name='label',operator='equals',value=1)
    return potential_flood_area


def otsu1(histogram):
    """
    Applies the OTSU method to an image to determine the threshold for flood detection.
    """
    # Get the frequency of each group
    counts = ee.Array(ee.Dictionary(histogram).get('histogram'))
    # Get the value of each group
    means = ee.Array(ee.Dictionary(histogram).get('bucketMeans'))
    # Get the number of groups
    size = means.length().get([0])
    # Get the total number of pixels
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    # Get the sum of all pixel values
    sum = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    # Get the mean value of the entire image
    mean = sum.divide(total)
    # Get an index with the same length as the number of groups
    indices = ee.List.sequence(1, size)
    def func_fok (i):
        # When i=1, aCounts =[counts[0]], when i=2, aCounts = [counts[0], counts[1]]
        # Split into two categories A and B at i and calculate the variance of A
        aCounts = counts.slice(0, 0, i) 
        aCount = aCounts.reduce(ee.Reducer.sum(), [0]).get([0])
        aMeans = means.slice(0, 0, i)
        # Mean value of category A
        aMean = aMeans.multiply(aCounts) \
            .reduce(ee.Reducer.sum(), [0]).get([0]) \
            .divide(aCount)
        
        bCount = total.subtract(aCount)
        # Mean value of category B
        bMean = sum.subtract(aCount.multiply(aMean)).divide(bCount)
        # Inter-class variance
        return aCount.multiply(aMean.subtract(mean).pow(2)).add(
            bCount.multiply(bMean.subtract(mean).pow(2)))
    bss = indices.map(func_fok)
    return means.sort(bss).get([-1])
    # print('variance', ee.ui.Chart.array.values(ee.Array(bss), 0, means))

def otsu(image,roi):
    """
    Applies the OTSU method to an image to determine the threshold for flood detection.
    """
    histogram = image.reduceRegion(
        reducer = ee.Reducer.histogram(10000, 0.01),   # Modify the maximum number of groups and the minimum group spacing as appropriate
        geometry = roi,
        scale = 30,
        bestEffort = True,)
    # print("distribution", histogram)
    return otsu1(histogram.get(histogram.keys().get(0)))


def final_mask (image):
    """
    Applies the final mask to an image to remove non-water areas, based on terrain slope.

    Args:
        image (ee.Image): The image to mask.
    
    Returns:
        ee.Image: The masked image.
    """
    AlosDEM = ee.Image('JAXA/ALOS/AW3D30_V1_1');
    slope = ee.Terrain.slope(AlosDEM);
    # Flooding is not considered to occur on slopes greater than 5 degrees
    image = image.updateMask(slope.lt(5)); 
    return image

def parse_TC_path(TC_path):
    """
    Parses the tropical cyclone path file to extract TC ID, name, and date range.

    Args:
        TC_path (str): The file path of the tropical cyclone data.
    
    Returns:
        dict: A dictionary containing the TC ID, name, start date, and end date.
    """
    # Input the path of the tropical cyclone file
    # Parse the TC ID and name
    TC_ID = TC_path.split('.')[0].split("_")[0];
    TC_name = TC_path.split('.')[0].split("_")[1];
    # Parse the start and end dates
    daterange = re.findall('\d{8}',TC_path,re.S)  # Parse the start and end dates
    start_date = daterange[0];
    start_date = start_date[0:4] + '-' + start_date[4:6] + '-' + start_date[6:9]
    end_date = daterange[1];
    end_date = end_date[0:4] + '-' + end_date[4:6] + '-' + end_date[6:9]
    year = ee.Date(start_date).get('year')  # The year in which the TC occurred
    # Output the start and end dates
    print('Start date:',start_date, 'End date:',end_date);
    # Write to a dictionary
    TC_information = {
        'TC_ID':TC_ID,
        'TC_name':TC_name,
        'start_date':start_date,
        'end_date':end_date,
    }
    return TC_information


# JRC Yearly Water Classification History global water dataset
def get_JRC_water(year,roi):
    """
    Retrieves the global water dataset from the JRC Yearly Water Classification History for a given year.

    Args:
        year (int): The year for which to retrieve the water classification.
        roi (ee.Geometry): The region of interest.
    
    Returns:
        ee.Image: An image representing the permanent water classification for the specified year.
    """
    jrc_perm = JRC = ee.Image(ee.ImageCollection("JRC/GSW1_4/YearlyHistory").filterMetadata('year','equals',year).first())\
                        .remap([0,1,2,3],[0,0,0,1]).unmask()\
                        .select(['remapped'],['jrc_perm_yearly']);
    return jrc_perm.clip(roi)

# Save image to Google Earth Engine Asset
def to_asset(save_asset,flood_img,bounds,res=250):
    """
    Saves an image to Google Earth Engine Asset.

    Args:
        save_asset (str): The asset ID where the image will be saved.
        flood_img (ee.Image): The image to save.
        bounds (ee.Geometry): The region bounds where the image is located.
        res (int): The resolution at which to save the image.
    """
    task = ee.batch.Export.image.toAsset(
        image=flood_img,
        description='ExportToAsset TC Flood'+ str(save_asset.split('/')[-1]),
        assetId=save_asset,
        region = bounds.getInfo()['coordinates'],
        scale =res,
        maxPixels=1e12)
    task.start()
    return
