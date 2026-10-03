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
import time
from typing import Optional, Tuple, List, Dict, Any
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminals to prevent charmap UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_clean_api_key(env_var: str) -> str:
    """Cleans up API keys loaded from .env to prevent common copy-paste errors."""
    val = os.getenv(env_var, "").strip()
    if not val or val == "your_key_here":
        return ""
    # Strip any comment hash or key name prefix if pasted incorrectly
    if "#" in val:
        val = re.sub(r"^#\s*([A-Za-z0-9_]+=\s*)?", "", val).strip()
    # Strip surrounding quotes if present
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    return val

# Database and Core Tools
from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary
from city_coordinates import CITY_COORDINATES
from live_pricing import calculate_distance_km

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
    {
        "name": "get_distance_and_route",
        "description": "Calculate road driving distance in kilometers, estimated travel time in hours, highway route, and night stay recommendations between two cities or places in Pakistan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_city": {"type": "string", "description": "Origin city in Pakistan (e.g. Sialkot, Lahore, Islamabad, Karachi)"},
                "to_city": {"type": "string", "description": "Destination city, valley, or district in Pakistan (e.g. Hunza, Swat, Skardu, Gwadar)"},
            },
            "required": ["from_city", "to_city"],
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
    {
        "type": "function",
        "function": {
            "name": "get_distance_and_route",
            "description": "Calculate road driving distance in kilometers, estimated travel time in hours, highway route, and night stay recommendations between two cities or places in Pakistan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_city": {"type": "string", "description": "Origin city in Pakistan (e.g. Sialkot, Lahore, Islamabad, Karachi)"},
                    "to_city": {"type": "string", "description": "Destination city, valley, or district in Pakistan (e.g. Hunza, Swat, Skardu, Gwadar)"},
                },
                "required": ["from_city", "to_city"],
            },
        },
    },
]


def find_city_in_db(city_name: str) -> Optional[Tuple[str, Tuple[float, float]]]:
    """Finds matched city name and coordinates from CITY_COORDINATES."""
    if not city_name:
        return None
    raw = city_name.strip().lower()
    raw = re.sub(r"\b(city|valley|district|town|the|kpk|punjab|sindh|balochistan)\b", "", raw).strip()
    
    # Check exact match
    for c, coords in CITY_COORDINATES.items():
        if c.lower() == raw:
            return c, coords
            
    # Check word match
    for c, coords in CITY_COORDINATES.items():
        if re.search(r"\b" + re.escape(c.lower()) + r"\b", raw) or re.search(r"\b" + re.escape(raw) + r"\b", c.lower()):
            return c, coords

    # Common aliases
    aliases = {
        "hunza": "Hunza",
        "skardu": "Skardu",
        "swat": "Swat",
        "kalam": "Swat",
        "mingora": "Swat",
        "naran": "Mansehra",
        "kaghan": "Mansehra",
        "shangarila": "Skardu",
        "karimabad": "Hunza",
        "passu": "Hunza",
        "attabad": "Hunza",
        "pindi": "Rawalpindi",
        "twin cities": "Islamabad",
    }
    for alias_k, canonical in aliases.items():
        if alias_k in raw:
            coords = CITY_COORDINATES.get(canonical)
            if coords:
                return canonical, coords
                
    return None


