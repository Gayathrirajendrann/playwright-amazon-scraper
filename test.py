import json
import os

INPUT_FILE = "product_urls.json"
OUTPUT_FILE = "urls_2.json"
BATCH_SIZE = 600


def process_json():
    # Step 1: Load input data
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list")

    # Step 2: Get last 1000 records
    batch = data[-BATCH_SIZE:]

    if not batch:
        print("No data to move")
        return

    # Step 3: Load existing output file (if exists)
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                output_data = json.load(f)
                if not isinstance(output_data, list):
                    output_data = []
            except:
                output_data = []
    else:
        output_data = []

    # Step 4: Append new batch
    output_data.extend(batch)

    # Save to output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Added {len(batch)} records to {OUTPUT_FILE}")

    # Step 5: Remove batch from input
    remaining = data[:-BATCH_SIZE]

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining, f, indent=2)

    print(f"Removed {len(batch)} records from {INPUT_FILE}")


if __name__ == "__main__":
    process_json()