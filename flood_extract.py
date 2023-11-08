import ee
import geemap
geemap.set_proxy(port=7890)
geemap.ee_initialize()
from flood_utils.flood_period import FloodPeriod
from flood_utils.flood_toolbox import format_db_path,get_bbox


# Set the start and end dates for analysis
start_date = ee.Date('2022-04-01')  # Start date of analysis
end_date = ee.Date('2022-04-03')  # End date of analysis

# Get the feature collection of Shenzhen
# Use the FAO global administrative unit layer (2015 simplified version) to filter Shenzhen's data
roi = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level2").filter(ee.Filter.eq('ADM2_NAME', 'Shenzhen'))

# Call the get_bbox function to get the bounding box of roi
# This function needs to be defined externally
bbox = get_bbox(roi)

# The Google Earth Engine project asset path where the water area analysis results will be saved
water_area_asset_path = 'projects/ee-axu229483572/assets/shenzhen_water_area'

# Set the resolution (unit: meters), which will affect the accuracy of the analysis
resolution = 1000  # Spatial resolution of analysis

# Set the threshold for water detection, which is used to distinguish between water and non-water areas
threshold = 2  # Water detection threshold

# The path where the data is stored temporarily
folder_path = '../../data/intermediate/Flood/'  # Folder path for storing intermediate data of flood analysis

# Database path template, used to format and save the path of data
db_path_template = '../../data/intermediate/Flood/flood_{start_date}_{end_date}.db'

# Format the database path by inserting the start and end dates
# Here, format_db_path is assumed to be a pre-defined function that formats the date and inserts it into the database path template
db_path = format_db_path(start_date, end_date, db_path_template)  # Formatted database path

# Create a FloodPeriod object
period = FloodPeriod(start_date,end_date,roi,bbox,water_area_asset_path,resolution,threshold,folder_path)

# Determine the flood events within the selected time range
flood_events_with_details = period.flood_list()

# Process the flood events, download flood images, and store event information in the database
period.process_flood_events(flood_events_with_details,db_path)