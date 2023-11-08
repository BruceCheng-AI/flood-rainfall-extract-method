# Flood Event Analysis Toolkit

## Overview

This toolkit provides a suite of scripts for analyzing flood events using meteorological data and satellite imagery. It supports flood extraction from typhoon tracks and rainfall analysis to identify significant flood events. The toolkit is implemented in Python and utilizes Google Earth Engine for processing remote sensing data.

## Components

The toolkit contains the following main scripts:

- `flood_toolbox.py` - Common utilities for flood data analysis.
- `flood_day.py` - Daily flood analysis using precipitation data.  
- `flood_event.py` - Aggregation of daily data into flood events.
- `flood_period.py` - Periodic flood assessment and event extraction.
- `rainfall_toolbox.py` - Utilities for rainfall data analysis.
- `rainfall_day.py` - Daily rainfall analysis.
- `rainfall_event.py` - Rainfall event aggregation.
- `rainfall_period.py` - Periodic rainfall assessment.
- `typhoon_process.py` - Typhoon track data preprocessing. 
- `flood_extract.py` - Flood extent extraction from typhoons.

## Workflow

1. Preprocess input data using the relevant toolbox scripts.
2. Perform daily analysis with the `*_day.py` scripts.
3. Aggregate daily data into events using `*_event.py` scripts.
4. Assess the full period and extract flood events with `*_period.py` scripts.

## Usage 

1. Set up Python environment and authenticate Earth Engine.
2. Prepare input data according to script requirements.
3. Customize parameters for your specific needs.
4. Run scripts following the workflow.

## Output

- Daily maps/metrics for rainfall and flooding.
- Extracted flood events with attributes. 
- Synthesized flood event collection.

## License

See LICENSE file for usage terms and conditions.

For detailed documentation, see code comments and the original specifications.