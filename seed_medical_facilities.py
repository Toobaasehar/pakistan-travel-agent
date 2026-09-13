"""
seed_medical_facilities.py
============================
Seeds one government DHQ (District Headquarters) Hospital record per
district into the MedicalFacility table, using the same real,
already-in-use district coordinates from city_coordinates.py that the
rest of this project relies on for map pins.

WHY ONE PER DISTRICT, NOT ONE PER DESTINATION (376+):
medical_routes.py already filters facilities by `district`, and
Pakistan's own administrative/health structure is organized by
district -- every district has a DHQ hospital. Seeding at district
level naturally covers all 376+ destinations (many destinations share
a district) without duplicating rows per attraction.

WHAT'S VERIFIED HERE VS. WHAT ISN'T -- READ THIS BEFORE DEMOING:
- District names, provinces, and coordinates: reused directly from
  city_coordinates.py (already fact-checked elsewhere in this repo).
- The *existence* of a DHQ hospital per district: a real, structural
  fact of Pakistan's public health system, not a guess.
- Exact hospital phone numbers, and current anti-venom / anti-rabies /
  trauma-care stock: NOT verified here, on purpose. Every record is
  seeded with contact_number = None and all three stock flags = False.
  Guessing "yes" on medical supply availability is exactly the kind of
  wrong information that costs someone time in a real emergency --
  wrong is worse than unknown for this kind of data. Flip a flag to
  True only after an actual phone call / health-department
  confirmation for that specific facility. This is the "Verified
  Medical Directory" partnership work already flagged as a next step
  for this project (see the pitch deck's "What's Next" slide).

Run with:
    python seed_medical_facilities.py
Safe to re-run: skips any district that already has a facility row,
so it won't create duplicates.
"""

from database import SessionLocal, engine, Base
from models import MedicalFacility
from city_coordinates import CITY_COORDINATES

