"""
Pakistan Travel Agent — Unified Engine (AI & Simulation Mode)
============================================================
Supports:
1. Groq (Free & Fast Llama-3.3-70b / GPT-OSS) Tool Calling
2. Anthropic Claude Tool Calling
3. Simulation Mode (Rule-based NLP Engine with Database Search & ML Fallback)

If no API keys are provided in .env, it automatically falls back
to Simulation (Mock) Mode seamlessly without throwing errors.

Run with:
    python agent.py
"""

import os
import re
import sys
import json
from typing import Optional, Tuple
from dotenv import load_dotenv

# Database and Core Tools
from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary

# ML Capabilities
from ml.predict_budget import predict_budget
from ml.similar_destinations import get_similar_destinations
from ml.explain_budget import explain_budget_prediction

# RAG — Retrieval-Augmented Generation (knowledge base search)
try:
    from rag.rag_tool import search_knowledge_base, get_rag_context
    _RAG_AVAILABLE = True
except Exception as _rag_err:
    print(f"[agent] RAG not available: {_rag_err}")
    _RAG_AVAILABLE = False
    def search_knowledge_base(query: str, top_k: int = 5) -> dict:
        return {"results": [], "count": 0, "engine": "disabled"}
    def get_rag_context(query: str, top_k: int = 5) -> str:
        return ""

load_dotenv()

# =====================================================================
# 1. ML HELPER FUNCTIONS (FOR AI TOOLS)
# =====================================================================

def predict_trip_budget(province: str, category: str, recommended_days: int, activities: list = None) -> dict:
    """
    ML-based budget estimate (Random Forest, trained on 150+ destinations).
    Use when the destination is not in the database or for general 'what would this cost' queries.
    """
    return predict_budget(
        province=province,
        category=category,
        recommended_days=recommended_days,
        activities=activities,
    )


def find_similar_destinations(destination_id: int, top_n: int = 5) -> dict:
    """
    ML-based recommendation (KMeans clustering) of destinations similar to a given one.
    """
    return get_similar_destinations(destination_id=destination_id, top_n=top_n)


def explain_trip_budget(province: str, category: str, recommended_days: int, activities: list = None) -> dict:
    """
    Explains WHY the ML budget model predicted what it did (SHAP breakdown).
    """
    return explain_budget_prediction(
        province=province,
        category=category,
        recommended_days=recommended_days,
        activities=activities,
    )


# =====================================================================
# 2. TOOL SCHEMAS FOR AI MODELS (ANTHROPIC & GROQ)
# =====================================================================

