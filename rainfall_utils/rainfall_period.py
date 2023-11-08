import ee
from datetime import datetime, timedelta
from rainfall_utils.rainfall_toolbox import initialize_database
from rainfall_utils.rainfall_day import RainfallDay
from rainfall_utils.rainfall_event import RainfallEvent
import duckdb

class RainfallPeriod:
    """
    A class representing a period of time for rainfall analysis.

    Attributes:
        start_date (ee.Date): The start date of the period for analysis.
        end_date (ee.Date): The end date of the period for analysis.
        roi (ee.FeatureCollection): The region of interest for the rainfall analysis.
        bbox (ee.Geometry): The bounding box of the region of interest.
        resolution (int): The resolution at which to perform calculations.
        time_list (list): A list of time intervals for cumulative rainfall calculations.
        rainy_day_threshold (float): The threshold value to identify rainy days.
        folder_path (str): Path to the folder where output files will be saved.
    """

    def __init__(self, start_date, end_date, roi,bbox,resolution,time_list,rainy_day_threshold,folder_path):
        """
        Initializes a RainfallPeriod object with the specified parameters.

        Args:
            start_date (str): The start date of the period for analysis in 'YYYY-MM-DD' format.
            end_date (str): The end date of the period for analysis in 'YYYY-MM-DD' format.
            roi (ee.FeatureCollection): The region of interest for the rainfall analysis.
            bbox (ee.Geometry): The bounding box of the region of interest.
            resolution (int): The resolution at which to perform calculations.
            time_list (list): A list of time intervals for cumulative rainfall calculations.
            rainy_day_threshold (float): The threshold value to identify rainy days.
            folder_path (str): Path to the folder where output files will be saved.
        """
        # Initialize all attributes with the given parameters
        self.start_date = ee.Date(start_date)
        self.end_date = ee.Date(end_date)
        self.roi = roi
        self.bbox = bbox
        self.resolution = resolution
        self.time_list = time_list
        self.rainy_day_threshold = rainy_day_threshold
        self.folder_path = folder_path  

    def is_rainy_day(self, day):
        """
        Determines if a given day is a rainy day.

        Args:
            day (int): The day to check, where 0 is the start date of the period.

        Returns:
            ee.Dictionary: A dictionary containing the date and a boolean indicating if the day is a rainy day.
        """
        date = self.start_date.advance(day, 'day')
        day_range = date.getRange('day')
        dataset = ee.ImageCollection('NASA/GPM_L3/IMERG_V06').filter(ee.Filter.date(day_range)).filterBounds(self.roi)
        precipitation = dataset.select('precipitationCal').max().clip(self.roi)
        
        # Create a binary image where areas with precipitation over the threshold are 1 and others are 0
        is_precipitation_over_threshold = precipitation.gt(self.rainy_day_threshold)
        
        # Calculate the proportion of area over the threshold within the ROI
        over_threshold_ratio = is_precipitation_over_threshold.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=self.roi.geometry(),
            scale=self.resolution
        ).get('precipitationCal')
        
        # Determine if over 50% of the area over the threshold within the ROI
        is_rainy_day = ee.Number(over_threshold_ratio).gt(0.5)
        
        return ee.Dictionary({
            'date': date.format('YYYY-MM-dd'),
            'is_rainy_day': is_rainy_day
        })

    def rainy_days(self):
        """
        Determines the rainy days within the period.

        Returns:
            list: A list of dates in 'YYYY-MM-DD' format that are rainy days.
        """
        n_days = self.end_date.difference(self.start_date, 'day')
        # Use a lambda function to pass self and day as parameters
        weather_days = ee.List.sequence(0, n_days.subtract(1)).map(lambda day: self.is_rainy_day(day))
        weather_days_list = weather_days.getInfo()
        return [day['date'] for day in weather_days_list if day['is_rainy_day'] == 1]

    @staticmethod
    def rainfall_events(rainy_days):
        """
        Determines the rainfall events from a list of rainy days.

        Args:
            rainy_days (list): A list of dates in 'YYYY-MM-DD' format that are rainy days.

        Returns:
            list: A list of dictionaries containing the start date, end date, and list of days for each rainfall event.
        """
        rainy_days_datetime = [datetime.strptime(date, "%Y-%m-%d") for date in rainy_days]
        rainfall_events = []
        start_date = None
        end_date = None
        for date in rainy_days_datetime:
            if start_date is None:
                start_date = date
                end_date = date + timedelta(days=1)
            elif date - end_date == timedelta(days=0):
                end_date = date + timedelta(days=1)
            else:
                rainfall_events.append({'start_date': start_date.strftime("%Y-%m-%d"), 'end_date': end_date.strftime("%Y-%m-%d")})
                start_date = date 
                end_date = date + timedelta(days=1)
        if start_date is not None:
            rainfall_events.append({'start_date': start_date.strftime("%Y-%m-%d"), 'end_date': end_date.strftime("%Y-%m-%d")})
        return rainfall_events

    def rainfall_list(self):
        """
        Determines the list of rainfall events with details.

        Returns:
            list: A list of dictionaries containing the start date, end date, and list of days for each rainfall event.
        """
        rainy_days_list = self.rainy_days()
        rainfall_events_list = self.rainfall_events(rainy_days_list)
        all_events_with_details = []  # Create an empty list to store details for all events

        # Iterate through the event list and create a dictionary with detailed information for each event
        for event in rainfall_events_list:
            start_date = datetime.strptime(event['start_date'], "%Y-%m-%d")
            end_date = datetime.strptime(event['end_date'], "%Y-%m-%d")
            # Only include dates before end_date and after start_date
            event_days = [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]
            event_days_str = [day.strftime("%Y-%m-%d") for day in event_days]

            # Create a dictionary with the desired information
            event_details = {
                'start_date': event['start_date'],
                'end_date': event['end_date'],
                'event_days_str': event_days_str
            }

            # Add the dictionary to the list
            all_events_with_details.append(event_details)

        # Return the list
        return all_events_with_details
    
    def process_rainfall_events(self,rainfall_events_with_details,db_path):
        """
        Processes a series of rainfall events, gets rainfall images, downloads rainfall maps, and stores event information to a database.

        Args:
            rainfall_events_with_details (list): A list containing detailed information for each rainfall event.
            db_path (str): The path to the database where event information will be stored.
        """       
        initialize_database(db_path,self.time_list)
        con = duckdb.connect(database=db_path)

        for rainfall_event in rainfall_events_with_details:
                event = RainfallEvent(
                        start_date=ee.Date(rainfall_event['start_date']),
                        end_date=ee.Date(rainfall_event['end_date']),
                        roi = self.roi, 
                        bbox = self.bbox,  
                        threshold = self.rainy_day_threshold,
                        folder_path = self.folder_path,
                        resolution = self.resolution,
                        time_list = self.time_list,
                )
                event.to_sql(con)
                # Get the EventID
                event_id = con.execute('SELECT EventID FROM RainfallEvent ORDER BY EventID DESC LIMIT 1').fetchone()[0]
                for rainfall_day in rainfall_event['event_days_str']:
                        day = RainfallDay(
                                date=ee.Date(rainfall_day),
                                roi = self.roi, 
                                bbox = self.bbox,  
                                threshold = self.rainy_day_threshold,
                                folder_path = self.folder_path,
                                resolution = self.resolution,
                                time_list = self.time_list,
                                event_id=event_id
                        )
                        day.to_sql(con)