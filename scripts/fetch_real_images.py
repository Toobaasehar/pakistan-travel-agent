"""
scripts/fetch_real_images.py
=============================
Replaces placeholder destination images with real photos, pulled
automatically from Wikipedia's public API (no API key needed).

For every destination whose stored image is still the PLACEHOLDER string
(see seed.py), this script:
  1. Searches Wikipedia for "<destination name>, Pakistan"
  2. Takes the best-matching page and pulls its thumbnail/lead image
  3. Updates (or inserts) the destination_images row with that real URL

Run with:
    python scripts/fetch_real_images.py            # only fills in placeholders
    python scripts/fetch_real_images.py --all       # re-fetches every destination, overwriting existing images too
    python scripts/fetch_real_images.py --limit 20  # useful for a quick test run first

Requires internet access and the `requests` package (already a project
dependency — see requirements.txt).

⚠️  LICENSING NOTE — read before using these images commercially:
Wikipedia/Wikimedia images are usually CC BY-SA or public domain, but the
exact license and required attribution differs *per image*. This script
records the source page as "attribution" so you can trace it back, but it
does NOT verify the individual license. Follow this project's existing
"needs verification" convention (see destinations_data.py / city_coordinates.py)
— spot-check licenses before using any of these images outside of
development/prototyping.
"""

import sys
import time
import argparse
import urllib.parse
from pathlib import Path
from typing import Optional

import requests

# Allow running this script from the project root or from scripts/ directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models import Destination, DestinationImage

WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
PLACEHOLDER_MARKER = "PLACEHOLDER"
REQUEST_DELAY_SECONDS = 0.4  # be polite to Wikipedia's free API
HEADERS = {"User-Agent": "PakistanTravelAgent/1.1 (educational project; contact: team@example.com)"}


def find_wikipedia_image(query: str) -> Optional[dict]:
    """
    Searches Wikipedia for `query`, then fetches the summary of the top
    result to get its lead image. Returns a dict with image_url, page_title,
    and page_url, or None if nothing usable was found.
    """
    try:
        search_resp = requests.get(
            WIKI_SEARCH_URL,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1,
            },
            headers=HEADERS,
            timeout=10,
        )
        search_resp.raise_for_status()
        results = search_resp.json().get("query", {}).get("search", [])
        if not results:
            return None
        title = results[0]["title"]

        summary_resp = requests.get(
            WIKI_SUMMARY_URL.format(title=urllib.parse.quote(title.replace(" ", "_"))),
            headers=HEADERS,
            timeout=10,
        )
        if summary_resp.status_code != 200:
            return None
        summary = summary_resp.json()

        image = summary.get("originalimage") or summary.get("thumbnail")
        if not image or not image.get("source"):
            return None

        return {
            "image_url": image["source"],
            "page_title": summary.get("title", title),
            "page_url": summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except requests.RequestException as e:
        print(f"    ⚠️  Wikipedia request failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Fetch real destination images from Wikipedia.")
    parser.add_argument("--all", action="store_true", help="Re-fetch every destination, not just placeholders.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N destinations (for testing).")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        destinations = db.query(Destination).order_by(Destination.id).all()
        if args.limit:
            destinations = destinations[: args.limit]

        updated, skipped, not_found = 0, 0, 0

        for i, dest in enumerate(destinations, 1):
            existing_image = (
                db.query(DestinationImage)
                .filter(DestinationImage.destination_id == dest.id)
                .first()
            )

            is_placeholder = (
                existing_image is None
                or not existing_image.image_url
                or PLACEHOLDER_MARKER in existing_image.image_url
            )
            if not args.all and not is_placeholder:
                skipped += 1
                continue

            query = f"{dest.name}, {dest.district or dest.province}, Pakistan"
            print(f"[{i}/{len(destinations)}] {dest.name} -> searching Wikipedia...")
            result = find_wikipedia_image(query)

            if not result:
                # Fall back to a plainer query without the district, in case
                # the district name confused the search (e.g. a very small
                # district Wikipedia has no page for).
                result = find_wikipedia_image(f"{dest.name}, Pakistan")

            if not result:
                print(f"    ✗ No Wikipedia image found for '{dest.name}'.")
                not_found += 1
                time.sleep(REQUEST_DELAY_SECONDS)
                continue

            if existing_image:
                existing_image.image_url = result["image_url"]
                existing_image.source = "Wikipedia"
                existing_image.author = "See Wikipedia page (per-image attribution needed)"
                existing_image.license = "Varies — verify on the Wikipedia page before commercial use"
                existing_image.attribution = result["page_url"] or result["page_title"]
            else:
                db.add(DestinationImage(
                    destination_id=dest.id,
                    image_url=result["image_url"],
                    source="Wikipedia",
                    author="See Wikipedia page (per-image attribution needed)",
                    license="Varies — verify on the Wikipedia page before commercial use",
                    attribution=result["page_url"] or result["page_title"],
                ))

            db.commit()
            print(f"    ✓ {result['page_title']} -> {result['image_url'][:80]}")
            updated += 1
            time.sleep(REQUEST_DELAY_SECONDS)

        print("\n" + "=" * 50)
        print("DONE")
        print(f"  Updated with real images : {updated}")
        print(f"  Skipped (already real)   : {skipped}")
        print(f"  No image found           : {not_found}")
        print("=" * 50)
        if not_found:
            print(f"\n{not_found} destinations still need a manually-sourced image (no matching Wikipedia page found).")
            print("Re-run with a more specific query, or add these manually.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
