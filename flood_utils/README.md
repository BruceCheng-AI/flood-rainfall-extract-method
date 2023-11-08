# Flood Extraction

## English Version

### Flood Mapping from Typhoon Tracks

This document outlines the preprocessing steps for typhoon track data and the subsequent flood mapping process. It serves as the core module for flood extraction, primarily involving the following Python scripts: `ALL_TC_extracted.py`, `modis_extract_method.py`, `modis_toolbox.py`, `Public_methods.py`, `Sentinel1_extract_method.py`, `Sentinel2_extract_method.py`, `Water_extract_main.py`.

#### Data Preprocessing

**Input**: Best track data set for typhoons (downloaded from the China Typhoon Network).

**Workflow**:

1. Utilize `split_txt.py` to separate the data for each typhoon into individual txt files.
2. Sequentially process each typhoon's txt file through `txt2shp_v2.py` to convert it into point shapefile (shp) format.
3. Read each point shp file in sequence and convert it into line shp files using `point2line.py`.

**Output**: Typhoon track shapefile data

- Naming convention: [ID]_[Name]_[Start_Date]_[End_Date].shp

#### Water Body Extraction

**Input**: Typhoon track shapefiles and the corresponding start and end dates of the typhoon events.

**Workflow**:

1. Convert the typhoon tracks into a buffered Region of Interest (ROI) using `Route2Roi` from `Public_methods` (buffer radius is adjustable).
2. Identify Potential Flood Areas (PFA) within the ROI based on the Global Precipitation Measurement (GPM) dataset.
3. Input the PFA into various satellite water body extraction modules to delineate water bodies separately.
4. Integrate and stack the water bodies extracted from different satellites (this step is subject to refinement).
5. Determine the extent of water bodies one month prior to the typhoon's arrival using the global water body dataset.
6. Subtract the pre-typhoon water body extent from the integrated water bodies to isolate the flood extent.

**Output**: Typhoon flood imagery

- Bands: Water body extents from various satellites, integrated water body extent, global water body dataset, and flood extent.
- Attributes: Typhoon start and end dates, typhoon ID, and name.

#### Flood Dataset

**Input**: Best track path of the typhoon, typhoon ID, name, and start and end dates.

**Workflow**:

1. Input relevant typhoon information and iteratively apply the water body extraction algorithm to obtain flood imagery for each typhoon.
2. Stack the flood images over time into an ImageCollection object and assign appropriate properties.

**Output**: Flood dataset ImageCollection

- Structure of ImageCollection:
  - **image1**:
    - bands: ***
    - property: ***
  - **image2**:
    - bands: ***
    - property: ***
  - **property**: Description of the dataset

### Flood Event Extraction Toolkit

This parts provides an overview of the Flood Event Extraction process utilizing the suite of tools provided in the accompanying Python scripts. The toolkit is designed to process remote sensing data and meteorological information to identify and analyze flood events.

#### Overview

The toolkit comprises several components, each responsible for a segment of the workflow to detect and analyze flood events:

- `flood_toolbox.py`: A collection of utilities and algorithms for processing and analyzing flood-related data.
- `flood_day.py`: Functions and classes for managing and analyzing flood data on a daily basis.
- `flood_event.py`: Classes and methods for aggregating daily flood data into comprehensive flood event assessments.
- `flood_period.py`: Workflow management for period-based flood event analysis, from data acquisition to final storage.

#### Workflow

The flood event extraction process involves the following steps:

1. **Data Preprocessing**: Initial raw data is processed to extract relevant features for flood detection.
2. **Daily Analysis**: Each day within the period of interest is analyzed for potential flooding using precipitation data and other relevant metrics.
3. **Event Aggregation**: Daily analyses are aggregated to identify specific flood events, characterized by their duration and intensity.
4. **Periodic Assessment**: The entire period is assessed to provide a synthesized view of flood activity, integrating data from individual events.

#### Usage

To utilize the toolkit:

1. Prepare your input data according to the expected format detailed in each script.
2. Run `flood_day.py` to perform the daily flood analysis.
3. Use the output from the daily analysis as input to `flood_event.py` for event aggregation.
4. Execute `flood_period.py` to assess the period and generate final outputs.

#### Outputs

The toolkit generates the following outputs:

- Daily flood maps with associated metrics.
- Aggregated flood event data characterizing the extent and severity of events.
- A comprehensive assessment of the flood period, including synthesized maps and metrics.

#### Requirements

The toolkit requires the following dependencies:

- Python 3.x
- Earth Engine Python API
- Additional Python libraries as specified in each script

Ensure you have set up the Earth Engine environment and authenticated your account before running the scripts.

#### License

Please see the license file for terms and conditions related to the use of this toolkit.

