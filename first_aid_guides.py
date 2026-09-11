"""
first_aid_guides.py
====================
Static step-by-step first-aid content for terrain-specific emergencies
tourists actually run into in Pakistan's northern areas and rural south.

This is general public safety information (not medication dosing advice)
meant to buy time until Rescue 1122 / Edhi / Chhipa or a real medical
facility is reached -- it does not replace professional care.

Kept as plain Python data (not DB rows) since this content is fixed and
should be bundled with the frontend for guaranteed offline access.
"""

FIRST_AID_GUIDES = [
    {
        "id": "ams",
        "title": "Acute Mountain Sickness (AMS)",
        "applies_to": ["Babusar Top", "Deosai", "Khunjerab Pass", "Fairy Meadows", "Any altitude above ~2,500m"],
        "symptoms": [
            "Headache (most common early sign)",
            "Nausea or loss of appetite",
            "Dizziness or fatigue out of proportion to exertion",
            "Trouble sleeping",
            "Severe cases: confusion, difficulty walking straight, breathlessness at rest",
        ],
        "steps": [
            "Stop ascending immediately at the first sign of symptoms -- do not push higher.",
            "If symptoms are mild, rest at the same altitude for 24-48 hours before deciding to continue.",
            "If symptoms worsen or don't improve with rest, descend at least 500m in altitude — this is the single most effective treatment.",
            "Keep the person hydrated and warm; avoid alcohol and sedatives.",
            "If there is confusion, inability to walk in a straight line, or breathlessness at rest, treat as an emergency: descend immediately and call Rescue 1122.",
        ],
        "seek_help_if": "Symptoms worsen despite rest, or any confusion/severe breathlessness appears.",
    },
    {
        "id": "waterborne_illness",
        "title": "Waterborne Illness / Severe Dehydration",
        "applies_to": ["Anywhere with unfiltered water or roadside food, especially in summer"],
        "symptoms": [
            "Watery diarrhea and/or vomiting",
            "Stomach cramps",
            "Signs of dehydration: dry mouth, dark urine, dizziness on standing",
        ],
        "steps": [
            "Prepare Oral Rehydration Salts (ORS) exactly as printed on the sachet and sip continuously, even after each loose stool.",
            "If ORS sachets aren't available, a rough home substitute is 1 litre of clean/boiled water with a pinch of salt and a spoon of sugar -- ORS sachets are strongly preferred when you have them.",
            "Continue small, frequent sips rather than large amounts at once if vomiting.",
            "Rest and avoid dairy, caffeine, and heavy/oily food until symptoms settle.",
            "Do not give any medication to a child without a doctor's guidance.",
        ],
        "seek_help_if": "Blood in stool/vomit, high fever, inability to keep any fluids down, or symptoms in a young child or elderly person — get to the nearest BHU/hospital.",
    },
    {
        "id": "leech_bite",
        "title": "Land Leech Bites",
        "applies_to": ["Swat", "Kashmir", "Monsoon/rainy forest trekking routes"],
        "symptoms": ["Painless attachment (often unnoticed until removal)", "Prolonged bleeding after the leech detaches (its saliva contains an anticoagulant)"],
        "steps": [
            "Do NOT pull the leech off forcefully — this can leave mouthparts in the skin and increase infection risk.",
            "Slide a fingernail or flat edge along the skin to break its suction at the front (narrow) end, then flick it away.",
            "Clean the wound with water/antiseptic and apply firm, direct pressure with a clean cloth to control bleeding.",
            "Keep the area clean and watch for signs of infection over the next few days.",
        ],
        "seek_help_if": "Bleeding doesn't stop after 10-15 minutes of firm pressure, or signs of infection (redness, swelling, pus) develop.",
    },
    {
        "id": "snake_bite",
        "title": "Snake Bites",
        "applies_to": ["Rural trekking routes nationwide, especially rocky/grassy terrain"],
        "symptoms": ["Puncture marks", "Pain and swelling at the bite site", "Possible nausea, blurred vision, or difficulty breathing in venomous bites"],
        "steps": [
            "Keep the person as still and calm as possible — movement speeds venom spread.",
            "Remove rings/watches/tight clothing near the bite before swelling starts.",
            "Keep the bitten limb at or slightly below heart level.",
            "Do NOT cut the wound, try to suck out venom, apply a tight tourniquet, or apply ice.",
            "Note the snake's appearance if safely possible (do not try to catch or kill it) to help identify anti-venom needs.",
            "Get to the nearest facility with anti-venom (see the Medical Locator) or call Rescue 1122 immediately — this is always a medical emergency.",
        ],
        "seek_help_if": "Always — every snake bite needs professional evaluation, even if symptoms seem mild at first.",
    },
    {
        "id": "fracture_splint",
        "title": "Fractures & Improvised Splints",
        "applies_to": ["Falls on trekking/hiking routes"],
        "symptoms": ["Deformity, inability to bear weight or move the limb normally", "Severe pain, swelling, bruising"],
        "steps": [
            "Do not try to straighten or realign the limb.",
            "Immobilize the joint above AND below the injury using sticks, trekking poles, or a rolled-up jacket as a splint.",
            "Pad the splint with cloth before tying, and secure with bandages/cloth strips — snug but not so tight it cuts off circulation.",
            "Check fingers/toes below the splint periodically for color and warmth to make sure it isn't too tight.",
            "Keep the limb elevated and still, and arrange transport to a facility with trauma care (CMH or DHQ hospital) rather than walking out on it.",
        ],
        "seek_help_if": "Always for a suspected fracture — especially if the limb looks deformed, or fingers/toes below it go numb, pale, or cold.",
    },
]


def get_first_aid_guide(guide_id: str = None):
    """Returns a single guide by id, or the full list if no id given."""
    if not guide_id:
        return FIRST_AID_GUIDES
    return next((g for g in FIRST_AID_GUIDES if g["id"] == guide_id), None)