# district_name -> province, using the same province-naming convention
# already used elsewhere in this project (e.g. emergency_contacts.py's
# "KPK" for Khyber Pakhtunkhwa). "Zone I"-"Zone V" from
# city_coordinates.py are sub-zones of Islamabad, not separate
# districts with their own hospital, so they're intentionally skipped.
DISTRICT_PROVINCE_MAP = {
    # Punjab
    "Lahore": "Punjab", "Bahawalpur": "Punjab", "Multan": "Punjab", "Faisalabad": "Punjab",
    "Rawalpindi": "Punjab", "Sialkot": "Punjab", "Sargodha": "Punjab", "Gujranwala": "Punjab",
    "Sheikhupura": "Punjab", "Jhelum": "Punjab", "Kasur": "Punjab", "Vehari": "Punjab",
    "Okara": "Punjab", "Attock": "Punjab", "Bahawalnagar": "Punjab", "Bhakkar": "Punjab",
    "Chakwal": "Punjab", "Chiniot": "Punjab", "Dera Ghazi Khan": "Punjab", "Gujrat": "Punjab",
    "Hafizabad": "Punjab", "Jhang": "Punjab", "Khanewal": "Punjab", "Khushab": "Punjab",
    "Layyah": "Punjab", "Lodhran": "Punjab", "Mandi Bahauddin": "Punjab", "Mianwali": "Punjab",
    "Muzaffargarh": "Punjab", "Nankana Sahib": "Punjab", "Narowal": "Punjab", "Pakpattan": "Punjab",
    "Rahim Yar Khan": "Punjab", "Rajanpur": "Punjab", "Sahiwal": "Punjab", "Toba Tek Singh": "Punjab",
    # Sindh
    "Karachi": "Sindh", "Hyderabad": "Sindh", "Sukkur": "Sindh", "Larkana": "Sindh",
    "Nawabshah": "Sindh", "Mirpurkhas": "Sindh", "Dadu": "Sindh", "Badin": "Sindh",
    "Thatta": "Sindh", "Tando Allahyar": "Sindh", "Tando Muhammad Khan": "Sindh",
    "Matiari": "Sindh", "Sujawal": "Sindh", "Khairpur": "Sindh", "Ghotki": "Sindh",
    "Shikarpur": "Sindh", "Jacobabad": "Sindh", "Kashmore": "Sindh", "Qambar Shahdadkot": "Sindh",
    "Umerkot": "Sindh", "Tharparkar": "Sindh", "Sanghar": "Sindh", "Naushahro Feroze": "Sindh",
    "Jamshoro": "Sindh",
    # Khyber Pakhtunkhwa
    "Peshawar": "KPK", "Abbottabad": "KPK", "Mardan": "KPK", "Swat": "KPK", "Chitral": "KPK",
    "Dir": "KPK", "Kohat": "KPK", "Bannu": "KPK", "Dera Ismail Khan": "KPK", "Nowshera": "KPK",
    "Mansehra": "KPK", "Haripur": "KPK", "Battagram": "KPK", "Allai": "KPK", "Kolai Palas": "KPK",
    "Torghar": "KPK", "Upper Kohistan": "KPK", "Lower Kohistan": "KPK", "Hangu": "KPK",
    "Karak": "KPK", "Kurram": "KPK", "Orakzai": "KPK", "Lakki Marwat": "KPK",
    "North Waziristan": "KPK", "Charsadda": "KPK", "Khyber": "KPK", "Mohmand": "KPK",
    "Tank": "KPK", "Paharpur": "KPK", "Upper South Waziristan": "KPK", "Lower South Waziristan": "KPK",
    "Swabi": "KPK", "Upper Swat": "KPK", "Upper Dir": "KPK", "Lower Dir": "KPK",
    "Central Dir": "KPK", "Upper Chitral": "KPK", "Lower Chitral": "KPK", "Malakand": "KPK",
    "Shangla": "KPK", "Buner": "KPK", "Bajaur": "KPK",
    # Balochistan
    "Quetta": "Balochistan", "Gwadar": "Balochistan", "Sibi": "Balochistan", "Zhob": "Balochistan",
    "Khuzdar": "Balochistan", "Loralai": "Balochistan", "Pishin": "Balochistan",
    "Killa Abdullah": "Balochistan", "Chaman": "Balochistan", "Qila Saifullah": "Balochistan",
    "Sherani": "Balochistan", "Musakhel": "Balochistan", "Duki": "Balochistan",
    "Barkhan": "Balochistan", "Kohlu": "Balochistan", "Dera Bugti": "Balochistan",
    "Ziarat": "Balochistan", "Harnai": "Balochistan", "Nasirabad": "Balochistan",
    "Jaffarabad": "Balochistan", "Sohbatpur": "Balochistan", "Jhal Magsi": "Balochistan",
    "Bolan": "Balochistan", "Kalat": "Balochistan", "Mastung": "Balochistan",
    "Awaran": "Balochistan", "Lasbela": "Balochistan", "Kharan": "Balochistan",
    "Washuk": "Balochistan", "Chagai": "Balochistan", "Nushki": "Balochistan",
    "Panjgur": "Balochistan", "Kech": "Balochistan",
    # Islamabad Capital Territory
    "Islamabad": "Islamabad",
    # Azad Kashmir
    "Muzaffarabad": "Azad Kashmir", "Rawalakot": "Azad Kashmir", "Neelum Valley": "Azad Kashmir",
    "Hattian Bala": "Azad Kashmir", "Bagh": "Azad Kashmir", "Haveli": "Azad Kashmir",
    "Sudhanoti": "Azad Kashmir", "Mirpur": "Azad Kashmir", "Kotli": "Azad Kashmir",
    "Bhimber": "Azad Kashmir",
    # Gilgit-Baltistan
    "Gilgit": "Gilgit-Baltistan", "Skardu": "Gilgit-Baltistan", "Astore": "Gilgit-Baltistan",
    "Diamer": "Gilgit-Baltistan", "Ghanche": "Gilgit-Baltistan", "Ghizer": "Gilgit-Baltistan",
    "Hunza": "Gilgit-Baltistan", "Kharmang": "Gilgit-Baltistan", "Nagar": "Gilgit-Baltistan",
    "Shigar": "Gilgit-Baltistan",
}


def seed_medical_facilities():
    Base.metadata.create_all(bind=engine)  # no-op if the table already exists
    db = SessionLocal()
    try:
        existing_districts = {row[0] for row in db.query(MedicalFacility.district).all()}
        added, skipped, missing_coords = 0, 0, []

        for district, province in DISTRICT_PROVINCE_MAP.items():
            if district in existing_districts:
                skipped += 1
                continue

            coords = CITY_COORDINATES.get(district)
            if not coords:
                missing_coords.append(district)
                continue
            lat, lon = coords

            db.add(MedicalFacility(
                name=f"{district} District Headquarters Hospital (DHQ)",
                facility_type="Government DHQ Hospital",
                province=province,
                district=district,
                latitude=lat,
                longitude=lon,
                contact_number=None,     # NOT guessed -- verify before relying on this
                is_24_7=True,            # DHQ hospitals run 24/7 emergency wards by design
                has_anti_venom=False,    # unverified -- confirm locally before trusting this
                has_anti_rabies=False,   # unverified -- confirm locally before trusting this
                has_trauma_care=False,   # unverified -- confirm locally before trusting this
                notes=(
                    "General district hospital entry (auto-seeded from district coordinates). "
                    "Stock/capacity flags are unverified placeholders — call ahead before "
                    "relying on this in a real emergency."
                ),
            ))
            added += 1

        db.commit()

        print(f"✅ Done. Added {added} new facility records, skipped {skipped} already-seeded districts.")
        print(f"   Total districts in map: {len(DISTRICT_PROVINCE_MAP)}")
        if missing_coords:
            print(f"   ⚠ No coordinates found for: {', '.join(missing_coords)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_medical_facilities()
