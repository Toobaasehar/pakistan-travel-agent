"""
scripts/fetch_real_images.py
=============================
Replaces placeholder destination images with real photos, pulled
automatically from Wikipedia / Wikimedia Commons's public APIs (no API
key needed).

For every destination whose stored image is still the PLACEHOLDER string
(see seed.py), this script tries, in order:
  1. Wikipedia search for "<destination name>, <district>, Pakistan"
  2. Wikipedia search for "<destination name>, Pakistan" (plainer query)
  3. Wikimedia Commons search for "<destination name>, <district>, Pakistan"
     -- Commons often has photos for small places that don't have a full
     Wikipedia article, which is why step 1/2 alone left ~1/3 of the 376+
     destinations with no image.
  4. Wikimedia Commons search for "<district>, Pakistan" as a last resort
     -- a representative photo of the district/city, clearly marked as
     such so it isn't mistaken for the exact attraction.
  5. If all four fail, the destination is reported as still needing a
     manually-sourced image.

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

# Force UTF-8 terminal output on Windows -- without this, printing the
# ✓ / ✗ / ⚠️ characters below can itself raise UnicodeEncodeError on the
# default Windows console codepage and crash the script mid-run.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Allow running this script from the project root or from scripts/ directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

# This script runs standalone (not through main.py), so it needs its own
# .env load -- without this, PEXELS_API_KEY/UNSPLASH_ACCESS_KEY below would
# always read as empty even if they're set in .env.
from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import Destination, DestinationImage

WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"
PLACEHOLDER_MARKER = "PLACEHOLDER"
REQUEST_DELAY_SECONDS = 0.4  # be polite to Wikipedia's/Commons's free APIs
MAX_RETRIES = 2             # per individual HTTP call, before giving up on it
RETRY_BACKOFF_SECONDS = 1.5
HEADERS = {"User-Agent": "PakistanTravelAgent/1.2 (educational project; contact: team@example.com)"}

# Optional stock-photo fallback (tier 5) -- only used for destinations that
# have NOTHING on Wikipedia or Wikimedia Commons. Get a free key from
# https://www.pexels.com/api/ or https://unsplash.com/developers and add it
# to your .env as PEXELS_API_KEY or UNSPLASH_ACCESS_KEY. If neither is set,
# this tier is silently skipped (script behaves exactly as before).
import os
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()


def _get_with_retry(url: str, params: dict) -> Optional[requests.Response]:
    """
    Thin wrapper around requests.get() that retries transient failures and
    NEVER raises -- returns None if every attempt fails, so callers never
    need to worry about an unhandled exception type crashing the batch.
    (The earlier version of this script only caught requests.RequestException,
    which doesn't cover every possible network-layer error -- e.g. some
    connection-reset / SSL edge cases on Windows -- and one uncaught error
    on a single destination was enough to kill the whole run.)
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            return resp
        except Exception as e:  # noqa: BLE001 -- intentionally broad, see docstring
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS)
    print(f"    ⚠️  Network request failed after {MAX_RETRIES} attempts: {last_error}")
    return None


def find_wikipedia_image(query: str) -> Optional[dict]:
    """
    Searches Wikipedia for `query`, then fetches the summary of the top
    result to get its lead image. Returns a dict with image_url, page_title,
    and page_url, or None if nothing usable was found (including on any
    network failure -- callers just move on to the next fallback).
    """
    search_resp = _get_with_retry(
        WIKI_SEARCH_URL,
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1,
        },
    )
    if search_resp is None or not search_resp.ok:
        return None

    try:
        results = search_resp.json().get("query", {}).get("search", [])
    except ValueError:
        return None  # malformed JSON response
    if not results:
        return None
    title = results[0]["title"]

    summary_resp = _get_with_retry(
        WIKI_SUMMARY_URL.format(title=urllib.parse.quote(title.replace(" ", "_"))),
        params={},
    )
    if summary_resp is None or summary_resp.status_code != 200:
        return None

    try:
        summary = summary_resp.json()
    except ValueError:
        return None

    image = summary.get("originalimage") or summary.get("thumbnail")
    if not image or not image.get("source"):
        return None

    return {
        "image_url": image["source"],
        "page_title": summary.get("title", title),
        "page_url": summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "source_label": "Wikipedia",
        "is_representative_only": False,
    }


