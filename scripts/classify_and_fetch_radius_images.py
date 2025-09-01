import os
import math
import time
import json
from typing import Iterator, Tuple
import sys
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'evals'))
from aaa_prompts import FEW_SHOT_PROMPT
from static_api_AAA_collection import (
    save_static_map_image,
    build_gmaps_static_url,
)


def km_per_deg_lat() -> float:
    return 110.574


def km_per_deg_lon(lat_deg: float) -> float:
    return 111.320 * math.cos(math.radians(lat_deg))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_tile_centers(lat: float, lon: float, radius_km: float, tile_km: float) -> Iterator[Tuple[float, float]]:
    dlat_deg = tile_km / km_per_deg_lat()
    dlon_deg = tile_km / max(1e-9, km_per_deg_lon(lat))

    lat_deg_radius = radius_km / km_per_deg_lat()
    lon_deg_radius = radius_km / max(1e-9, km_per_deg_lon(lat))

    min_lat = lat - lat_deg_radius
    max_lat = lat + lat_deg_radius
    min_lon = lon - lon_deg_radius
    max_lon = lon + lon_deg_radius

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


def classify_image_url(client: OpenAI, model: str, image_url: str) -> str:
    """Return 'yes' or 'no' using the model on an image URL with structured output."""
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "aaa_presence",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "aaa_present": {"type": "string", "enum": ["yes", "no"]}
                        },
                        "required": ["aaa_present"],
                        "additionalProperties": False
                    },
                    "strict": True,
                },
            },
            messages=[
                {
                    "role": "developer",
                    "content": FEW_SHOT_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Does this image contain an anti-aircraft artillery (AAA) site?"},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        ans = str(data.get("aaa_present", "no")).strip().lower()
        return "yes" if ans == "yes" else "no"
    except Exception as e:
        print(f"Classification error: {e}")
        return "no"


def _sanitize_tag(s: str) -> str:
    """Sanitize a tag for folder names (replace problematic chars)."""
    return str(s).replace(":", "_").replace("/", "_").replace("\\", "_")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Classify tiles within a radius using a fine-tuned model; only save tiles predicted 'yes'.")
    parser.add_argument("--lat", type=float, required=True, help="Center latitude")
    parser.add_argument("--lon", type=float, required=True, help="Center longitude")
    parser.add_argument("--radius_km", type=float, required=True, help="Radius in kilometers")
    parser.add_argument("--output", default="../IMINT-Images/AAA_found_NK", help="Output directory for images (only 'yes' saved)")
    parser.add_argument("--tile_km", type=float, default=2.0, help="Tile width/height in km (default 2.0)")
    parser.add_argument("--size", type=int, default=1024, help="Image size in pixels (square)")
    parser.add_argument("--maptype", default="satellite", choices=["roadmap", "satellite", "hybrid", "terrain"], help="Map type")
    parser.add_argument("--date", help="Date for historical imagery (YYYY-MM or YYYY-MM-DD)")
    parser.add_argument("--name_prefix", default="AAA", help="Filename prefix for saved images")
    parser.add_argument("--model", default="ft:gpt-4o-2024-08-06:vannevar-labs::Buk6Uyac", help="OpenAI model (use your fine-tuned model id if available)")
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep seconds between classifications to avoid rate limits")

    args = parser.parse_args()

    load_dotenv()
    gmaps_key = os.getenv("GOOGLE_MAPS_STATIC_API_KEY")
    if not gmaps_key:
        print("Error: GOOGLE_MAPS_STATIC_API_KEY not set.")
        raise SystemExit(1)

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OPENAI_API_KEY not set.")
        raise SystemExit(1)

    client = OpenAI(api_key=openai_key)

    # Compute centers first so we can include total count in folder name
    centers = list(generate_tile_centers(args.lat, args.lon, args.radius_km, args.tile_km))
    total = len(centers)

    # Build output subfolder in the requested format:
    # AAA_found_{lat}_{lon}_R{radius km}_T{tile km}_{model}_{num-total-images}_{date}
    # Example: AAA_found_39.064618_125.956587_R5.0km_T1.0km_ft_gpt-4o-2024-08-06_56-total-images_Aug-22-2025
    coords = f"{args.lat:.6f}_{args.lon:.6f}"
    radius_str = f"{args.radius_km:.1f}km"
    tile_str = f"{args.tile_km:.1f}km"
    date_str = datetime.now().strftime("%b-%d-%Y")
    model_tag = _sanitize_tag(args.model)
    subfolder = f"AAA_found_{coords}_R{radius_str}_T{tile_str}_{model_tag}_{total}-total-images_{date_str}"
    out_dir = os.path.join(args.output, subfolder)
    os.makedirs(out_dir, exist_ok=True)

    # Progress tracking for resumable runs
    progress_path = os.path.join(out_dir, "progress.json")
    start_index = 1
    if os.path.isfile(progress_path):
        try:
            with open(progress_path, "r") as pf:
                prog = json.load(pf)
                last_processed = int(prog.get("last_processed", 0))
                # Ensure within bounds
                if 1 <= last_processed < total:
                    start_index = last_processed + 1
        except Exception as e:
            print(f"Warning: could not read progress file '{progress_path}': {e}. Starting from 1.")

    print(f"Resume mode: starting from index {start_index} of {total}")

    print("Configuration:")
    print(f"  Center: ({args.lat}, {args.lon})")
    print(f"  Radius: {args.radius_km} km")
    print(f"  Tile size: {args.tile_km} km; image size: {args.size}")
    print(f"  Output directory (only 'yes' saved): {out_dir}")
    print(f"  Model: {args.model}")
    print(f"  Total tiles to evaluate: {total}")

    saved = 0
    for idx, (tlat, tlon) in enumerate(centers, 1):
        # Skip already processed indices when resuming
        if idx < start_index:
            continue
        # Build URL first for classification
        url = build_gmaps_static_url(
            tlat,
            tlon,
            gmaps_key,
            ground_distance_km=args.tile_km,
            image_size=args.size,
            maptype=args.maptype,
            timestamp=args.date,
            scale=2,
        )

        label = classify_image_url(client, args.model, url)
        print(f"[{idx}/{total}] Classification: {label} at ({tlat:.5f},{tlon:.5f})")

        if label == "yes":
            # Filenames do not include numeric indices; helper will append lat/lon/km.
            name = f"{args.name_prefix}"
            ok = save_static_map_image(
                tlat,
                tlon,
                name,
                gmaps_key,
                out_dir,
                ground_distance_km=args.tile_km,
                image_size=args.size,
                maptype=args.maptype,
                timestamp=args.date,
                current=idx,
                total=total,
            )
            if ok:
                saved += 1
        # Update progress after handling this tile (regardless of label)
        try:
            with open(progress_path, "w") as pf:
                json.dump({
                    "last_processed": idx,
                    "saved_in_this_run": saved,
                    "total": total,
                    "timestamp": datetime.now().isoformat()
                }, pf)
        except Exception as e:
            print(f"Warning: could not write progress file '{progress_path}': {e}")
        time.sleep(max(0.0, args.sleep))

    print(f"\nFinished. {saved} images saved (predicted 'yes') out of {total} evaluated tiles.")


if __name__ == "__main__":
    main()
