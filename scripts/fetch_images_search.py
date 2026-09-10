import sys
import os
import time
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import SessionLocal
from models import Destination, DestinationImage

WIKI_API = "https://en.wikipedia.org/w/api.php"


def search_wikipedia(query):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 5,
        "origin": "*",
    }

    try:
        response = requests.get(WIKI_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = data.get("query", {}).get("search", [])

        if results:
            return results[0]["title"]

    except Exception as e:
        print(f"  Search error: {e}")

    return None


def get_wikipedia_image(title):
    params = {
        "action": "query",
        "prop": "pageimages|info",
        "inprop": "url",
        "piprop": "original|thumbnail",
        "pithumbsize": 1200,
        "titles": title,
        "format": "json",
        "origin": "*",
    }

    try:
        response = requests.get(WIKI_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})

        for page in pages.values():
            if "missing" in page:
                return None

            image = page.get("original") or page.get("thumbnail")

            if image and image.get("source"):
                return {
                    "url": image["source"],
                    "page_url": page.get("fullurl"),
                    "title": page.get("title"),
                }

    except Exception as e:
        print(f"  Image error: {e}")

    return None


def find_image(destination):
    searches = [
        destination.name,
        f"{destination.name}, Pakistan",
    ]

    if destination.district:
        searches.append(f"{destination.name} {destination.district}")
        searches.append(f"{destination.name} {destination.district} Pakistan")

    for query in searches:
        print(f"  Searching: {query}")

        title = search_wikipedia(query)

        if not title:
            continue

        print(f"  Found page: {title}")

        image = get_wikipedia_image(title)

        if image:
            return image

        time.sleep(0.2)

    return None


def save_image(db, destination, image):
    existing = (
        db.query(DestinationImage)
        .filter(DestinationImage.destination_id == destination.id)
        .first()
    )

    if existing:
        existing.image_url = image["url"]
        existing.source = "Wikipedia"
        existing.author = "Wikipedia contributors"
        existing.license = "See Wikipedia page for image license"
        existing.attribution = image.get("page_url", "Wikipedia")
    else:
        new_image = DestinationImage(
            destination_id=destination.id,
            image_url=image["url"],
            source="Wikipedia",
            author="Wikipedia contributors",
            license="See Wikipedia page for image license",
            attribution=image.get("page_url", "Wikipedia"),
        )
        db.add(new_image)


def main():
    db = SessionLocal()

    try:
        destinations = db.query(Destination).order_by(Destination.id).all()

        print("=" * 70)
        print(f"IMAGE SEARCH FOR {len(destinations)} DESTINATIONS")
        print("=" * 70)

        found = 0
        not_found = 0

        for index, destination in enumerate(destinations, start=1):

            print(
                f"\n[{index}/{len(destinations)}] "
                f"{destination.name} ({destination.province})"
            )

            image = find_image(destination)

            if image:
                save_image(db, destination, image)
                db.commit()

                found += 1
                print("  ✓ IMAGE SAVED")
                print(f"  URL: {image['url']}")
            else:
                not_found += 1
                print("  ✗ NO IMAGE FOUND")

            time.sleep(0.3)

        print("\n" + "=" * 70)
        print("DONE")
        print("=" * 70)
        print(f"Images found:       {found}")
        print(f"No image found:     {not_found}")
        print(f"Total destinations: {len(destinations)}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()