def get_distance_and_route(from_city: str, to_city: str) -> Dict[str, Any]:
    """
    Computes road distance, driving duration, major highway routes, and night stay
    recommendations between any two cities in Pakistan.
    """
    c1 = find_city_in_db(from_city)
    c2 = find_city_in_db(to_city)
    
    if not c1 or not c2:
        missing = []
        if not c1: missing.append(from_city)
        if not c2: missing.append(to_city)
        return {
            "error": f"Could not locate coordinates for {', '.join(missing)} in Pakistan database."
        }
        
    start_name, (lat1, lon1) = c1
    dest_name, (lat2, lon2) = c2
    
    crow_km = calculate_distance_km(start_name, dest_name)
    if crow_km is None:
        import math
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        crow_km = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Mountainous / Northern regions have high winding road factors
    mountain_areas = {"Hunza", "Skardu", "Gilgit", "Swat", "Chitral", "Naran", "Kaghan", "Astore", "Diamer", "Ghizer", "Nagar"}
    is_mountain_route = (start_name in mountain_areas or dest_name in mountain_areas or lat2 > 34.0 or lat1 > 34.0)
    
    if is_mountain_route:
        road_km = round(crow_km * 1.72)
        avg_speed = 46.0  # km/h on mountain highways
    elif any(x in (start_name, dest_name) for x in ["Gwadar", "Pasni", "Ormara"]):
        road_km = round(crow_km * 1.25)
        avg_speed = 75.0
    else:
        road_km = round(crow_km * 1.20)
        avg_speed = 85.0  # km/h on Motorways M-1, M-2, M-3, M-5
        
    drive_hours = round(road_km / avg_speed, 1)
    
    # Specific known corridor logic
    if (start_name in ["Sialkot", "Lahore", "Gujranwala", "Faisalabad"] and dest_name in ["Hunza", "Gilgit", "Skardu"]):
        route_steps_en = [
            f"{start_name} to Islamabad via M-11 / M-2 Motorway (~2.5 - 3 hours)",
            "Islamabad to Mansehra / Thakot via Hazara Motorway M-15 (~1.5 - 2 hours)",
            f"Mansehra to Chilas to Gilgit to {dest_name} via Karakoram Highway (KKH / N-35) or via Babusar Pass during summer (~11 - 13 hours)",
        ]
        route_steps_ur = [
            f"{start_name} se Islamabad: M-11 / M-2 Motorway ke zariye (2.5 se 3 ghante)",
            "Islamabad se Mansehra: Hazara Motorway (M-15) ke zariye, nihayat smooth safar (1.5 se 2 ghante)",
            f"Mansehra se Chilas ➔ Gilgit ➔ {dest_name}: Karakoram Highway (KKH) ke zariye (Garmiyon mein Naran Babusar Top wala rasta 3 ghante bachaata hai)",
        ]
        night_stay_en = "Highly recommended to make a 1-night stop at Besham or Chilas (or Naran Valley if traveling in summer via Babusar Pass)."
        night_stay_ur = "Safar lamba hone ki wajah se 1 night stay zaroor karein — Besham ya Chilas mein raat guzaarna behtareen hai (garmiyon mein Naran Valley mein ruk sakte hain)."
    elif (start_name in ["Islamabad", "Rawalpindi"] and dest_name in ["Hunza", "Gilgit"]):
        route_steps_en = [
            "Islamabad to Mansehra via Hazara Motorway M-15 (~1.5 hours)",
            "Mansehra via KKH (N-35) through Besham, Dasu, Chilas to Gilgit and Hunza (~12 - 14 hours)",
        ]
        route_steps_ur = [
            "Islamabad se Mansehra: Hazara Motorway M-15 (1.5 ghante)",
            "Mansehra se KKH ke zariye Besham, Chilas, Gilgit aur Hunza (12 se 14 ghante)",
        ]
        night_stay_en = "Break the journey with an overnight stay in Chilas or Besham."
        night_stay_ur = "Raat ke qayam ke liye Chilas ya Besham behtareen stopover hain."
    elif (start_name in ["Karachi"] and dest_name in ["Gwadar"]):
        route_steps_en = [
            "Karachi to Hub via RCD Highway",
            "Hub to Gwadar via Makran Coastal Highway (N-10) passing Kund Malir and Ormara Beach (~8 - 9 hours)",
        ]
        route_steps_ur = [
            "Karachi se Hub (RCD Highway)",
            "Hub se Gwadar: Khubsoorat Makran Coastal Highway (N-10) ke zariye, Kund Malir aur Ormara Beach se hotay hue (8 se 9 ghante)",
        ]
        night_stay_en = "Direct 8-hour scenic drive; optional lunch/rest stop at Kund Malir or Ormara Beach."
        night_stay_ur = "Direct 8 ghante ki drive hai; raste mein Kund Malir ya Ormara Beach par rest aur lunch kar sakte hain."
    else:
        route_steps_en = [
            f"Depart {start_name} connecting to National Highway / Motorway network.",
            f"Follow main transit corridor toward {dest_name} (approx. {road_km} km).",
        ]
        route_steps_ur = [
            f"{start_name} se rawangi aur motorway / highway network par safar.",
            f"Main national route par {dest_name} ki taraf safar (takreeban {road_km} km).",
        ]
        if drive_hours > 8:
            night_stay_en = f"Since drive time is ~{drive_hours} hours, an overnight stop at an intermediate city is recommended."
            night_stay_ur = f"Chunkay safar {drive_hours} ghante ka hai, darmiyani shehar mein 1 raat ka qayam tajweez kiya jata hai."
        else:
            night_stay_en = "Can be comfortably completed in a single day drive."
            night_stay_ur = "Yeh safar aik hi din mein aasani se mukammal kiya ja sakta hai."
            
    return {
        "from_city": start_name,
        "to_city": dest_name,
        "straight_distance_km": round(crow_km),
        "road_distance_km": road_km,
        "estimated_hours": drive_hours,
        "is_mountain_route": is_mountain_route,
        "route_en": route_steps_en,
        "route_ur": route_steps_ur,
        "night_stay_en": night_stay_en,
        "night_stay_ur": night_stay_ur,
    }


