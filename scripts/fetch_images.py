"""
fetch_images.py
=============================
Automatically fetches a real photo for every destination in your
database, using Wikipedia's free public API (no key/signup needed).

WHY THIS APPROACH instead of manually finding 119 individual URLs:
Wikipedia's REST API can look up a page by name and return its lead
image directly. This gets you real, properly-sourced photos for
nearly all destinations in one run, instead of one-by-one manual
searching -- which would take hours for 119 entries.

WHAT IT DOES
-------------
1. Goes through every destination in your database.
2. Searches Wikipedia for a matching page (e.g. "Badshahi Mosque").
3. If found, updates that destination's image with:
     - the real photo URL
     - source = "Wikipedia"
     - attribution = a link back to the Wikipedia page (so credit is
       always visible, matching your project's existing honesty rule)
4. If NOT found (some smaller/local spots won't have a Wikipedia
   page), it leaves the placeholder alone rather than guessing wrong.

IMPORTANT HONESTY NOTE (same spirit as your data_source fields):
Automated name-matching isn't perfect. A few results may be a
near-match rather than the exact spot (e.g. a valley vs. a specific
viewpoint in it). This prints a report at the end -- spot-check a
handful before treating every image as fully verified, the same way
your coordinates are flagged as "needs verification."

RUN (after seed.py and seed_my_cities.py have already run once):
    python fetch_images.py

Safe to re-run -- it updates existing image rows rather than
duplicating them.
"""

import time
import urllib.request
import urllib.parse
import json

from database import SessionLocal
from models import Destination, DestinationImage

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
HEADERS = {"User-Agent": "PakistanTravelAgentStudentProject/1.0 (educational use)"}


def fetch_wikipedia_summary(title):
    """Looks up one page on Wikipedia and returns (image_url, page_url) or (None, None)."""
    url = WIKI_API + urllib.parse.quote(title)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None, None

    # "disambiguation" pages mean Wikipedia wasn't sure which exact page we meant -- skip those
    if data.get("type") == "disambiguation":
        return None, None

    image_url = None
    if "originalimage" in data:
        image_url = data["originalimage"]["source"]
    elif "thumbnail" in data:
        image_url = data["thumbnail"]["source"]

    page_url = data.get("content_urls", {}).get("desktop", {}).get("page")
    return image_url, page_url


def main():
    db = SessionLocal()
    destinations = db.query(Destination).all()
    print(f"Checking {len(destinations)} destinations against Wikipedia...\n", flush=True)

    found = 0
    not_found = []

    for i, dest in enumerate(destinations, 1):
        image_url, page_url = fetch_wikipedia_summary(dest.name)

        # A couple of common name variations worth trying if the exact name fails
        if not image_url:
            image_url, page_url = fetch_wikipedia_summary(f"{dest.name}, Pakistan")
        if not image_url:
            image_url, page_url = fetch_wikipedia_summary(f"{dest.name} ({dest.district})")

        if image_url:
            existing_image = db.query(DestinationImage).filter(
                DestinationImage.destination_id == dest.id
            ).first()

            if existing_image:
                existing_image.image_url = image_url
                existing_image.source = "Wikipedia"
                existing_image.author = "See Wikipedia page history"
                existing_image.license = "See Wikipedia page for license details"
                existing_image.attribution = page_url or "https://en.wikipedia.org"
            else:
                db.add(DestinationImage(
                    destination_id=dest.id,
                    image_url=image_url,
                    source="Wikipedia",
                    author="See Wikipedia page history",
                    license="See Wikipedia page for license details",
                    attribution=page_url or "https://en.wikipedia.org",
                ))

            db.commit()  # commit each destination immediately so results appear live
            print(f"  [{i}/{len(destinations)}] [OK] {dest.name}", flush=True)
            found += 1
        else:
            print(f"  [{i}/{len(destinations)}] [--] {dest.name} -- no Wikipedia match", flush=True)
            not_found.append(dest.name)

        time.sleep(0.2)  # be polite to Wikipedia's free API -- avoid hammering it

    db.close()

    print("\n" + "=" * 60)
    print(f"Found real images for {found}/{len(destinations)} destinations")
    if not_found:
        print(f"\nNo match found for {len(not_found)} destinations (still showing placeholder):")
        for name in not_found:
            print(f"   - {name}")
    print("\nSpot-check a few of the found images before your presentation --")
    print("automatic name-matching is usually right, but not guaranteed 100%.")


if __name__ == "__main__":
    main()