"""
fix_images3.py
==============
Final-pass image fixer. Uses a 2-step approach for destinations whose
Wikipedia pages have no designated lead image:
  Step 1: Get all image filenames embedded in the article
  Step 2: Resolve filenames to real URLs via the imageinfo API
  (skips icons, flags, SVGs, and tiny images < 200px wide)

Run after fix_images2.py:
    python fix_images3.py
"""

import time
import urllib.request
import urllib.parse
import json
from database import SessionLocal
from models import Destination, DestinationImage

MW_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "PakistanTravelAgentStudentProject/1.0 (educational use)"}

MANUAL_OVERRIDES = {
    "Naran Kaghan":                                          "Naran, Khyber Pakhtunkhwa",
    "Multan Shrine (Shah Rukn-e-Alam)":                     "Shrine of Shah Rukn-e-Alam",
    "Hazarganji-Chiltan National Park":                      "Hazarganji Chiltan National Park",
    "Naltar Valley":                                         "Naltar",
    "Shangrila Resort (Lower Kachura Lake)":                 "Shangrila Resort, Pakistan",
    "Pakistan Monument":                                     "Pakistan Monument",
    "Lok Virsa Museum":                                      "Lok Virsa Museum",
    "Ilyasi Mosque":                                         "Abbottabad",
    "Abbottabad Cantt & Mall Road":                          "Abbottabad",
    "Qissa Khwani Bazaar":                                   "Qissa Khwani Bazaar",
    "Bala Hisar Fort":                                       "Bala Hisar Fort, Peshawar",
    "Peshawar Museum":                                       "Peshawar Museum",
    "Kalam Valley":                                          "Kalam, Khyber Pakhtunkhwa",
    "Swat Museum":                                           "Swat Museum",
    "White Palace (Marghazar)":                              "Marghazar",
    "Noor Mahal":                                            "Noor Mahal, Bahawalpur",
    "Derawar Fort":                                          "Derawar Fort",
    "Sadiq Garh Palace":                                     "Sadiq Garh Palace",
    "Lal Suhanra National Park":                             "Lal Suhanra National Park",
    "Central Library Bahawalpur":                            "Bahawalpur",
    "Clock Tower (Ghanta Ghar) & the Eight Bazaars":         "Faisalabad",
    "Lyallpur Museum":                                       "Faisalabad",
    "Jinnah Garden (Company Bagh)":                          "Faisalabad",
    "Chenab Club":                                           "Faisalabad",
    "D-Ground":                                              "Faisalabad",
    "Gujranwala Fort remains":                               "Gujranwala",
    "Nandi Shah Park":                                       "Gujranwala",
    "Shrine of Shah Rukn-e-Alam":                            "Shrine of Shah Rukn-e-Alam",
    "Sindh Museum":                                          "Hyderabad, Sindh",
    "Tombs of the Talpur Mirs":                              "Talpur",
    "Resham Gali & Shahi Bazaar":                            "Hyderabad, Sindh",
    "Empress Market":                                        "Empress Market, Karachi",
    "Mohatta Palace":                                        "Mohatta Palace",
    "Garhi Khuda Bakhsh (Bhutto family mausoleum)":          "Garhi Khuda Bakhsh",
    "Kot Diji Fort (day trip)":                              "Kot Diji",
    "Mirpurkhas mango orchards":                             "Mirpur Khas",
    "Mirpurkhas Buddhist Stupa":                             "Mirpur Khas",
    "Bhitshah (Shrine of Shah Abdul Latif Bhittai, day trip)": "Shah Abdul Latif Bhittai",
    "Nawabshah city bazaars":                                "Shaheed Benazirabad",
    "Sukkur Barrage":                                        "Sukkur Barrage",
    "Sadhu Bela Temple":                                     "Sadhu Bela",
    "Lansdowne Bridge":                                      "Sukkur",
    "Moola Chotok waterfall":                                "Khuzdar District",
    "Khuzdar bazaars":                                       "Khuzdar",
    "Sibi Mela grounds":                                     "Sibi",
    "Zhob Fort":                                             "Zhob District",
    "Zhob River valley":                                     "Zhob River",
    "Tirich Mir viewpoint":                                  "Tirich Mir",
    "Lowari Tunnel viewpoint":                               "Lowari Pass",
    "Dir Fort remains":                                      "Dir, Khyber Pakhtunkhwa",
    "Kohat Fort":                                            "Kohat",
    "Tanda Dam":                                             "Tanda Dam",
    "Kohat Pass":                                            "Kohat Pass",
    "Banjosa Lake":                                          "Banjosa",
    "Toli Pir":                                              "Toli Pir",
    "Loralai River valley":                                  "Loralai",
    "Loralai local bazaars":                                 "Loralai",
    "Indus River waterfront":                                "Indus River",
    "Dera Ismail Khan bazaars":                              "Dera Ismail Khan",
    "Kabul River confluence":                                "Kabul River",
    "Cherat Hill Station":                                   "Cherat",
    "Tomb of Bulleh Shah":                                   "Bulleh Shah",
    "Kasur old city bazaars":                                "Kasur",
    "Okara Cantt & Renala Khurd":                            "Okara District",
    "Okara dairy/agricultural farms":                        "Okara District",
    "Vehari agricultural belt":                              "Vehari District",
}

