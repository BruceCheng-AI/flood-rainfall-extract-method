import ee
import geemap
import sys
geemap.set_proxy(port=7890)
geemap.ee_initialize()
from flood_utils.modis_extract_method import modis_main
from flood_utils.flood_toolbox import convert_ee_date_to_py_date
from flood_utils.flood_event import FloodEvent

class FloodDay(FloodEvent):
    """
    A class representing a single day flood event.

    Attributes:
    -----------
    date : ee.Date
        The date of the flood event.
    roi : ee.Geometry
        The region of interest.
    bbox : tuple
        The bounding box of the region of interest.
    water_area_asset_path : str
        The asset path of the water area image collection.
    resolution : float
        The resolution of the image.
    threshold : float
        The threshold value for flood detection.
    folder_path : str
        The folder path to save the output files.
    event_id : str, optional
        The ID of the flood event.
    """

    def __init__(self, date, roi, bbox, water_area_asset_path, resolution, threshold, folder_path, event_id=None):
        start_date = date 
        end_date = start_date.advance(1, 'day')
        # Initialize the superclass with the start and end date being the same for a single day event
        super().__init__(start_date=start_date, end_date=end_date, roi=roi, bbox=bbox, water_area_asset_path=water_area_asset_path, resolution=resolution, threshold=threshold, folder_path=folder_path)

        self.event_id = event_id
    
    # 重写生成数据函数
    def generate_flood_water(self):
        """
        Generate the flood water extent map for the given date.

        Returns:
        --------
        dict
            A dictionary containing the following keys:
            - DayID: The ID of the day in the format YYMMDD.
            - EventID: The ID of the flood event.
            - Date: The date of the flood event.
            - FloodExtentValue: The flood extent value.
            - FloodExtentMapPath: The file path of the flood extent map.
        """
        try:
            # Call the individual methods to generate the maps
            flood_water = self.obtain_flood_water()
            flood_occurrence = self.flood_occurrence(flood_water).getInfo()
            flood_map_path = self.folder_path + f"{self.EventID}_flood_map.tif"
        except Exception as e:
            print(f"Error generating rainfall data: {e}")
            sys.exit(1)  # 非零退出码通常表示程序遇到了错误 
        
        start_date_py = convert_ee_date_to_py_date(self.start_date)
        DayID = int(f"{start_date_py.strftime('%y%m%d')}")
        
        # Compile results into a dictionary
        result = {
            'DayID': DayID,
            'EventID': self.event_id,
            'Date': start_date_py,
            'FloodExtentValue':flood_occurrence,
            'FloodExtentMapPath': flood_map_path
        }

        return result
    
    # 重写保存函数
    def to_sql(self, connection):
        """
        Save the flood event data to a SQL database.

        Parameters:
        -----------
        connection : sqlalchemy.engine.base.Connection
            The database connection object.
        """
        # 调用父类的 to_sql 方法并指定表名为 FloodDay
        super().to_sql(connection, table_name="FloodDay")