ROMAN_URDU_VOCAB = {
    "se", "kitni", "kitna", "door", "kahan", "jaun", "jao", "kaise", "batao", "bataen",
    "chahiye", "kharcha", "hoga", "hain", "kya", "hai", "ha", "mujhe", "hum", "jana", "safari",
    "raasta", "rasta", "waqt", "lagay", "lagta", "gaari", "gari", "mausam", "sasta",
    "roman", "urdu", "shukriya", "acha", "theek", "bhai", "din", "log", "jagah", "ghoomne",
    "kisi", "wahan", "hota", "konsa", "behtareen", "khana", "rehaish", "hotel", "sawari"
}

def is_roman_urdu(text: str) -> bool:
    t = text.lower()
    if "roman urdu" in t or "in urdu" in t or "urdu main" in t or "urdu mein" in t:
        return True
    words = set(re.findall(r"\b[a-z]+\b", t))
    matches = words.intersection(ROMAN_URDU_VOCAB)
    if "se" in words and ("door" in words or "kitni" in words or "kitna" in words or "rasta" in words):
        return True
    return len(matches) >= 2


def check_distance_intent(user_message: str) -> Optional[Dict[str, Any]]:
    text = user_message.lower().strip()
    
    # 1. Regex pattern: "CITY1 se/to CITY2"
    m = re.search(r"([a-z\s]+?)\s+(?:se|to|from)\s+([a-z\s]+?)(?:\s+(?:kitni|kitna|door|distance|km|time|ghante|hours|ha|hai|hoga|raasta|rasta|\?|$))", text)
    if m:
        c1 = find_city_in_db(m.group(1))
        c2 = find_city_in_db(m.group(2))
        if c1 and c2 and c1[0] != c2[0]:
            return get_distance_and_route(c1[0], c2[0])
            
    # 2. Regex pattern: "between CITY1 and CITY2"
    m2 = re.search(r"(?:between|fasla|distance)\s+([a-z\s]+?)\s+(?:and|to|se)\s+([a-z\s]+)", text)
    if m2:
        c1 = find_city_in_db(m2.group(1))
        c2 = find_city_in_db(m2.group(2))
        if c1 and c2 and c1[0] != c2[0]:
            return get_distance_and_route(c1[0], c2[0])
            
    # 3. Check for distance keywords with any two recognized cities
    dist_keywords = ["door", "distance", "fasla", "faasla", "how far", "kitni door", "kitna door", "kitne km", "travel time", "kitna time", "kitne ghante", "raasta", "rasta"]
    if any(k in text for k in dist_keywords):
        detected = []
        for city in CITY_COORDINATES.keys():
            if re.search(r"\b" + re.escape(city.lower()) + r"\b", text):
                if city not in detected:
                    detected.append(city)
        if len(detected) >= 2:
            return get_distance_and_route(detected[0], detected[1])
            
    return None


