import ee
import geemap 
import sys
geemap.set_proxy(port=7890)
geemap.ee_initialize()
from rainfall_utils.rainfall_toolbox import get_band_name, convert_ee_date_to_py_date,generate_numeric_id

class RainfallEvent:
    """
    A class to handle processing of rainfall events using Google Earth Engine.
    
    Attributes:
        start_date (ee.Date): The start date of the rainfall event.
        end_date (ee.Date): The end date of the rainfall event.
        roi (ee.FeatureCollection): The region of interest.
        bbox (ee.Geometry): The bounding box of the region of interest.
        threshold (float): The threshold value to identify rainy days.
        folder_path (str): Path to the folder where output files will be saved.
        resolution (int): The resolution at which to perform calculations.
        time_list (list): List of time intervals for cumulative rainfall calculations.
        date_range (ee.DateRange): The range between start and end dates.
        start_date_py (datetime): The start date as a Python datetime object.
        end_date_py (datetime): The end date as a Python datetime object.
        EventID (int): A numeric ID generated for the rainfall event.
        dataset (ee.ImageCollection): The dataset used for the rainfall calculations.
        max_precipitation (ee.Image): The maximum precipitation image.
        precipitation (ee.ImageCollection): Collection of precipitation images.
    """
    def __init__(self, start_date, end_date, roi, bbox, threshold, folder_path, resolution,time_list):
        """Initialize the RainfallEvent class with the specified parameters."""
        self.start_date = start_date
        self.end_date = end_date
        self.roi = roi
        self.bbox = bbox
        self.threshold = threshold
        self.folder_path = folder_path
        self.resolution = resolution
        self.time_list = time_list
        self.date_range = ee.DateRange(start_date, end_date)
        self.start_date_py = convert_ee_date_to_py_date(self.start_date)
        self.end_date_py = convert_ee_date_to_py_date(self.end_date)
        self.EventID = generate_numeric_id(self.start_date_py,self.end_date_py)

        # Initialize the dataset with the specified date range and region of interest.
        self.dataset = ee.ImageCollection('NASA/GPM_L3/IMERG_V06').filterDate(self.date_range).filterBounds(self.roi)

        # Calculate the maximum precipitation image and the collection of precipitation images.
        self.max_precipitation = self.dataset.select('precipitationCal').max().clip(self.roi)
        self.precipitation = self.dataset.select('precipitationCal').map(lambda image: image.divide(2).clip(self.roi))

    def calculate_max_precipitation(self):
        """
        Calculates the maximum precipitation within the region of interest (ROI) and exports it to a TIF file.
        
        It creates a mask to identify the pixels with precipitation values greater than the threshold.
        Then it updates the maximum precipitation image to apply this mask and exports the resulting image.

        Returns:
            str: The file path to the exported maximum precipitation map TIF file.
        """
        # Create a mask for values greater than the threshold
        mask = self.max_precipitation.gt(self.threshold)
        # Update the max precipitation image to only include values above the threshold
        max_precipitation_mask = self.max_precipitation.updateMask(mask)
        # Define the path for the output TIF file
        max_precipitation_map_path = self.folder_path + str(self.EventID)  + '_max_precipitation.tif'
        # Export the masked image as a TIF file to the defined path
        geemap.ee_export_image(
            max_precipitation_mask, filename=max_precipitation_map_path, scale=self.resolution, region=self.bbox
        )
        # Return the path to the output TIF file
        return max_precipitation_map_path

    def calculate_total_precipitation(self):
        """
        Calculates the total precipitation over the ROI and exports it as a TIF file.
        
        This method sums the precipitation over all images in the collection to create a total precipitation image.
        Then, it exports this image and also calculates the mean total precipitation over the ROI.

        Returns:
            tuple: A tuple containing the file path to the exported total precipitation map TIF file and the mean total precipitation value.
        """
        # Calculate the total precipitation by summing over the image collection
        total_precipitation = self.precipitation.sum()
        # Export the total precipitation map
        total_precipitation_map_path = self.folder_path + str(self.EventID)  + '_total_rainfall.tif'
        geemap.ee_export_image(
            total_precipitation, filename=total_precipitation_map_path, scale=self.resolution, region=self.bbox
        )
        # Calculate the mean total precipitation over the ROI
        total_precipitation = total_precipitation.reduceRegion(
            reducer=ee.Reducer.mean(), 
            geometry=self.roi, 
            scale=self.resolution
        ).get('precipitationCal').getInfo()
        # Return both the path to the exported map and the mean total precipitation value
        return total_precipitation_map_path, total_precipitation

    def calculate_max_intensity_precipitation(self):
        """
        Calculates the image with the maximum precipitation intensity over the event period and exports it.

        This method calculates the sum of precipitation for each image in the collection, sorts them
        in descending order to find the one with the maximum precipitation intensity, and then exports this image.

        Returns:
            str: The file path to the exported maximum intensity precipitation map TIF file.
        """
        # Sort the images by total precipitation in descending order
        total_precipitation_per_image = self.precipitation.map(lambda img: img.set('total_precipitation_per_image', img.reduceRegion(reducer=ee.Reducer.sum(), geometry=self.roi, scale=11132).get('precipitationCal')))
        # Get the first image from the sorted list, which has the maximum precipitation intensity
        sorted_images = total_precipitation_per_image.sort('total_precipitation_per_image', False)
        # Define the path for the output TIF file
        max_intensity_precipitation = ee.Image(sorted_images.first())
        max_intensity_precipitation_map_path = self.folder_path + str(self.EventID)  + '_max_intensity_rainfall.tif'
        # Export the image with the maximum intensity precipitation to the defined path
        geemap.ee_export_image(
            max_intensity_precipitation, filename=max_intensity_precipitation_map_path, scale=self.resolution, region=self.bbox
        )
        # Return the path to the output TIF file
        return max_intensity_precipitation_map_path
    
    def calculate_cumulative_precipitation(self, time_resolution, time_list):
        """
        Calculates and exports cumulative precipitation maps for specified time intervals.
        
        Args:
            time_resolution (int): The resolution in minutes for the cumulative precipitation calculation.
            time_list (list): A list of time intervals in minutes over which to calculate cumulative precipitation.
        
        Returns:
            tuple: A tuple containing two dictionaries, one with paths to the exported cumulative precipitation maps,
                and another with the calculated cumulative values for each time interval.
        """        
        cumulative_precipitation_paths = {} # Stores the file paths to the exported maps
        cumulative_values = {}  # Stores the calculated cumulative values

        # Function to calculate cumulative sum over a moving window
        def calculate_window_sum(start_index, end_index, image_collection):
            window_collection = ee.ImageCollection(image_collection.toList(end_index.subtract(start_index), start_index))
            return window_collection.reduce(ee.Reducer.sum())

        for time_window in time_list:
            window_size = ee.Number(time_window).divide(time_resolution)

            # Create an ee.List of indices to iterate over
            sequence = ee.List.sequence(0, self.precipitation.size().subtract(window_size))

            # Map over the sequence to calculate the window sum
            cumulative_precipitation_images = sequence.map(lambda start_index: calculate_window_sum(ee.Number(start_index), ee.Number(start_index).add(window_size), self.precipitation))

            # Convert the list of images back to an ImageCollection
            cumulative_precipitation_collection = ee.ImageCollection.fromImages(cumulative_precipitation_images)
            max_cumulative_precipitation = cumulative_precipitation_collection.max()

            # Calculate the mean cumulative value over the ROI
            cumulative_value = max_cumulative_precipitation.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=self.roi,
                scale=self.resolution
            ).get(get_band_name(max_cumulative_precipitation)).getInfo()  # Note: getInfo() is still needed here to get a number

            # Store the cumulative value
            cumulative_values[time_window] = cumulative_value

            # Define the path for the cumulative precipitation map
            cumulative_precipitation_path = self.folder_path + str(self.EventID)  + f'_cumulative_rainfall_{time_window}.tif'

            print(cumulative_precipitation_path)

            # Export the cumulative precipitation map
            geemap.ee_export_image(
                max_cumulative_precipitation, filename=cumulative_precipitation_path, scale=self.resolution, region=self.bbox
            )

            # Store the path to the exported map
            cumulative_precipitation_paths[time_window] = cumulative_precipitation_path

        return cumulative_precipitation_paths, cumulative_values

    def generate_rainfall(self):
        """
        Generates various rainfall metrics and maps including maximum, total, maximum intensity,
        and cumulative rainfall for the event.
        
        Returns:
            dict: A dictionary containing the EventID, date range, total rainfall, paths to the rainfall maps,
                and cumulative rainfall values for specified intervals.
        """
        try:
            # Call the individual methods to generate the maps
            max_precipitation_map_path = self.calculate_max_precipitation()
            total_precipitation_map_path, total_precipitation = self.calculate_total_precipitation()
            max_intensity_precipitation_map_path = self.calculate_max_intensity_precipitation()
            cumulative_precipitation_paths, cumulative_values = self.calculate_cumulative_precipitation(
                time_resolution=30,
                time_list= self.time_list
            )
        except Exception as e:
            print(f"Error generating rainfall data: {e}")
            sys.exit(1)  # 非零退出码通常表示程序遇到了错误            

        # Compile results into a dictionary
        result = {
            'EventID': self.EventID,
            'StartDate': self.start_date_py,
            'EndDate': self.end_date_py,
            'TotalRainfall': total_precipitation,
            'MaxRainfallMapPath': max_precipitation_map_path,
            'TotalRainfallMapPath': total_precipitation_map_path,
            'MaxIntensityRainfallMapPath': max_intensity_precipitation_map_path
        }

        # Add the cumulative values and paths to the result dictionary
        for time_interval in cumulative_values:
            result[f'CumulativeRainfall{time_interval}'] = cumulative_values[time_interval]
            result[f'CumulativeRainfallMapPath{time_interval}'] = cumulative_precipitation_paths[time_interval]

        return result

    def to_sql(self, connection,table_name='RainfallEvent'):
        """
        Generates rainfall data and inserts it into a specified SQL table.

        This method invokes the rainfall data generation process, formats the resulting data,
        and inserts it into a SQL table.

        Args:
            connection: The database connection object to execute SQL commands.
            table_name (str): The name of the table where data will be inserted. Defaults to 'RainfallEvent'.

        If an error occurs during the rainfall data generation, the program will exit with a status code of 1,
        which indicates an error.
        """
        try:
            # Attempt to generate rainfall data
            data = self.generate_rainfall()
        except Exception as e:
            # Print the error message and exit the program if rainfall data generation fails
            print(f"Error generating rainfall data: {e}")
            sys.exit(1)   # A non-zero exit code generally indicates an error
        
         # Prepare the column names and corresponding placeholders for the SQL INSERT statement
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        
        # Create the INSERT INTO statement
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        # Execute the SQL command
        connection.execute(sql, values)