For further details on each script's functionality and input/output specifications, refer to the inline comments within the code. This toolkit is intended for use by researchers, analysts, and practitioners in the field of remote sensing and disaster management.

## 中文版

### 台风路径洪水映射

本文档概述了台风路径数据的预处理步骤以及随后的洪水映射流程，这是洪水提取的核心驱动模块，主要涉及 `ALL_TC_extracted.py`, `modis_extract_method.py`, `modis_toolbox.py`, `Public_methods.py`, `Sentinel1_extract_method.py`, `Sentinel2_extract_method.py`, `Water_extract_main.py`。

#### 数据预处理

**输入**: 台风最佳路径数据集（来源于中国台风网）。

**流程**:

1. 使用 `split_txt.py` 脚本，将每场台风的数据分割成独立的 txt 文件。
2. 逐个处理每场台风的 txt 文件，通过 `txt2shp_v2.py` 转换成点状 shp 文件。
3. 读取点状 shp 文件，并用 `point2line.py` 转换成线状 shp 文件。

**输出**: 台风路径 shp 数据集。

- 命名规则: `编号_名称_开始日期_结束日期.shp`。

#### 水体提取

**输入**: 台风路径 shp 数据及台风的起止时间。

**流程**:

1. 利用 `Public_methods` 中的 `Route2Roi` 函数，将台风路径转换成缓冲区域 ROI（可设定缓冲半径）。
2. 根据 GPM（全球降水测量数据集）分析 ROI 内的潜在洪水区域（PFA）。
3. 将 PFA 作为输入，通过各卫星水体提取模块单独提取水体。
4. 合并叠加各卫星提取得到的水体范围（该步骤有待完善）。
5. 参考全球水体数据集，确定台风到达前一个月的水体范围。
6. 对第四步和第五步的数据进行差值处理，以识别洪水范围。

**输出**: 台风洪水图像。

- 波段信息: 各卫星提取的水体范围、合成的水体范围、全球水体数据集、洪水范围。
- 属性信息: 台风起止时间、编号及名称。

#### 洪水数据集整合

**输入**: 台风最佳路径、编号、名称及起止时间。

**流程**:

1. 依次输入台风相关信息，循环运行水体提取算法，获取各台风的洪水图像。
2. 按时间序列将洪水图像组合成 ImageCollection 对象，并配置相关属性。

**输出**: 洪水数据集 ImageCollection。

- ImageCollection 结构示例:
  - **image1**:
    - bands: ***
    - property: ***
  - **image2**:
    - bands: ***
    - property: ***
  - **property**: 数据集描述信息。

### 洪涝事件提取工具包

这部分材料提供了使用随附 Python 脚本进行洪涝事件提取过程的概览。该工具包旨在处理遥感数据和气象信息，以识别和分析洪涝事件。

#### 概述

工具包包含几个组件，每个组件负责工作流中的一个环节，以检测和分析洪涝事件：

- `flood_toolbox.py`: 一系列用于处理和分析与洪涝相关数据的工具和算法。
- `flood_day.py`: 用于管理和分析每日洪涝数据的函数和类。
- `flood_event.py`: 用于将每日洪涝分析聚合为全面洪涝事件评估的类和方法。
- `flood_period.py`: 工作流管理，用于基于周期的洪涝事件分析，从数据获取到最终存储。

#### 工作流程

洪涝事件提取过程包括以下步骤：

1. **数据预处理**：处理初始原始数据，提取洪涝检测的相关特征。
2. **每日分析**：使用降水数据和其他相关指标分析感兴趣周期内的每一天，以确定潜在洪涝。
3. **事件聚合**：聚合每日分析以识别具体洪涝事件，特征是其持续时间和强度。
4. **周期性评估**：评估整个周期，提供洪涝活动的综合视图，整合单个事件的数据。

#### 使用方法

使用工具包：

1. 根据每个脚本中详细的说明准备输入数据。
2. 运行 `flood_day.py` 进行每日洪涝分析。
3. 使用每日分析的输出作为 `flood_event.py` 的输入进行事件聚合。
4. 执行 `flood_period.py` 对周期进行评估并生成最终输出。

#### 输出结果

工具包生成以下输出：

- 带有相关指标的每日洪涝地图。
- 描述事件范围和严重性的聚合洪涝事件数据。
- 包括综合地图和指标的周期洪涝评估综合报告。

#### 系统要求

工具包需要以下依赖项：

- Python 3.x
- Earth Engine Python API
- 其他在每个脚本中指定的 Python 库

在运行脚本之前，请确保已经设置了 Earth Engine 环境并对您的账户进行了认证。

#### 许可证

请参阅许可证文件，了解与此工具包使用相关的条款和条件。

有关每个脚本功能和输入/输出规格的更多详细信息，请参考代码中的内联注释。此工具包面向遥感和灾害管理领域的研究人员、分析师和从业人员。
