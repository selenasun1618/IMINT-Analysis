import re
import pandas as pd

raw_data = 'csv'
# 1) Fix the bad characters
raw_data = raw_data.replace("�", "°")

# 2) Convert to decimals
def parse_dd(coord: str) -> float:
    """
    Convert a coordinate of the form '12.345°N' / '12.345°S' / '12.345°E' / '12.345°W'
    to signed decimal degrees.
    """
    m = re.fullmatch(r"([0-9.+-]+)°?([NSEW])", coord)
    if not m:
        raise ValueError(f"Bad coordinate: {coord!r}")
    value, hemi = float(m.group(1)), m.group(2)
    return -value if hemi in "SW" else value

rows = []
for line in raw_data.splitlines()[1:]:                    # skip the header
    name, lat_str, lon_str = [s.strip() for s in line.split(",", 2)]
    rows.append({
        "Name":       name,
        "Latitude":   parse_dd(lat_str),
        "Longitude":  parse_dd(lon_str),
    })

# 3) Write to CSV ---------------------------------------------------------------
df = pd.DataFrame(rows)
df.to_csv("china_nuclear_sites_cleaned.csv", index=False)

print("Saved → china_nuclear_sites_cleaned.csv")