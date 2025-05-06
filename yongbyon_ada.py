import zipfile
import os
import io
from xml.etree import ElementTree as ET
import math
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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
    st.title("Yongbyon ADA Analysis")

    kmz_file = st.file_uploader("Upload KMZ file", type=["kmz"])
    if not kmz_file:
        st.info("Please upload a KMZ file to continue.")
        return

    # Save uploaded file
    kmz_path = "uploaded.kmz"
    kml_extract_path = "uploaded_kml"
    kml_filename = "doc.kml"
    with open(kmz_path, "wb") as f:
        f.write(kmz_file.read())

    # User input for target location and parameters
    st.sidebar.header("Target Site Parameters")
    lat_str = st.sidebar.text_input("Target Latitude", value="39.7961")
    lon_str = st.sidebar.text_input("Target Longitude", value="125.7558")
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except ValueError:
        st.sidebar.error("Please enter valid numbers for latitude and longitude.")
        return
    radius_miles = st.sidebar.number_input("Radius (miles)", value=5.0, min_value=0.1, step=0.1, format="%f")
    keywords_str = st.sidebar.text_input("Keywords (comma separated)", value="aaa")
    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

    # Extract and parse KMZ/KML
    extract_kmz(kmz_path, kml_extract_path)
    kml_file_path = os.path.join(kml_extract_path, kml_filename)
    placemark_data = parse_kml_placemarks(kml_file_path)

    # Find matching sites
    count, matching_sites = count_nearby_sites(placemark_data, (lat, lon), keywords, radius_miles)
    st.write(f"Found {count} matching sites within {radius_miles} miles of ({lat}, {lon}) for keywords: {', '.join(keywords)}")

    # Prepare DataFrame for display and mapping
    if matching_sites:
        df = pd.DataFrame(matching_sites)

        # --- Download KMZ for found sites ---
        def generate_kml(sites):
            kml = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<kml xmlns="http://www.opengis.net/kml/2.2">',
                '  <Document>'
            ]
            for site in sites:
                kml.append(f'''    <Placemark>\n      <name>{site['name']}</name>\n      <Point><coordinates>{site['lon']},{site['lat']},0</coordinates></Point>\n    </Placemark>''')
            kml.append('  </Document>')
            kml.append('</kml>')
            return '\n'.join(kml)

        kml_str = generate_kml(matching_sites)
        kml_bytes = kml_str.encode("utf-8")
        kmz_buf = io.BytesIO()
        with zipfile.ZipFile(kmz_buf, 'w', zipfile.ZIP_DEFLATED) as kmz:
            kmz.writestr('doc.kml', kml_bytes)
        kmz_buf.seek(0)
        st.download_button(
            label="Download found sites as KMZ",
            data=kmz_buf,
            file_name=f"found_sites_{radius_miles}miles_{'_'.join(keywords)}.kmz",
            mime="application/vnd.google-earth.kmz"
        )

        # Plot map with pins and a radius circle using scattermap (Plotly Maplibre)
        fig = px.scatter_map(
            df,
            lat="lat",
            lon="lon",
            hover_name="name",
            zoom=9,
            height=600,
        )
        # Add target location as a marker (with legend)
        target_trace = px.scatter_map(
            pd.DataFrame({"lat": [lat], "lon": [lon], "name": ["Target Site"]}),
            lat="lat", lon="lon", hover_name="name",
            size=[16], color_discrete_sequence=["red"]
        ).data[0]
        target_trace.name = "Target Site"
        target_trace.showlegend = True
        fig.add_trace(target_trace)
        # Draw a circle for the search radius using line_map (with legend)
        theta = np.linspace(0, 2 * np.pi, 100)
        earth_radius = 3958.8  # miles
        dlat = (radius_miles / earth_radius) * (180 / np.pi)
        dlon = dlat / np.cos(np.radians(lat))
        circle_lat = lat + dlat * np.sin(theta)
        circle_lon = lon + dlon * np.cos(theta)
        circle_df = pd.DataFrame({"lat": circle_lat, "lon": circle_lon})
        radius_trace = px.line_map(
            circle_df,
            lat="lat",
            lon="lon",
        ).data[0]
        radius_trace.line = dict(width=2, color="blue")
        radius_trace.name = f"{radius_miles} mile radius"
        radius_trace.showlegend = True
        fig.add_trace(radius_trace)

        fig.update_layout(
            mapbox_style="maplibre",
            mapbox_center_lat=lat,
            mapbox_center_lon=lon,
            margin={"r":0,"t":0,"l":0,"b":0},
            mapbox_zoom=9,
            autosize=True,
            dragmode='zoom',
        )
        st.plotly_chart(fig, use_container_width=True)
        st.write("")
        st.write("")
        st.write("")
        st.dataframe(df)
    else:
        st.warning("No matching sites found.")

if __name__ == "__main__":
    main()