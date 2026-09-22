"""
One-time migration: copy the destination data from the local SQLite file
(travel.db) into your Neon PostgreSQL database.

What gets copied  : destinations, destination_images, medical_facilities
What is NOT copied: users, user_wishlists, saved_trips, reviews
                    (those are old test data - production starts clean)

How to run (PowerShell, inside the project folder, venv active):

    $env:DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
    python migrate_to_neon.py

Safe to run once. If the tables in Neon already contain data, the script
stops and does nothing. To wipe those 3 tables and copy again, run:

    python migrate_to_neon.py --force

The connection string lives only in your terminal session - it is never
written to any file.
"""

import os
import sys

from sqlalchemy import create_engine, select, insert, text, func
from sqlalchemy.engine import make_url

TABLES = ["destinations", "destination_images", "medical_facilities"]  # parents first
BATCH = 100


def main() -> None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url.startswith(("postgres://", "postgresql://")):
        sys.exit(
            "DATABASE_URL is missing or is not a PostgreSQL URL.\n"
            'Set it first, e.g.  $env:DATABASE_URL = "postgresql://..."'
        )

    here = os.path.dirname(os.path.abspath(__file__))
    sqlite_path = os.path.join(here, "travel.db")
    if not os.path.exists(sqlite_path):
        sys.exit(f"Cannot find {sqlite_path}")

    # Importing database uses DATABASE_URL, so pg_engine points at Neon.
    from database import Base, engine as pg_engine
    import models  # noqa: F401  (registers the table definitions on Base)

    missing = [t for t in TABLES if t not in Base.metadata.tables]
    if missing:
        sys.exit(
            f"These tables are not defined in models.py: {missing}\n"
            "Find where they are defined with:\n"
            '  Select-String -Path *.py -Pattern "__tablename__"\n'
            "and add `import <that_file>` next to `import models` in this script."
        )

    host = make_url(url).host
    print(f"Target : Neon / PostgreSQL at {host}")
    print(f"Source : {sqlite_path}\n")

    Base.metadata.create_all(pg_engine)  # creates any missing tables (all models)
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    force = "--force" in sys.argv

    with sqlite_engine.connect() as src, pg_engine.begin() as dst:  # one transaction
        tables = {name: Base.metadata.tables[name] for name in TABLES}

        existing = {
            name: dst.execute(select(func.count()).select_from(tbl)).scalar()
            for name, tbl in tables.items()
        }
        if any(existing.values()):
            if not force:
                print("Neon already contains data:", existing)
                sys.exit("Nothing was changed. Use --force to wipe these 3 tables and re-copy.")
            for name in reversed(TABLES):  # children first
                dst.execute(tables[name].delete())
            print("Existing rows in the 3 tables were deleted (--force).\n")

        for name in TABLES:
            tbl = tables[name]
            rows = [dict(r._mapping) for r in src.execute(select(tbl))]
            for i in range(0, len(rows), BATCH):
                dst.execute(insert(tbl), rows[i:i + BATCH])
            print(f"  copied {len(rows):>4} rows -> {name}")

        # Rows were inserted with their old ids, so move each table's id
        # counter forward. Otherwise the next INSERT would clash with an old id.
        for name in TABLES:
            if "id" in tables[name].c:
                dst.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {name}), 1), "
                    f"(SELECT MAX(id) FROM {name}) IS NOT NULL)"
                ))

    # Verify
    print("\nChecking counts (SQLite vs Neon):")
    ok = True
    with sqlite_engine.connect() as src, pg_engine.connect() as dst:
        for name in TABLES:
            tbl = Base.metadata.tables[name]
            a = src.execute(select(func.count()).select_from(tbl)).scalar()
            b = dst.execute(select(func.count()).select_from(tbl)).scalar()
            flag = "OK" if a == b else "MISMATCH"
            ok = ok and a == b
            print(f"  {name:<20} {a:>4} vs {b:>4}  {flag}")

    print("\nDone. Data copied successfully." if ok else "\nCounts differ - do not deploy yet.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
