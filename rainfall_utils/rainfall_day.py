import geemap 
import sys
geemap.set_proxy(port=7890)
geemap.ee_initialize()
from rainfall_utils.rainfall_event import RainfallEvent
from rainfall_utils.rainfall_toolbox import convert_ee_date_to_py_date

class RainfallDay(RainfallEvent):
    """
    A class that represents a single day's rainfall event, extending the functionality
    of the RainfallEvent class to handle daily rainfall data.
    """
    def __init__(self, date, roi, bbox, threshold, folder_path, resolution, time_list,event_id):
        """
        Initializes a RainfallDay object with the specified parameters for a single day.
        
        Inherits from RainfallEvent and sets the start and end dates to the same day.
        """
        start_date = date
        end_date = start_date.advance(1, 'day') # End date is the start date plus one day
        super().__init__(start_date=start_date, end_date=end_date, roi=roi, bbox=bbox,
                         threshold=threshold, folder_path=folder_path,
                         resolution=resolution, time_list=time_list)
        self.event_id = event_id # Unique identifier for the event


    def generate_rainfall(self):
        """
        Generates rainfall data for a single day by calling methods from the parent class.
        
        Overrides the generate_rainfall method of RainfallEvent to include DayID.
        """
        try:
            # Call the individual methods from RainfallEvent to generate the maps
            max_precipitation_map_path = self.calculate_max_precipitation()
            total_precipitation_map_path, total_precipitation = self.calculate_total_precipitation()
            max_intensity_precipitation_map_path = self.calculate_max_intensity_precipitation()
            cumulative_precipitation_paths, cumulative_values = self.calculate_cumulative_precipitation(
                time_resolution=30,
                time_list= self.time_list
            )
        except Exception as e:
            # If an error occurs, print the error and exit with status code 1
            print(f"Error generating rainfall data: {e}")
            sys.exit(1)  # Create a DayID based on the date

        start_date_py = convert_ee_date_to_py_date(self.start_date)
        DayID = int(f"{start_date_py.strftime('%y%m%d')}")

        # Compile results into a dictionary
        result = {
            'DayID': DayID,
            'EventID': self.event_id,
            'Date': start_date_py,
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
    
    # 重写保存函数
    def to_sql(self, connection):
        """
        Saves the generated rainfall data for a single day into a SQL database.
        
        Overrides the to_sql method of RainfallEvent to specify the table name for daily data.
        """
        # Use the parent class method to insert data into the 'RainfallDay' table
        super().to_sql(connection, table_name="RainfallDay")
