# Rainfall Analysis and Flood Event Extraction Toolkit

## English Version

### Overview

The Rainfall Analysis and Flood Event Extraction Toolkit provides a suite of tools for analyzing rainfall data and extracting flood events using Google Earth Engine (GEE). This toolkit is designed for researchers and practitioners in hydrology, meteorology, and disaster management.

### Components

The toolkit comprises four main scripts, each serving a specific function in the rainfall analysis and flood event extraction workflow:

- `rainfall_toolbox.py`: A utility script containing functions for common operations like retrieving band names, calculating global maxima and minima, and initializing databases for storing rainfall events.

- `rainfall_day.py`: This script defines the `RainfallDay` class, which extends the functionality of the `RainfallEvent` class to handle daily rainfall data. It includes methods for initializing daily rainfall events and exporting them to a database.

- `rainfall_event.py`: Contains the `RainfallEvent` class that processes individual rainfall events. It includes attributes for start and end dates, region of interest (ROI), and methods for calculating various rainfall statistics.

- `rainfall_period.py`: Defines the `RainfallPeriod` class for representing a period of rainfall analysis. It manages the workflow for analyzing a series of rainfall events within a specified time frame and stores the results in a structured format.

### Workflow

The workflow for using this toolkit involves:

1. Preprocessing rainfall data using the `rainfall_toolbox.py` script to prepare the data for analysis.
2. Analyzing daily rainfall events with the `rainfall_day.py` script to identify significant precipitation.
3. Aggregating daily events into larger flood events using the `rainfall_event.py` script, considering the cumulative rainfall over each event's duration.
4. Assessing the entire period of interest using the `rainfall_period.py` script to identify and extract significant flood events and compile them into an ImageCollection for further analysis or visualization.

### Usage

1. Set up the GEE environment and ensure all dependencies are installed.
2. Use the functions and classes provided in the scripts to process your rainfall data.
3. Customize the buffer radius and thresholds according to your specific analysis needs.
4. Execute the scripts in the order of the workflow to obtain the final flood event data.

## Output

The toolkit will output:

- Daily rainfall maps with associated metrics.
- Aggregated flood event data, including extent and severity.
- A comprehensive ImageCollection representing the synthesized flood events over the analyzed period.

### License

Please refer to the accompanying license file for terms and conditions related to the use of this toolkit.

For a detailed explanation of each script's functionality, input requirements, and output specifications, please refer to the inline comments within the codebase. This toolkit aims to facilitate the comprehensive analysis of flood events, contributing to the advancement of flood risk management and response strategies.

## 中文版

### 概览

洪涝事件分析与提取工具集提供了一系列工具，用于利用 Google Earth Engine (GEE) 分析降雨数据并提取洪涝事件。该工具集适用于水文学、气象学和灾害管理领域的研究人员和从业者。

### 组件

工具集包含四个主要脚本，每个脚本在降雨分析和洪涝事件提取工作流中承担特定功能：

- `rainfall_toolbox.py`：一个实用程序脚本，包含常见操作的函数，如检索波段名称、计算全局最大值和最小值，以及初始化用于存储降雨事件的数据库。

- `rainfall_day.py`：此脚本定义了 `RainfallDay` 类，该类扩展了 `RainfallEvent` 类的功能，以处理每日降雨数据。它包括初始化每日降雨事件和将它们导出到数据库的方法。

- `rainfall_event.py`：包含处理个别降雨事件的 `RainfallEvent` 类。它包括开始和结束日期、兴趣区域 (ROI) 的属性，以及计算各种降雨统计数据的方法。

- `rainfall_period.py`：定义了表示降雨分析周期的 `RainfallPeriod` 类。它管理了在指定时间框架内分析一系列降雨事件的工作流，并以结构化的格式存储结果。

### 工作流程

使用此工具集的工作流程包括：

1. 使用 `rainfall_toolbox.py` 脚本预处理降雨数据，为分析准备数据。
2. 使用 `rainfall_day.py` 脚本分析每日降雨事件，以识别显著降水。
3. 使用 `rainfall_event.py` 脚本聚合每日事件，形成更大的洪涝事件，考虑每个事件持续期间的累积降雨。
4. 使用 `rainfall_period.py` 脚本评估整个感兴趣的周期，识别和提取显著的洪涝事件，并将它们编译成 ImageCollection，以便进一步分析或可视化。

### 使用方法

1. 设置 GEE 环境，并确保安装了所有依赖项。
2. 使用脚本中提供的函数和类处理您的降雨数据。
3. 根据您的具体分析需求自定义缓冲半径和阈值。
4. 按照工作流程的顺序执行脚本，以获得最终的洪涝事件数据。

### 输出结果

工具集将输出：

- 每日降雨地图及相关指标。
- 聚合洪涝事件数据，包括范围和严重性。
- 代表分析期间合成洪涝事件的综合 ImageCollection。

### 许可证

请参阅随附的许可证文件，了解与此工具集使用相关的条款和条件。

有关每个脚本的功能、输入要求和输出规格的详细说明，请参阅代码库中的内联注释。该工具集旨在促进洪涝事件的全面分析，有助于推进洪涝风险管理和应对策略的发展。
