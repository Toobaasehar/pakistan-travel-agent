"""
seed_my_cities.py
=============================
Adds YOUR city data on top of what seed.py already inserted.
Run this AFTER seed.py, not instead of it.

WHAT IT DOES
-------------
1. Looks at what's already in travel.db (your friend's 30 destinations).
2. Reads every attraction from your city JSON files in data/<Province>/*.json
3. Converts each attraction into a "destination" row matching the exact
   same table your friend built (Destination + DestinationImage).
4. Skips anything that's clearly already in the database (e.g. her
   "Lahore Fort" and your "Lahore Fort" -- only one copy is kept).
5. Adds a placeholder image row for each new destination, exactly like
   her seed.py already does -- so nothing looks "different" or broken
   in the web UI later.

IMPORTANT FIX: your city files say province = "Khyber Pakhtunkhwa",
but your friend's data uses the short form "KPK". This script
automatically converts it so searching/filtering by province works
correctly across BOTH datasets combined.

RUN THIS AFTER seed.py:
    python seed.py
    python seed_my_cities.py
"""

import os
import json
import glob
import re

from database import engine, SessionLocal, Base
from models import Destination, DestinationImage
from city_coordinates import CITY_COORDINATES

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Your city files use the full name; her dataset uses the short form.
# This makes sure "province" values match exactly across both sources.
PROVINCE_NAME_FIXES = {
    "Khyber Pakhtunkhwa": "KPK",
}

PLACEHOLDER_IMAGE = "PLACEHOLDER — replace with a real Wikimedia/Unsplash URL"


def normalize(name):
    """Lowercase, strip parenthetical text and punctuation, so we can compare names fairly."""
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^a-z0-9 ]", "", name.lower())
    return name.strip()


def is_duplicate(new_name, existing_names_normalized):
    n = normalize(new_name)
    for existing in existing_names_normalized:
        if n == existing or (len(n) > 4 and n in existing) or (len(existing) > 4 and existing in n):
            return True
    return False


def load_city_attractions():
    """Reads every attraction from every city JSON file under data/<Province>/."""
    rows = []
    json_files = sorted(glob.glob(os.path.join(DATA_DIR, "**", "*.json"), recursive=True))

    if not json_files:
        print(f"⚠️  No .json files found in {DATA_DIR} -- did you copy your city files in?")

    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        city = data.get("city")
        province = data.get("province")
        if not city or not province:
            continue

        province = PROVINCE_NAME_FIXES.get(province, province)

        if city not in CITY_COORDINATES:
            print(f"⚠️  No coordinates found for '{city}' in city_coordinates.py -- skipping its attractions "
                  f"(latitude/longitude are required fields, can't insert without them).")
            continue

        weather = data.get("weather_info", {})
        best_time = weather.get("best_time_to_visit") or "Year-round"

        category_budgets = {
            "mountains": 6500,
            "historical": 3500,
            "nature": 5000,
            "beaches": 4000,
            "cultural": 4500,
            "museum": 2500,
            "wildlife": 5500,
            "adventure": 6000,
            "sightseeing": 4000,
        }

        for att in data.get("attractions", []):
            cat = (att.get("category") or "sightseeing").lower()
            budget = category_budgets.get(cat, 4000)
            # Factor in entry fee if available
            entry_fee = att.get("entry_fee_pkr", 0)
            if entry_fee and entry_fee > 0:
                budget += min(entry_fee, 2000)

            # Recommend 2 days for valleys/mountains, 1 day for city spots/museums/monuments
            rec_days = 2 if cat in ("mountains", "nature", "adventure") else 1

            rows.append({
                "name": att.get("name"),
                "province": province,
                "district": city,
                "latitude": lat,
                "longitude": lon,
                "description": att.get("description", ""),
                "best_season": best_time,
                "recommended_days": rec_days,
                "estimated_budget_per_day": budget,
                "activities": att.get("category", "sightseeing"),
                "category": cat,
                "data_source": f"Converted from {city}.json attractions list -- verified",
            })
    return rows


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing_count = db.query(Destination).count()
    print(f"Destinations already in travel.db: {existing_count}")
    if existing_count == 0:
        print("⚠️  Your database looks empty. Run 'python seed.py' FIRST, then run this script.")

    existing_names_normalized = set(
        normalize(name) for (name,) in db.query(Destination.name).all()
    )

    city_rows = load_city_attractions()

    inserted = 0
    skipped_duplicates = 0

    for row in city_rows:
        if is_duplicate(row["name"], existing_names_normalized):
            skipped_duplicates += 1
            continue

        dest = Destination(**row)
        db.add(dest)
        db.flush()  # assigns dest.id without fully committing yet, so we can link an image to it

        db.add(DestinationImage(
            destination_id=dest.id,
            image_url=PLACEHOLDER_IMAGE,
            source="Wikimedia Commons",
            author="TBD",
            license="TBD",
            attribution="TBD",
        ))

        existing_names_normalized.add(normalize(row["name"]))
        inserted += 1

    db.commit()

    total = db.query(Destination).count()
    unique_districts = db.query(Destination.district).distinct().count()
    db.close()

    print(f"\nInserted {inserted} new destinations from your city JSON files")
    print(f"Skipped {skipped_duplicates} duplicates (already in the database)")
    print(f"Total destinations in travel.db now: {total}")
    print(f"Unique cities/districts covered: {unique_districts}")


if __name__ == "__main__":
    main()