def format_distance_response(route_info: Dict[str, Any], is_urdu: bool = False) -> str:
    from_c = route_info["from_city"]
    to_c = route_info["to_city"]
    km = route_info["road_distance_km"]
    hrs = route_info["estimated_hours"]
    
    if is_urdu:
        steps = "\n".join(f"{i+1}. {step}" for i, step in enumerate(route_info["route_ur"]))
        stay = route_info.get("night_stay_ur", "")
        return (
            f"### 🚗 {from_c} se {to_c} ka Fasla aur Rasta\n\n"
            f"- **Kul Fasla (Road Distance)**: Lagbhag **{km:,} kilometers**\n"
            f"- **Driving ka Waqt**: Takreeban **{hrs} ghante** (musalsal safar)\n\n"
            f"#### 🛣️ Behtareen Route (Highways & Motorways):\n{steps}\n\n"
            f"#### 🏨 Qayam / Night Stay ki Tajweez:\n- {stay}\n\n"
            f"#### 💡 Safar ke Zaroori Mashware (Tips):\n"
            f"- Rawangi se pehle gaari ki servicing aur tyre condition zaroor check karein.\n"
            f"- Gilgit aur Hunza ke pahari raaston par daylight (din ki roshni) mein driving karein."
        )
    else:
        steps = "\n".join(f"{i+1}. {step}" for i, step in enumerate(route_info["route_en"]))
        stay = route_info.get("night_stay_en", "")
        return (
            f"### 🚗 Distance and Route: {from_c} to {to_c}\n\n"
            f"- **Total Road Distance**: Approximately **{km:,} km**\n"
            f"- **Estimated Driving Time**: Around **{hrs} hours** (continuous driving)\n\n"
            f"#### 🛣️ Recommended Route:\n{steps}\n\n"
            f"#### 🏨 Recommended Overnight Stops:\n- {stay}\n\n"
            f"#### 💡 Essential Travel Tips:\n"
            f"- Check vehicle brakes, tire pressure, and engine fluids before departure.\n"
            f"- Mountain driving is best scheduled during daylight hours."
        )


