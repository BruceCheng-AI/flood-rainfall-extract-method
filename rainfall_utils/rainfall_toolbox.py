import ee
from datetime import datetime 
import duckdb

def get_band_name(precipitation):
    """Get the name of the band"""
    band_names = precipitation.bandNames().getInfo()
    return band_names[0]

def get_global_max(precipitation, roi):
    """Calculate the global maximum"""
    band_name = get_band_name(precipitation)
    max_value = precipitation.reduceRegion(
        reducer=ee.Reducer.max(), 
        geometry=roi.geometry(), 
        scale=1000
    ).get(band_name)
    return ee.Number(max_value).getInfo()

def get_global_min(precipitation, roi):
    """Calculate the global minimum"""
    band_name = get_band_name(precipitation)
    min_value = precipitation.reduceRegion(
        reducer=ee.Reducer.min(), 
        geometry=roi.geometry(), 
        scale=100
    ).get(band_name)
    return ee.Number(min_value).getInfo()

def get_vis_params(precipitation, roi):
    """Get visualization parameters"""
    palette = [
        '000096', '0064ff', '00b4ff', '33db80', '9beb4a',
        'ffeb00', 'ffb300', 'ff6400', 'eb1e00', 'af0000'
    ]
    min_value = get_global_min(precipitation, roi)
    max_value = get_global_max(precipitation, roi)
    vis_params = {
        'min': min_value,
        'max': max_value,
        'palette': palette,
        'opacity': 1.0
    }
    return vis_params

def convert_ee_date_to_py_date(ee_date):
    """
    Convert a Google Earth Engine date to a Python datetime.date object.
    
    Parameters:
    ee_date (ee.Date): The Google Earth Engine date object to convert.
    
    Returns:
    datetime.date: The corresponding Python date object.
    """
    # Convert ee.Date object to string
    date_str = ee_date.format('YYYY-MM-dd').getInfo()
    
    # Convert string to datetime object
    py_datetime = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Return the date part
    return py_datetime.date()

def generate_numeric_id(start_date, end_date):
    # Extract the last two digits of the year, month, and day of the date, and concatenate them into a string
    start_str = start_date.strftime('%y%m%d')
    end_str = end_date.strftime('%y%m%d')
    return int(f"{start_str}{end_str}")


def initialize_database(db_path,time_lists):
    """
    Initialize a database with two tables: RainfallEvent and RainfallDay.
    Each table contains cumulative rainfall data for different time intervals.
    The database is created at the specified path.

    Args:
    - db_path (str): The path where the database will be created.
    - time_lists (list): A list of integers representing the time intervals for which cumulative rainfall data will be stored.

    Returns:
    - None
    """
    # Define base fields
    base_fields = {
        'RainfallEvent': [
            "EventID BIGINT PRIMARY KEY",
            "StartDate DATE",
            "EndDate DATE",
            "TotalRainfall FLOAT",
            "MaxRainfallMapPath VARCHAR",
            "TotalRainfallMapPath VARCHAR",
            "MaxIntensityRainfallMapPath VARCHAR"
        ],
        'RainfallDay': [
            "DayID INTEGER PRIMARY KEY",
            "EventID BIGINT",  
            "Date DATE",
            "TotalRainfall FLOAT",
            "MaxRainfallMapPath VARCHAR",
            "TotalRainfallMapPath VARCHAR",
            "MaxIntensityRainfallMapPath VARCHAR"
        ]
    }

    # Build fields for all time intervals
    def build_cumulative_fields(table_name):
        cumulative_fields = [f"CumulativeRainfall{interval} FLOAT" for interval in time_lists]
        map_path_fields = [f"CumulativeRainfallMapPath{interval} VARCHAR" for interval in time_lists]
        return base_fields[table_name] + cumulative_fields + map_path_fields

    # Create SQL command for RainfallEvent table
    rainfall_event_fields = build_cumulative_fields('RainfallEvent')

    # Create SQL command for RainfallDay table
    rainfall_day_fields = build_cumulative_fields('RainfallDay')

    # Define a new line variable to avoid using backslashes in f-strings
    new_line = "\n"

    # Create SQL command for RainfallEvent table
    rainfall_event_sql = f"CREATE TABLE IF NOT EXISTS RainfallEvent ({new_line}    {f',{new_line}    '.join(rainfall_event_fields)}{new_line})"

    # Create SQL command for RainfallDay table
    rainfall_day_sql = f"CREATE TABLE IF NOT EXISTS RainfallDay ({new_line}    {f',{new_line}    '.join(rainfall_day_fields)},{new_line}    FOREIGN KEY(EventID) REFERENCES RainfallEvent(EventID){new_line})"

    # Connect to DuckDB
    con = duckdb.connect(db_path)
    
    # Execute SQL command for creating RainfallEvent table
    con.execute(rainfall_event_sql)

    # Execute SQL command for creating RainfallDay table
    con.execute(rainfall_day_sql)

    # Close database connection
    con.close()

    print(f"Database initialized at {db_path}")

def format_db_path(start_date, end_date, folder_path_template):
    
    # Convert dates to string format for embedding in file path
    start_date_formatted = start_date.format('YYYYMMdd').getInfo()
    end_date_formatted = end_date.format('YYYYMMdd').getInfo()
    
    # Format database path
    db_path = folder_path_template.format(start_date=start_date_formatted, end_date=end_date_formatted)
    
    return db_path

def get_bbox(roi):
    # Calculate the outer boundary
    roi_bounds = roi.geometry().bounds()

    # Get the coordinate information of the boundary
    bbox = roi_bounds.getInfo()['coordinates'][0]

    # The coordinates of the boundary are usually a closed loop, so take the first point (southwest corner) and the diagonal point (northeast corner)
    west, south = bbox[0][:2]
    east, north = bbox[2][:2]

    # Format as [west longitude, south latitude, east longitude, north latitude]
    bbox = [west, south, east, north]
    
    return bbox