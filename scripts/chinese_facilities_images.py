import os
import re
import pandas as pd
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Reuse URL construction and download logic from the existing script
from static_api_AAA_collection import (
    dms_to_decimal,
    save_static_map_image,
)   


def read_csv_robust(csv_path: str) -> pd.DataFrame:
    """Read a CSV with best-effort encoding handling and trimmed column names."""
    encodings_to_try = [None, "utf-8", "utf-8-sig", "latin1", "cp1252", "utf-16", "utf-16le", "utf-16be"]
    last_err = None
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to read CSV '{csv_path}' with multiple encodings. Last error: {last_err}")


def best_name(row: pd.Series, idx: int) -> str:
    """Choose a name from common columns or synthesize one."""
    name_cols = [
        "Name",
        "Facility",
        "Site",
        "Title",
        "Location",
    ]
    for col in name_cols:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col]).strip()
    return f"Location_{idx}"


def parse_coord_value(val: object) -> Optional[float]:
    """Parse a coordinate value that may be decimal, DD with hemisphere (e.g., 12.3°N), or DMS.

    Returns float or None if unparsable.
    """
    if pd.isna(val):
        return None
    s = str(val).strip().replace("�", "°")

    # Try direct float first
    try:
        return float(s)
    except ValueError:
        pass

    # Try removing degree symbol and parsing as float (e.g., "21.669727°" -> 21.669727)
    if "°" in s:
        try:
            return float(s.replace("°", ""))
        except ValueError:
            pass

    # Try DD with hemisphere, e.g., 12.345°N
    m = re.fullmatch(r"\s*([+-]?[0-9]*\.?[0-9]+)°?\s*([NnSsEeWw])\s*", s)
    if m:
        value = float(m.group(1))
        hemi = m.group(2).upper()
        if hemi in ("S", "W"):
            value = -value
        return value

    # Try DMS using existing helper (supports strings like 39° 5'27.29"N)
    try:
        return float(dms_to_decimal(s))
    except Exception:
        return None


def extract_coordinates(df: pd.DataFrame) -> List[Dict[str, object]]:
    """Extract coordinates from a DataFrame with flexible column detection.

    Looks for common latitude/longitude column names or combined fields.
    Returns list of {name, lat, lon} dicts for rows with valid coords.
    """
    # Debug: print available columns
    print(f"Available columns: {list(df.columns)}")
    
    # Candidate columns for latitude and longitude
    lat_candidates = [
        "Entrance Latitude",
        "Entrance Latitute",  # Handle typo in CSV
        "Latitude",
        "Lat",
        "LAT",
        "Y (North-South direction)",
        "Y",
        "Northing",
    ]
    lon_candidates = [
        "Entrance Longitude",
        "Longitude",
        "Lon",
        "LON",
        "X (East-West direction)",
        "X",
        "Easting",
    ]
    combined_candidates = [
        "Coordinates",
        "Coord",
        "Lat/Lon",
        "Location (Lat Lon)",
    ]

    # Resolve which columns exist
    def first_present(cands: List[str]) -> Optional[str]:
        for c in cands:
            # also try case-insensitive exact matches
            for col in df.columns:
                if col.strip() == c:
                    return col
                if col.strip().lower() == c.lower():
                    return col
        return None

    lat_col = first_present(lat_candidates)
    lon_col = first_present(lon_candidates)
    comb_col = first_present(combined_candidates)
    
    print(f"Found lat column: {lat_col}")
    print(f"Found lon column: {lon_col}")
    print(f"Found combined column: {comb_col}")

    coords: List[Dict[str, object]] = []
    for idx, row in df.iterrows():
        name = best_name(row, idx + 1)

        lat: Optional[float] = None
        lon: Optional[float] = None

        if lat_col and lon_col:
            lat_val = row.get(lat_col)
            lon_val = row.get(lon_col)
            print(f"Row {idx}: {name} - lat_val='{lat_val}', lon_val='{lon_val}'")
            lat = parse_coord_value(lat_val)
            lon = parse_coord_value(lon_val)
            print(f"  Parsed: lat={lat}, lon={lon}")
        elif comb_col:
            # Try to split combined like "39° 5'27.29\"N 125°37'2.83\"E" or "12.3N, 45.6E"
            val = row.get(comb_col)
            if pd.notna(val):
                s = str(val)
                # Common separators
                for sep in [",", ";", " "]:
                    parts = [p for p in s.replace("\u00A0", " ").split(sep) if p.strip()]
                    if len(parts) >= 2:
                        lat = parse_coord_value(parts[0])
                        lon = parse_coord_value(parts[1])
                        break
                # If still not parsed, try dms_to_decimal tuple mode from static script
                if (lat is None or lon is None) and ("N" in s.upper() or "S" in s.upper()) and ("E" in s.upper() or "W" in s.upper()):
                    try:
                        res = dms_to_decimal(s)
                        if isinstance(res, tuple) and len(res) == 2:
                            lat, lon = float(res[0]), float(res[1])
                    except Exception:
                        pass

        if lat is None or lon is None:
            # Skip if cannot parse
            continue

        coords.append({"name": name, "lat": lat, "lon": lon})

    return coords


