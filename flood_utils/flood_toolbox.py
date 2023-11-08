from datetime import datetime 
import duckdb
import ee
import os

def convert_ee_date_to_py_date(ee_date):
    """
    Convert a Google Earth Engine date to a Python datetime.date object.
    
    Args:
        ee_date (ee.Date): The Google Earth Engine date object to convert.
    
    Returns:
        datetime.date: The corresponding Python date object.
    """
    # Convert the ee.Date object to a string
    date_str = ee_date.format('YYYY-MM-dd').getInfo()
    
    # Convert the string to a datetime object
    py_datetime = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Return only the date part
    return py_datetime.date()

def generate_numeric_id(start_date, end_date):
    """
    Generates a numeric ID based on the provided start and end dates.
    
    Args:
        start_date (datetime.date): The start date.
        end_date (datetime.date): The end date.
    
    Returns:
        int: The generated numeric ID.
    """
    # Extract the last two digits of the year, month, and day, and concatenate them into a string
    start_str = start_date.strftime('%y%m%d')
    end_str = end_date.strftime('%y%m%d')
    # Return the concatenated string as an integer
    return int(f"{start_str}{end_str}")

def ininialize_database(db_path):
    """
    Initialize a new DuckDB database at the specified path, creating FloodEvent and FloodDay tables.
    
    Args:
        db_path (str): The path where the database file will be located.
    
    Returns:
        None
    """
    # Check if the database file already exists at the path
    if os.path.exists(db_path):
        # If it exists, remove the database file
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")

    # Create SQL commands for creating the FloodEvent table
    create_flood_event_sql = """
        CREATE TABLE IF NOT EXISTS FloodEvent (
            EventID BIGINT PRIMARY KEY,
            StartDate DATE,
            EndDate DATE,
            FloodExtentValue FLOAT,
            FloodExtentMapPath VARCHAR
    )
    """

    # Create SQL commands for creating the FloodDay table
    create_flood_day_sql = """
        CREATE TABLE IF NOT EXISTS FloodDay (
            DayID INTEGER PRIMARY KEY,
            EventID BIGINT,
            Date DATE,
            FloodExtentValue FLOAT,
            FloodExtentMapPath VARCHAR,
            FOREIGN KEY(EventID) REFERENCES FloodEvent(EventID)
    )
    """

    # Connect to DuckDB
    con = duckdb.connect(db_path)

    # Execute the SQL command for creating the FloodEvent table
    con.execute(create_flood_event_sql)

    # Execute the SQL command for creating the FloodDay table
    con.execute(create_flood_day_sql)

    # Close the database connection
    con.close()
    
    print(f"Database initialized at {db_path}")


def format_db_path(start_date, end_date, folder_path_template):
    """
    Formats the database path using the start and end dates.
    
    Args:
        start_date (ee.Date): The start date.
        end_date (ee.Date): The end date.
        folder_path_template (str): A template string for the folder path that includes placeholders for dates.
    
    Returns:
        str: The formatted database path.
    """
    # Convert the dates to string format for embedding in the file path
    start_date_formatted = start_date.format('YYYYMMdd').getInfo()
    end_date_formatted = end_date.format('YYYYMMdd').getInfo()
    
    # Format the database path with the start and end dates
    db_path = folder_path_template.format(start_date=start_date_formatted, end_date=end_date_formatted)
    
    return db_path

def get_bbox(roi):
    """
    Calculates the bounding box for the given region of interest (ROI).
    
    Args:
        roi (ee.FeatureCollection): The region of interest.
    
    Returns:
        list: The bounding box coordinates in the format [west, south, east, north].
    """
    # Compute the bounding box of the ROI
    roi_bounds = roi.geometry().bounds()

    # Retrieve the coordinates of the bounding box
    bbox = roi_bounds.getInfo()['coordinates'][0]

    # Bounding box coordinates are typically a closed loop, so take the first point (southwest corner) and the diagonal point (northeast corner)
    west, south = bbox[0][:2]
    east, north = bbox[2][:2]

    # Format the coordinates as [west longitude, south latitude, east longitude, north latitude]
    bbox = [west, south, east, north]
    
    return bbox