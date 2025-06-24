"""
Script: gee_export_satellite.py
Purpose: Load coordinates from CSV, filter Earth Engine imagery by date & cloud cover, export each clipped tile to Google Drive.
"""

import ee
import pandas as pd
import os
import re
from datetime import datetime

# Initialize Earth Engine
try:
    ee.Initialize(project='imint-459015')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='imint-459015')

def sanitize_name(name):
    """Sanitize strings to be safe for GEE export description."""
    return re.sub(r'[^a-zA-Z0-9._:;\-]', '_', name)[:100]

def dms_to_decimal(dms_string):
    dms_string = str(dms_string).strip()
    try:
        return float(dms_string)
    except ValueError:
        pass

    pattern = r'(\d+)\D+(\d+)\D+([\d.]+)\D*([NSEW])'
    match = re.search(pattern, dms_string)
    if not match:
        raise ValueError(f"Invalid DMS format: {dms_string}")

    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

def parse_csv_coordinates(csv_file_path):
    df = pd.read_csv(csv_file_path)
    df.columns = df.columns.str.strip()
    filtered_df = df[(df['Y/N'] == 'Y') & (df['IMDATE Visible'].isna() | (df['IMDATE Visible'] == ''))]

    coordinates = []
    for _, row in filtered_df.iterrows():
        name = row['Name'] if pd.notna(row['Name']) else f"Location_{len(coordinates)+1}"
        try:
            lat = dms_to_decimal(row['Y (North-South direction)'])
            lon = dms_to_decimal(row['X (East-West direction)'])
            coordinates.append({'name': sanitize_name(name.strip()), 'lat': lat, 'lon': lon})
        except Exception as e:
            print(f"Warning: Failed to parse coordinates for {name}: {e}")
    return coordinates

def export_tile_to_drive(num, total_count, name, lat, lon, buffer_km=0.25, date_start='2022-01-01', date_end='2022-12-31', cloud_thresh=20, scale=10):
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(buffer_km * 1000).bounds().getInfo()['coordinates']

    image = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(ee.Geometry.Polygon(region)) \
        .filterDate(date_start, date_end) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_thresh)) \
        .sort('CLOUDY_PIXEL_PERCENTAGE') \
        .first()

    if image:
        task = ee.batch.Export.image.toDrive(
            image=image.clip(ee.Geometry.Polygon(region)),
            description=f"{name}_export",
            folder='GEE_Exports',
            fileNamePrefix=f"{name}_{lat:.5f}_{lon:.5f}",
            region=region,
            scale=scale,
            maxPixels=1e13
        )
        task.start()
        print(f"Exporting image {num}/{total_count}.")
    else:
        print(f"No cloud-free image found for {name} between {date_start} and {date_end}")

def export_all(csv_path, date_start, date_end):
    coords = parse_csv_coordinates(csv_path)
    total = len(coords)
    print(f"Exporting {len(coords)} locations...")
    print(f"Check Earth Engine Tasks tab or https://code.earthengine.google.com/tasks to monitor status.")
    for i, c in enumerate(coords):
        export_tile_to_drive(i, total, c['name'], c['lat'], c['lon'], date_start=date_start, date_end=date_end)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Export satellite image tiles from GEE to Google Drive')
    parser.add_argument('--csv', default='../AAA.csv', help='CSV file with coordinates')
    parser.add_argument('--start', default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2024-12-31', help='End date (YYYY-MM-DD)')
    args = parser.parse_args()

    export_all(args.csv, args.start, args.end)