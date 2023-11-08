import ee
import geemap
import sys
geemap.set_proxy(port=7890)
geemap.ee_initialize()
from flood_utils.modis_extract_method import modis_main
from flood_utils.flood_toolbox import convert_ee_date_to_py_date,generate_numeric_id

class FloodEvent:
    """
    A class to determine flood events using MODIS satellite data for a given time period and region.
    
    Attributes:
        start_date (ee.Date): Start date of the period to check for flooding.
        end_date (ee.Date): End date of the period to check for flooding.
        roi (ee.Geometry): Region of interest to check for flooding.
        water_area_asset_path (str): Earth Engine asset path for regular water bodies.
        resolution (int): Spatial resolution at which to perform analysis.
        threshold (float): Threshold percentage for determining flood occurrence.
    """
    
    def __init__(self, start_date, end_date, roi, bbox, water_area_asset_path, resolution, threshold,folder_path):
        """
        Initializes a new instance of the FloodEvent class.

        Args:
            start_date (ee.Date): Start date of the period to check for flooding.
            end_date (ee.Date): End date of the period to check for flooding.
            roi (ee.Geometry): Region of interest to check for flooding.
            bbox (list): Bounding box coordinates for the region of interest.
            water_area_asset_path (str): Earth Engine asset path for regular water bodies.
            resolution (int): Spatial resolution at which to perform analysis.
            threshold (float): Threshold percentage for determining flood occurrence.
            folder_path (str): Path to the folder where the flood map will be saved.
        """
        self.start_date = ee.Date(start_date)
        self.end_date = ee.Date(end_date)
        self.roi = roi
        self.bbox = bbox
        self.water_area_asset_path = water_area_asset_path
        self.resolution = resolution
        self.threshold = threshold
        self.folder_path = folder_path

        self.start_date_py = convert_ee_date_to_py_date(self.start_date)
        self.end_date_py = convert_ee_date_to_py_date(self.end_date)
        self.EventID = generate_numeric_id(self.start_date_py,self.end_date_py)
        
        # Load the regular water bodies FeatureCollection
        self.water_area = ee.FeatureCollection(water_area_asset_path)

    def obtain_flood_water(self):
        """
        Retrieve the flood water image by masking out regular water areas from MODIS data.

        Returns:
            ee.Image: The flood water image.
        """
        modis_water = modis_main(self.start_date, self.end_date, self.roi)
        water_mask = self.water_area.reduceToImage(
            properties=['code'], 
            reducer=ee.Reducer.first()
        ).gt(0)
        flood_water = modis_water.where(water_mask, 0)
        return flood_water
    
    def flood_occurrence(self, image):
        """
        Calculate the proportion of flood water pixels in the region of interest.

        Args:
            image (ee.Image): The flood water image.

        Returns:
            ee.Number: The proportion of flood water pixels in the region of interest.
        """
        total_pixels = ee.Number(image.reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=self.roi.geometry(),
            scale=self.resolution
        ).get('Modis_water'))
        
        flood_mask = image.eq(1).selfMask()
        flood_pixels = ee.Number(flood_mask.reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=self.roi.geometry(),
            scale=self.resolution
        ).get('Modis_water'))
        
        flood_proportion = flood_pixels.divide(total_pixels).multiply(100)
        return flood_proportion

    def is_flooding_event(self, image):
        """
        Determine if the flood water proportion exceeds the threshold for a flooding event.

        Args:
            image (ee.Image): The flood water image.

        Returns:
            dict: A dictionary containing the date and whether a flooding event occurred.
        """
        flood_proportion = self.flood_occurrence(image)
        is_flooding = flood_proportion.gt(self.threshold)
        return {
            'date': self.start_date.format('YYYY-MM-dd').getInfo(),
            'is_flooding_event': is_flooding.getInfo()
        }

    def download_flood_map(self, image):
        """
        Download the flood map for a given date.

        Args:
            image (ee.Image): The flood water image.

        Returns:
            str: The path to the downloaded flood map.
        """
        flood_map_path = self.folder_path + f"{self.EventID}_flood_map.tif"
        geemap.ee_export_image(
            image, filename=flood_map_path, scale=self.resolution, region=self.bbox
        )
        return flood_map_path
    
    def generate_flood_water(self):
        """
        Generate the flood water data.

        Returns:
            dict: A dictionary containing the flood event ID, start date, end date, flood extent value, and flood extent map path.
        """
        try:
            # Call the individual methods to generate the maps
            flood_water = self.obtain_flood_water()
            flood_occurrence = self.flood_occurrence(flood_water).getInfo()
            flood_map_path = self.download_flood_map(flood_water)
        except Exception as e:
            print(f"Error generating rainfall data: {e}")
            sys.exit(1)  # Non-zero exit codes usually indicate that the program encountered an error

        # Compile results into a dictionary
        result = {
            'EventID': self.EventID,
            'StartDate': self.start_date_py,
            'EndDate': self.end_date_py,
            'FloodExtentValue':flood_occurrence,
            'FloodExtentMapPath': flood_map_path
        }

        return result

    def to_sql(self, connection, table_name="FloodEvent"):
        """
        Insert the flood event data into a SQL database.

        Args:
            connection (sqlite3.Connection): The connection to the SQL database.
            table_name (str, optional): The name of the table to insert the data into. Defaults to "FloodEvent".
        """
        try:
            # Try to generate the flood data
            data = self.generate_flood_water()
        except Exception as e:
            print(f"Error generating flood data: {e}")
            sys.exit(1)  # Non-zero exit codes usually indicate that the program encountered an error

        # Prepare the column names and corresponding values
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())

        # Create the INSERT INTO statement
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # Execute the SQL command
        connection.execute(sql, values)