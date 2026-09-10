"""
rag/knowledge_base.py
=====================
Loads and chunks all Pakistan travel data from:
  1. data/**/*.json  — rich city-level data (attractions, weather, tips, history, food, transport)
  2. SQLite destinations table — all 154+ destination records

Each chunk is a dict:
  {
    "id":       str   — unique chunk identifier,
    "text":     str   — the textual content to embed/search,
    "metadata": dict  — {city, province, section, category}
  }
"""

import os
import json
import glob
from typing import List, Dict, Any

# Root directory of the project (one level up from rag/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def _sanitize(text: str) -> str:
    """Strip excessive whitespace from a text chunk."""
    return " ".join(str(text).split())


def _load_json_chunks() -> List[Dict[str, Any]]:
    """
    Walk every JSON file in data/**/ and produce one chunk per meaningful section.
    Sections: history, weather_info, travel_tips, attractions, food_places,
              transportation, accommodations
    """
    chunks = []
    pattern = os.path.join(DATA_DIR, "**", "*.json")
    json_files = glob.glob(pattern, recursive=True)

    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception:
            continue  # skip malformed files silently

        city = doc.get("city", os.path.splitext(os.path.basename(filepath))[0])
        province = doc.get("province", "")
        base_id = f"{province.lower().replace(' ', '_')}_{city.lower().replace(' ', '_')}"

        # ---- history ----
        history = doc.get("history", {})
        if history:
            text_parts = []
            if history.get("city_history"):
                text_parts.append(history["city_history"])
            if history.get("province_history"):
                text_parts.append(history["province_history"])
            if history.get("founded"):
                text_parts.append(f"Founded/established: {history['founded']}")
            if text_parts:
                chunks.append({
                    "id": f"{base_id}_history",
                    "text": _sanitize(f"{city}, {province} — History & Background: " + " ".join(text_parts)),
                    "metadata": {"city": city, "province": province, "section": "history", "category": "historical"},
                })

        # ---- weather_info ----
        weather = doc.get("weather_info", {})
        if weather:
            parts = []
            if weather.get("climate_type"):
                parts.append(f"Climate: {weather['climate_type']}.")
            if weather.get("best_time_to_visit"):
                parts.append(f"Best time to visit: {weather['best_time_to_visit']}.")
            if weather.get("avoid_months"):
                parts.append(f"Avoid: {weather['avoid_months']}.")
            for sn in weather.get("seasonal_notes", []):
                parts.append(f"{sn.get('season', '')}: {sn.get('avg_condition', '')}")
            if parts:
                chunks.append({
                    "id": f"{base_id}_weather",
                    "text": _sanitize(f"{city}, {province} — Weather & Best Season: " + " ".join(parts)),
                    "metadata": {"city": city, "province": province, "section": "weather", "category": "weather"},
                })

        # ---- travel_tips ----
        tips = doc.get("travel_tips", [])
        if tips:
            tip_texts = [t.get("tip", "") for t in tips if t.get("tip")]
            if tip_texts:
                chunks.append({
                    "id": f"{base_id}_tips",
                    "text": _sanitize(
                        f"{city}, {province} — Travel Tips & Advice: " + " | ".join(tip_texts)
                    ),
                    "metadata": {"city": city, "province": province, "section": "travel_tips", "category": "tips"},
                })

        # ---- attractions (one chunk per attraction for fine-grained retrieval) ----
        for att in doc.get("attractions", []):
            att_id = att.get("id", f"att_{len(chunks)}")
            name = att.get("name", "Attraction")
            desc = att.get("description", "")
            cat = att.get("category", "sightseeing")
            loc = att.get("location_text", city)
            fee = att.get("entry_fee_pkr")
            fee_str = f"Entry fee: PKR {fee}." if fee is not None else "Free entry."
            duration = att.get("visit_duration_min")
            dur_str = f"Typical visit: {duration} minutes." if duration else ""
            chunks.append({
                "id": f"{base_id}_{att_id}",
                "text": _sanitize(
                    f"{name} — {city}, {province}. Category: {cat}. Location: {loc}. "
                    f"{desc} {fee_str} {dur_str}"
                ),
                "metadata": {"city": city, "province": province, "section": "attraction", "category": cat},
            })

        # ---- food_places ----
        food_places = doc.get("food_places", [])
        if food_places:
            food_parts = []
            for fp in food_places:
                name = fp.get("name", "")
                cuisine = fp.get("cuisine", "")
                specialty = fp.get("specialty", "")
                price = fp.get("price_level", "")
                cost = fp.get("approx_cost_per_person_pkr", "")
                food_parts.append(
                    f"{name} ({cuisine}): {specialty}. Price level: {price}. "
                    + (f"Approx. PKR {cost}/person." if cost else "")
                )
            chunks.append({
                "id": f"{base_id}_food",
                "text": _sanitize(f"{city}, {province} — Food & Dining: " + " | ".join(food_parts)),
                "metadata": {"city": city, "province": province, "section": "food", "category": "food"},
            })

        # ---- transportation ----
        transport = doc.get("transportation", [])
        if transport:
            trans_parts = []
            for t in transport:
                frm = t.get("from_city", city)
                to = t.get("to_city", "")
                ttype = t.get("transport_type", "")
                cost = t.get("estimated_cost_pkr", "")
                dur = t.get("duration_min", "")
                notes = t.get("notes", "")
                trans_parts.append(
                    f"{frm} → {to} by {ttype}: PKR {cost}, ~{dur} min. {notes}"
                )
            chunks.append({
                "id": f"{base_id}_transport",
                "text": _sanitize(f"{city}, {province} — Transport & Getting Around: " + " | ".join(trans_parts)),
                "metadata": {"city": city, "province": province, "section": "transport", "category": "transport"},
            })

        # ---- accommodations ----
        accommodations = doc.get("accommodations", [])
        if accommodations:
            acc_parts = []
            for acc in accommodations:
                name = acc.get("name", "")
                price_range = acc.get("price_range", "")
                approx = acc.get("approx_price_pkr", "")
                rating = acc.get("rating", "")
                acc_parts.append(
                    f"{name}: {price_range} range, approx. PKR {approx}/night, rated {rating}/5."
                )
            chunks.append({
                "id": f"{base_id}_accommodations",
                "text": _sanitize(f"{city}, {province} — Accommodations: " + " | ".join(acc_parts)),
                "metadata": {"city": city, "province": province, "section": "accommodations", "category": "hotels"},
            })

    return chunks


