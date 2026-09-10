"""
fix_images_search.py
=====================
Uses Wikipedia's opensearch + pageimages API with better search terms
to find images for the remaining 45 destinations.
Strategy:
  1. Try searching by alternate/simplified name via Wikipedia opensearch
  2. Take the top search result's page title
  3. Fetch its pageimages thumbnail
"""

import time
import urllib.request
import urllib.parse
import json
import sqlite3

MW_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "PakistanTravelAgentStudentProject/1.0 (educational)"}

# Better search terms for each destination that's still missing
SEARCH_TERMS = {
    2:   ["Naran Valley KPK", "Naran Kaghan Valley"],
    14:  ["Shah Rukn-e-Alam Multan", "Shrine of Shah Rukn-e-Alam"],
    38:  ["Hazarganji Chiltan National Park Balochistan"],
    44:  ["Naltar Valley Gilgit-Baltistan", "Naltar Lakes Pakistan"],
    45:  ["Shangrila Resort Skardu", "Lower Kachura Lake Pakistan"],
    47:  ["Pakistan Monument Islamabad", "Pakistan Monument"],
    48:  ["Lok Virsa Museum Islamabad"],
    52:  ["Ilyasi Mosque Abbottabad", "Abbottabad KPK"],
    53:  ["Abbottabad Mall Road KPK", "Abbottabad city"],
    56:  ["Qissa Khwani Bazaar Peshawar"],
    57:  ["Bala Hisar Fort Peshawar"],
    58:  ["Peshawar Museum", "Peshawar Museum Pakistan"],
    61:  ["Kalam Valley Swat", "Kalam Pakistan"],
    62:  ["Swat Museum Pakistan", "Saidu Sharif Museum"],
    64:  ["Noor Mahal Bahawalpur", "Noor Mahal palace Bahawalpur"],
    72:  ["Faisalabad city Pakistan", "Chenab Club Faisalabad"],
    73:  ["Faisalabad Pakistan", "D-Ground Faisalabad"],
    74:  ["Gujranwala city Punjab", "Gujranwala Pakistan"],
    75:  ["Gujranwala Punjab Pakistan"],
    83:  ["Shah Rukn-e-Alam shrine Multan"],
    103: ["Hyderabad Sindh city", "Hyderabad Sindh Pakistan"],
    104: ["Talpur Mirs tombs Hyderabad", "Tombs Talpur Mirs"],
    105: ["Hyderabad Sindh bazaar"],
    107: ["Empress Market Karachi"],
    108: ["Mohatta Palace Karachi"],
    111: ["Garhi Khuda Bakhsh mausoleum", "Bhutto mausoleum Larkana"],
    112: ["Kot Diji Fort Khairpur", "Kot Diji"],
    113: ["Mirpur Khas city Sindh"],
    114: ["Mirpur Khas Sindh"],
    115: ["Shah Abdul Latif Bhittai Bhitshah"],
    116: ["Shaheed Benazirabad city", "Nawabshah Sindh"],
    117: ["Sukkur Barrage Sindh"],
    118: ["Sadhu Bela temple Sukkur"],
    119: ["Lansdowne Bridge Sukkur"],
    120: ["Moola Chotok Balochistan waterfall"],
    121: ["Khuzdar city Balochistan"],
    123: ["Sibi city Balochistan", "Sibi Mela"],
    124: ["Zhob city Balochistan", "Zhob District"],
    132: ["Dir Valley KPK Pakistan", "Dir Lower Pakistan"],
    138: ["Loralai city Balochistan"],
    139: ["Loralai Balochistan"],
    140: ["Indus River Pakistan", "Indus River Sindh"],
    141: ["Dera Ismail Khan city", "Dera Ismail Khan KPK"],
    142: ["Kabul River Pakistan", "Kabul River Nowshera"],
    143: ["Cherat hill station Pakistan"],
    144: ["Bulleh Shah shrine Kasur", "Bulleh Shah"],
    145: ["Kasur city Punjab Pakistan"],
    146: ["Okara city Punjab Pakistan"],
    147: ["Okara district Pakistan"],
    148: ["Vehari district Punjab Pakistan"],
}


