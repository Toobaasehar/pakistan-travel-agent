"""
Mock Agent — Simulation Mode (Rule-based NLP Engine)
=====================================================
Mimics Claude tool-calling without requiring Anthropic API credits.
Extracts budget, duration, locations, and interests from natural language,
calls the real tools.py functions against the database, and composes a rich response.
"""

import re
from typing import Optional, Tuple
from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary


CITIES = [
    "hunza", "skardu", "gilgit", "swat", "naran", "kaghan", "chitral",
    "malam jabba", "kumrat", "lahore", "karachi", "islamabad", "rawalpindi",
    "peshawar", "quetta", "gwadar", "multan", "bahawalpur", "faisalabad",
    "sialkot", "gujranwala", "sargodha", "jhelum", "murree", "ziarat",
    "abbottabad", "mardan", "dir", "kohat", "sukkur", "hyderabad", "larkana",
    "thatta", "muzaffarabad", "rawalakot"
]

PROVINCES = {
    "kpk": "KPK",
    "khyber": "KPK",
    "khyber pakhtunkhwa": "KPK",
    "punjab": "Punjab",
    "sindh": "Sindh",
    "balochistan": "Balochistan",
    "gilgit": "Gilgit-Baltistan",
    "baltistan": "Gilgit-Baltistan",
    "gilgit-baltistan": "Gilgit-Baltistan",
    "islamabad": "Islamabad Capital Territory",
    "kashmir": "Azad Kashmir",
    "azad kashmir": "Azad Kashmir",
}


def extract_budget(text: str) -> Optional[int]:
    """Parses budget in PKR from various notations (e.g. 50k, 50,000, 1.5 lac, 40000 PKR)."""
    text = text.lower().replace(",", "")

    # Match '50k' or '25.5k'
    k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", text)
    if k_match:
        return int(float(k_match.group(1)) * 1000)

    # Match 'lakh' or 'lac'
    lac_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)s?\b", text)
    if lac_match:
        return int(float(lac_match.group(1)) * 100000)

    # Match raw digits
    match = re.search(r"\b(\d{4,7})\b", text)
    if match:
        return int(match.group(1))

    return None


def extract_days(text: str) -> int:
    """Parses trip duration in days."""
    text = text.lower()
    if "weekend" in text:
        return 2
    if "one week" in text or "1 week" in text:
        return 7
    if "two week" in text or "2 week" in text:
        return 14

    match = re.search(r"(\d+)\s*(?:days?|nights?|d)\b", text)
    if match:
        val = int(match.group(1))
        return min(max(val, 1), 30)

    return 3


def extract_category(text: str) -> Optional[str]:
    """Matches category keywords in the user query."""
    text = text.lower()
    if any(w in text for w in ["mountain", "hiking", "trek", "ski", "alpine", "peak", "valley", "glacier"]):
        return "mountains"
    if any(w in text for w in ["beach", "sea", "ocean", "coastal", "coast"]):
        return "beaches"
    if any(w in text for w in ["lake", "forest", "nature", "park", "waterfall", "river", "scenery"]):
        return "nature"
    if any(w in text for w in ["fort", "mosque", "tomb", "shrine", "ruins", "monument", "temple", "historical", "history"]):
        return "historical"
    if any(w in text for w in ["culture", "cultural", "festival", "tradition", "heritage", "craft"]):
        return "cultural"
    if any(w in text for w in ["museum", "gallery", "exhibit"]):
        return "museum"
    if any(w in text for w in ["wildlife", "safari", "animal", "bear"]):
        return "wildlife"
    return None


def extract_location(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extracts province and district/city from user text."""
    text_lower = text.lower()
    found_province = None
    found_district = None

    for kw, prov in PROVINCES.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            found_province = prov
            break

    for city in CITIES:
        if re.search(r"\b" + re.escape(city) + r"\b", text_lower):
            found_district = city.title()
            break

    return found_province, found_district


def run_mock_agent(user_message: str) -> str:
    """Executes rule-based agent reasoning and returns a structured response."""
    budget = extract_budget(user_message)
    days = extract_days(user_message)
    category = extract_category(user_message)
    province, district = extract_location(user_message)

    per_day_budget = (budget // days) if budget else None

    # Search with all extracted criteria
    matches = search_destinations(
        province=province,
        district=district,
        max_budget_per_day=per_day_budget,
        category=category,
    )

    # If no exact match, relax budget constraint first
    if not matches and per_day_budget:
        matches = search_destinations(
            province=province,
            district=district,
            category=category,
        )

    # If still no match, search by province or category alone
    if not matches and (province or category):
        matches = search_destinations(
            province=province,
            category=category,
        )

    # Absolute fallback to top destinations
    if not matches:
        matches = search_destinations()

    if not matches:
        return "I couldn't find any destinations matching your criteria. Try asking for popular spots in KPK, Punjab, Sindh, Balochistan, or Gilgit-Baltistan!"

    chosen = matches[0]
    details = get_destination_details(chosen["id"])
    cost = estimate_cost(chosen["id"], days=days, people=1)
    itinerary = generate_itinerary(chosen["id"], days=days)

    lines = [
        f"### Recommended Destination: {chosen['name']}",
        f"**Location**: {chosen.get('district', '') + ', ' if chosen.get('district') else ''}{chosen['province']} | **Category**: {chosen.get('category', 'sightseeing').title()}",
        "",
        f"*{details.get('description', '')}*",
        "",
        f"#### Estimated Cost for {days} Day(s) (1 Traveler)",
        f"- **Estimated Total**: PKR {cost['estimated_total_pkr']:,}",
        f"  - Accommodation: PKR {cost['breakdown_pkr']['accommodation']:,}",
        f"  - Food & Meals: PKR {cost['breakdown_pkr']['food']:,}",
        f"  - Activities & Sightseeing: PKR {cost['breakdown_pkr']['activities']:,}",
        f"  - Local Transport: PKR {cost['breakdown_pkr']['transport']:,}",
        "",
        "#### Day-by-Day Itinerary Plan"
    ]

    for day in itinerary["itinerary"]:
        lines.append(f"- **Day {day['day']}**: {day['plan']}")

    if len(matches) > 1:
        alt_names = [m["name"] for m in matches[1:4]]
        lines.append("")
        lines.append(f"**Other Great Options Nearby**: {', '.join(alt_names)}")

    return "\n".join(lines)


if __name__ == "__main__":
    print("Pakistan Travel Agent — SIMULATION MODE")
    print("Type a trip query (e.g. 'Plan 3 days in Swat with 25k budget') or 'quit':\n")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("quit", "exit"):
            break
        if not user_input.strip():
            continue
        answer = run_mock_agent(user_input)
        print(f"\n{answer}\n")
