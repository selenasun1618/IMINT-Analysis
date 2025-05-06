import zipfile
import os
from xml.etree import ElementTree as ET
from geopy.distance import geodesic
import pandas as pd


kmz_path = "NKEconWatch_2010.kmz"
kml_extract_path = "NKEconWatch_2010"
with zipfile.ZipFile(kmz_path, 'r') as kmz:
    kmz.extractall(kml_extract_path)


kml_file_path = os.path.join(kml_extract_path, 'doc.kml')
tree = ET.parse(kml_file_path)
root = tree.getroot()

namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
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


target_sites = {
    "Yongbyon Nuclear Science and Weapons center": (39.7961, 125.7558),
    "Kangson U enrichment plant": (38.9513, 125.6123),
    "Pyongsan uranium mine and mill": (38.200, 126.4365),
    "Yongbyon U enrichment": (39.7679, 125.7511),
    "Yongbyon Pu reprocessing": (39.7802, 125.7535)
}
radius_miles = 5
keywords = ['aaa']

#we should add more target sites? can we add strategic hub into the map as well?

def count_nearby_sites(target_coord, keywords):
    count = 0
    matching_sites = []
    for site in placemark_data:
        if any(keyword in site['name'].lower() for keyword in keywords):
            distance = geodesic((site['lat'], site['lon']), target_coord).miles
            if distance <= radius_miles:
                count += 1
                matching_sites.append(site)
    return count, matching_sites


results = {}
for name, coord in target_sites.items():
    count, matches = count_nearby_sites(coord, keywords)
    results[name] = {
        'count': count,
        'matches': matches
    }

summary_df = pd.DataFrame([
    {"Location": name, "Nearby AAA Sites (within 5 miles)": data['count']}
    for name, data in results.items()
]).sort_values(by="Nearby AAA Sites (within 5 miles)", ascending=False)

summary_df

def main():
    pass

if __name__ == "__main__":
    main()