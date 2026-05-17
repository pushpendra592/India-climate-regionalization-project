"""
CLI entrypoint for exact-location or place-name-based climate cluster prediction.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prediction.location_predictor import LocationPredictor


predictor = LocationPredictor()


def build_parser():
    parser = argparse.ArgumentParser(description="Predict climate cluster for one exact location.")
    parser.add_argument("--lat", type=float, help="Latitude of the target location.")
    parser.add_argument("--lon", type=float, help="Longitude of the target location.")
    parser.add_argument("--place", type=str, help="Free-form place name instead of raw coordinates.")
    parser.add_argument("--city", type=str, help="Alias for --place.")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()

    place_name = args.place or args.city
    if place_name:
        result = predictor.predict_place(place_name)
    else:
        if args.lat is None or args.lon is None:
            raise SystemExit("Provide either --place <name> or both --lat and --lon.")
        result = predictor.predict(args.lat, args.lon)

    print("\nExact Location Climate Cluster Prediction")
    print("=" * 50)
    if result.get("location_name"):
        location_line = result["location_name"]
        if result.get("state"):
            location_line = f"{location_line}, {result['state']}"
        print(f"Location: {location_line}")
    if result.get("address"):
        print(f"Resolved address: {result['address']}")
    print(f"Coordinates: ({result['latitude']}, {result['longitude']})")
    print(f"Best training algorithm: {result['best_algorithm']}")
    print(f"Assigned cluster: {result['cluster_id']}")
    print(f"Cluster label: {result['cluster_label']}")
    print(f"Assignment method: {result['assignment_method']}")
    print(f"Summary: {result['summary']}")
    print("\nTop cluster characteristics:")
    for item in result["top_characteristics"]:
        print(f"  - {item['summary']} (cluster={item['cluster_mean']}, India sample={item['global_mean']})")

    if result["nearest_examples"]:
        print("\nNearest training points in the same cluster:")
        for item in result["nearest_examples"]:
            print(
                f"  - ({item['latitude']}, {item['longitude']}) "
                f"[distance={item['distance_deg']} degrees]"
            )
