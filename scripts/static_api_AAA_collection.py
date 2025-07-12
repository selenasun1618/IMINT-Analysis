import pandas as pd
from dotenv import load_dotenv
import os
import requests

def dms_to_decimal(dms_string):
    """Converts DMS (Degrees, Minutes, Seconds) coordinate string to decimal degrees.
    
    Args:
        dms_string: String like "39° 5'27.29\"N" or "125°37'2.83\"E"
    
    Returns:
        float: Decimal degrees (negative for S/W directions)
    """
    import re
    
    # Handle case where coordinates might be combined (lat lon in one cell)
    if ' ' in dms_string and ('N' in dms_string or 'S' in dms_string) and ('E' in dms_string or 'W' in dms_string):
        # Split combined coordinates like "39° 5'27.29"N 125°37'2.83"E"
        parts = dms_string.split()
        lat_part = None
        lon_part = None
        
        for part in parts:
            if 'N' in part or 'S' in part:
                lat_part = part
            elif 'E' in part or 'W' in part:
                lon_part = part
        
        if lat_part and lon_part:
            return dms_to_decimal(lat_part), dms_to_decimal(lon_part)
    
    # Clean up the string
    dms_string = str(dms_string).strip()
    
    # Check if it's already a decimal number
    try:
        return float(dms_string)
    except ValueError:
        pass
    
    # Extract degrees, minutes, seconds, and direction
    pattern = r'(\d+)°?\s*(\d+)\'?\s*([0-9.]+)\"?\s*([NSEW])?'
    match = re.search(pattern, dms_string)
    
    if not match:
        # Try simpler pattern for just degrees
        pattern = r'(\d+\.?\d*)°?\s*([NSEW])?'
        match = re.search(pattern, dms_string)
        if match:
            degrees = float(match.group(1))
            direction = match.group(2)
            if direction in ['S', 'W']:
                degrees = -degrees
            return degrees
        else:
            raise ValueError(f"Could not parse coordinate: {dms_string}")
    
    degrees = float(match.group(1))
    minutes = float(match.group(2))
    seconds = float(match.group(3))
    direction = match.group(4)
    
    # Convert to decimal degrees
    decimal = degrees + minutes/60 + seconds/3600
    
    # Make negative for South/West
    if direction in ['S', 'W']:
        decimal = -decimal
    
    return decimal

def parse_csv_coordinates(csv_file_path):
    """Parses a CSV file and returns a list of coordinate dicts with name, lat, lon.
    Only includes rows where Y/N column is 'Y' and IMDATE Visible is empty."""
    
    # Read CSV file
    df = pd.read_csv(csv_file_path)
    
    # Clean column names (remove leading/trailing spaces)
    df.columns = df.columns.str.strip()
    
    # Filter rows where Y/N is 'Y' and IMDATE Visible is empty/NaN
    filtered_df = df[
        (df['Y/N'] == 'Y') & 
        (df['IMDATE Visible'].isna() | (df['IMDATE Visible'] == ''))
    ]
    
    coordinate_data = []
    for _, row in filtered_df.iterrows():
        # Use Name column, or create a generic name if empty
        name = row['Name'] if pd.notna(row['Name']) and row['Name'].strip() else f"Location_{len(coordinate_data)+1}"
        
        # Handle coordinate conversion
        try:
            lat_raw = row['Y (North-South direction)']
            lon_raw = row['X (East-West direction)']
            
            # Check if coordinates are combined in one cell
            if pd.isna(lon_raw) or lon_raw == '' or str(lon_raw).strip() == '':
                # Try to extract both lat and lon from the lat column
                coords = dms_to_decimal(str(lat_raw))
                if isinstance(coords, tuple):
                    lat, lon = coords
                else:
                    raise ValueError("Could not extract both coordinates")
            else:
                # Convert each coordinate separately
                lat = dms_to_decimal(str(lat_raw))
                lon = dms_to_decimal(str(lon_raw))
            
            coordinate_data.append({
                'name': name.strip(),
                'lat': lat,
                'lon': lon
            })
        except Exception as e:
            print(f"Warning: Could not parse coordinates for {name}: {e}")
            print(f"  Lat: {lat_raw}")
            print(f"  Lon: {lon_raw}")
            continue
    
    return coordinate_data

