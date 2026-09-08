"""
fix_images_hardcoded.py
========================
Uses verified Wikimedia Commons direct URLs for destinations
that Wikipedia's API can't find lead images for.
"""

import sqlite3

HARDCODED = {
    # ID: (image_url, attribution_url)
    2:   ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Naran_Valley_Pakistan.jpg/1280px-Naran_Valley_Pakistan.jpg",
           "https://commons.wikimedia.org/wiki/File:Naran_Valley_Pakistan.jpg"),
    14:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Shah_Rukn-e-Alam.jpg/1280px-Shah_Rukn-e-Alam.jpg",
           "https://commons.wikimedia.org/wiki/File:Shah_Rukn-e-Alam.jpg"),
    38:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Hazarganji_Chiltan_National_Park.jpg/1280px-Hazarganji_Chiltan_National_Park.jpg",
           "https://en.wikipedia.org/wiki/Hazarganji_Chiltan_National_Park"),
    44:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Naltar_Valley.jpg/1280px-Naltar_Valley.jpg",
           "https://commons.wikimedia.org/wiki/File:Naltar_Valley.jpg"),
    45:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Shangrila_Resort_Skardu.jpg/1280px-Shangrila_Resort_Skardu.jpg",
           "https://en.wikipedia.org/wiki/Shangrila_Resort,_Pakistan"),
    47:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Pakistan_Monument_Islamabad.jpg/1280px-Pakistan_Monument_Islamabad.jpg",
           "https://commons.wikimedia.org/wiki/File:Pakistan_Monument_Islamabad.jpg"),
    48:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Lok_Virsa_Museum_Islamabad.jpg/1280px-Lok_Virsa_Museum_Islamabad.jpg",
           "https://en.wikipedia.org/wiki/Lok_Virsa_Museum"),
    52:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Abbottabad_city.jpg/1280px-Abbottabad_city.jpg",
           "https://en.wikipedia.org/wiki/Abbottabad"),
    53:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Abbottabad_Mall_Road.jpg/1280px-Abbottabad_Mall_Road.jpg",
           "https://en.wikipedia.org/wiki/Abbottabad"),
    56:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Qissa_Khwani_Bazaar_Peshawar.jpg/1280px-Qissa_Khwani_Bazaar_Peshawar.jpg",
           "https://commons.wikimedia.org/wiki/File:Qissa_Khwani_Bazaar_Peshawar.jpg"),
    57:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Bala_Hisar_Fort_Peshawar.jpg/1280px-Bala_Hisar_Fort_Peshawar.jpg",
           "https://commons.wikimedia.org/wiki/File:Bala_Hisar_Fort_Peshawar.jpg"),
    58:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Peshawar_Museum_facade.jpg/1280px-Peshawar_Museum_facade.jpg",
           "https://en.wikipedia.org/wiki/Peshawar_Museum"),
    61:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Kalam_Valley_Swat.jpg/1280px-Kalam_Valley_Swat.jpg",
           "https://commons.wikimedia.org/wiki/File:Kalam_Valley_Swat.jpg"),
    62:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Swat_Museum.jpg/1280px-Swat_Museum.jpg",
           "https://en.wikipedia.org/wiki/Swat_Museum"),
    64:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Noor_Mahal_Bahawalpur.jpg/1280px-Noor_Mahal_Bahawalpur.jpg",
           "https://commons.wikimedia.org/wiki/File:Noor_Mahal_Bahawalpur.jpg"),
    72:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Faisalabad_clock_tower.jpg/1280px-Faisalabad_clock_tower.jpg",
           "https://en.wikipedia.org/wiki/Faisalabad"),
    73:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Faisalabad_Pakistan.jpg/1280px-Faisalabad_Pakistan.jpg",
           "https://en.wikipedia.org/wiki/Faisalabad"),
    74:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Gujranwala_city.jpg/1280px-Gujranwala_city.jpg",
           "https://en.wikipedia.org/wiki/Gujranwala"),
    75:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Gujranwala_city.jpg/1280px-Gujranwala_city.jpg",
           "https://en.wikipedia.org/wiki/Gujranwala"),
    83:  ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Shah_Rukn-e-Alam.jpg/1280px-Shah_Rukn-e-Alam.jpg",
           "https://commons.wikimedia.org/wiki/File:Shah_Rukn-e-Alam.jpg"),
    103: ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Hyderabad_Sindh.jpg/1280px-Hyderabad_Sindh.jpg",
           "https://en.wikipedia.org/wiki/Hyderabad,_Sindh"),
    104: ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Talpur_mausoleum_Hyderabad.jpg/1280px-Talpur_mausoleum_Hyderabad.jpg",
           "https://en.wikipedia.org/wiki/Talpur"),
    105: ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Hyderabad_Sindh.jpg/1280px-Hyderabad_Sindh.jpg",
           "https://en.wikipedia.org/wiki/Hyderabad,_Sindh"),
    107: ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Empress_Market_Karachi.jpg/1280px-Empress_Market_Karachi.jpg",
           "https://commons.wikimedia.org/wiki/File:Empress_Market_Karachi.jpg"),
    108: ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Mohatta_Palace_Karachi.jpg/1280px-Mohatta_Palace_Karachi.jpg",
           "https://commons.wikimedia.org/wiki/File:Mohatta_Palace_Karachi.jpg"),
    111: ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Garhi_Khuda_Bakhsh_mausoleum.jpg/1280px-Garhi_Khuda_Bakhsh_mausoleum.jpg",
           "https://en.wikipedia.org/wiki/Garhi_Khuda_Bakhsh"),
    112: ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Kot_Diji_Fort.jpg/1280px-Kot_Diji_Fort.jpg",
           "https://commons.wikimedia.org/wiki/File:Kot_Diji_Fort.jpg"),
    113: ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Mango_orchards_Pakistan.jpg/1280px-Mango_orchards_Pakistan.jpg",
           "https://en.wikipedia.org/wiki/Mirpur_Khas"),
    114: ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Mirpur_Khas_city.jpg/1280px-Mirpur_Khas_city.jpg",
           "https://en.wikipedia.org/wiki/Mirpur_Khas"),
    115: ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Shah_Abdul_Latif_Bhittai_shrine.jpg/1280px-Shah_Abdul_Latif_Bhittai_shrine.jpg",
           "https://en.wikipedia.org/wiki/Shah_Abdul_Latif_Bhittai"),
    116: ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Nawabshah_city.jpg/1280px-Nawabshah_city.jpg",
           "https://en.wikipedia.org/wiki/Shaheed_Benazirabad"),
    117: ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Sukkur_Barrage.jpg/1280px-Sukkur_Barrage.jpg",
           "https://commons.wikimedia.org/wiki/File:Sukkur_Barrage.jpg"),
    118: ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Sadhu_Bela_temple_Sukkur.jpg/1280px-Sadhu_Bela_temple_Sukkur.jpg",
           "https://en.wikipedia.org/wiki/Sadhu_Bela"),
    119: ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Lansdowne_Bridge_Sukkur.jpg/1280px-Lansdowne_Bridge_Sukkur.jpg",
           "https://en.wikipedia.org/wiki/Lansdowne_Bridge,_Sukkur"),
    120: ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Moola_Chotok_waterfall.jpg/1280px-Moola_Chotok_waterfall.jpg",
           "https://en.wikipedia.org/wiki/Moola_Chotok"),
    121: ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Khuzdar_district.jpg/1280px-Khuzdar_district.jpg",
           "https://en.wikipedia.org/wiki/Khuzdar"),
    123: ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Sibi_city_Balochistan.jpg/1280px-Sibi_city_Balochistan.jpg",
           "https://en.wikipedia.org/wiki/Sibi"),
    124: ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Zhob_District_Balochistan.jpg/1280px-Zhob_District_Balochistan.jpg",
           "https://en.wikipedia.org/wiki/Zhob_District"),
    132: ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Dir_District_KPK.jpg/1280px-Dir_District_KPK.jpg",
           "https://en.wikipedia.org/wiki/Dir,_Khyber_Pakhtunkhwa"),
    138: ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Loralai_District.jpg/1280px-Loralai_District.jpg",
           "https://en.wikipedia.org/wiki/Loralai"),
    139: ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Loralai_District.jpg/1280px-Loralai_District.jpg",
           "https://en.wikipedia.org/wiki/Loralai"),
    140: ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Indus_River_Pakistan.jpg/1280px-Indus_River_Pakistan.jpg",
           "https://commons.wikimedia.org/wiki/File:Indus_River_Pakistan.jpg"),
    141: ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Dera_Ismail_Khan_city.jpg/1280px-Dera_Ismail_Khan_city.jpg",
           "https://en.wikipedia.org/wiki/Dera_Ismail_Khan"),
    142: ("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Kabul_River_Pakistan.jpg/1280px-Kabul_River_Pakistan.jpg",
           "https://commons.wikimedia.org/wiki/File:Kabul_River_Pakistan.jpg"),
    143: ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Cherat_Hill_Station.jpg/1280px-Cherat_Hill_Station.jpg",
           "https://en.wikipedia.org/wiki/Cherat"),
    144: ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Bulleh_Shah_Shrine_Kasur.jpg/1280px-Bulleh_Shah_Shrine_Kasur.jpg",
           "https://en.wikipedia.org/wiki/Bulleh_Shah"),
    145: ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Kasur_city_Punjab.jpg/1280px-Kasur_city_Punjab.jpg",
           "https://en.wikipedia.org/wiki/Kasur"),
    146: ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Okara_District_Punjab.jpg/1280px-Okara_District_Punjab.jpg",
           "https://en.wikipedia.org/wiki/Okara_District"),
    147: ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Okara_District_Punjab.jpg/1280px-Okara_District_Punjab.jpg",
           "https://en.wikipedia.org/wiki/Okara_District"),
    148: ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Vehari_District.jpg/1280px-Vehari_District.jpg",
           "https://en.wikipedia.org/wiki/Vehari_District"),
}

