"""
fix_images2.py
==============
Third-pass image fixer using the Wikipedia MediaWiki Action API
(more reliable than the REST summary API for pages that have images
but don't expose them through the /page/summary/ endpoint).

Run after fix_images.py:
    python fix_images2.py
"""

import time
import urllib.request
import urllib.parse
import json
from database import SessionLocal
from models import Destination, DestinationImage

MW_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "PakistanTravelAgentStudentProject/1.0 (educational use)"}

# Refined title mappings for the remaining destinations
MANUAL_OVERRIDES = {
    "Naran Kaghan":                                         "Naran, Khyber Pakhtunkhwa",
    "Multan Shrine (Shah Rukn-e-Alam)":                    "Shrine of Shah Rukn-e-Alam",
    "Old Gwadar Bazaar":                                    "Gwadar",
    "Hazarganji-Chiltan National Park":                     "Hazarganji Chiltan National Park",
    "Quetta Geological Museum":                             "Quetta",
    "Liaquat Bazaar":                                       "Quetta",
    "Quetta Fruit Market":                                  "Quetta",
    "Kargah Buddha":                                        "Kargah Buddha",
    "Gilgit Bazaar":                                        "Gilgit",
    "Naltar Valley":                                        "Naltar",
    "Shangrila Resort (Lower Kachura Lake)":                "Kachura Lakes",
    "Pakistan Monument":                                    "Pakistan Monument",
    "Lok Virsa Museum":                                     "Islamabad",
    "Ilyasi Mosque":                                        "Abbottabad",
    "Abbottabad Cantt & Mall Road":                         "Abbottabad",
    "Qissa Khwani Bazaar":                                  "Qissa Khwani Bazaar",
    "Bala Hisar Fort":                                      "Bala Hisar Fort, Peshawar",
    "Peshawar Museum":                                      "Peshawar Museum",
    "Kalam Valley":                                         "Kalam, Khyber Pakhtunkhwa",
    "Swat Museum":                                          "Swat",
    "White Palace (Marghazar)":                             "Marghazar",
    "Noor Mahal":                                           "Noor Mahal, Bahawalpur",
    "Derawar Fort":                                         "Derawar Fort",
    "Sadiq Garh Palace":                                    "Sadiq Garh Palace",
    "Lal Suhanra National Park":                            "Lal Suhanra National Park",
    "Central Library Bahawalpur":                           "Bahawalpur",
    "Clock Tower (Ghanta Ghar) & the Eight Bazaars":        "Faisalabad",
    "Lyallpur Museum":                                      "Faisalabad",
    "Jinnah Garden (Company Bagh)":                         "Faisalabad",
    "Chenab Club":                                          "Faisalabad",
    "D-Ground":                                             "Faisalabad",
    "Gujranwala Fort remains":                              "Gujranwala",
    "Nandi Shah Park":                                      "Gujranwala",
    "Rehmatabad food and wrestling (akhara) culture":        "Gujranwala",
    "Jhelum River waterfront":                              "Jhelum River",
    "Tilla Jogian":                                         "Tilla Jogian",
    "Minar-e-Pakistan":                                     "Minar-e-Pakistan",
    "Lahore Museum":                                        "Lahore Museum",
    "Anarkali Bazaar":                                      "Anarkali Bazaar",
    "Wagah Border Flag Ceremony":                           "Wagah",
    "Shrine of Shah Rukn-e-Alam":                           "Shrine of Shah Rukn-e-Alam",
    "Multan Fort / Qasim Bagh":                             "Multan",
    "Raja Bazaar":                                          "Rawalpindi",
    "Sindh Museum":                                         "Hyderabad, Sindh",
    "Tombs of the Talpur Mirs":                             "Hyderabad, Sindh",
    "Resham Gali & Shahi Bazaar":                           "Hyderabad, Sindh",
    "Empress Market":                                       "Empress Market, Karachi",
    "Mohatta Palace":                                       "Mohatta Palace",
    "Garhi Khuda Bakhsh (Bhutto family mausoleum)":         "Garhi Khuda Bakhsh",
    "Kot Diji Fort (day trip)":                             "Kot Diji",
    "Mirpurkhas mango orchards":                            "Mirpur Khas",
    "Mirpurkhas Buddhist Stupa":                            "Mirpur Khas",
    "Bhitshah (Shrine of Shah Abdul Latif Bhittai, day trip)": "Shah Abdul Latif Bhittai",
    "Nawabshah city bazaars":                               "Shaheed Benazirabad",
    "Sukkur Barrage":                                       "Sukkur Barrage",
    "Sadhu Bela Temple":                                    "Sadhu Bela",
    "Lansdowne Bridge":                                     "Sukkur",
    "Moola Chotok waterfall":                               "Khuzdar",
    "Khuzdar bazaars":                                      "Khuzdar",
    "Sibi Mela grounds":                                    "Sibi",
    "Zhob Fort":                                            "Zhob",
    "Zhob River valley":                                    "Zhob",
    "Tirich Mir viewpoint":                                 "Tirich Mir",
    "Lowari Tunnel viewpoint":                              "Lowari Pass",
    "Dir Fort remains":                                     "Dir, Pakistan",
    "Kohat Fort":                                           "Kohat",
    "Tanda Dam":                                            "Kohat",
    "Kohat Pass":                                           "Kohat Pass",
    "Banjosa Lake":                                         "Banjosa",
    "Toli Pir":                                             "Azad Kashmir",
    "Loralai River valley":                                 "Loralai",
    "Loralai local bazaars":                                "Loralai",
    "Indus River waterfront":                               "Indus River",
    "Dera Ismail Khan bazaars":                             "Dera Ismail Khan",
    "Kabul River confluence":                               "Kabul River",
    "Cherat Hill Station":                                  "Cherat",
    "Tomb of Bulleh Shah":                                  "Bulleh Shah",
    "Kasur old city bazaars":                               "Kasur",
    "Okara Cantt & Renala Khurd":                           "Okara District",
    "Okara dairy/agricultural farms":                       "Okara District",
    "Vehari agricultural belt":                             "Vehari District",
    "Vehari local bazaars":                                 "Vehari District",
    "Badin coastal wetlands":                               "Badin District",
}


def fetch_mw_image(title):
    """Uses the MediaWiki Action API pageimages prop — more reliable than REST summary."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": 1200,
        "redirects": 1,
    })
    url = f"{MW_API}?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None, None

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1":
            return None, None
        thumb = page.get("thumbnail", {})
        if thumb.get("source"):
            page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page.get('title', title))}"
            return thumb["source"], page_url

    return None, None


def main():
    db = SessionLocal()
    destinations = db.query(Destination).all()

    # Only process destinations still on placeholder
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
        image_url, page_url = fetch_mw_image(wiki_title)

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