TOOL_FUNCTIONS = {
    "search_destinations": search_destinations,
    "get_destination_details": get_destination_details,
    "estimate_cost": estimate_cost,
    "generate_itinerary": generate_itinerary,
    "predict_trip_budget": predict_trip_budget,
    "find_similar_destinations": find_similar_destinations,
    "explain_trip_budget": explain_trip_budget,
    "search_knowledge_base": search_knowledge_base,
    "get_distance_and_route": get_distance_and_route,
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
    Rule-based agent with RAG context enrichment and bilingual Roman Urdu support.
    Directly answers distance/route queries without dumping unrelated packages.
    """
    is_urdu = is_roman_urdu(user_message)

    # 1. Direct Distance & Route Intent Detection (e.g. Sialkot se Hunza kitni door ha)
    dist_info = check_distance_intent(user_message)
    if dist_info:
        return format_distance_response(dist_info, is_urdu=is_urdu)

    # 2. Check if user specifically requested Roman Urdu explanation
    is_explain_urdu = bool(re.search(r"\b(explain\s+it\s+in\s+roman\s+urdu|explain\s+in\s+roman\s+urdu|roman\s+urdu\s+me|roman\s+urdu\s+main)\b", user_message.lower()))
    if is_explain_urdu:
        is_urdu = True

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

            if score < 0.05 or not text:
                continue

            section_icons = {
                "weather": "🌤️ **Weather & Season**" if not is_urdu else "🌤️ **Mausam & Season**",
                "travel_tips": "💡 **Travel Tips**" if not is_urdu else "💡 **Safar ke Mashware**",
                "history": "🏛️ **History**" if not is_urdu else "🏛️ **Tareekh**",
                "attraction": "📍 **Attraction**" if not is_urdu else "📍 **Khas Maqamat**",
                "food": "🍽️ **Local Food**" if not is_urdu else "🍽️ **Khaas Khanay**",
                "transport": "🚌 **Getting There**" if not is_urdu else "🚌 **Rasta & Sawari**",
                "accommodations": "🏨 **Accommodation**" if not is_urdu else "🏨 **Rehaish**",
                "destination": "📌 **Destination Info**" if not is_urdu else "📌 **Ilaqai Maloomat**",
            }
            icon = section_icons.get(section, "ℹ️")
            snippet = text[:380] + ("..." if len(text) > 380 else "")
            rag_context_lines.append(f"{icon}: {snippet}")
    except Exception as _rag_ex:
        pass

    # ── Standard destination search ────────────────────────────────────────────
    matches = search_destinations(
        province=province,
        district=district,
        max_budget_per_day=per_day_budget,
        category=category,
    )

    if not matches and per_day_budget:
        matches = search_destinations(
            province=province,
            district=district,
            category=category,
        )

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
            if is_urdu:
                lines = [
                    "### ⚡ Live Market Kharcha Estimate (2026)",
                    f"Hamare pas exact destination database mein mojood nahi jo **{province} mein {category}** se match kare, lekin yeh live ML market estimate hai:",
                    "",
                    f"- **Rozana ka Standard Kharcha**: PKR {std_day:,.0f} / din / fard",
                    f"- **Kul Kharcha ({days} Din, {people} Sayyah)**: PKR {total_est:,.0f}",
                    "",
                    "Aap is province ke deegar mashhoor maqamat ke baray mein bhi daryaft kar sakte hain!",
                ]
            else:
                lines = [
                    "### ⚡ Live Market Budget Estimate (2026)",
                    f"I don't have an exact destination in the database matching "
                    f"**{category} in {province}**, but here's a live ML market estimate:",
                    "",
                    f"- **Standard Daily Rate**: PKR {std_day:,.0f} / day / person",
                    f"- **Total for {days} Day(s) ({people} Traveler{'s' if people > 1 else ''})**: PKR {total_est:,.0f}",
                    "",
                    "Try browsing other destinations in that province or category for a specific plan!",
                ]
            if rag_context_lines:
                lines.append("")
                lines.append("---")
                lines.append("#### 📚 " + ("Relevant Travel Knowledge" if not is_urdu else "Safar ki Zaroori Maloomat"))
                lines.extend(f"- {cl}" for cl in rag_context_lines[:3])
            return "\n".join(lines)

    if not matches and (province or category):
        matches = search_destinations(
            province=province,
            category=category,
        )

    if not matches:
        matches = search_destinations()

    if not matches:
        if is_urdu:
            return "Mujhe aap ke matlooba mayaar ke mutabiq koi maqam nahi mila. Baraye meharbani KPK, Punjab, Sindh, Balochistan ya Gilgit-Baltistan ke mashhoor maqamat ke baray mein poochein!"
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

    if is_urdu:
        lines = [
            f"### Tajweez Karda Maqam: {chosen['name']}",
            f"**Ilaqa (Location)**: {chosen.get('district', '') + ', ' if chosen.get('district') else ''}{chosen['province']} | **Category**: {chosen.get('category', 'sightseeing').title()}",
            "",
            f"*{details.get('description', '')}*",
            "",
            f"#### ⚡ Live Market Kharcha Breakdown ({days} Din, {people} Sayyah — {cost.get('travel_style_label', 'Standard')})",
            f"- **Kul Kharcha (Total)**: **{total_str}**",
            f"  - 🏨 **Rehaish (Accommodation)**: PKR {cost['breakdown_pkr']['accommodation']:,} ({cost.get('travel_style_label', 'Hotel')})",
            f"  - 🚗 **Sawari (Transport)**: PKR {cost['breakdown_pkr']['transport']:,} ({cost.get('transport_label', 'Private Transport')})",
            f"  - 🍽️ **Khana Peena**: PKR {cost['breakdown_pkr']['food']:,} ({cost.get('dining_style', 'Dining')})",
            f"  - 🎟️ **Sair o Tafreeh (Activities)**: PKR {cost['breakdown_pkr']['activities']:,}",
            f"  - 🧾 **Service & Taxes**: PKR {cost['breakdown_pkr'].get('service_and_taxes', 0):,}",
            "",
            "#### Din-ba-Din Safar ka Mansooba (Itinerary):"
        ]
        for day in itinerary["itinerary"]:
            lines.append(f"- **Din {day['day']}**: {day['plan']}")

        if len(matches) > 1:
            alt_names = [m["name"] for m in matches[1:4]]
            lines.append("")
            lines.append(f"**Qareeb ke mazeed dilchasp maqamat**: {', '.join(alt_names)}")

        if rag_context_lines:
            lines.append("")
            lines.append("---")
            lines.append("#### 📚 Safar ki Zaroori Maloomat (Travel Tips & Info):")
            for cl in rag_context_lines[:4]:
                lines.append(f"- {cl}")

        return "\n".join(lines)

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

def resolve_groq_model(client) -> str:
    """Returns a valid model from Groq API, prioritizing user setting and working models."""
    configured = os.getenv("GROQ_MODEL", "").strip()
    preferred_candidates = [configured, "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    try:
        remote_models = [m.id for m in client.models.list().data]
        for candidate in preferred_candidates:
            if candidate and candidate in remote_models:
                return candidate
        chat_models = [m for m in remote_models if "llama" in m or "oss" in m or "qwen" in m]
        if chat_models:
            return chat_models[0]
    except Exception:
        pass
    return configured or "llama-3.3-70b-versatile"


SYSTEM_PROMPT = (
    "You are an expert, warm, and helpful Pakistan Travel AI Assistant. "
    "You have access to tools for querying a real database of 376+ verified destinations in Pakistan "
    "AND a rich knowledge base with detailed city histories, weather guides, travel tips, "
    "attractions, food recommendations, and transport information.\n\n"
    "CRITICAL LANGUAGE RULE: Always reply in the same language and style the user wrote in. "
    "If the user writes in Roman Urdu (e.g. 'sialkot se hunza kitni door ha', 'kya hal hai', 'explain it in roman urdu'), "
    "you MUST reply entirely in natural, friendly Roman Urdu. NEVER reply in English when addressed in Roman Urdu. "
    "If they write in Urdu script, reply in Urdu script. If they write in English, reply in English.\n\n"
    "DIRECT ANSWERING RULE: If the user asks a specific question (such as distance or driving time between cities, "
    "weather, best season, food, or safety), answer that specific question directly and concisely first. "
    "Do NOT dump an entire unrelated 3-day budget itinerary unless the user explicitly asks to plan a trip or budget.\n\n"
    "TOOL USAGE GUIDELINES:\n"
    "1. For distance & travel duration queries (e.g. 'Sialkot to Hunza'): call get_distance_and_route FIRST.\n"
    "2. For questions about history, culture, weather, attractions, food, or safety: call search_knowledge_base.\n"
    "3. For trip planning and budget estimation: use search_destinations, estimate_cost, and generate_itinerary.\n"
    "4. Format costs clearly in PKR with bullet points and emojis. Ground your answers in retrieved context."
)


def run_groq_agent(user_message: str, max_turns: int = 8, history: Optional[List[Dict[str, str]]] = None) -> str:
    """Runs the Groq AI agent with function calling and conversation memory."""
    api_key = get_clean_api_key("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in .env.")

    from groq import Groq
    client = Groq(api_key=api_key)
    model = resolve_groq_model(client)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Incorporate conversation memory (up to last 10 turns)
    if history:
        for turn in history[-10:]:
            r = turn.get("role")
            c = turn.get("content")
            if r in ("user", "assistant") and c:
                messages.append({"role": r, "content": str(c)})

    messages.append({"role": "user", "content": user_message})

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

        # Serialize assistant response with tool calls into clean dict
        assistant_dict = {
            "role": "assistant",
            "content": response_msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in response_msg.tool_calls
            ],
        }
        messages.append(assistant_dict)

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
                "content": json.dumps(result, ensure_ascii=False),
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

    system_prompt = (
        "You are an expert, warm, and helpful Pakistan Travel AI Assistant. "
        "You have access to tools for querying a real database of 376+ verified destinations "
        "across Pakistan's 4 provinces, 3 territories, and 161+ cities/districts, plus a knowledge "
        "base with city histories, weather guides, travel tips, attractions, food, and transport info.\n\n"
        "LANGUAGE RULE: Always reply in the same language and script the user just wrote in. "
        "If they write in Roman Urdu (Urdu words spelled in English letters, e.g. 'mujhe Hunza "
        "ka plan chahiye'), reply in Roman Urdu — do NOT switch to English. If they write in Urdu "
        "script, reply in Urdu script. If they write in English, reply in English. Match their "
        "language on every turn, even mid-conversation.\n\n"
        "TOOL USAGE GUIDELINES:\n"
        "1. For questions about history, culture, weather/seasons, travel tips, safety, "
        "attractions, local food, or transport — call search_knowledge_base FIRST to retrieve "
        "accurate, curated context before answering.\n"
        "2. For trip planning, budget estimation, and itinerary generation — use "
        "search_destinations, estimate_cost, and generate_itinerary.\n"
        "3. Always format costs clearly in PKR with bullet points and emojis.\n"
        "4. Ground your answers in the retrieved context — do NOT invent facts."
    )

    messages = [{"role": "user", "content": user_message}]
    turns = 0

    while turns < max_turns:
        turns += 1
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
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

def run_agent_with_meta(user_message: str, max_turns: int = 5, history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, str, Optional[str]]:
    """
    Unified entry point returning metadata for web/API endpoints:
    Returns (reply_content, engine_used, error_notice_if_any).
    - engine_used: "groq", "claude", or "mock"
    - error_notice_if_any: Error string if live model failed and triggered fallback to simulation.
    """
    groq_key = get_clean_api_key("GROQ_API_KEY")
    anthropic_key = get_clean_api_key("ANTHROPIC_API_KEY")

    if groq_key:
        try:
            reply = run_groq_agent(user_message, max_turns=max_turns, history=history)
            return reply, "groq", None
        except Exception as e:
            err_msg = str(e)
            print(f"[Groq AI Error] {err_msg}. Falling back to Simulation Mode...")
            mock_reply = run_mock_agent(user_message)
            return mock_reply, "mock", f"Groq AI error: {err_msg}"

    if anthropic_key:
        try:
            reply = run_claude_agent(user_message, max_turns=max_turns)
            return reply, "claude", None
        except Exception as e:
            err_msg = str(e)
            print(f"[Claude AI Error] {err_msg}. Falling back to Simulation Mode...")
            mock_reply = run_mock_agent(user_message)
            return mock_reply, "mock", f"Claude AI error: {err_msg}"

    return run_mock_agent(user_message), "mock", None


def run_agent(user_message: str, max_turns: int = 5, mode: str = "auto", history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Unified entry point:
    - mode="auto": Checks Groq -> Anthropic -> Fallback to Simulation (Mock) Mode.
    - mode="ai": Force AI only (Groq or Claude).
    - mode="mock": Force Simulation Mode directly.
    """
    if mode == "mock":
        return run_mock_agent(user_message)

    reply, engine, notice = run_agent_with_meta(user_message, max_turns=max_turns, history=history)
    if mode == "ai" and engine == "mock" and notice:
        raise RuntimeError(notice)
    return reply


def stream_agent(user_message: str, history: Optional[List[Dict[str, str]]] = None):
    """
    Generator yielding Server-Sent Events (SSE) for live typing chat streaming.
    Yields data: {"type": "status"|"token"|"done", "content": ...}\n\n
    """
    groq_key = get_clean_api_key("GROQ_API_KEY")

    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            model = resolve_groq_model(client)

            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]
            if history:
                for turn in history[-10:]:
                    r = turn.get("role")
                    c = turn.get("content")
                    if r in ("user", "assistant") and c:
                        messages.append({"role": r, "content": str(c)})
            messages.append({"role": "user", "content": user_message})

            turns = 0
            while turns < 8:
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
                    # Final response text - stream in natural token chunks
                    final_text = response_msg.content or "I have prepared your travel recommendations."
                    words = final_text.split(" ")
                    for i, w in enumerate(words):
                        space = " " if i < len(words) - 1 else ""
                        yield f"data: {json.dumps({'type': 'token', 'content': w + space})}\n\n"
                        time.sleep(0.012)
                    yield f"data: {json.dumps({'type': 'done', 'engine': 'groq'})}\n\n"
                    return

                # Record assistant tool call
                assistant_dict = {
                    "role": "assistant",
                    "content": response_msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in response_msg.tool_calls
                    ],
                }
                messages.append(assistant_dict)

                for tool_call in response_msg.tool_calls:
                    func_name = tool_call.function.name
                    try:
                        func_args = json.loads(tool_call.function.arguments)
                    except Exception:
                        func_args = {}

                    tool_label = func_name.replace("_", " ").title()
                    yield f"data: {json.dumps({'type': 'status', 'content': f'Searching {tool_label}...' })}\n\n"

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
                        "content": json.dumps(result, ensure_ascii=False),
                    })

            yield f"data: {json.dumps({'type': 'done', 'engine': 'groq'})}\n\n"
            return
        except Exception as e:
            yield f"data: {json.dumps({'type': 'status', 'content': f'Groq: {e}. Using simulation engine...' })}\n\n"

    # Fallback to simulation engine
    sim_reply = run_mock_agent(user_message)
    words = sim_reply.split(" ")
    for i, w in enumerate(words):
        space = " " if i < len(words) - 1 else ""
        yield f"data: {json.dumps({'type': 'token', 'content': w + space})}\n\n"
        time.sleep(0.012)
    yield f"data: {json.dumps({'type': 'done', 'engine': 'mock'})}\n\n"


