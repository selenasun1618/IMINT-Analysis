import csv
import random

def generate_random_coordinates(n, output_path):
    # Approximate bounding box for North Korea
    min_lat = 37.5
    max_lat = 43.0
    min_lon = 124.0
    max_lon = 130.7

    header = [
        '', 'Y (North-South direction)', 'X (East-West direction)', 
        'Z', 'Name', 'Y/N', 'Correction', 'IMDATE Visible'
    ]

    rows = []
    for _ in range(n):
        lat = round(random.uniform(min_lat, max_lat), 6)
        lon = round(random.uniform(min_lon, max_lon), 6)
        row = ['', lat, lon, 0, 'AAA', 'Y', '', '']
        rows.append(row)

    # Write to CSV
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"✅ Generated {n} coordinates and saved to '{output_path}'")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate random coordinates in North Korea")
    parser.add_argument('--n', type=int, default=100, help='Number of coordinates to generate')
    parser.add_argument('--out', default='north_korea_coords.csv', help='Output CSV filename')

    args = parser.parse_args()
    generate_random_coordinates(args.n, args.out)