def screenshot_china_facilities(csv_path: str, api_key: str, out_dir: str,
                                 ground_distance_km: float = 0.5,
                                 image_size: int = 640,
                                 maptype: str = "satellite",
                                 timestamp: Optional[str] = None) -> None:
    os.makedirs(out_dir, exist_ok=True)

    df = read_csv_robust(csv_path)
    coords = extract_coordinates(df)

    total = len(coords)
    print(f"Total coordinates to process: {total}")
    print(f"Output folder: {out_dir}")

    saved = 0
    for i, c in enumerate(coords, 1):
        expected_filename = f"{c['name'].replace(' ', '_')}_{c['lat']:.5f}_{c['lon']:.5f}_{ground_distance_km}km.png"
        expected_path = os.path.join(out_dir, expected_filename)
        if os.path.exists(expected_path):
            print(f"Skipping ({i}/{total}): {expected_filename} already exists")
            saved += 1
            continue

        ok = save_static_map_image(
            c["lat"], c["lon"], c["name"], api_key, out_dir,
            ground_distance_km=ground_distance_km,
            image_size=image_size,
            maptype=maptype,
            timestamp=timestamp,
            current=i,
            total=total,
        )
        if ok:
            saved += 1

    print(f"\n✅ Finished. {saved} images saved out of {total} valid coordinates.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch satellite images for Chinese facilities coordinates")
    parser.add_argument("--csv", default="coordinates/non_double_fences_ch_coords.csv", help="Path to the CSV file")
    parser.add_argument("--output", default="../IMINT-Images/Non_double_fences_all", help="Output directory for images")
    parser.add_argument("--distance", type=float, default=0.5, help="Ground distance in km for image width/height")
    parser.add_argument("--size", type=int, default=640, help="Image size in pixels (square)")
    parser.add_argument("--maptype", default="satellite", choices=["roadmap", "satellite", "hybrid", "terrain"], help="Map type")
    parser.add_argument("--date", help="Date for historical imagery (YYYY-MM or YYYY-MM-DD)")

    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_STATIC_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_STATIC_API_KEY environment variable is not set. Add it to your .env or environment.")
        raise SystemExit(1)

    if not os.path.exists(args.csv):
        print(f"Error: CSV file '{args.csv}' not found.")
        raise SystemExit(1)

    print("Configuration:")
    print(f"  CSV file: {args.csv}")
    print(f"  Output directory: {args.output}")
    print(f"  Ground distance: {args.distance} km")
    print(f"  Image size: {args.size}x{args.size}")
    print(f"  Map type: {args.maptype}")
    print(f"  Date: {args.date if args.date else 'Current (latest available)'}")

    screenshot_china_facilities(
        csv_path=args.csv,
        api_key=api_key,
        out_dir=args.output,
        ground_distance_km=args.distance,
        image_size=args.size,
        maptype=args.maptype,
        timestamp=args.date,
    )