import ee,time
from flood_utils import modis_toolbox
from flood_utils.Public_methods import otsu,final_mask

def modis_water_detection(modis_collection, thresh_b1b2, thresh_b7,base_res):
    """
    Detects water bodies in MODIS satellite images based on given thresholds for band ratios and reflectance.
    
    Args:
        modis_collection (ee.ImageCollection): The MODIS image collection to process.
        thresh_b1b2 (float): The threshold for the ratio of band 1 to band 2.
        thresh_b7 (float): The threshold for band 7 reflectance.
        base_res (float): The base resolution for the analysis.
    
    Returns:
        ee.ImageCollection: An image collection with water detection flags.
    """
    def water_flag(img):
        # Apply thresholds to each ratio/ band
        b1b2_ratio = ee.Image(img.select('b1b2_ratio'))
        b1b2_sliced = b1b2_ratio.lt(ee.Image.constant(thresh_b1b2)) # Band 1/Band 2
        b1_sliced = img.select(["red_250m"],["b1_thresh"])\
                        .lt(ee.Image.constant(2027)) # Band 1 Threshold
        b7_sliced = img.select(["swir"],["b7_thresh"])\
                        .lt(ee.Image.constant(thresh_b7)) # Band 7 Threshold
        # Add all the thresholds to one image and then sum()
        thresholds = b1b2_sliced.addBands(b1_sliced).addBands(b7_sliced)
        thresholds_count = thresholds.reduce(ee.Reducer.sum())
        # Apply water_flage threshold to final image
        water_flag = thresholds_count.gte(ee.Image.constant(3))
        return water_flag.copyProperties(img).set("system:time_start",
                                        img.get("system:time_start"))
    # Apply the 'water_flag' function over the modis collection
    modis_water_collection = modis_collection.map(water_flag)
    return modis_water_collection.set({'threshold_b1b2': round(thresh_b1b2,3),
                                     'threshold_b7': round(thresh_b7,2),
                                     'otsu_sample_res': base_res})


def modis_main(start_date,end_date,roi):
    """
    The main function to execute the water detection process using MODIS data.
    
    Args:
        start_date (ee.Date): The start date for the analysis period.
        end_date (ee.Date): The end date for the analysis period.
        roi (ee.Geometry): The region of interest for water detection.
    
    Returns:
        ee.Image: An image representing detected water bodies or a constant image in case of failure.
    """
    try:
        # Clip the range
        date_range = ee.DateRange(start_date.advance(-2,"day"),
                                end_date.advance(3,"day"))
        # Collect Terra and Aqua satellite data
        terra = modis_toolbox.get_terra(roi, date_range)
        aqua = modis_toolbox.get_aqua(roi, date_range)
        # Apply Pan-sharpen function to Terra and Auqa data
        terra_sharp = terra.map(modis_toolbox.pan_sharpen)
        aqua_sharp = aqua.map(modis_toolbox.pan_sharpen)
        # Add NIR/RED ratio to the images band
        terra_ratio = terra_sharp.map(modis_toolbox.b1b2_ratio)
        aqua_ratio = aqua_sharp.map(modis_toolbox.b1b2_ratio)
        # Apply QA Band Extract to Terra & Aqua
        terra_final = terra_ratio.map(modis_toolbox.add_qa_bands)
        aqua_final = aqua_ratio.map(modis_toolbox.add_qa_bands)
        # Finally, combine Terra and Aqua into the same image collection
        modis = ee.ImageCollection(terra_final.merge(aqua_final).sort("system:time_start", True))
        time.sleep(2)
        # Mask the image before OSTU extraction to exclude interference
        modis_masked = modis.map(modis_toolbox.qa_mask)
        sample_frame = modis_masked.median().clip(roi)
        # Otsu histrograms require a "bi-modal histogram". We need to constrain
        # the reflectance range that can be used in the histogram as it may
        # include high-reflectance features (e.g. missed clouds) that will make
        # the histogram "multi-modal". Below are the steps to constrain the
        # histograms into a reasonable range that one might expect water/ land
        swir_mask = sample_frame.select("swir").gt(-500)\
                    .And(sample_frame.select("swir").lt(3000))
        cleaned_swir = sample_frame.select("swir").updateMask(swir_mask)

        # Merge all masks into the final sample image
        sample_img = sample_frame.addBands(cleaned_swir, overwrite=True)
        base_res = ee.Image(modis.first()).select("red_250m").projection().nominalScale().multiply(1).getInfo();
        base_res = round(base_res,2)
        # Apply otsu method to extract thresholds respectively
        b1b2_thresh = otsu(sample_img.select("b1b2_ratio"),roi)
        time.sleep(1)
        swir_thresh = otsu(sample_img.select("swir"),roi)
        time.sleep(1)
        # Store each threshold in a dictionary
        thresh_dict = {'b1b2': b1b2_thresh.getInfo(),
                    'b7': swir_thresh.getInfo(),
                    'base_res':base_res}
        # Extract water bodies based on b1b2_ratio, b1 and b7 thresholds
        modis_water_collection = modis_water_detection(modis, thresh_dict["b1b2"],thresh_dict["b7"],thresh_dict["base_res"])
        time.sleep(1)
        # Combine all images into one image
        modis_water = modis_water_collection.mosaic().select(['sum'],['Modis_water']).clip(roi)
        modis_water = final_mask(modis_water)
        return modis_water.unmask()
    except Exception as e:
        print("No image during this period")  
        zero_image = ee.Image.constant(999).clip(roi).rename('Modis_water')
        return zero_image