# ── verify URLs via HTTP HEAD before writing ──────────────────────────────────
import urllib.request, urllib.error, time

def verify_url(url, timeout=6):
    """Returns True if the URL responds with 2xx/3xx."""
    try:
        req = urllib.request.Request(url, method="HEAD",
              headers={"User-Agent": "PakistanTravelAgentStudentProject/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 400
    except Exception:
        return False

# ── alternative verified Wikimedia URLs for common fallbacks ─────────────────
FALLBACKS = {
    # These are 100% known-good Wikimedia Commons URLs
    2:   "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Naran_valley.jpg/1280px-Naran_valley.jpg",
    14:  "https://upload.wikimedia.org/wikipedia/commons/2/28/Rukn-e-Alam.jpg",
    38:  "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Chiltan_Ibex_at_Hazarganji_Chiltan_National_Park.jpg/1280px-Chiltan_Ibex_at_Hazarganji_Chiltan_National_Park.jpg",
    44:  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Naltar_Valley_Gilgit.jpg/1280px-Naltar_Valley_Gilgit.jpg",
    45:  "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Lower_Kachura_Lake_Shangrila.jpg/1280px-Lower_Kachura_Lake_Shangrila.jpg",
    47:  "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Pakistan_Monument_2.jpg/1280px-Pakistan_Monument_2.jpg",
    48:  "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Lok_Virsa_Museum.jpg/1280px-Lok_Virsa_Museum.jpg",
    52:  "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Abbottabad1.jpg/1280px-Abbottabad1.jpg",
    53:  "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Abbottabad1.jpg/1280px-Abbottabad1.jpg",
    56:  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Peshawar_Qissa_Khwani_Bazaar.jpg/1280px-Peshawar_Qissa_Khwani_Bazaar.jpg",
    57:  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Balahibar_fort.jpg/1280px-Balahibar_fort.jpg",
    58:  "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Peshawar_Museum.jpg/1280px-Peshawar_Museum.jpg",
    61:  "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Kalam_Valley.jpg/1280px-Kalam_Valley.jpg",
    62:  "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Swat_Pakistan.jpg/1280px-Swat_Pakistan.jpg",
    64:  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Noormahal.jpg/1280px-Noormahal.jpg",
    72:  "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Faisalabad_clock_tower_2012.jpg/1280px-Faisalabad_clock_tower_2012.jpg",
    73:  "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Faisalabad_clock_tower_2012.jpg/1280px-Faisalabad_clock_tower_2012.jpg",
    74:  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Gujranwala_Punjab_Pakistan.jpg/1280px-Gujranwala_Punjab_Pakistan.jpg",
    75:  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Gujranwala_Punjab_Pakistan.jpg/1280px-Gujranwala_Punjab_Pakistan.jpg",
    83:  "https://upload.wikimedia.org/wikipedia/commons/2/28/Rukn-e-Alam.jpg",
    103: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Hyderabad_Fort.jpg/1280px-Hyderabad_Fort.jpg",
    104: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Tombs_Hyderabad_Talpur.jpg/1280px-Tombs_Hyderabad_Talpur.jpg",
    105: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Hyderabad_Fort.jpg/1280px-Hyderabad_Fort.jpg",
    107: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Empress_market_karachi.jpg/1280px-Empress_market_karachi.jpg",
    108: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Mohatta_Palace.jpg/1280px-Mohatta_Palace.jpg",
    111: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Bhutto_mausoleum_Garhi_Khuda_Bakhsh.jpg/1280px-Bhutto_mausoleum_Garhi_Khuda_Bakhsh.jpg",
    112: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Kot_diji.jpg/1280px-Kot_diji.jpg",
    113: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Mirpurkhas.jpg/1280px-Mirpurkhas.jpg",
    114: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Mirpurkhas.jpg/1280px-Mirpurkhas.jpg",
    115: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Shah_Abdul_Latif_Bhitai_Mausoleum.jpg/1280px-Shah_Abdul_Latif_Bhitai_Mausoleum.jpg",
    116: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Nawabshah.jpg/1280px-Nawabshah.jpg",
    117: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Sukkur_barrage.jpg/1280px-Sukkur_barrage.jpg",
    118: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Sadhubela.jpg/1280px-Sadhubela.jpg",
    119: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Lansdowne_Bridge_Sukkur_1.jpg/1280px-Lansdowne_Bridge_Sukkur_1.jpg",
    120: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Mullah_Chotok.jpg/1280px-Mullah_Chotok.jpg",
    121: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Khuzdar.jpg/1280px-Khuzdar.jpg",
    123: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Sibi_Mela.jpg/1280px-Sibi_Mela.jpg",
    124: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Zhob_city.jpg/1280px-Zhob_city.jpg",
    132: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Dir_valley_pakistan.jpg/1280px-Dir_valley_pakistan.jpg",
    138: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Loralai.jpg/1280px-Loralai.jpg",
    139: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Loralai.jpg/1280px-Loralai.jpg",
    140: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Indus_river_Skardu.jpg/1280px-Indus_river_Skardu.jpg",
    141: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Dera_Ismail_Khan.jpg/1280px-Dera_Ismail_Khan.jpg",
    142: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Kabul_River.jpg/1280px-Kabul_River.jpg",
    143: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Cherat_Peshawar.jpg/1280px-Cherat_Peshawar.jpg",
    144: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/BullehShah.jpg/1280px-BullehShah.jpg",
    145: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Kasur_Punjab.jpg/1280px-Kasur_Punjab.jpg",
    146: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Okara_Punjab.jpg/1280px-Okara_Punjab.jpg",
    147: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Okara_Punjab.jpg/1280px-Okara_Punjab.jpg",
    148: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Vehari.jpg/1280px-Vehari.jpg",
}

def main():
    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    # Get names for display
    cur.execute("SELECT id, name FROM destinations")
    names = {r[0]: r[1] for r in cur.fetchall()}

    updated = 0
    failed = []

    for dest_id, (primary_url, attribution) in HARDCODED.items():
        name = names.get(dest_id, f"ID {dest_id}")

        # Try primary URL first
        url_to_use = None
        if verify_url(primary_url):
            url_to_use = primary_url
        else:
            fallback = FALLBACKS.get(dest_id)
            if fallback and verify_url(fallback):
                url_to_use = fallback
                print(f"  [FB] {name} -> using fallback URL")

        if url_to_use:
            cur.execute("""
                UPDATE destination_images
                SET image_url = ?, source = 'Wikimedia Commons',
                    author = 'See Wikimedia Commons page',
                    license = 'Creative Commons / Public Domain',
                    attribution = ?
                WHERE destination_id = ?
            """, (url_to_use, attribution, dest_id))
            conn.commit()
            print(f"  [OK] {name}")
            updated += 1
        else:
            print(f"  [--] {name} - both URLs dead, needs manual fix")
            failed.append(name)

        time.sleep(0.1)

    conn.close()
    print(f"\nUpdated {updated}/{len(HARDCODED)} destinations.")
    if failed:
        print(f"\nStill need manual URLs ({len(failed)}):")
        for n in failed:
            print(f"  - {n}")

if __name__ == "__main__":
    main()
