"""
Unified Seed Script
===================
Combines base destinations from destinations_data.py and city attractions
from data/<Province>/*.json into a single unified database seeding process.

Features:
- Initializes database schema.
- Inserts curated baseline destinations (destinations_data.py).
- Parses JSON files in data/<Province>/*.json using city_coordinates.py.
- Normalizes names and automatically skips duplicates.
- Fixes province naming inconsistencies (e.g. 'Khyber Pakhtunkhwa' -> 'KPK').
- Attaches DestinationImage placeholder rows for each inserted record.

Run with:
    python seed.py
"""

import os
import glob
import json
import re
from database import engine, SessionLocal, Base
from models import Destination, DestinationImage
from destinations_data import DESTINATIONS

# Optional import for city coordinates from JSON files
try:
    from city_coordinates import CITY_COORDINATES
except ImportError:
    CITY_COORDINATES = {}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PLACEHOLDER_IMAGE = "PLACEHOLDER — replace with a real Wikimedia/Unsplash URL"

# Makes sure province names match across both sources
PROVINCE_NAME_FIXES = {
    "Khyber Pakhtunkhwa": "KPK",
    "kpk": "KPK",
    "khyber": "KPK",
}


def normalize(name: str) -> str:
    """Lowercase, strip parenthetical text and punctuation for fair name comparison."""
    if not name:
        return ""
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^a-z0-9 ]", "", name.lower())
    return name.strip()


def is_duplicate(new_name: str, existing_names_normalized: set) -> bool:
    """Checks whether the attraction/destination is already present."""
    n = normalize(new_name)
    if not n:
        return True
    for existing in existing_names_normalized:
        if n == existing or (len(n) > 4 and n in existing) or (len(existing) > 4 and existing in n):
            return True
    return False


def load_city_attractions() -> list:
    """Reads attractions from all city JSON files under data/<Province>/."""
    rows = []
    json_files = sorted(glob.glob(os.path.join(DATA_DIR, "**", "*.json"), recursive=True))

    if not json_files:
        print(f"ℹ️  No JSON files found in '{DATA_DIR}' — skipping city JSON import.")
        return rows

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

    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading {filepath}: {e}")
            continue

        city = data.get("city")
        province = data.get("province")
        if not city or not province:
            continue

        province = PROVINCE_NAME_FIXES.get(province, province)

        if city not in CITY_COORDINATES:
            print(f"⚠️  No coordinates found for '{city}' in city_coordinates.py — skipping.")
            continue

        lat, lon = CITY_COORDINATES[city]
        weather = data.get("weather_info", {})
        best_time = weather.get("best_time_to_visit") or "Year-round"

        for att in data.get("attractions", []):
            cat = (att.get("category") or "sightseeing").lower()
            budget = category_budgets.get(cat, 4000)

            # Factor in entry fee if available
            entry_fee = att.get("entry_fee_pkr", 0)
            if entry_fee and entry_fee > 0:
                budget += min(entry_fee, 2000)

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


def seed_database():
    """Main database seed orchestration."""
    print("🚀 Initializing Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing_names_normalized = set(
        normalize(name) for (name,) in db.query(Destination.name).all()
    )

    total_inserted = 0
    total_skipped = 0

    # -------------------------------------------------------------
    # Step 1: Insert Core Baseline Destinations (destinations_data)
    # -------------------------------------------------------------
    print("📦 Seeding core destinations from destinations_data.py...")
    base_inserted = 0
    for entry in DESTINATIONS:
        if is_duplicate(entry.get("name", ""), existing_names_normalized):
            total_skipped += 1
            continue

        dest = Destination(**entry)
        db.add(dest)
        db.flush()

        db.add(DestinationImage(
            destination_id=dest.id,
            image_url=PLACEHOLDER_IMAGE,
            source="Wikimedia Commons",
            author="TBD",
            license="TBD",
            attribution="TBD",
        ))

        existing_names_normalized.add(normalize(dest.name))
        base_inserted += 1

    db.commit()
    total_inserted += base_inserted
    print(f"   ✓ Inserted {base_inserted} core destinations.")

    # -------------------------------------------------------------
    # Step 2: Insert Additional Cities & Attractions (JSON files)
    # -------------------------------------------------------------
    print("🏙️  Seeding city attractions from data directory...")
    city_rows = load_city_attractions()
    city_inserted = 0

    for row in city_rows:
        if is_duplicate(row.get("name", ""), existing_names_normalized):
            total_skipped += 1
            continue

        dest = Destination(**row)
        db.add(dest)
        db.flush()

        db.add(DestinationImage(
            destination_id=dest.id,
            image_url=PLACEHOLDER_IMAGE,
            source="Wikimedia Commons",
            author="TBD",
            license="TBD",
            attribution="TBD",
        ))

        existing_names_normalized.add(normalize(row["name"]))
        city_inserted += 1

    db.commit()
    total_inserted += city_inserted
    print(f"   ✓ Inserted {city_inserted} destinations from city JSON files.")

    # -------------------------------------------------------------
    # Summary Report
    # -------------------------------------------------------------
    total_in_db = db.query(Destination).count()
    unique_districts = db.query(Destination.district).distinct().count()
    db.close()

    print("\n" + "="*45)
    print("🎉 SEEDING COMPLETE")
    print("="*45)
    print(f"• Newly Inserted Destinations : {total_inserted}")
    print(f"• Duplicates Skipped          : {total_skipped}")
    print(f"• Total Destinations in DB    : {total_in_db}")
    print(f"• Unique Districts Covered    : {unique_districts}")
    print("="*45)


if __name__ == "__main__":
    seed_database()