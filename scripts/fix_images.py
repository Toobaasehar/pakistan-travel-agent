"""
fix_images.py
=============
Fills in Wikipedia images for destinations that the automatic
name-matcher couldn't find, using corrected/alternate Wikipedia titles.
Run AFTER Fetch images.py:
    python fix_images.py
"""

import time
import urllib.request
import urllib.parse
import json
from database import SessionLocal
from models import Destination, DestinationImage

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
HEADERS = {"User-Agent": "PakistanTravelAgentStudentProject/1.0 (educational use)"}

# Corrected Wikipedia page titles for destinations that failed auto-matching.
# Format: "Destination name in DB" -> "Wikipedia article title"
MANUAL_OVERRIDES = {
    "Naran Kaghan":                         "Naran, Khyber Pakhtunkhwa",
    "Kalash Valley (Bumburet)":             "Kalash people",
    "Multan Shrine (Shah Rukn-e-Alam)":     "Shrine of Shah Rukn-e-Alam",
    "Murree":                               "Murree",
    "Rohtas Fort":                          "Rohtas Fort",
    "Katas Raj Temples":                    "Katas Raj",
    "Mohenjo-daro":                         "Mohenjo-daro",
    "Clifton Beach":                        "Clifton, Karachi",
    "Ranikot Fort":                         "Ranikot Fort",
    "Skardu (Lower Kachura Lake)":          "Kachura Lakes",
    "Fairy Meadows":                        "Fairy Meadows",
    "Red Fort (Muzaffarabad Fort)":         "Muzaffarabad",
    "Neelum Valley":                        "Neelum Valley",
    "Pir Chinasi":                          "Pir Chinasi",
    "Gwadar Port & Marina":                 "Gwadar",
    "Hammerhead / Koh-e-Batil":             "Gwadar",
    "Gwadar Beach":                         "Gwadar",
    "Hazarganji-Chiltan National Park":     "Hazarganji Chiltan National Park",
    "Kargah Buddha":                        "Kargah Buddha",
    "Naltar Valley":                        "Naltar",
    "Shangrila Resort (Lower Kachura Lake)":"Shangrila Resort Pakistan",
    "Sarfaranga Cold Desert":               "Skardu",
    "Pakistan Monument":                    "Pakistan Monument",
    "Lok Virsa Museum":                     "Lok Virsa Museum",
    "Centaurus Mall":                       "Islamabad",
    "Ilyasi Mosque":                        "Abbottabad",
    "Abbottabad Cantt & Mall Road":         "Abbottabad",
    "Mardan Museum":                        "Mardan",
    "Qissa Khwani Bazaar":                  "Qissa Khwani Bazaar",
    "Bala Hisar Fort":                      "Bala Hisar Fort, Peshawar",
    "Peshawar Museum":                      "Peshawar Museum",
    "Chowk Yadgar":                         "Peshawar",
    "Sethi House / Sethi Mohalla":          "Peshawar",
    "Kalam Valley":                         "Kalam, Khyber Pakhtunkhwa",
    "Swat Museum":                          "Swat Museum",
    "White Palace (Marghazar)":             "White Palace, Marghazar",
    "Noor Mahal":                           "Noor Mahal",
    "Derawar Fort":                         "Derawar Fort",
    "Sadiq Garh Palace":                    "Sadiq Garh Palace",
    "Lal Suhanra National Park":            "Lal Suhanra National Park",
    "Central Library Bahawalpur":           "Bahawalpur",
    "Clock Tower (Ghanta Ghar) & the Eight Bazaars": "Faisalabad",
    "Lyallpur Museum":                      "Faisalabad",
    "Jinnah Garden (Company Bagh)":         "Faisalabad",
    "Chenab Club":                          "Faisalabad",
    "D-Ground":                             "Faisalabad",
    "Gujranwala Fort remains":              "Gujranwala",
    "Nandi Shah Park":                      "Gujranwala",
    "Rehmatabad food and wrestling (akhara) culture": "Gujranwala",
    "Jhelum River waterfront":              "Jhelum River",
    "Tilla Jogian":                         "Tilla Jogian",
    "Minar-e-Pakistan":                     "Minar-e-Pakistan",
    "Lahore Museum":                        "Lahore Museum",
    "Anarkali Bazaar":                      "Anarkali Bazaar",
    "Wagah Border Flag Ceremony":           "Wagah border ceremony",
    "Shrine of Shah Rukn-e-Alam":          "Shrine of Shah Rukn-e-Alam",
    "Multan Fort / Qasim Bagh":             "Qasim Bagh Stadium",
    "Shrine of Bahauddin Zakariya":         "Bahauddin Zakariya",
    "Ghanta Ghar (Clock Tower) & Hussain Agahi Bazaar": "Multan",
    "Multan Museum":                        "Multan",
    "Raja Bazaar":                          "Raja Bazaar, Rawalpindi",
    "Ayub National Park":                   "Ayub National Park",
    "Rawalpindi Cantt / Mall Road":         "Rawalpindi",
    "Army Museum Rawalpindi":               "Rawalpindi",
    "Clock Tower Sargodha":                 "Sargodha",
    "Kirana Hills":                         "Sargodha",
    "Sargodha Fruit Orchards (citrus belt)":"Sargodha",
    "Hiran Minar":                          "Hiran Minar",
    "Nankana Sahib (day trip)":             "Nankana Sahib",
    "Sialkot Sports Industry Tours":        "Sialkot",
    "Jinnah Islamia College grounds and old city bazaars": "Sialkot",
    "Pacco Qillo (Hyderabad Fort)":         "Hyderabad Fort",
    "Sindh Museum":                         "Hyderabad, Sindh",
    "Tombs of the Talpur Mirs":             "Talpur",
    "Resham Gali & Shahi Bazaar":           "Hyderabad, Sindh",
    "Mazar-e-Quaid (Quaid's Mausoleum)":   "Mazar-e-Quaid",
    "Empress Market":                       "Empress Market",
    "Mohatta Palace":                       "Mohatta Palace",
    "Do Darya":                             "Karachi",
    "Port Grand":                           "Karachi",
    "Garhi Khuda Bakhsh (Bhutto family mausoleum)": "Garhi Khuda Bakhsh",
    "Kot Diji Fort (day trip)":             "Kot Diji",
    "Mirpurkhas mango orchards":            "Mirpur Khas",
    "Mirpurkhas Buddhist Stupa":            "Mirpur Khas",
    "Bhitshah (Shrine of Shah Abdul Latif Bhittai, day trip)": "Shah Abdul Latif Bhittai",
    "Nawabshah city bazaars":               "Nawabshah",
    "Sukkur Barrage":                       "Sukkur Barrage",
    "Sadhu Bela Temple":                    "Sadhu Bela",
    "Lansdowne Bridge":                     "Lansdowne Bridge, Sukkur",
    "Moola Chotok waterfall":               "Moola Chotok",
    "Khuzdar bazaars":                      "Khuzdar",
    "Sibi Mela grounds":                    "Sibi",
    "Zhob Fort":                            "Zhob",
    "Zhob River valley":                    "Zhob River",
    "Bannu Fort (Dhamtaur area)":           "Bannu",
    "Bannu bazaars":                        "Bannu",
    "Chitral Fort (Qaqlasht)":              "Chitral",
    "Shahi Mosque Chitral":                 "Chitral",
    "Tirich Mir viewpoint":                 "Tirich Mir",
    "Lowari Tunnel viewpoint":              "Lowari Pass",
    "Dir Fort remains":                     "Dir, Pakistan",
    "Kohat Fort":                           "Kohat",
    "Tanda Dam":                            "Tanda Dam",
    "Kohat Pass":                           "Kohat Pass",
    "Banjosa Lake":                         "Banjosa Lake",
    "Toli Pir":                             "Toli Pir",
    "Loralai River valley":                 "Loralai",
    "Loralai local bazaars":                "Loralai",
    "Indus River waterfront":               "Indus River",
    "Dera Ismail Khan bazaars":             "Dera Ismail Khan",
    "Kabul River confluence":               "Kabul River",
    "Cherat Hill Station":                  "Cherat",
    "Tomb of Bulleh Shah":                  "Bulleh Shah",
    "Kasur old city bazaars":               "Kasur",
    "Okara Cantt & Renala Khurd":           "Okara, Punjab",
    "Okara dairy/agricultural farms":       "Okara, Punjab",
    "Vehari agricultural belt":             "Vehari",
    "Vehari local bazaars":                 "Vehari",
    "Badin coastal wetlands":               "Badin District",
    "Badin local bazaars":                  "Badin District",
    "Manchar Lake":                         "Manchar Lake",
    "Johi & Khirthar National Park (day trip)": "Kirthar National Park",
    "Keenjhar Lake":                        "Keenjhar Lake",
}


def fetch_wikipedia_summary(title):
    url = WIKI_API + urllib.parse.quote(title)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None, None

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

    # Only process destinations that still have placeholder images
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
        image_url, page_url = fetch_wikipedia_summary(wiki_title)

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
        print(f"Still missing ({len(still_missing)}):")
        for n in still_missing:
            print(f"   - {n}")


if __name__ == "__main__":
    main()
