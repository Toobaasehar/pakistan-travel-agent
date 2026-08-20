"""
Seed script — Phase 5 version.
==================================
Reads from destinations_data.py (single source of truth for the
dataset) and inserts everything into the database. Replaces the
Phase 2 version of this file.

Run with:
    python seed.py
"""

from database import engine, SessionLocal, Base
from models import Destination, DestinationImage
from destinations_data import DESTINATIONS

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if db.query(Destination).count() > 0:
    print("Database already has data — skipping seed. Delete travel.db to reset.")
else:
    inserted = []
    for entry in DESTINATIONS:
        dest = Destination(**entry)
        db.add(dest)
        inserted.append(dest)
    db.commit()

    # One placeholder image per destination — replace with real
    # Wikimedia/Unsplash URLs in Phase 5.5 (image sourcing pass).
    for dest in inserted:
        db.add(
            DestinationImage(
                destination_id=dest.id,
                image_url="PLACEHOLDER — replace with a real Wikimedia/Unsplash URL",
                source="Wikimedia Commons",
                author="TBD",
                license="TBD",
                attribution="TBD",
            )
        )
    db.commit()

    print(f"Inserted {len(inserted)} destinations with placeholder images.")

db.close()