def wiki_request(params):
    url = f"{MW_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return {}


def search_wiki_page(query):
    """Use opensearch to find the best matching Wikipedia page title."""
    data = wiki_request({
        "action": "opensearch",
        "search": query,
        "limit": 3,
        "format": "json",
    })
    titles = data[1] if data and len(data) > 1 else []
    return titles[0] if titles else None


def get_page_image(title):
    """Get thumbnail image for a Wikipedia page title."""
    data = wiki_request({
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": 1200,
        "redirects": 1,
    })
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if pid != "-1":
            thumb = page.get("thumbnail", {})
            if thumb.get("source"):
                return thumb["source"], f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page.get('title', title))}"
    return None, None


def get_article_images(title):
    """Get list of image files embedded in an article."""
    data = wiki_request({
        "action": "query",
        "titles": title,
        "prop": "images",
        "format": "json",
        "imlimit": 30,
        "redirects": 1,
    })
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if pid != "-1":
            imgs = page.get("images", [])
            return [i["title"] for i in imgs]
    return []


def resolve_image_url(file_title):
    """Resolve 'File:xxx' to actual download URL."""
    name = file_title.lower()
    # Skip icons/flags/maps/SVGs
    if any(kw in name for kw in ["flag", "icon", "logo", "seal", "map",
                                   "locator", "blank", "coat", "emblem"]):
        return None
    if name.endswith(".svg") or name.endswith(".gif"):
        return None

    data = wiki_request({
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url|size",
        "iiurlwidth": 1200,
        "format": "json",
    })
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if pid != "-1":
            info_list = page.get("imageinfo", [])
            if info_list:
                info = info_list[0]
                w = info.get("width", 0)
                h = info.get("height", 0)
                # Skip tiny images
                if w < 300 or h < 200:
                    return None
                return info.get("thumburl") or info.get("url")
    return None


def fetch_image_for_dest(dest_id):
    """Try all search terms for a destination, return (url, attribution) or (None, None)."""
    terms = SEARCH_TERMS.get(dest_id, [])

    for term in terms:
        # Step 1: search for the page
        page_title = search_wiki_page(term)
        if not page_title:
            continue
        time.sleep(0.15)

        # Step 2: try pageimages (fast path)
        url, attrib = get_page_image(page_title)
        if url:
            return url, attrib
        time.sleep(0.15)

        # Step 3: scan article images (slow path)
        image_files = get_article_images(page_title)
        time.sleep(0.15)
        for file_title in image_files[:10]:
            url = resolve_image_url(file_title)
            time.sleep(0.1)
            if url:
                attrib = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title)}"
                return url, attrib

    return None, None


def main():
    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM destinations")
    names = {r[0]: r[1] for r in cur.fetchall()}

    dest_ids = list(SEARCH_TERMS.keys())
    print(f"Processing {len(dest_ids)} destinations...\n")

    updated = 0
    still_missing = []

    for i, dest_id in enumerate(dest_ids, 1):
        name = names.get(dest_id, f"ID {dest_id}")
        print(f"  [{i}/{len(dest_ids)}] {name}...", end=" ", flush=True)

        url, attrib = fetch_image_for_dest(dest_id)

        if url:
            cur.execute("""
                UPDATE destination_images
                SET image_url = ?,
                    source = 'Wikipedia',
                    author = 'See Wikipedia page history',
                    license = 'Creative Commons / see Wikipedia page',
                    attribution = ?
                WHERE destination_id = ?
            """, (url, attrib, dest_id))
            conn.commit()
            print(f"[OK] {url[:70]}")
            updated += 1
        else:
            print("[--] not found")
            still_missing.append(name)

        time.sleep(0.2)

    conn.close()
    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(dest_ids)}")
    if still_missing:
        print(f"\nStill missing ({len(still_missing)}):")
        for n in still_missing:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
