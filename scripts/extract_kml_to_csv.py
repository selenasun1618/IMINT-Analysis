import argparse
import csv
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# KML namespaces
NS = {
    "kml": "http://www.opengis.net/kml/2.2",
    "gx": "http://www.google.com/kml/ext/2.2",
    "atom": "http://www.w3.org/2005/Atom",
}


def parse_kml_points(kml_path: Path):
    """Yield (name, lat, lon) tuples for each Placemark with a Point in the KML."""
    tree = ET.parse(kml_path)
    root = tree.getroot()

    for pm in root.findall('.//kml:Placemark', NS):
        # Placemark name (optional)
        name_el = pm.find('kml:name', NS)
        name = name_el.text.strip() if name_el is not None and name_el.text else ""

        # Coordinates from Point (lon,lat[,alt])
        coord_el = pm.find('.//kml:Point/kml:coordinates', NS)
        if coord_el is None or (coord_el.text or '').strip() == "":
            continue
        coord_text = coord_el.text.strip()

        # coordinates may contain multiple tuples separated by whitespace
        first_tuple = coord_text.split()[0]
        parts = first_tuple.split(',')
        if len(parts) < 2:
            continue
        try:
            lon = float(parts[0])
            lat = float(parts[1])
        except ValueError:
            continue

        yield (name, lat, lon)


def write_csv(rows, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["name", "latitude", "longitude"])
        for name, lat, lon in rows:
            writer.writerow([name, f"{lat:.8f}", f"{lon:.8f}"])


def main():
    parser = argparse.ArgumentParser(description="Extract Placemark Point coordinates from KML into a CSV.")
    parser.add_argument("kml", type=Path, help="Path to input KML file")
    parser.add_argument("csv", type=Path, nargs="?", help="Path to output CSV (default: <kml>.csv)")
    args = parser.parse_args()

    kml_path: Path = args.kml
    if not kml_path.exists():
        print(f"Error: file not found: {kml_path}")
        sys.exit(1)

    out_csv = args.csv or kml_path.with_suffix('.csv')

    rows = list(parse_kml_points(kml_path))
    if not rows:
        print("Warning: no Placemark Point coordinates found.")
    write_csv(rows, out_csv)

    print(f"✅ Wrote {len(rows)} rows to {out_csv}")


if __name__ == "__main__":
    main()
