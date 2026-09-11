"""
emergency_contacts.py
======================
Fixed, nationwide/provincial emergency dialing numbers for the
"Offline Medical SOS Hub". These numbers don't change per-destination
and don't need a database lookup, so they're hardcoded here and served
as a small static JSON blob the frontend can cache once and keep
working with forever, even with zero connectivity.

NEEDS VERIFICATION: numbers below are the commonly published ones as of
2026, but please double-check each against the operator's own site
before shipping -- see the pattern already used elsewhere in this repo
(models.py's `data_source` field convention).
"""

EMERGENCY_CONTACTS = [
    {
        "id": "rescue_1122",
        "name": "Rescue 1122",
        "number": "1122",
        "description": "Primary government emergency medical & rescue service.",
        "coverage": ["Punjab", "KPK", "Balochistan", "Gilgit-Baltistan (partial)", "Azad Kashmir (partial)"],
        "category": "ambulance",
    },
    {
        "id": "edhi_ambulance",
        "name": "Edhi Ambulance",
        "number": "115",
        "description": "World's largest volunteer ambulance network; strong in Sindh and inter-city transfers.",
        "coverage": ["Nationwide", "Especially Sindh"],
        "category": "ambulance",
    },
    {
        "id": "chhipa_ambulance",
        "name": "Chhipa Ambulance",
        "number": "1020",
        "description": "Active rescue network, especially in Sindh and major urban centres.",
        "coverage": ["Sindh", "Major urban hubs nationwide"],
        "category": "ambulance",
    },
    {
        "id": "tourist_police",
        "name": "Tourist Police Helpline",
        "number": "1422",
        "description": "For tourists facing security or emergency logistics issues, especially in KPK and northern areas.",
        "coverage": ["KPK", "Northern hubs (Swat, Naran, Hunza, etc.)"],
        "category": "tourist_safety",
    },
    {
        "id": "police",
        "name": "Police",
        "number": "15",
        "description": "General police emergency line.",
        "coverage": ["Nationwide"],
        "category": "security",
    },
]


def get_emergency_contacts(province: str = None) -> list:
    """
    Returns all emergency contacts, optionally filtered to ones that
    explicitly list the given province in their coverage (contacts
    tagged 'Nationwide' are always included).
    """
    if not province:
        return EMERGENCY_CONTACTS

    province_lower = province.lower()
    return [
        c for c in EMERGENCY_CONTACTS
        if any(province_lower in area.lower() or "nationwide" in area.lower() for area in c["coverage"])
    ]