def _load_db_chunks() -> List[Dict[str, Any]]:
    """
    Load all destination rows from the SQLite database and convert
    each to a rich text chunk.
    """
    chunks = []
    try:
        from database import SessionLocal
        from models import Destination

        db = SessionLocal()
        try:
            destinations = db.query(Destination).all()
            for d in destinations:
                activities = d.activities or ""
                text = (
                    f"{d.name} — {d.district or ''}, {d.province}. "
                    f"Category: {d.category}. "
                    f"{d.description or ''} "
                    f"Best season: {d.best_season or 'year-round'}. "
                    f"Recommended stay: {d.recommended_days} days. "
                    f"Budget per day: PKR {d.estimated_budget_per_day:,}. "
                    f"Activities: {activities}."
                )
                chunks.append({
                    "id": f"db_dest_{d.id}",
                    "text": _sanitize(text),
                    "metadata": {
                        "city": d.district or "",
                        "province": d.province or "",
                        "section": "destination",
                        "category": d.category or "sightseeing",
                        "destination_id": d.id,
                    },
                })
        finally:
            db.close()
    except Exception as e:
        print(f"[RAG] Warning: could not load DB chunks: {e}")

    return chunks


def build_knowledge_base() -> List[Dict[str, Any]]:
    """
    Returns all chunks from JSON files + DB destinations combined.
    This is the full knowledge base that will be indexed.
    """
    json_chunks = _load_json_chunks()
    db_chunks = _load_db_chunks()
    all_chunks = json_chunks + db_chunks
    print(f"[RAG] Knowledge base built: {len(json_chunks)} JSON chunks + {len(db_chunks)} DB chunks = {len(all_chunks)} total")
    return all_chunks


if __name__ == "__main__":
    chunks = build_knowledge_base()
    print(f"Total chunks: {len(chunks)}")
    print("Sample chunk:", chunks[0] if chunks else "none")
