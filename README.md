# Glove Sensor Pipeline

## Overview

I built this project to work with sensor data collected from my wearable glove. The idea was to use Python to check the data, find possible issues, and prepare it for further analysis.

I tested the pipeline using two activities: typing and picking up a book. The glove records readings from five fingertip sensors, along with movement and orientation data from an IMU sensor.

## Why I Built This Project

When working with sensor data, not every reading is necessarily reliable or easy to interpret. There can be missing values, repeated timestamps, gaps between readings, or unusual sensor patterns.

I wanted to build a simple pipeline that could check for these issues and help me understand the quality of the data before using it for further analysis.

## Tools I Used

- **ChatGPT** - to understand the hardware and build the glove prototype
- **Python** – to build and run the pipeline
- **Pandas** – to read, process and check the sensor data
- **Matplotlib** – to create graphs and understand sensor readings over time
- **CSV and JSON** – to store the input data and quality reports

## How the Pipeline Works

The pipeline takes a recorded CSV file from the glove and processes it in a few steps:

1. Reads the sensor data from the CSV file.
2. Checks whether the required columns are present and the values are in the expected format.
3. Looks for missing or invalid values, duplicate sample numbers, repeated timestamps, timestamps going backwards, and unusually large gaps between readings.
4. Converts the original timestamps into a readable date and time while keeping the original timestamps unchanged.
5. Flags rows that may need further investigation instead of automatically deleting them.
6. Saves the processed data, flagged rows, a quality report, and graphs showing how the sensors behaved during the recording.

## Data Collected

The glove records data from five fingertip sensors:

- Thumb
- Index
- Middle
- Ring
- Pinky

It also records data from the IMU, including roll, pitch, yaw, magnetometer readings, accelerometer readings and gyroscope readings.

The timestamps are recorded in milliseconds since January 1, 1970.

## Results and What I Observed

I ran the pipeline on two recordings: one of typing and another of picking up a book.

**Typing recording**
- Processed 2,243 rows.
- No missing or non-numeric values were found in the required columns.
- Three rows had duplicate timestamps.
- The thumb and ring sensor readings remained constant throughout the recording.

<img width="1400" height="700" alt="fingertip_readings" src="https://github.com/user-attachments/assets/b544c1a7-57c8-49ff-bb81-54e29444275e" />

Since I mainly use my index, middle and ring fingers while typing, I wanted to investigate how finger activity affects the readings. Constant values do not automatically mean a sensor is faulty; they could also indicate that a finger was not applying pressure during the activity.

**Book-picking recording**
- Processed 3,110 rows.
- No missing or non-numeric values were found in the required columns.
- Eight rows had duplicate timestamps.
- One row was flagged for a large gap between timestamps.

<img width="1400" height="700" alt="fingertip_readings" src="https://github.com/user-attachments/assets/4affd679-f859-4319-aebf-6795598a796a" />

The graphs showed different sensor patterns during typing and book picking. This helped me explore how the readings change across activities. However, without video or other activity labels, I cannot confirm exactly what action caused a particular reading.

## How I Handle Data Quality Issues

One important decision I made was to flag questionable data instead of deleting it automatically.

For example, if a sensor reading stays constant, I don't immediately assume the sensor is broken. The finger might simply not be applying pressure. Similarly, a repeated timestamp needs investigation, but it doesn't necessarily mean the entire row is unusable.

This approach allows me to preserve the original data and investigate potential problems before deciding what should happen to those records.

## Limitations

There are a few things this project cannot currently do:

- It cannot identify which hand action is happening just from the sensor readings.
- It does not confirm whether the force readings are physically accurate through calibration.
- The actual sampling rate needs to be checked against the intended hardware settings.
- It does not use a camera to verify the actions performed during each recording.
- It processes saved CSV files rather than monitoring sensor data in real time.

## What I Would Like to Improve Next

There are several ways I could build on this project in the future:

- Add a camera and synchronize video with sensor timestamps to help verify when an action occurs.
- Add more sensors across the palm and other parts of the glove to capture more detailed hand movements and contact.
- Add more automated tests to check that the pipeline handles different data-quality issues correctly.

## How to Run the Project

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

To process the typing recording:

```bash
python pipeline.py "data/raw/typing.csv"
```

To process the book-picking recording:

```bash
python pipeline.py "data/raw/picking up a book.csv"
```


The pipeline saves its outputs in the `data/processed/` folder.

## Project Scope

This is a batch data pipeline, which means it processes recordings after they have been saved rather than handling sensor readings in real time.

My main focus was learning how to work with real sensor data, check its quality, investigate unusual patterns and prepare the data for further analysis. I have kept the project focused on data engineering rather than building a machine learning model.