CLAUDE_TOOLS = [
    {
        "name": "search_destinations",
        "description": "Search Pakistan destinations by optional province, district/city, max budget per day (PKR), or category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "province": {"type": "string", "description": "e.g. KPK, Punjab, Sindh, Balochistan, Gilgit-Baltistan, Azad Kashmir, Islamabad"},
                "district": {"type": "string", "description": "e.g. Swat, Lahore, Karachi, Hunza, Skardu, Quetta, Multan"},
                "max_budget_per_day": {"type": "integer", "description": "Maximum budget per person per day, in PKR"},
                "category": {"type": "string", "description": "e.g. mountains, historical, beaches, nature, cultural, museum"},
            },
        },
    },
    {
        "name": "get_destination_details",
        "description": "Get full details for one destination by its integer id.",
        "input_schema": {
            "type": "object",
            "properties": {"destination_id": {"type": "integer"}},
            "required": ["destination_id"],
        },
    },
    {
        "name": "estimate_cost",
        "description": "Estimate a formula-based trip cost breakdown for a destination id, number of days, and number of people.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination_id": {"type": "integer"},
                "days": {"type": "integer"},
                "people": {"type": "integer"},
            },
            "required": ["destination_id", "days"],
        },
    },
    {
        "name": "generate_itinerary",
        "description": "Generate a structured day-by-day itinerary for a destination id and number of days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination_id": {"type": "integer"},
                "days": {"type": "integer"},
            },
            "required": ["destination_id", "days"],
        },
    },
    {
        "name": "predict_trip_budget",
        "description": "Predict a typical budget per day (PKR) using a trained ML model for hypothetical or non-listed destinations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "province": {"type": "string"},
                "category": {"type": "string"},
                "recommended_days": {"type": "integer"},
                "activities": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["province", "category", "recommended_days"],
        },
    },
    {
        "name": "find_similar_destinations",
        "description": "Find destinations similar to a given one using ML clustering.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination_id": {"type": "integer"},
                "top_n": {"type": "integer", "description": "How many to return (default 5)"},
            },
            "required": ["destination_id"],
        },
    },
    {
        "name": "explain_trip_budget",
        "description": "Explain WHY the ML budget model gave the estimate it did (SHAP breakdown).",
        "input_schema": {
            "type": "object",
            "properties": {
                "province": {"type": "string"},
                "category": {"type": "string"},
                "recommended_days": {"type": "integer"},
                "activities": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["province", "category", "recommended_days"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": (
            "Search the Pakistan travel knowledge base for rich contextual information. "
            "Use this tool FIRST for questions about: history of a city/region, weather & best season, "
            "travel tips & safety advice, local attractions & what to do, food & dining culture, "
            "transport options between cities, and general travel advice. "
            "This retrieves curated expert knowledge that goes beyond the destinations database."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language question or topic, e.g. 'best time to visit Hunza' or 'travel tips for Swat Valley'",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default 5, max 10)",
                },
            },
            "required": ["query"],
        },
    },
]

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_destinations",
            "description": "Search Pakistan destinations by optional province, district/city, max budget per day (PKR), or category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {"type": "string"},
                    "district": {"type": "string"},
                    "max_budget_per_day": {"type": "integer"},
                    "category": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_destination_details",
            "description": "Get full details for one destination by its integer id.",
            "parameters": {
                "type": "object",
                "properties": {"destination_id": {"type": "integer"}},
                "required": ["destination_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_cost",
            "description": "Estimate a formula-based trip cost breakdown for a destination id, number of days, and number of people.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_id": {"type": "integer"},
                    "days": {"type": "integer"},
                    "people": {"type": "integer"},
                },
                "required": ["destination_id", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_itinerary",
            "description": "Generate a structured day-by-day itinerary for a destination id and number of days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_id": {"type": "integer"},
                    "days": {"type": "integer"},
                },
                "required": ["destination_id", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_trip_budget",
            "description": "Predict a typical budget per day (PKR) using ML model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {"type": "string"},
                    "category": {"type": "string"},
                    "recommended_days": {"type": "integer"},
                    "activities": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["province", "category", "recommended_days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_similar_destinations",
            "description": "Find destinations similar to a given one using ML clustering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_id": {"type": "integer"},
                    "top_n": {"type": "integer"},
                },
                "required": ["destination_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_trip_budget",
            "description": "Explain WHY the ML budget model gave the estimate it did (SHAP breakdown).",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {"type": "string"},
                    "category": {"type": "string"},
                    "recommended_days": {"type": "integer"},
                    "activities": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["province", "category", "recommended_days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the Pakistan travel knowledge base for rich contextual information. "
                "Use this tool FIRST for questions about: history of a city/region, weather & best season, "
                "travel tips & safety advice, local attractions & what to do, food & dining culture, "
                "transport options between cities, and general travel advice. "
                "This retrieves curated expert knowledge that goes beyond the destinations database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language question or topic",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "search_destinations": search_destinations,
    "get_destination_details": get_destination_details,
    "estimate_cost": estimate_cost,
    "generate_itinerary": generate_itinerary,
    "predict_trip_budget": predict_trip_budget,
    "find_similar_destinations": find_similar_destinations,
    "explain_trip_budget": explain_trip_budget,
    "search_knowledge_base": search_knowledge_base,
}


# =====================================================================
# 3. RULE-BASED EXTRACTION & SIMULATION ENGINE (FROM MOCK AGENT)
# =====================================================================

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

    k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", text)
    if k_match:
        return int(float(k_match.group(1)) * 1000)

    lac_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)s?\b", text)
    if lac_match:
        return int(float(lac_match.group(1)) * 100000)

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


def extract_currency(text: str) -> str:
    """Extracts target currency from user message."""
    t = text.lower()
    if any(k in t for k in ["usd", "$", "dollar", "dollars"]):
        return "USD"
    if any(k in t for k in ["eur", "€", "euro", "euros"]):
        return "EUR"
    if any(k in t for k in ["gbp", "£", "pound", "pounds"]):
        return "GBP"
    if any(k in t for k in ["aed", "dirham", "dirhams"]):
        return "AED"
    if any(k in t for k in ["sar", "riyal", "riyals"]):
        return "SAR"
    if any(k in t for k in ["cad", "ca$"]):
        return "CAD"
    if any(k in t for k in ["aud", "a$"]):
        return "AUD"
    return "PKR"


def extract_travel_style(text: str) -> str:
    """Extracts desired travel comfort tier."""
    t = text.lower()
    if any(k in t for k in ["luxury", "5 star", "5-star", "deluxe", "resort", "premium", "vip"]):
        return "luxury"
    if any(k in t for k in ["budget", "cheap", "backpacker", "hostel", "low cost", "economical"]):
        return "budget"
    return "standard"


def extract_people(text: str) -> int:
    """Extracts number of travelers."""
    t = text.lower()
    if "solo" in t or "alone" in t or "myself" in t:
        return 1
    if "couple" in t or "2 of us" in t or "two of us" in t:
        return 2

    m = re.search(r"(\d+)\s*(?:people|person|persons|travelers|passengers|adults|friends|pax)\b", t)
    if m:
        return min(max(int(m.group(1)), 1), 20)

    fam_m = re.search(r"family of (\d+)\b", t)
    if fam_m:
        return min(max(int(fam_m.group(1)), 1), 20)

    return 1


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
    """
    Rule-based agent with RAG context enrichment.
    Retrieves relevant knowledge base passages before building the
    structured trip plan, so the response includes tips, weather info,
    and attraction highlights grounded in real curated data.
    """
    budget = extract_budget(user_message)
    days = extract_days(user_message)
    category = extract_category(user_message)
    province, district = extract_location(user_message)
    currency = extract_currency(user_message)
    travel_style = extract_travel_style(user_message)
    people = extract_people(user_message)

    per_day_budget = (budget // days) if budget else None

    # ── RAG: Retrieve relevant knowledge base context ──────────────────────────
    rag_context_lines = []
    try:
        rag_results = search_knowledge_base(user_message, top_k=4)
        for r in rag_results.get("results", []):
            meta = r.get("metadata", {})
            section = meta.get("section", "")
            text = r.get("text", "")
            score = r.get("score", 0)

            # Only include high-confidence results, skip generic/low-score ones
            if score < 0.05 or not text:
                continue

            # Map sections to user-friendly emoji prefixes
            section_icons = {
                "weather": "🌤️ **Weather & Season**",
                "travel_tips": "💡 **Travel Tips**",
                "history": "🏛️ **History**",
                "attraction": "📍 **Attraction**",
                "food": "🍽️ **Local Food**",
                "transport": "🚌 **Getting There**",
                "accommodations": "🏨 **Accommodation**",
                "destination": "📌 **Destination Info**",
            }
            icon = section_icons.get(section, "ℹ️")
            # Truncate long passages
            snippet = text[:380] + ("..." if len(text) > 380 else "")
            rag_context_lines.append(f"{icon}: {snippet}")
    except Exception as _rag_ex:
        pass  # RAG failure is non-blocking

    # ── Standard destination search ────────────────────────────────────────────
    # 1. Search with all extracted criteria
    matches = search_destinations(
        province=province,
        district=district,
        max_budget_per_day=per_day_budget,
        category=category,
    )

    # 2. Relax budget if needed
    if not matches and per_day_budget:
        matches = search_destinations(
            province=province,
            district=district,
            category=category,
        )

    # 3. If no exact match but user specified province/category, fall back to ML estimate
    if not matches and province and category:
        try:
            ml_estimate = predict_budget(
                province=province,
                category=category,
                recommended_days=days,
                currency=currency,
            )
        except Exception:
            ml_estimate = None

        if ml_estimate:
            per_day = ml_estimate["predicted_budget_per_day"]
            std_day = ml_estimate.get("standard_tier_per_day", per_day)
            total_est = std_day * days * people
            lines = [
                "### ⚡ Live Market Budget Estimate (2026)",
                f"I don't have an exact destination in the database matching "
                f"**{category} in {province}**, but here's a live ML market estimate:",
                "",
                f"- **Standard Daily Rate**: PKR {std_day:,.0f} / day / person",
                f"- **Total for {days} Day(s) ({people} Traveler{'s' if people > 1 else ''})**: PKR {total_est:,.0f}",
            ]
            if currency != "PKR":
                conv_data = ml_estimate.get("conversions", {}).get(currency, {})
                std_c = conv_data.get("standard_per_day")
                if std_c:
                    lines.append(f"- **Converted ({currency})**: approx. {currency} {std_c * days * people:,.2f}")
            lines.extend([
                "",
                "Try browsing other destinations in that province or category for a specific plan!",
            ])
            # Append RAG context if available
            if rag_context_lines:
                lines.append("")
                lines.append("---")
                lines.append("#### 📚 Relevant Travel Knowledge")
                lines.extend(f"- {cl}" for cl in rag_context_lines[:3])
            return "\n".join(lines)

    # 4. Search by province or category alone
    if not matches and (province or category):
        matches = search_destinations(
            province=province,
            category=category,
        )

    # 5. Fallback to top destinations
    if not matches:
        matches = search_destinations()

    if not matches:
        return "I couldn't find any destinations matching your criteria. Try asking for popular spots in KPK, Punjab, Sindh, Balochistan, or Gilgit-Baltistan!"

    chosen = matches[0]
    details = get_destination_details(chosen["id"])
    cost = estimate_cost(
        chosen["id"],
        days=days,
        people=people,
        travel_style=travel_style,
        currency=currency,
    )
    itinerary = generate_itinerary(chosen["id"], days=days)

    curr_total = cost.get("converted_total", {})
    total_str = f"PKR {cost['total_pkr']:,}"
    if currency != "PKR" and curr_total:
        total_str += f" ({curr_total.get('formatted', '')})"

    lines = [
        f"### Recommended Destination: {chosen['name']}",
        f"**Location**: {chosen.get('district', '') + ', ' if chosen.get('district') else ''}{chosen['province']} | **Category**: {chosen.get('category', 'sightseeing').title()}",
        "",
        f"*{details.get('description', '')}*",
        "",
        f"#### ⚡ Live Market Pricing Breakdown ({days} Days, {people} Traveler{'s' if people > 1 else ''} — {cost.get('travel_style_label', 'Standard')})",
        f"- **Total Trip Cost**: **{total_str}**",
        f"  - 🏨 **Accommodation**: PKR {cost['breakdown_pkr']['accommodation']:,} ({cost.get('travel_style_label', 'Hotel')})",
        f"  - 🚗 **Transport**: PKR {cost['breakdown_pkr']['transport']:,} ({cost.get('transport_label', 'Private Transport')})",
        f"  - 🍽️ **Food & Dining**: PKR {cost['breakdown_pkr']['food']:,} ({cost.get('dining_style', 'Dining')})",
        f"  - 🎟️ **Activities & Tickets**: PKR {cost['breakdown_pkr']['activities']:,}",
        f"  - 🧾 **Service & Taxes**: PKR {cost['breakdown_pkr'].get('service_and_taxes', 0):,}",
        "",
        "#### Day-by-Day Itinerary Plan"
    ]

    for day in itinerary["itinerary"]:
        lines.append(f"- **Day {day['day']}**: {day['plan']}")

    if len(matches) > 1:
        alt_names = [m["name"] for m in matches[1:4]]
        lines.append("")
        lines.append(f"**Other Great Options Nearby**: {', '.join(alt_names)}")

    # ── Append RAG knowledge context ───────────────────────────────────────────
    if rag_context_lines:
        lines.append("")
        lines.append("---")
        lines.append("#### 📚 Additional Travel Knowledge")
        for cl in rag_context_lines[:4]:
            lines.append(f"- {cl}")

    return "\n".join(lines)


# =====================================================================
# 4. AI AGENT RUNNERS (GROQ & ANTHROPIC)
# =====================================================================

def run_groq_agent(user_message: str, max_turns: int = 8) -> str:
    """Runs the Groq AI agent with function calling."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_key_here":
        raise ValueError("GROQ_API_KEY is not configured in .env.")

    from groq import Groq
    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert, warm, and helpful Pakistan Travel AI Assistant. "
                "You have access to tools for querying a real database of 150+ verified destinations in Pakistan "
                "AND a rich knowledge base with detailed city histories, weather guides, travel tips, "
                "attractions, food recommendations, and transport information.\n\n"
                "TOOL USAGE GUIDELINES:\n"
                "1. For questions about history, culture, weather/seasons, travel tips, safety, "
                "   attractions, local food, or transport — call search_knowledge_base FIRST "
                "   to retrieve accurate, curated context before answering.\n"
                "2. For trip planning, budget estimation, and itinerary generation — use "
                "   search_destinations, estimate_cost, and generate_itinerary.\n"
                "3. Always format costs clearly in PKR with bullet points and emojis.\n"
                "4. Ground your answers in the retrieved context — do NOT invent facts."
            )
        },
        {"role": "user", "content": user_message}
    ]

    turns = 0
    while turns < max_turns:
        turns += 1
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

        choice = response.choices[0]
        response_msg = choice.message

        if not response_msg.tool_calls:
            return response_msg.content or "I have processed your travel inquiry."

        messages.append(response_msg)

        for tool_call in response_msg.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except Exception:
                func_args = {}

            print(f"  [Groq Tool Call] {func_name}({func_args})")
            func = TOOL_FUNCTIONS.get(func_name)
            if func:
                try:
                    result = func(**func_args)
                except Exception as err:
                    result = {"error": str(err)}
            else:
                result = {"error": f"Tool '{func_name}' not recognized."}

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(result),
            })

    return "Reached maximum agent reasoning turns without a final answer."


def run_claude_agent(user_message: str, max_turns: int = 5) -> str:
    """Runs the Claude AI Agent with tool-calling support."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key == "your_key_here":
        raise ValueError("ANTHROPIC_API_KEY is not configured in .env.")

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    messages = [{"role": "user", "content": user_message}]
    turns = 0

    while turns < max_turns:
        turns += 1
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=CLAUDE_TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
            return final_text

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if getattr(block, "type", "") != "tool_use":
                continue

            print(f"  [Claude Tool Call] {block.name}({block.input})")
            func = TOOL_FUNCTIONS.get(block.name)
            if func:
                try:
                    result = func(**block.input)
                except Exception as err:
                    result = {"error": str(err)}
            else:
                result = {"error": f"Tool '{block.name}' not recognized."}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_results})

    return "Reached maximum agent reasoning turns without final answer."


# =====================================================================
# 5. UNIFIED MAIN ENTRY POINT (AUTO-DETECT & FALLBACK)
# =====================================================================

def run_agent(user_message: str, max_turns: int = 5, mode: str = "auto") -> str:
    """
    Unified entry point:
    - mode="auto": Checks Groq -> Anthropic -> Fallback to Simulation (Mock) Mode.
    - mode="ai": Force AI only (Groq or Claude).
    - mode="mock": Force Simulation Mode directly.
    """
    if mode == "mock":
        return run_mock_agent(user_message)

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    # Try Groq AI
    if groq_key and groq_key != "your_key_here":
        try:
            return run_groq_agent(user_message, max_turns=max_turns)
        except Exception as e:
            if mode == "ai":
                raise e
            print(f"⚠️ Groq AI encountered an error: {e}. Falling back to Simulation Mode...")
            return run_mock_agent(user_message)

    # Try Anthropic Claude
    if anthropic_key and anthropic_key != "your_key_here":
        try:
            return run_claude_agent(user_message, max_turns=max_turns)
        except Exception as e:
            if mode == "ai":
                raise e
            print(f"⚠️ Claude AI encountered an error: {e}. Falling back to Simulation Mode...")
            return run_mock_agent(user_message)

    # Fallback to Mock Engine if no API keys are present
    if mode == "ai":
        raise ValueError("Neither GROQ_API_KEY nor ANTHROPIC_API_KEY is configured in .env.")

    return run_mock_agent(user_message)


# =====================================================================
# 6. CLI INTERACTIVE LOOP
# =====================================================================

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    if groq_key and groq_key != "your_key_here":
        print("🇵🇰 Pakistan Travel Agent — AI Mode (Groq Llama / GPT-OSS)")
    elif anthropic_key and anthropic_key != "your_key_here":
        print("🇵🇰 Pakistan Travel Agent — AI Mode (Anthropic Claude)")
    else:
        print("🇵🇰 Pakistan Travel Agent — Simulation Mode (Rule-based NLP Engine)")
        print("💡 (Optional: Add GROQ_API_KEY or ANTHROPIC_API_KEY in .env for full LLM mode)")

    print("Type a trip request (e.g. 'Plan 3 days in Swat with 25k budget') or 'quit' to exit\n")
    while True:
        try:
            user_input = input("You: ")
            if user_input.strip().lower() in ("quit", "exit"):
                break
            if not user_input.strip():
                continue
            answer = run_agent(user_input)
            print(f"\nAgent: {answer}\n")
        except Exception as e:
            print(f"\n[Agent Error]: {e}\n")