import os
import math
import requests
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
from tqdm import tqdm

# CONFIG
COUNTRY = "North Korea"
BUFFER_DISTANCE = 2000  # meters
TILE_SIZE_KM = 0.5
IMAGE_SIZE_PX = 640
API_KEY = os.getenv("GOOGLE_MAPS_STATIC_API_KEY")
OUT_DIR = "static_api_images"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Download road network
print("Downloading road network...")
G = ox.graph_from_place(COUNTRY, network_type='drive')
roads = ox.graph_to_gdfs(G, nodes=False)

# 2. Buffer roads
print("Buffering roads...")
buffered = roads.buffer(BUFFER_DISTANCE)
unified = gpd.GeoSeries(buffered).unary_union
bounds = unified.bounds  # minx, miny, maxx, maxy

# 3. Generate 0.5km x 0.5km tiles
print("Generating grid...")
def create_grid(minx, miny, maxx, maxy, size_km):
    size_deg = size_km / 111  # rough degrees per km
    x_coords = list(frange(minx, maxx, size_deg))
    y_coords = list(frange(miny, maxy, size_deg))
    tiles = []
    for x in x_coords:
        for y in y_coords:
            tile = box(x, y, x + size_deg, y + size_deg)
            if unified.intersects(tile):
                tiles.append(tile.centroid)
    return tiles

def frange(start, stop, step):
    while start < stop:
        yield start
        start += step

tiles = create_grid(*bounds, TILE_SIZE_KM)
print(f"Total tiles to fetch: {len(tiles)}")

# 4. Download satellite images
def download_tile(lat, lon, name, zoom=18):
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom={zoom}&size={IMAGE_SIZE_PX}x{IMAGE_SIZE_PX}&maptype=satellite&key={API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        with open(os.path.join(OUT_DIR, f"{name}_{lat:.5f}_{lon:.5f}.png"), 'wb') as f:
            f.write(r.content)
    else:
        print(f"Failed to download: {lat},{lon} — Code {r.status_code}")

print("Downloading images...")
for i, pt in enumerate(tqdm(tiles)):
    download_tile(pt.y, pt.x, f"tile_{i}")
