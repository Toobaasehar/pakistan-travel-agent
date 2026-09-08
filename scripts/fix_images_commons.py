"""
fix_images_commons.py
======================
Uses Wikimedia Commons generator=search to find real photos
by keyword for the 48 destinations that Wikipedia API can't handle.
"""

import time, urllib.request, urllib.parse, json, sqlite3

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "PakistanTravelAgentStudentProject/1.0 (educational)"}

# Destination ID -> list of search keywords to try (most specific first)
SEARCH_TERMS = {
    14:  ["Shah Rukn-e-Alam Multan shrine", "Rukn-e-Alam shrine", "Multan shrine"],
    38:  ["Hazarganji Chiltan National Park", "Chiltan National Park Balochistan"],
    44:  ["Naltar Valley Gilgit", "Naltar Lakes Pakistan", "Naltar Valley"],
    45:  ["Shangrila Resort Skardu", "Lower Kachura Lake Skardu", "Kachura Lake Pakistan"],
    48:  ["Lok Virsa Museum Islamabad", "Lok Virsa Islamabad"],
    52:  ["Ilyasi Mosque Abbottabad", "Abbottabad mosque"],
    53:  ["Abbottabad city Pakistan", "Abbottabad KPK"],
    56:  ["Qissa Khwani Bazaar Peshawar", "Qissakhwani bazaar"],
    57:  ["Bala Hisar Fort Peshawar"],
    58:  ["Peshawar Museum", "Peshawar Museum Pakistan"],
    61:  ["Kalam Valley Swat Pakistan", "Kalam Swat Pakistan"],
    62:  ["Swat Museum Pakistan", "Saidu Sharif Swat"],
    64:  ["Noor Mahal Bahawalpur palace", "Noor Mahal Bahawalpur"],
    72:  ["Faisalabad city Pakistan", "Faisalabad clock tower"],
    73:  ["Faisalabad Pakistan", "Lyallpur Faisalabad"],
    74:  ["Gujranwala Punjab Pakistan"],
    75:  ["Gujranwala city Punjab"],
    83:  ["Shah Rukn-e-Alam shrine Multan", "Multan Rukn-e-Alam"],
    103: ["Hyderabad Sindh museum", "Hyderabad fort Sindh"],
    104: ["Talpur Mirs tombs Hyderabad Sindh", "Talpur mausoleum"],
    105: ["Hyderabad Sindh Pakistan", "Shahi Bazaar Hyderabad"],
    107: ["Empress Market Karachi", "Empress Market"],
    108: ["Mohatta Palace Karachi", "Mohatta Palace museum"],
    111: ["Garhi Khuda Bakhsh Bhutto mausoleum", "Bhutto mausoleum Larkana"],
    112: ["Kot Diji fort Khairpur", "Kot Diji fort Sindh"],
    113: ["Mirpur Khas Sindh Pakistan", "Mirpurkhas city"],
    114: ["Mirpur Khas Sindh", "Mirpurkhas Pakistan"],
    115: ["Shah Abdul Latif Bhittai shrine Bhitshah", "Bhitshah shrine Sindh"],
    116: ["Nawabshah city Sindh", "Shaheed Benazirabad Pakistan"],
    117: ["Sukkur Barrage Sindh", "Sukkur Barrage"],
    118: ["Sadhu Bela temple Sukkur Sindh", "Sadhu Bela island"],
    119: ["Lansdowne Bridge Sukkur", "Sukkur bridge Sindh"],
    120: ["Moola Chotok waterfall Balochistan", "Moola Chotok"],
    121: ["Khuzdar Balochistan Pakistan", "Khuzdar city"],
    123: ["Sibi city Balochistan", "Sibi mela festival"],
    124: ["Zhob city Balochistan Pakistan", "Zhob district"],
    132: ["Dir valley KPK Pakistan", "Dir Lower Pakistan"],
    138: ["Loralai Balochistan Pakistan"],
    139: ["Loralai city Balochistan"],
    140: ["Indus River Pakistan", "Indus River Sindh"],
    141: ["Dera Ismail Khan city", "DI Khan KPK Pakistan"],
    142: ["Kabul River Nowshera Pakistan", "Kabul River KPK"],
    143: ["Cherat hill station Peshawar", "Cherat Pakistan"],
    144: ["Bulleh Shah shrine Kasur", "Bulleh Shah mausoleum"],
    145: ["Kasur city Punjab Pakistan", "Kasur Punjab"],
    146: ["Okara Punjab Pakistan", "Okara city"],
    147: ["Okara district Pakistan", "Renala Khurd Okara"],
    148: ["Vehari Punjab Pakistan", "Vehari district"],
}

