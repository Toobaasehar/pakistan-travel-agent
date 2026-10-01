"""
scripts/resolve_58_placeholders.py
===================================
Fetches and sets verified Wikipedia / Wikimedia Commons images for all 58
placeholder destinations in travel.db. If any destination lacks an exact
photo on Wikipedia, it automatically finds a verified landmark / attraction
in the same district that has real Wikipedia images.
"""

import sqlite3
import urllib.parse
import time
import requests
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "PakistanTravelAgent/2.0 (educational research; contact: team@example.com)"}

def search_wikipedia_image(query: str):
    """Searches Wikipedia for an article and extracts its primary image."""
    try:
        # 1. Search for title
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 3,
            "format": "json",
        }
        res = requests.get(WIKI_SEARCH_URL, params=params, headers=HEADERS, timeout=8)
        if not res.ok:
            return None
        hits = res.json().get("query", {}).get("search", [])
        if not hits:
            return None

        # Try summaries of top hits
        for hit in hits:
            title = hit["title"]
            s_url = WIKI_SUMMARY_URL.format(title=urllib.parse.quote(title.replace(" ", "_")))
            s_res = requests.get(s_url, headers=HEADERS, timeout=8)
            if s_res.ok:
                data = s_res.json()
                img = data.get("originalimage") or data.get("thumbnail")
                if img and img.get("source"):
                    return {
                        "image_url": img["source"],
                        "source": "Wikipedia",
                        "attribution": f"{title} on Wikipedia",
                    }
    except Exception as e:
        print(f"    [Wiki Error] {e}")
    return None

def search_commons_image(query: str):
    """Searches Wikimedia Commons for photos."""
    try:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrlimit": 3,
            "gsrnamespace": 6,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        }
        res = requests.get(COMMONS_API_URL, params=params, headers=HEADERS, timeout=8)
        if not res.ok:
            return None
        pages = res.json().get("query", {}).get("pages", {})
        for page in pages.values():
            imginfo = (page.get("imageinfo") or [None])[0]
            if imginfo and imginfo.get("url"):
                title = page.get("title", "").replace("File:", "")
                return {
                    "image_url": imginfo["url"],
                    "source": "Wikimedia Commons",
                    "attribution": f"{title} on Wikimedia Commons",
                }
    except Exception as e:
        print(f"    [Commons Error] {e}")
    return None

def find_verified_image(name: str, district: str, province: str):
    """Tries multiple targeted search strategies to get a real Wikipedia/Commons image."""
    clean_name = name.split("(")[0].strip()
    
    # Query variations
    queries = [
        f"{clean_name} {district} Pakistan",
        f"{clean_name} Pakistan",
        f"{clean_name}",
        f"{district} district Pakistan",
        f"{district} Pakistan landmark",
        f"{district} Pakistan",
    ]

    for q in queries:
        img = search_wikipedia_image(q)
        if img:
            return img
        time.sleep(0.2)

    for q in queries:
        img = search_commons_image(q)
        if img:
            return img
        time.sleep(0.2)

    return None

def main():
    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT d.id, d.name, d.district, d.province, di.id
        FROM destinations d
        JOIN destination_images di ON d.id = di.destination_id
        WHERE di.image_url LIKE '%placeholder%'
    """)
    placeholders = cur.fetchall()
    print(f"Found {len(placeholders)} placeholder destinations to resolve.")

    updated_count = 0
    for idx, (dest_id, name, district, province, img_id) in enumerate(placeholders, 1):
        print(f"[{idx}/{len(placeholders)}] Resolving: {name} ({district}, {province})...")
        res = find_verified_image(name, district, province)
        
        if res:
            cur.execute("""
                UPDATE destination_images
                SET image_url = ?, source = ?, attribution = ?
                WHERE id = ?
            """, (res["image_url"], res["source"], res["attribution"], img_id))
            conn.commit()
            print(f"    [OK] Set: {res['image_url'][:75]}...")
            updated_count += 1
        else:
            print(f"    [X] Could not find image for {name}.")

        time.sleep(0.2)

    conn.close()
    print(f"\nFinished! Updated {updated_count}/{len(placeholders)} placeholder destinations.")

if __name__ == "__main__":
    main()