def find_commons_image(query: str, representative_only: bool = False) -> Optional[dict]:
    """
    Searches Wikimedia Commons (Wikipedia's photo-only sister project) for
    an image matching `query`. This is the fallback for smaller places that
    have no full Wikipedia article but often still have photos on Commons.

    `representative_only=True` marks the result as a general district/city
    photo rather than an exact match for the specific attraction -- used
    for the last-resort "district, Pakistan" query.
    """
    search_resp = _get_with_retry(
        COMMONS_API_URL,
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrlimit": 1,
            "gsrnamespace": 6,  # File: namespace only
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        },
    )
    if search_resp is None or not search_resp.ok:
        return None

    try:
        pages = search_resp.json().get("query", {}).get("pages", {})
    except ValueError:
        return None
    if not pages:
        return None

    page = next(iter(pages.values()))
    imageinfo = (page.get("imageinfo") or [None])[0]
    if not imageinfo or not imageinfo.get("url"):
        return None

    page_title = page.get("title", "").replace("File:", "")
    commons_page_url = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(page.get('title', ''))}"

    return {
        "image_url": imageinfo["url"],
        "page_title": page_title,
        "page_url": commons_page_url,
        "source_label": "Wikimedia Commons",
        "is_representative_only": representative_only,
    }


def find_stock_photo(query: str) -> Optional[dict]:
    """
    Last-resort fallback: searches Pexels (preferred) or Unsplash for a
    generic stock photo matching `query` (e.g. "bazaar in Pakistan",
    "historic fort Pakistan"). Always returned as is_representative_only,
    since it's a category match, not the exact place.

    Returns None immediately (no network call) if neither API key is
    configured -- this tier is opt-in.
    """
    if PEXELS_API_KEY:
        resp = _get_with_retry(
            PEXELS_SEARCH_URL,
            params={"query": query, "per_page": 1, "orientation": "landscape"},
        )
        if resp is not None and resp.ok:
            try:
                photos = resp.json().get("photos", [])
            except ValueError:
                photos = []
            if photos:
                photo = photos[0]
                return {
                    "image_url": photo["src"]["large"],
                    "page_title": f"Photo by {photo.get('photographer', 'unknown')} on Pexels",
                    "page_url": photo.get("url", ""),
                    "source_label": "Pexels (stock photo)",
                    "is_representative_only": True,
                }

    if UNSPLASH_ACCESS_KEY:
        resp = _get_with_retry(
            UNSPLASH_SEARCH_URL,
            params={"query": query, "per_page": 1, "orientation": "landscape", "client_id": UNSPLASH_ACCESS_KEY},
        )
        if resp is not None and resp.ok:
            try:
                results = resp.json().get("results", [])
            except ValueError:
                results = []
            if results:
                photo = results[0]
                photographer = photo.get("user", {}).get("name", "unknown")
                return {
                    "image_url": photo["urls"]["regular"],
                    "page_title": f"Photo by {photographer} on Unsplash",
                    "page_url": photo.get("links", {}).get("html", ""),
                    "source_label": "Unsplash (stock photo)",
                    "is_representative_only": True,
                }

    return None


# Rough per-category search terms for the stock-photo fallback -- kept
# separate from the DB's `category` values in case those don't line up
# 1:1 with good search phrasing.
CATEGORY_STOCK_QUERIES = {
    "historical": "historic monument Pakistan",
    "mountains": "mountain valley Pakistan",
    "nature": "nature landscape Pakistan",
    "beaches": "beach coastline Pakistan",
    "cultural": "cultural heritage Pakistan",
    "museum": "museum Pakistan",
    "wildlife": "wildlife nature reserve Pakistan",
    "adventure": "trekking mountains Pakistan",
    "sightseeing": "old town bazaar Pakistan",
}


