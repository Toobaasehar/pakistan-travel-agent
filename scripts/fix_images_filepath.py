"""
fix_images_filepath.py
=======================
Uses Commons Special:FilePath redirect (simple GET, no API calls)
with known-correct filenames + retry on network errors.
"""

import time, urllib.request, sqlite3

COMMONS_FP = "https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=1200"
HEADERS = {"User-Agent": "PakistanTravelAgent/1.0 (student project; educational)"}

# destination_id -> list of candidate Commons filenames (try in order)
CANDIDATES = {
    14:  ["Rukn-e-Alam.jpg",
          "Shah_Rukn-e-Alam_Multan.jpg",
          "Shah_Rukn_e_Alam.jpg"],
    38:  ["Chiltan_Ibex_at_Hazarganji_Chiltan_National_Park.jpg",
          "Hazarganji_Chiltan_National_Park.jpg",
          "Hazarganji-Chiltan.jpg"],
    44:  ["Naltar_valley.jpg",
          "Naltar_Valley_Gilgit.jpg",
          "Naltar_Lakes.jpg",
          "Naltar.jpg"],
    45:  ["Lower_Kachura_Lake.jpg",
          "Shangrila_Resort_Pakistan.jpg",
          "Shangrila_resort_skardu.jpg"],
    48:  ["Lok_Virsa_Museum_Islamabad.jpg",
          "Lok_Virsa_Museum.jpg",
          "Lok_Virsa.jpg"],
    52:  ["Ilyasi_mosque_Abbottabad.jpg",
          "Abbottabad_view.jpg",
          "Abbottabad1.jpg"],
    53:  ["Abbottabad1.jpg",
          "Abbottabad_city.jpg",
          "Abbottabad_KPK.jpg"],
    56:  ["Qissa_Khwani_Bazaar.jpg",
          "Qissakhwani_bazar.jpg",
          "Peshawar_Qissa_Khwani_Bazaar.jpg"],
    57:  ["Bala_Hisar_Fort,_Peshawar.jpg",
          "Balahibar_fort.jpg",
          "Bala_Hisar_Fort.jpg"],
    58:  ["Peshawar_Museum_facade.jpg",
          "Peshawar_Museum.jpg",
          "The_Peshawar_Museum.jpg"],
    61:  ["Kalam,_Khyber_Pakhtunkhwa.jpg",
          "Kalam_Valley.jpg",
          "Kalam_Pakistan.jpg"],
    62:  ["Swat_Museum.jpg",
          "Saidu_Sharif_Museum.jpg",
          "Swat_valley_Pakistan.jpg"],
    64:  ["Noormahal.jpg",
          "Noor_Mahal_Bahawalpur.jpg",
          "Noor_mahal_bahawalpur.jpg"],
    72:  ["Ghanta_Ghar,_Faisalabad.jpg",
          "Faisalabad_clock_tower.jpg",
          "Faisalabad_city.jpg"],
    73:  ["Faisalabad_city.jpg",
          "Lyallpur_Faisalabad.jpg",
          "Faisalabad_Pakistan.jpg"],
    74:  ["Gujranwala_city_view.jpg",
          "Gujranwala_Punjab.jpg",
          "Gujranwala.jpg"],
    75:  ["Gujranwala_city_view.jpg",
          "Gujranwala.jpg",
          "Gujranwala_Pakistan.jpg"],
    83:  ["Rukn-e-Alam.jpg",
          "Shah_Rukn-e-Alam_Multan.jpg",
          "Shah_rukn_e_alam_shrine_Multan.jpg"],
    103: ["Hyderabad_Fort.jpg",
          "Hyderabad_Sindh.jpg",
          "Kachehri_Hyderabad.jpg"],
    104: ["Tombs_of_the_Talpur_Mirs.jpg",
          "Talpur_Mirs_tombs.jpg",
          "Chaukhandi_tombs.jpg"],
    105: ["Hyderabad_Fort.jpg",
          "Hyderabad_Sindh.jpg",
          "Shahi_Bazaar_Hyderabad.jpg"],
    107: ["Empress_Market,_Karachi.jpg",
          "Empress_Market_Karachi.jpg",
          "Empress_market_karachi.jpg"],
    108: ["Mohatta_Palace.jpg",
          "Mohatta_Palace_Karachi.jpg",
          "Mohatta_palace_museum.jpg"],
    111: ["Garhi_Khuda_Bakhsh.jpg",
          "Bhutto_mausoleum.jpg",
          "Bhutto_mausoleum_Garhi_Khuda_Bakhsh.jpg"],
    112: ["Kot_Diji.jpg",
          "Kot_Diji_Fort.jpg",
          "Kot_diji_fort_sindh.jpg"],
    113: ["Mirpur_Khas.jpg",
          "Mirpurkhas.jpg",
          "Mirpur_Khas_city.jpg"],
    114: ["Mirpur_Khas.jpg",
          "Mirpurkhas.jpg",
          "Mirpur_Khas_Sindh.jpg"],
    115: ["Shah_Abdul_Latif_Bhittai_shrine.jpg",
          "Shah_Abdul_Latif_Bhitai_Mausoleum.jpg",
          "Bhitshah_shrine.jpg"],
    116: ["Nawabshah.jpg",
          "Shaheed_Benazirabad.jpg",
          "Nawabshah_city.jpg"],
    117: ["Sukkur_Barrage.jpg",
          "Sukkur_barrage.jpg",
          "Lloyd_Barrage_Sukkur.jpg"],
    118: ["Sadhubela.jpg",
          "Sadhu_Bela_temple.jpg",
          "Sadhu_Bela_island.jpg"],
    119: ["Lansdowne_Bridge,_Sukkur.jpg",
          "Lansdowne_Bridge_Sukkur.jpg",
          "Sukkur_bridge.jpg"],
    120: ["Moola_Chotok.jpg",
          "Mullah_Chotok.jpg",
          "Moola_Chotok_waterfall.jpg"],
    121: ["Khuzdar.jpg",
          "Khuzdar_city.jpg",
          "Khuzdar_Balochistan.jpg"],
    123: ["Sibi_Fort.jpg",
          "Sibi_mela.jpg",
          "Sibi.jpg"],
    124: ["Zhob.jpg",
          "Zhob_city.jpg",
          "Zhob_district.jpg"],
    132: ["Dir_valley_pakistan.jpg",
          "Dir_Pakistan.jpg",
          "Dir_Lower_Pakistan.jpg"],
    138: ["Loralai.jpg",
          "Loralai_Balochistan.jpg",
          "Loralai_city.jpg"],
    139: ["Loralai.jpg",
          "Loralai_Balochistan.jpg",
          "Loralai_Pakistan.jpg"],
    140: ["Indus_river.jpg",
          "Indus_River_Pakistan.jpg",
          "Indus_river_Pakistan.jpg"],
    141: ["Dera_Ismail_Khan.jpg",
          "Dera_Ismail_Khan_city.jpg",
          "DI_Khan.jpg"],
    142: ["Kabul_River.jpg",
          "Kabul_River_Pakistan.jpg",
          "Kabul_river_nowshera.jpg"],
    143: ["Cherat.jpg",
          "Cherat_hill_station.jpg",
          "Cherat_Pakistan.jpg"],
    144: ["Baba_Bulleh_Shah_Shrine.jpg",
          "Bulleh_Shah_Kasur.jpg",
          "BullehShah.jpg"],
    145: ["Kasur.jpg",
          "Kasur_Pakistan.jpg",
          "Kasur_city.jpg"],
    146: ["Okara_district.jpg",
          "Okara_Punjab.jpg",
          "Okara_Pakistan.jpg"],
    147: ["Okara_district.jpg",
          "Okara_farms.jpg",
          "Renala_Khurd.jpg"],
    148: ["Vehari.jpg",
          "Vehari_district.jpg",
          "Vehari_Punjab.jpg"],
}


