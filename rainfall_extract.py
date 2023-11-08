import ee
import geemap
geemap.set_proxy(port=7890)
geemap.ee_initialize()

from rainfall_utils.rainfall_period import RainfallPeriod
from rainfall_utils.rainfall_toolbox import format_db_path,get_bbox

# Set the start and end dates for analysis
start_date = ee.Date('2023-08-20')  # Start date of analysis
end_date = ee.Date('2023-09-10')  # End date of analysis

# Get the feature collection of Shenzhen City
# Use the FAO Global Administrative Unit Layers (2015 simplified version) to filter the data of Shenzhen City
roi = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level2").filter(ee.Filter.eq('ADM2_NAME', 'Shenzhen'))

# Call the get_bbox function to get the bounding box of roi
# This function needs to be defined externally
bbox = get_bbox(roi)

# Set the spatial resolution (unit: meters), which will affect the accuracy of the analysis
resolution = 1000  # Spatial resolution of analysis

# Set the rainfall threshold for judging rainy days
rainy_day_threshold = 5  # Rainfall threshold, unit: mm

# Define the time interval list for cumulative rainfall, unit: minutes
time_list = [30, 60, 120, 240, 480, 960, 1440]

# Set the storage path of intermediate data
folder_path = '../../data/intermediate/Rainfall/'  # Intermediate folder path for storing rainfall data

# Build the database path template
db_path_template = '../../data/intermediate/Rainfall/rainfall_{start_date}_{end_date}.db'

# Format the database path by inserting the start and end dates into the database path template
# Assume that format_db_path is a pre-defined function used to format dates and insert them into the database path template
db_path = format_db_path(start_date, end_date, db_path_template)  # Formatted database path

# Create a RainfallPeriod object
period = RainfallPeriod(
    start_date=start_date,
    end_date=end_date,
    roi=roi,
    bbox=bbox,
    resolution=resolution,
    time_list=time_list,
    rainy_day_threshold=rainy_day_threshold,
    folder_path=folder_path
)

# Judge the rainfall events within the selected time range
rainfall_events_with_details = period.rainfall_list()

# Process rainfall events, download rainfall images, and store event information in the database
period.process_rainfall_events(rainfall_events_with_details,db_path)