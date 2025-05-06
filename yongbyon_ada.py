import zipfile
import os
from xml.etree import ElementTree as ET
import math
import pandas as pd
import json

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

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth (specified in decimal degrees). Returns miles."""

    # convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    # haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 3958.8  # Radius of earth (mi)
    return c * r

def count_nearby_sites(placemark_data, target_coord, keywords, radius_miles):
    """Counts placemarks matching keywords within radius_miles of target_coord."""
    count = 0
    matching_sites = []
    for site in placemark_data:
        if any(keyword in site['name'].lower() for keyword in keywords):
            distance = haversine_distance(site['lat'], site['lon'], target_coord[0], target_coord[1])
            if distance <= radius_miles:
                count += 1
                matching_sites.append(site)
    return count, matching_sites


def analyze_kmz_sites(kmz_path, kml_extract_path, kml_filename, target_sites, radius_miles, keywords):
    """
    Extracts KMZ, parses KML, and summarizes nearby sites.
    Returns a DataFrame summary.
    """
    if target_sites is None:
        target_sites = {
            "Yongbyon Nuclear Science and Weapons center": (39.7961, 125.7558),
            "Kangson U enrichment plant": (38.9513, 125.6123),
            "Pyongsan uranium mine and mill": (38.200, 126.4365),
            "Yongbyon U enrichment": (39.7679, 125.7511),
            "Yongbyon Pu reprocessing": (39.7802, 125.7535)
        }
    if keywords is None:
        keywords = ['aaa']

    extract_kmz(kmz_path, kml_extract_path)
    kml_file_path = os.path.join(kml_extract_path, kml_filename)
    placemark_data = parse_kml_placemarks(kml_file_path)

    results = {}
    for name, coord in target_sites.items():
        count, matches = count_nearby_sites(placemark_data, coord, keywords, radius_miles)
        results[name] = {
            'count': count,
            'matches': matches
        }

    keywords_label = ', '.join(keywords)
    col_name = f"Nearby {keywords_label} Sites (within {radius_miles} miles)"
    summary_df = pd.DataFrame([
        {"Location": name, col_name: data['count']}
        for name, data in results.items()
    ]).sort_values(by=col_name, ascending=False)

    return summary_df, results

def main():
    kmz_path="NKEconWatch_2010.kmz"
    kml_extract_path="NKEconWatch_2010"
    kml_filename="doc.kml"
    target_sites = {
            "Yongbyon Nuclear Science and Weapons center": (39.7961, 125.7558),
            "Kangson U enrichment plant": (38.9513, 125.6123),
            "Pyongsan uranium mine and mill": (38.200, 126.4365),
            "Yongbyon U enrichment": (39.7679, 125.7511),
            "Yongbyon Pu reprocessing": (39.7802, 125.7535)
        }
    radius_miles=5
    keywords=['aaa']
    
    summary_df, results = analyze_kmz_sites(kmz_path, kml_extract_path, kml_filename, target_sites, radius_miles, keywords)

    keyword_labels = ', '.join(keywords)
    results_with_metadata = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'keywords': keyword_labels,
        'radius_miles': radius_miles,
        'results': results
    }

    filename = f"results_{keyword_labels}_{radius_miles}miles.json"
    with open(filename, 'w') as json_file:
        json.dump(results_with_metadata, json_file, indent=4)
    
    print(summary_df)

if __name__ == "__main__":
    main()