def calculate_zoom_level(ground_distance_km, image_size_px=640):
    """Calculate the appropriate zoom level based on ground distance in kilometers.
    
    Args:
        ground_distance_km: Desired ground distance in kilometers (width/height of the image)
        image_size_px: Size of the image in pixels (default: 640x640)
        
    Returns:
        int: Zoom level (0-21)
    """
    import math
    # Earth's circumference in kilometers
    EQUATOR_CIRCUMFERENCE = 40075.0
    
    # Calculate the ground resolution at the equator for each zoom level
    zoom_levels = {}
    for zoom in range(0, 22):
        # At zoom 0, the whole world is 256x256 pixels
        # Each zoom level doubles the resolution
        pixels = 256 * (2 ** zoom)
        # Ground resolution at the equator (km/pixel)
        resolution = EQUATOR_CIRCUMFERENCE / pixels
        # Ground distance covered by the image (km)
        ground_distance = resolution * image_size_px
        zoom_levels[zoom] = ground_distance
    
    # Find the zoom level that most closely matches the desired ground distance
    best_zoom = 0
    min_diff = float('inf')
    for zoom, distance in zoom_levels.items():
        diff = abs(distance - ground_distance_km)
        if diff < min_diff:
            min_diff = diff
            best_zoom = zoom
    
    return best_zoom

def build_gmaps_static_url(lat, lon, api_key, ground_distance_km=1.0, image_size=640, maptype='satellite', timestamp=None):
    """Constructs a Google Maps Static API URL for a given location.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        api_key: Google Maps API key
        ground_distance_km: Desired ground distance in kilometers (width/height of the image)
        image_size: Size of the image in pixels (square image)
        maptype: Map type ('roadmap', 'satellite', 'hybrid', 'terrain')
        timestamp: Optional timestamp for historical imagery (format: 'YYYY-MM-DD', 'YYYY-MM', or Unix timestamp)
    """
    zoom = calculate_zoom_level(ground_distance_km, image_size)
    
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        'center': f"{lat},{lon}",
        'zoom': str(zoom),
        'size': f"{image_size}x{image_size}",
        'maptype': maptype,
        'key': api_key
    }
    
    # Add timestamp parameter for historical imagery if provided
    if timestamp:
        # Convert date string to Unix timestamp if needed
        if isinstance(timestamp, str) and ('-' in timestamp):
            import datetime
            import time
            try:
                # Try parsing as YYYY-MM-DD
                if len(timestamp.split('-')) == 3:
                    dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d')
                # Try parsing as YYYY-MM
                elif len(timestamp.split('-')) == 2:
                    dt = datetime.datetime.strptime(timestamp, '%Y-%m')
                unix_timestamp = int(time.mktime(dt.timetuple()))
                params['timestamp'] = str(unix_timestamp)
            except ValueError:
                print(f"Warning: Invalid timestamp format '{timestamp}'. Using current date.")
        else:
            # Assume it's already a Unix timestamp
            params['timestamp'] = str(timestamp)
    param_str = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{base_url}?{param_str}"

