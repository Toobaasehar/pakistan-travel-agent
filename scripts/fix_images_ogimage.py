"""
fix_images_ogimage.py
======================
Fetches each Wikipedia page as HTML and extracts the og:image
meta tag — every Wikipedia article that has a lead image exposes
it here. No API, no rate-limiting, just a plain GET + regex.
"""

import time, re, urllib.request, urllib.parse, sqlite3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Destination ID -> list of Wikipedia article slugs to try (best first)
WIKI_SLUGS = {
    14:  ["Shrine_of_Shah_Rukn-e-Alam", "Shah_Rukn-e-Alam"],
    38:  ["Hazarganji_Chiltan_National_Park"],
    44:  ["Naltar_Valley", "Naltar,_Gilgit-Baltistan"],
    45:  ["Shangrila_Resort,_Pakistan", "Lower_Kachura_Lake"],
    48:  ["Lok_Virsa_Museum"],
    52:  ["Ilyasi_Mosque", "Abbottabad"],
    53:  ["Abbottabad"],
    56:  ["Qissa_Khwani_Bazaar"],
    57:  ["Bala_Hisar_Fort,_Peshawar"],
    58:  ["Peshawar_Museum"],
    61:  ["Kalam,_Khyber_Pakhtunkhwa"],
    62:  ["Swat_Museum", "Saidu_Sharif"],
    64:  ["Noor_Mahal,_Bahawalpur"],
    72:  ["Faisalabad"],
    73:  ["Faisalabad"],
    74:  ["Gujranwala"],
    75:  ["Gujranwala"],
    83:  ["Shrine_of_Shah_Rukn-e-Alam"],
    103: ["Hyderabad,_Sindh"],
    104: ["Talpur_Mirs", "Hyderabad,_Sindh"],
    105: ["Hyderabad,_Sindh"],
    107: ["Empress_Market,_Karachi"],
    108: ["Mohatta_Palace"],
    111: ["Garhi_Khuda_Bakhsh"],
    112: ["Kot_Diji"],
    113: ["Mirpur_Khas"],
    114: ["Mirpur_Khas"],
    115: ["Shah_Abdul_Latif_Bhittai"],
    116: ["Shaheed_Benazirabad"],
    117: ["Sukkur_Barrage"],
    118: ["Sadhu_Bela"],
    119: ["Lansdowne_Bridge,_Sukkur"],
    120: ["Moola_Chotok"],
    121: ["Khuzdar"],
    123: ["Sibi"],
    124: ["Zhob_District", "Zhob"],
    132: ["Dir,_Khyber_Pakhtunkhwa"],
    138: ["Loralai"],
    139: ["Loralai"],
    140: ["Indus_River"],
    141: ["Dera_Ismail_Khan"],
    142: ["Kabul_River"],
    143: ["Cherat"],
    144: ["Bulleh_Shah"],
    145: ["Kasur"],
    146: ["Okara_District"],
    147: ["Okara_District"],
    148: ["Vehari_District"],
}

OG_IMG_RE = re.compile(
    r'<meta\s+property=["\']og:image["\']\s+content=["\'](https?://[^"\']+)["\']',
    re.IGNORECASE,
)
OG_IMG_RE2 = re.compile(
    r'<meta\s+content=["\'](https?://[^"\']+)["\']\s+property=["\']og:image["\']',
    re.IGNORECASE,
)


def fetch_og_image(slug, retries=3):
    """Fetch Wikipedia page and return og:image URL."""
    url = f"https://en.wikipedia.org/wiki/{slug}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                # Read first 30 KB — og:image is always in <head>
                html = resp.read(30720).decode("utf-8", errors="ignore")
                m = OG_IMG_RE.search(html) or OG_IMG_RE2.search(html)
                if m:
                    img_url = m.group(1)
                    # Convert to higher-res version (replace /200px- with /1200px-)
                    img_url = re.sub(r'/\d+px-', '/1200px-', img_url)
                    return img_url, url
                return None, None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, None
            time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    return None, None


def main():
    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM destinations")
    names = {r[0]: r[1] for r in cur.fetchall()}

    dest_ids = list(WIKI_SLUGS.keys())
    print(f"Fetching og:image for {len(dest_ids)} destinations...\n")

    updated = 0
    still_missing = []

    for i, dest_id in enumerate(dest_ids, 1):
        name = names.get(dest_id, f"ID {dest_id}")
        print(f"  [{i}/{len(dest_ids)}] {name}...", end=" ", flush=True)

        found_url = None
        found_attrib = None

        for slug in WIKI_SLUGS[dest_id]:
            img_url, page_url = fetch_og_image(slug)
            time.sleep(0.5)
            if img_url:
                found_url = img_url
                found_attrib = page_url
                break

        if found_url:
            cur.execute("""
                UPDATE destination_images
                SET image_url   = ?,
                    source      = 'Wikipedia',
                    author      = 'See Wikipedia page history',
                    license     = 'Creative Commons / see Wikipedia page',
                    attribution = ?
                WHERE destination_id = ?
            """, (found_url, found_attrib, dest_id))
            conn.commit()
            print(f"[OK] {found_url[:65]}...")
            updated += 1
        else:
            print("[--] no og:image found")
            still_missing.append((dest_id, name))

        time.sleep(0.5)

    conn.close()
    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(dest_ids)}")
    if still_missing:
        print(f"\nStill missing ({len(still_missing)}):")
        for did, n in still_missing:
            print(f"  [{did}] {n}")


if __name__ == "__main__":
    main()