def resolve_filepath(filename, retries=3):
    """
    Follow the Special:FilePath redirect to get the actual CDN URL.
    Returns (final_url, None) or (None, error_msg).
    """
    url = COMMONS_FP.format(filename=urllib.parse.quote(filename))
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                final_url = resp.url
                # Sanity check: must be a real upload URL
                if "upload.wikimedia.org" in final_url:
                    return final_url, None
                return None, "unexpected redirect destination"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "404"
            wait = 2 ** attempt
            time.sleep(wait)
        except Exception as e:
            wait = 2 ** attempt
            time.sleep(wait)
    return None, "failed after retries"


def main():
    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM destinations")
    names = {r[0]: r[1] for r in cur.fetchall()}

    dest_ids = list(CANDIDATES.keys())
    print(f"Resolving images for {len(dest_ids)} destinations via Special:FilePath...\n")

    updated = 0
    still_missing = []

    for i, dest_id in enumerate(dest_ids, 1):
        name = names.get(dest_id, f"ID {dest_id}")
        print(f"  [{i}/{len(dest_ids)}] {name}...", end=" ", flush=True)

        found_url = None
        found_attrib = None

        for filename in CANDIDATES[dest_id]:
            final_url, err = resolve_filepath(filename)
            time.sleep(0.4)
            if final_url:
                found_url = final_url
                found_attrib = f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(filename)}"
                break

        if found_url:
            cur.execute("""
                UPDATE destination_images
                SET image_url    = ?,
                    source       = 'Wikimedia Commons',
                    author       = 'See Wikimedia Commons page',
                    license      = 'Creative Commons / see Commons page',
                    attribution  = ?
                WHERE destination_id = ?
            """, (found_url, found_attrib, dest_id))
            conn.commit()
            print(f"[OK] {found_url[:65]}...")
            updated += 1
        else:
            print("[--] no file found")
            still_missing.append((dest_id, name))

        time.sleep(0.4)

    conn.close()
    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(dest_ids)}")
    if still_missing:
        print(f"\nStill missing ({len(still_missing)}):")
        for did, n in still_missing:
            print(f"  [{did}] {n}")


if __name__ == "__main__":
    import urllib.parse
    main()