# Extensions to skip (icons, flags, diagrams)
SKIP_EXTENSIONS = {".svg", ".gif", ".png"}
SKIP_KEYWORDS = ["flag", "icon", "logo", "seal", "coat_of_arms", "emblem",
                 "map", "locator", "blank", "wikipedia", "commons"]


def is_good_image(filename):
    """Returns True if the filename looks like a real photograph."""
    name_lower = filename.lower()
    if any(name_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False
    if any(kw in name_lower for kw in SKIP_KEYWORDS):
        return False
    return True


def get_article_images(title):
    """Step 1: Get a list of image filenames embedded in the Wikipedia article."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": title,
        "prop": "images",
        "format": "json",
        "imlimit": 20,
        "redirects": 1,
    })
    req = urllib.request.Request(f"{MW_API}?{params}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1":
            return []
        return [img["title"] for img in page.get("images", [])
                if is_good_image(img.get("title", ""))]
    return []


def get_image_url(file_title):
    """Step 2: Resolve a 'File:xxx' title to its actual download URL."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url|size",
        "iiurlwidth": 1200,
        "format": "json",
    })
    req = urllib.request.Request(f"{MW_API}?{params}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1":
            return None
        info_list = page.get("imageinfo", [])
        if info_list:
            info = info_list[0]
            # Skip tiny images (likely icons)
            if info.get("width", 0) < 200:
                return None
            return info.get("thumburl") or info.get("url")
    return None


def fetch_best_image(wiki_title):
    """Try pageimages first (fast), then fall back to article image scan."""
    # Fast path: pageimages prop
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": wiki_title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": 1200,
        "redirects": 1,
    })
    req = urllib.request.Request(f"{MW_API}?{params}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id != "-1":
                thumb = page.get("thumbnail", {})
                if thumb.get("source"):
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page.get('title', wiki_title))}"
                    return thumb["source"], page_url
    except Exception:
        pass

    # Slow path: scan article images
    image_files = get_article_images(wiki_title)
    time.sleep(0.1)  # polite extra gap for the second call
    for file_title in image_files[:8]:  # check first 8 candidates
        url = get_image_url(file_title)
        time.sleep(0.1)
        if url:
            page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(wiki_title)}"
            return url, page_url

    return None, None


def main():
    db = SessionLocal()
    destinations = db.query(Destination).all()

    needs_image = []
    for dest in destinations:
        img = db.query(DestinationImage).filter(
            DestinationImage.destination_id == dest.id
        ).first()
        if img and img.image_url and img.image_url.startswith("PLACEHOLDER"):
            needs_image.append(dest)
        elif not img:
            needs_image.append(dest)

    print(f"Destinations still needing images: {len(needs_image)}\n", flush=True)

    found = 0
    still_missing = []

    for i, dest in enumerate(needs_image, 1):
        wiki_title = MANUAL_OVERRIDES.get(dest.name, dest.name)
        image_url, page_url = fetch_best_image(wiki_title)

        if image_url:
            existing = db.query(DestinationImage).filter(
                DestinationImage.destination_id == dest.id
            ).first()
            if existing:
                existing.image_url = image_url
                existing.source = "Wikipedia"
                existing.author = "See Wikipedia page history"
                existing.license = "See Wikipedia page for license details"
                existing.attribution = page_url or "https://en.wikipedia.org"
            else:
                db.add(DestinationImage(
                    destination_id=dest.id,
                    image_url=image_url,
                    source="Wikipedia",
                    author="See Wikipedia page history",
                    license="See Wikipedia page for license details",
                    attribution=page_url or "https://en.wikipedia.org",
                ))
            db.commit()
            print(f"  [{i}/{len(needs_image)}] [OK] {dest.name} (via '{wiki_title}')", flush=True)
            found += 1
        else:
            print(f"  [{i}/{len(needs_image)}] [--] {dest.name}", flush=True)
            still_missing.append(dest.name)

        time.sleep(0.2)

    db.close()
    print(f"\nFixed {found}/{len(needs_image)} remaining destinations.")
    if still_missing:
        print(f"\nStill missing ({len(still_missing)}):")
        for n in still_missing:
            print(f"   - {n}")


if __name__ == "__main__":
    main()