def test_groq_connection() -> Dict[str, Any]:
    """Tests the Groq API key and returns detailed diagnostic status."""
    key = get_clean_api_key("GROQ_API_KEY")
    if not key:
        return {
            "status": "missing_key",
            "message": "GROQ_API_KEY is not configured in .env. Obtain a free key from https://console.groq.com/keys",
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        }
    try:
        from groq import Groq
        client = Groq(api_key=key)
        model_list = client.models.list().data
        model_ids = [m.id for m in model_list]
        configured_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"
        model_found = configured_model in model_ids
        return {
            "status": "ok",
            "message": "Groq API key is valid and connected successfully!",
            "configured_model": configured_model,
            "configured_model_valid": model_found,
            "available_models": [m for m in model_ids if "llama" in m or "mixtral" in m or "gemma" in m][:6],
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "configured_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        }


# =====================================================================
# 6. CLI INTERACTIVE LOOP
# =====================================================================

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    groq_key = get_clean_api_key("GROQ_API_KEY")
    anthropic_key = get_clean_api_key("ANTHROPIC_API_KEY")

    if groq_key:
        print("[AI Mode] Groq Llama 3.3 Active")
    elif anthropic_key:
        print("[AI Mode] Anthropic Claude Active")
    else:
        print("[Simulation Mode] Rule-based NLP Engine Active")
        print("(Optional: Add valid GROQ_API_KEY in .env for full LLM mode)")

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