def save_static_map_image(lat, lon, name, api_key, out_dir, ground_distance_km=1.0, image_size=640, maptype='satellite', timestamp=None, current=None, total=None):
    """Downloads and saves a Google Maps Static image for the location.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        name: Name of the location (used for filename)
        api_key: Google Maps API key
        out_dir: Directory to save images to
        ground_distance_km: Desired ground distance in kilometers (width/height of the image)
        image_size: Size of the image in pixels (square image)
        maptype: Map type ('roadmap', 'satellite', 'hybrid', 'terrain')
        timestamp: Optional timestamp for historical imagery (format: 'YYYY-MM-DD', 'YYYY-MM', or Unix timestamp)
        current: Current image number (for progress reporting)
        total: Total number of images (for progress reporting)
    """
    url = build_gmaps_static_url(lat, lon, api_key, ground_distance_km, image_size, maptype, timestamp)
    response = requests.get(url)
    if response.status_code == 200:
        # Include timestamp in filename if provided
        timestamp_str = f"_{timestamp}" if timestamp else ""
        filename = f"{name.replace(' ', '_')}_{lat:.5f}_{lon:.5f}_{ground_distance_km}km{timestamp_str}_{image_size}x{image_size}.png"
        filepath = os.path.join(out_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        if current is not None and total is not None:
            print(f"Saved ({current}/{total}): {filepath}")
        else:
            print(f"Saved: {filepath}")
    else:
        print(f"Failed to fetch image for {name} ({lat}, {lon}): {response.status_code} - {response.text}")


def screenshot_all_csv_locations(csv_path, api_key, base_out_dir, ground_distance_km=1.0, image_size=640, maptype='satellite', timestamp=None):
    """Takes screenshots of all CSV locations using the Google Maps Static API.
    Only processes rows where Y/N is 'Y' and IMDATE Visible is empty.
    Creates a subfolder for each distance/resolution combination.
    
    Args:
        csv_path: Path to the CSV file
        api_key: Google Maps API key
        base_out_dir: Base output directory for screenshots
        ground_distance_km: Desired ground distance in kilometers (width/height of the image)
        image_size: Size of the image in pixels (square image)
        maptype: Map type ('roadmap', 'satellite', 'hybrid', 'terrain')
        timestamp: Optional timestamp for historical imagery (format: 'YYYY-MM-DD', 'YYYY-MM', or Unix timestamp)
    """
    # Create subfolder name based on distance and resolution
    folder_name = f"{ground_distance_km}km_{image_size}x{image_size}_{maptype}"
    if timestamp:
        folder_name += f"_{timestamp}"
    
    out_dir = os.path.join(base_out_dir, folder_name)
    os.makedirs(out_dir, exist_ok=True)
    
    coordinates = parse_csv_coordinates(csv_path)
    total = len(coordinates)
    print(f"Total images to screenshot: {total}")
    print(f"Ground distance per image: {ground_distance_km} km")
    print(f"Image size: {image_size}x{image_size} pixels")
    print(f"Map type: {maptype}")
    print(f"Output folder: {out_dir}")
    print(f"Processing coordinates where Y/N='Y' and IMDATE Visible is empty")
    
    for idx, coord in enumerate(coordinates, 1):
        save_static_map_image(
            coord['lat'], coord['lon'], coord['name'], api_key, out_dir, 
            ground_distance_km=ground_distance_km, 
            image_size=image_size, 
            maptype=maptype,
            timestamp=timestamp, 
            current=idx, 
            total=total
        )

if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Take screenshots of CSV coordinate locations using Google Maps Static API')
    parser.add_argument('--csv', default="coordinates/AAA.csv", help='Path to CSV file')
    parser.add_argument('--output', default="google_earth_images", help='Output directory for screenshots')
    parser.add_argument('--distance', type=float, default=0.5, 
                        help='Ground distance in kilometers (width/height of the image)')
    parser.add_argument('--size', type=int, default=1280, 
                        help='Image size in pixels (square image)')
    parser.add_argument('--maptype', default="satellite", 
                        choices=['roadmap', 'satellite', 'hybrid', 'terrain'], 
                        help='Map type')
    parser.add_argument('--date', help='Date for historical imagery (format: YYYY-MM-DD or YYYY-MM)')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    CSV_PATH = args.csv
    API_KEY = os.getenv("GOOGLE_MAPS_STATIC_API_KEY")
    if not API_KEY:
        print("Error: GOOGLE_MAPS_STATIC_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment variables.")
        exit(1)
        
    OUT_DIR = args.output
    GROUND_DISTANCE_KM = args.distance
    IMAGE_SIZE = args.size
    MAPTYPE = args.maptype
    TIMESTAMP = args.date
    
    # Print configuration
    print(f"Configuration:")
    print(f"  CSV file: {CSV_PATH}")
    print(f"  Output directory: {OUT_DIR}")
    print(f"  Ground distance: {GROUND_DISTANCE_KM} km")
    print(f"  Image size: {IMAGE_SIZE}x{IMAGE_SIZE} pixels")
    print(f"  Map type: {MAPTYPE}")
    print(f"  Date: {TIMESTAMP if TIMESTAMP else 'Current (latest available)'}")
    
    # Check if CSV file exists
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file '{CSV_PATH}' not found.")
        exit(1)
    
    # Take screenshots
    screenshot_all_csv_locations(
        CSV_PATH, API_KEY, OUT_DIR, 
        ground_distance_km=GROUND_DISTANCE_KM,
        image_size=IMAGE_SIZE,
        maptype=MAPTYPE, 
        timestamp=TIMESTAMP
    )