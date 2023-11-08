import ee
from datetime import timedelta,datetime
from flood_utils.flood_day import FloodDay
from flood_utils.flood_event import FloodEvent
from flood_utils.flood_toolbox import ininialize_database
import duckdb

class FloodPeriod:
    """
    A class for generating flood events from a given period.

    Attributes:
    -----------
    start_date : ee.Date
        Start date of the period.
    end_date : ee.Date
        End date of the period.
    roi : ee.Geometry
        Region of interest.
    bbox : list
        Bounding box of the region of interest.
    water_area_asset_path : str
        Earth Engine Asset path of the water area.
    resolution : float
        Resolution of the output image.
    threshold : float
        Threshold value.
    folder_path : str
        Folder path for downloading files.

    Methods:
    --------
    generate_flood_days()
        Generates a list of flood days.
    flood_events(flood_days)
        Converts a list of flood days to a list of flood events.
    flood_list()
        Generates a list containing detailed information about flood events.
    process_flood_events(flood_events_with_details, db_path)
        Processes a series of flood events, obtains flood images, downloads flood maps, and stores event information in a database.
    """

    def __init__(self, start_date, end_date, roi, bbox, water_area_asset_path, resolution, threshold, folder_path):
        """
        Initializes the FloodPeriod class.

        :param start_date: ee.Date, start date
        :param end_date: ee.Date, end date
        :param roi: ee.Geometry, region of interest
        :param bbox: list, bounding box of the region of interest
        :param water_area_asset_path: str, Earth Engine Asset path of the water area
        :param resolution: float, resolution of the output image
        :param threshold: float, threshold value
        :param folder_path: str, folder path for downloading files
        """
        self.start_date = ee.Date(start_date)
        self.end_date = ee.Date(end_date)
        self.roi = roi
        self.bbox = bbox
        self.water_area_asset_path = water_area_asset_path
        self.resolution = resolution
        self.threshold = threshold
        self.folder_path = folder_path

    def generate_flood_days(self):
        """
        Generates a list of flood days.

        :return: list, list of flood days
        """
        # Create an instance of FloodDay for each day in the period
        current_date = self.start_date
        flood_days = []
        while current_date.difference(self.end_date, 'day').getInfo() <= 0:
            print(f"Processing {current_date.format('YYYY-MM-dd').getInfo()}")
            next_day = current_date.advance(1, 'day')  # Move to the next day
            flood_day = FloodDay(
                current_date, 
                self.roi,
                self.bbox,
                self.water_area_asset_path,
                self.resolution,
                self.threshold,
                self.folder_path
            )
            flood_map = flood_day.obtain_flood_water()
            if flood_day.is_flooding_event(flood_map)['is_flooding_event'] == 1:
                # Format the current date to be used in file naming
                formatted_date = current_date.format('YYYYMMdd').getInfo()
                # Call the download function from the FloodDay instance
                download_path = flood_day.download_flood_map(flood_map)
                print(f"Downloaded flood map for {formatted_date} to {download_path}")
                # Append the date to the flood_days list
                flood_days.append(current_date.format('YYYY-MM-dd').getInfo())

            current_date = next_day  # Advance the current date to the next day
        return flood_days
    
    @staticmethod
    def flood_events(flood_days):
        """
        Converts a list of flood days to a list of flood events.

        :param flood_days: list, list of flood days
        :return: list, list of flood events
        """
        flood_days_datetime = [datetime.strptime(date, "%Y-%m-%d") for date in flood_days]
        flood_events = []
        start_date = None
        end_date = None

        for date in flood_days_datetime:
            if start_date is None:
                start_date = date
                end_date = date + timedelta(days=1)
            elif date == end_date + timedelta(days=0):
                end_date = date + timedelta(days=1)
            else:
                flood_events.append({
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    'end_date': end_date.strftime("%Y-%m-%d")
                })
                start_date = date
                end_date = date + timedelta(days=1)

        # After the loop ends, add the last event
        if start_date is not None:
            flood_events.append({
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date .strftime("%Y-%m-%d")
            })

        return flood_events

    def flood_list(self):
        """
        Generates a list containing detailed information about flood events.

        :return: list, list containing detailed information about flood events
        """
        flood_days_list = self.generate_flood_days()

        flood_events_list = self.flood_events(flood_days_list)
        all_events_with_details = []  # Create an empty list to store details of all events

        # Iterate through the event list and create a dictionary containing detailed information for each event
        for event in flood_events_list:
            start_date = datetime.strptime(event['start_date'], "%Y-%m-%d")
            end_date = datetime.strptime(event['end_date'], "%Y-%m-%d")
            # Include all dates from start_date to end_date
            event_days = [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]
            event_days_str = [day.strftime("%Y-%m-%d") for day in event_days]

            # Create a dictionary containing the required information
            event_details = {
                'start_date': event['start_date'],
                'end_date': event['end_date'],
                'event_days_str': event_days_str
            }

            # Add the dictionary to the list
            all_events_with_details.append(event_details)

        # Return the list
        return all_events_with_details
    

    def process_flood_events(self,flood_events_with_details,db_path):
        """
        Processes a series of flood events, obtains flood images, downloads flood maps, and stores event information in a database.

        :param flood_events_with_details: list, list containing detailed information about flood events
        :param con: database connection object
        """
        ininialize_database(db_path)
        con = duckdb.connect(database=db_path)

        for flood_event in flood_events_with_details:
            # Create an instance of the flood event
            event = FloodEvent(
                start_date=ee.Date(flood_event['start_date']),
                end_date=ee.Date(flood_event['end_date']),
                roi= self.roi,
                bbox=self.bbox,
                water_area_asset_path=self.water_area_asset_path,
                resolution=self.resolution,
                threshold=self.threshold,
                folder_path=self.folder_path
            )
            
            # Obtain the water image for the flood event
            event_image = event.obtain_flood_water()
            # 下载洪水地图
            event_download_path = event.download_flood_map(event_image)

            # 打印下载洪水地图的地址    
            print(f"Downloaded flood map for event from {flood_event['start_date']} to {flood_event['end_date']}: {event_download_path}")
            
            # 将洪水事件信息存储到数据库
            event.to_sql(con)
            
            # 从数据库中获取最新的事件ID
            event_id = con.execute('SELECT EventID FROM FloodEvent ORDER BY EventID DESC LIMIT 1').fetchone()[0]
            
            # 处理每一天的洪水数据
            for flood_day in flood_event['event_days_str']:
                # 创建每一天洪水的实例
                day = FloodDay(
                    date=ee.Date(flood_day),
                    roi = self.roi,
                    bbox = self.bbox,
                    water_area_asset_path = self.water_area_asset_path,
                    resolution = self.resolution,
                    threshold = self.threshold,
                    folder_path = self.folder_path,
                    event_id = event_id
                )
                
                # 将每天的洪水数据存储到数据库
                day.to_sql(con)
