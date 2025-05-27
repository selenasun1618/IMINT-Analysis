import zipfile
from dotenv import load_dotenv
import os
import requests
from xml.etree import ElementTree as ET

def extract_kmz(kmz_path, extract_to):
    """Extracts a KMZ file to the specified directory."""
    with zipfile.ZipFile(kmz_path, 'r') as kmz:
        kmz.extractall(extract_to)

def parse_kml_placemarks(kml_file_path):
    """Parses a KML file and returns a list of placemark dicts with name, lat, lon."""
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
    tree = ET.parse(kml_file_path)
    root = tree.getroot()
    placemarks = root.findall('.//kml:Placemark', namespace)
    placemark_data = []
    for placemark in placemarks:
        name_elem = placemark.find('kml:name', namespace)
        coord_elem = placemark.find('.//kml:coordinates', namespace)
        if name_elem is not None and coord_elem is not None:
            name = name_elem.text.strip()
            coords_text = coord_elem.text.strip()
            lon, lat, *_ = map(float, coords_text.split(','))
            placemark_data.append({
                'name': name,
                'lat': lat,
                'lon': lon
            })
    return placemark_data

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


def screenshot_all_kml_locations(kml_path, api_key, out_dir, ground_distance_km=1.0, image_size=640, maptype='satellite', timestamp=None):
    """Takes screenshots of all KML locations using the Google Maps Static API.
    
    Args:
        kml_path: Path to the KML file
        api_key: Google Maps API key
        out_dir: Directory to save images to
        ground_distance_km: Desired ground distance in kilometers (width/height of the image)
        image_size: Size of the image in pixels (square image)
        maptype: Map type ('roadmap', 'satellite', 'hybrid', 'terrain')
        timestamp: Optional timestamp for historical imagery (format: 'YYYY-MM-DD', 'YYYY-MM', or Unix timestamp)
    """
    os.makedirs(out_dir, exist_ok=True)
    placemarks = parse_kml_placemarks(kml_path)
    total = len(placemarks)
    print(f"Total images to screenshot: {total}")
    print(f"Ground distance per image: {ground_distance_km} km")
    print(f"Image size: {image_size}x{image_size} pixels")
    
    for idx, pm in enumerate(placemarks, 1):
        save_static_map_image(
            pm['lat'], pm['lon'], pm['name'], api_key, out_dir, 
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
    parser = argparse.ArgumentParser(description='Take screenshots of KML locations using Google Maps Static API')
    parser.add_argument('--kmz', default="NKEconWatch_2010.kmz", help='Path to KMZ file')
    parser.add_argument('--output', default="google_earth_screenshots", help='Output directory for screenshots')
    parser.add_argument('--distance', type=float, default=1.0, 
                        help='Ground distance in kilometers (width/height of the image)')
    parser.add_argument('--size', type=int, default=640, 
                        help='Image size in pixels (square image)')
    parser.add_argument('--maptype', default="satellite", 
                        choices=['roadmap', 'satellite', 'hybrid', 'terrain'], 
                        help='Map type')
    parser.add_argument('--date', help='Date for historical imagery (format: YYYY-MM-DD or YYYY-MM)')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    KMZ_PATH = args.kmz
    KML_EXTRACT_PATH = "extracted_coordinates"
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
    print(f"  KMZ file: {KMZ_PATH}")
    print(f"  Output directory: {OUT_DIR}")
    print(f"  Ground distance: {GROUND_DISTANCE_KM} km")
    print(f"  Image size: {IMAGE_SIZE}x{IMAGE_SIZE} pixels")
    print(f"  Map type: {MAPTYPE}")
    print(f"  Date: {TIMESTAMP if TIMESTAMP else 'Current (latest available)'}")
    
    # Extract KMZ file
    extract_kmz(KMZ_PATH, KML_EXTRACT_PATH)
    
    # Find KML file
    kml_files = [f for f in os.listdir(KML_EXTRACT_PATH) if f.lower().endswith('.kml')]
    if not kml_files:
        print(f"Error: No KML files found in {KML_EXTRACT_PATH}")
        exit(1)
    KML_PATH = os.path.join(KML_EXTRACT_PATH, kml_files[0])
    
    # Take screenshots
    screenshot_all_kml_locations(
        KML_PATH, API_KEY, OUT_DIR, 
        ground_distance_km=GROUND_DISTANCE_KM,
        image_size=IMAGE_SIZE,
        maptype=MAPTYPE, 
        timestamp=TIMESTAMP
    )