SKIP_KW = ["flag", "icon", "logo", "seal", "map", "locator",
           "blank", "coat", "emblem", "symbol", "sign", "stamp"]

def commons_search(query, limit=8):
    """Search Wikimedia Commons for images matching query."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrnamespace": "6",          # File namespace
        "gsrsearch": query,
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": "1200",
        "format": "json",
    }
    req = urllib.request.Request(
        f"{COMMONS_API}?{urllib.parse.urlencode(params)}",
        headers=HEADERS,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"      API error: {e}")
        return {}


def best_image_from_results(data):
    """Pick the best (largest, most photo-like) image from API results."""
    pages = data.get("query", {}).get("pages", {})
    candidates = []

    for pid, page in pages.items():
        title = page.get("title", "").lower()
        # Skip icons/maps/diagrams
        if any(kw in title for kw in SKIP_KW):
            continue
        if title.endswith(".svg") or title.endswith(".gif"):
            continue

        info_list = page.get("imageinfo", [])
        if not info_list:
            continue
        info = info_list[0]

        w = info.get("width", 0)
        h = info.get("height", 0)
        if w < 400 or h < 300:
            continue

        url = info.get("thumburl") or info.get("url", "")
        if not url:
            continue

        # Prefer landscape images (wider than tall)
        score = w * h
        candidates.append((score, url, page.get("title", "")))

    if not candidates:
        return None, None

    candidates.sort(reverse=True)
    _, best_url, file_title = candidates[0]
    attrib = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(file_title)}"
    return best_url, attrib


def main():
    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM destinations")
    names = {r[0]: r[1] for r in cur.fetchall()}

    dest_ids = list(SEARCH_TERMS.keys())
    print(f"Searching Wikimedia Commons for {len(dest_ids)} destinations...\n")

    updated = 0
    still_missing = []

    for i, dest_id in enumerate(dest_ids, 1):
        name = names.get(dest_id, f"ID {dest_id}")
        print(f"  [{i}/{len(dest_ids)}] {name}...", end=" ", flush=True)

        found_url = None
        found_attrib = None

        for term in SEARCH_TERMS[dest_id]:
            data = commons_search(term)
            time.sleep(0.3)
            url, attrib = best_image_from_results(data)
            if url:
                found_url = url
                found_attrib = attrib
                break

        if found_url:
            cur.execute("""
                UPDATE destination_images
                SET image_url = ?,
                    source = 'Wikimedia Commons',
                    author = 'See Wikimedia Commons page',
                    license = 'Creative Commons / see Commons page',
                    attribution = ?
                WHERE destination_id = ?
            """, (found_url, found_attrib, dest_id))
            conn.commit()
            print(f"[OK] {found_url[:65]}...")
            updated += 1
        else:
            print("[--] not found")
            still_missing.append((dest_id, name))

        time.sleep(0.2)

    conn.close()
    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(dest_ids)}")

    if still_missing:
        print(f"\nStill missing ({len(still_missing)}) - IDs for manual fix:")
        for did, n in still_missing:
            print(f"  [{did}] {n}")


if __name__ == "__main__":
    main()
