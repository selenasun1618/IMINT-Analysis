import os
import math
from typing import Iterator, Tuple
from dotenv import load_dotenv

# Reuse existing download helper
from static_api_AAA_collection import save_static_map_image


def km_per_deg_lat() -> float:
    """Approximate km per degree latitude (fairly constant)."""
    return 110.574


def km_per_deg_lon(lat_deg: float) -> float:
    """Approximate km per degree longitude at a given latitude."""
    return 111.320 * math.cos(math.radians(lat_deg))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between (lat1,lon1) and (lat2,lon2) in km."""
    R = 6371.0088
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_tile_centers(lat: float, lon: float, radius_km: float, tile_km: float) -> Iterator[Tuple[float, float]]:
    """Yield centers on a grid spaced by tile_km that fall within radius_km of (lat, lon)."""
    # Convert km steps to degree steps at the center latitude
    dlat_deg = tile_km / km_per_deg_lat()
    # Use conservative lon degree using center latitude
    dlon_deg = tile_km / max(1e-9, km_per_deg_lon(lat))

    # Compute bounding box in degrees large enough to cover the radius
    lat_deg_radius = radius_km / km_per_deg_lat()
    lon_deg_radius = radius_km / max(1e-9, km_per_deg_lon(lat))

    min_lat = lat - lat_deg_radius
    max_lat = lat + lat_deg_radius
    min_lon = lon - lon_deg_radius
    max_lon = lon + lon_deg_radius

    # Iterate grid; filter by true distance to keep only tiles within radius
    i = 0
    lat_val = min_lat
    while lat_val <= max_lat + 1e-12:
        j = 0
        lon_val = min_lon
        while lon_val <= max_lon + 1e-12:
            if haversine_km(lat, lon, lat_val, lon_val) <= radius_km + 1e-9:
                yield (lat_val, lon_val)
            j += 1
            lon_val = min_lon + j * dlon_deg
        i += 1
        lat_val = min_lat + i * dlat_deg


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fetch 2x2 km satellite images within a radius of a coordinate using Google Static Maps API")
    parser.add_argument("--lat", type=float, required=True, help="Center latitude")
    parser.add_argument("--lon", type=float, required=True, help="Center longitude")
    parser.add_argument("--radius_km", type=float, required=True, help="Radius in kilometers")
    parser.add_argument("--output", default="../IMINT-Images/AAA_test_images_NK", help="Output directory for images")
    parser.add_argument("--tile_km", type=float, default=2.0, help="Tile width/height in km (default 2.0 for 2x2 km images)")
    parser.add_argument("--size", type=int, default=640, help="Image size in pixels (square)")
    parser.add_argument("--maptype", default="satellite", choices=["roadmap", "satellite", "hybrid", "terrain"], help="Map type")
    parser.add_argument("--date", help="Date for historical imagery (YYYY-MM or YYYY-MM-DD)")
    parser.add_argument("--name_prefix", default="AAA", help="Filename prefix for saved images")

    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_STATIC_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_STATIC_API_KEY environment variable is not set. Add it to your .env or environment.")
        raise SystemExit(1)

    os.makedirs(args.output, exist_ok=True)

    # Prepare tile centers
    centers = list(generate_tile_centers(args.lat, args.lon, args.radius_km, args.tile_km))
    total = len(centers)

    print("Configuration:")
    print(f"  Center: ({args.lat}, {args.lon})")
    print(f"  Radius: {args.radius_km} km")
    print(f"  Tile size: {args.tile_km} km")
    print(f"  Output directory: {args.output}")
    print(f"  Total tiles to fetch: {total}")

    saved = 0
    for idx, (tlat, tlon) in enumerate(centers, 1):
        name = f"{args.name_prefix}_{idx:04d}"
        ok = save_static_map_image(
            tlat,
            tlon,
            name,
            api_key,
            args.output,
            ground_distance_km=args.tile_km,
            image_size=args.size,
            maptype=args.maptype,
            timestamp=args.date,
            current=idx,
            total=total,
        )
        if ok:
            saved += 1

    print(f"\n✅ Finished. {saved} images saved out of {total} requested tiles.")


if __name__ == "__main__":
    main()