def find_best_image(dest_name: str, district: Optional[str], province: str, category: Optional[str] = None) -> Optional[dict]:
    """
    Runs the full fallback chain described in the module docstring and
    returns the first usable result, or None if every source came up empty.
    """
    area = district or province

    # 1. Wikipedia, specific query
    result = find_wikipedia_image(f"{dest_name}, {area}, Pakistan")
    if result:
        return result

    # 2. Wikipedia, plainer query (drop the district in case it confused the search)
    result = find_wikipedia_image(f"{dest_name}, Pakistan")
    if result:
        return result

    # 3. Wikimedia Commons, specific query
    result = find_commons_image(f"{dest_name}, {area}, Pakistan")
    if result:
        return result

    # 4. Wikimedia Commons, district/city-level fallback (clearly marked)
    if area:
        result = find_commons_image(f"{area}, Pakistan", representative_only=True)
        if result:
            return result

    # 5. Stock photo (Pexels/Unsplash) by category, generic but on-theme.
    # Opt-in: only runs if PEXELS_API_KEY or UNSPLASH_ACCESS_KEY is set.
    stock_query = CATEGORY_STOCK_QUERIES.get((category or "").lower(), "Pakistan tourism")
    result = find_stock_photo(stock_query)
    if result:
        return result

    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch real destination images from Wikipedia/Wikimedia Commons.")
    parser.add_argument("--all", action="store_true", help="Re-fetch every destination, not just placeholders.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N destinations (for testing).")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        destinations = db.query(Destination).order_by(Destination.id).all()
        if args.limit:
            destinations = destinations[: args.limit]

        updated, skipped, not_found, representative = 0, 0, 0, 0
        not_found_names = []

        for i, dest in enumerate(destinations, 1):
            try:
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

                print(f"[{i}/{len(destinations)}] {dest.name} -> searching Wikipedia / Commons / stock...")
                result = find_best_image(dest.name, dest.district, dest.province, dest.category)

                if not result:
                    print(f"    ✗ No image found anywhere for '{dest.name}'.")
                    not_found += 1
                    not_found_names.append(dest.name)
                    time.sleep(REQUEST_DELAY_SECONDS)
                    continue

                license_note = "Varies — verify on the source page before commercial use"
                if result["is_representative_only"]:
                    license_note += " (representative district/city photo, not the exact attraction — replace if you find a better match)"

                if existing_image:
                    existing_image.image_url = result["image_url"]
                    existing_image.source = result["source_label"]
                    existing_image.author = "See source page (per-image attribution needed)"
                    existing_image.license = license_note
                    existing_image.attribution = result["page_url"] or result["page_title"]
                else:
                    db.add(DestinationImage(
                        destination_id=dest.id,
                        image_url=result["image_url"],
                        source=result["source_label"],
                        author="See source page (per-image attribution needed)",
                        license=license_note,
                        attribution=result["page_url"] or result["page_title"],
                    ))

                db.commit()
                tag = " [representative photo]" if result["is_representative_only"] else ""
                print(f"    ✓ ({result['source_label']}) {result['page_title']}{tag} -> {result['image_url'][:80]}")
                updated += 1
                if result["is_representative_only"]:
                    representative += 1
                time.sleep(REQUEST_DELAY_SECONDS)

            except Exception as e:
                # Defense in depth: even an unexpected DB or parsing error on
                # ONE destination should never kill the whole batch anymore.
                db.rollback()
                print(f"    ⚠️  Unexpected error on '{dest.name}', skipping it: {e}")
                not_found += 1
                not_found_names.append(dest.name)
                continue

        print("\n" + "=" * 50)
        print("DONE")
        print(f"  Updated with images        : {updated}  (of which representative-only: {representative})")
        print(f"  Skipped (already real)     : {skipped}")
        print(f"  No image found anywhere    : {not_found}")
        print("=" * 50)
        if not_found_names:
            print(f"\n{len(not_found_names)} destinations still need a manually-sourced image:")
            for name in not_found_names:
                print(f"  - {name}")
            print("\nThese found nothing on Wikipedia OR Wikimedia Commons -- try a manual")
            print("image search (Unsplash/Pexels/Google Images), or add one by hand.")

    finally:
        db.close()


if __name__ == "__main__":
    main()