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

def build_gmaps_static_url(lat, lon, api_key, size=400, zoom=17, maptype='satellite'):
    """Constructs a Google Maps Static API URL for a given location."""
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        'center': f"{lat},{lon}",
        'zoom': str(zoom),
        'size': f"{size}x{size}",
        'maptype': maptype,
        'key': api_key
    }
    param_str = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{base_url}?{param_str}"

def save_static_map_image(lat, lon, name, api_key, out_dir, size=400, zoom=17, maptype='satellite', current=None, total=None):
    """Downloads and saves a Google Maps Static image for the location."""
    url = build_gmaps_static_url(lat, lon, api_key, size, zoom, maptype)
    response = requests.get(url)
    if response.status_code == 200:
        filename = f"{name.replace(' ', '_')}_{lat:.5f}_{lon:.5f}_{size}x{size}.png"
        filepath = os.path.join(out_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        if current is not None and total is not None:
            print(f"Saved ({current}/{total}): {filepath}")
        else:
            print(f"Saved: {filepath}")
    else:
        print(f"Failed to fetch image for {name} ({lat}, {lon}): {response.status_code} - {response.text}")


def screenshot_all_kml_locations(kml_path, api_key, out_dir, size=400, zoom=17, maptype='satellite'):
    """Takes X by X screenshots of all KML locations using the Google Maps Static API."""
    os.makedirs(out_dir, exist_ok=True)
    placemarks = parse_kml_placemarks(kml_path)
    total = len(placemarks)
    print(f"Total images to screenshot: {total}")
    for idx, pm in enumerate(placemarks, 1):
        save_static_map_image(
            pm['lat'], pm['lon'], pm['name'], api_key, out_dir, size=size, zoom=zoom, maptype=maptype,
            current=idx, total=total
        )

if __name__ == "__main__":
    load_dotenv()
    KMZ_PATH = "NKEconWatch_2010.kmz"
    KML_EXTRACT_PATH = "extracted_coordinates"
    API_KEY = os.getenv("GOOGLE_MAPS_STATIC_API_KEY")
    OUT_DIR = "google_earth_screenshots"
    SIZE = 400   # X by X pixels
    ZOOM = 17    # Adjust
    MAPTYPE = "satellite"  # 'roadmap', 'hybrid', 'terrain'

    extract_kmz(KMZ_PATH, KML_EXTRACT_PATH)

    kml_files = [f for f in os.listdir(KML_EXTRACT_PATH) if f.lower().endswith('.kml')]
    KML_PATH = os.path.join(KML_EXTRACT_PATH, kml_files[0])

    screenshot_all_kml_locations(KML_PATH, API_KEY, OUT_DIR, size=SIZE, zoom=ZOOM, maptype=MAPTYPE)