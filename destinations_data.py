"""
Destinations dataset — Phase 5.
===================================
Kept SEPARATE from seed.py so the data itself is easy to review, add
to, or correct without touching the insertion logic.

IMPORTANT — data-trust note:
Coordinates below reflect general publicly-known locations for these
landmarks. Per this project's own data-trust rule, spot-check each one
against Google Maps before treating this as production-verified data —
that's exactly why every record's data_source says "needs verification"
rather than claiming a survey-grade source.
"""

DESTINATIONS = [
    # --- Originally seeded (Phase 2) ---
    {
        "name": "Hunza Valley", "province": "Gilgit-Baltistan", "district": "Hunza",
        "latitude": 36.3167, "longitude": 74.6500,
        "description": "Mountain valley known for scenic views, Karimabad, and Attabad Lake.",
        "best_season": "April to October", "recommended_days": 4,
        "estimated_budget_per_day": 8000, "activities": "hiking,sightseeing,photography",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Naran Kaghan", "province": "KPK", "district": "Mansehra",
        "latitude": 34.9078, "longitude": 73.6500,
        "description": "Valley famous for Saif-ul-Malook Lake and alpine scenery.",
        "best_season": "May to September", "recommended_days": 3,
        "estimated_budget_per_day": 7000, "activities": "lake visit,hiking,jeep tours",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Swat Valley", "province": "KPK", "district": "Swat",
        "latitude": 34.7717, "longitude": 72.3604,
        "description": "Known as the 'Switzerland of Pakistan', with rivers and green valleys.",
        "best_season": "March to October", "recommended_days": 4,
        "estimated_budget_per_day": 6500, "activities": "sightseeing,river visits,hiking",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Badshahi Mosque", "province": "Punjab", "district": "Lahore",
        "latitude": 31.5881, "longitude": 74.3095,
        "description": "Mughal-era mosque, one of the largest in the world, in the Walled City of Lahore.",
        "best_season": "October to March", "recommended_days": 1,
        "estimated_budget_per_day": 3000, "activities": "historical sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Faisal Mosque", "province": "Islamabad Capital Territory", "district": "Islamabad",
        "latitude": 33.7295, "longitude": 73.0374,
        "description": "Iconic modern mosque at the foot of the Margalla Hills.",
        "best_season": "Year-round", "recommended_days": 1,
        "estimated_budget_per_day": 2500, "activities": "sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },

    # --- KPK ---
    {
        "name": "Kaghan Valley", "province": "KPK", "district": "Mansehra",
        "latitude": 34.7833, "longitude": 73.4333,
        "description": "Alpine valley along the Kunhar River, gateway to Naran and Saif-ul-Malook.",
        "best_season": "May to September", "recommended_days": 2,
        "estimated_budget_per_day": 6500, "activities": "river views,hiking,camping",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Chitral Valley", "province": "KPK", "district": "Chitral",
        "latitude": 35.8492, "longitude": 71.7861,
        "description": "Remote valley beneath Tirich Mir, gateway to the Kalash valleys.",
        "best_season": "May to October", "recommended_days": 3,
        "estimated_budget_per_day": 6000, "activities": "cultural visits,hiking,photography",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Kalash Valley (Bumburet)", "province": "KPK", "district": "Chitral",
        "latitude": 35.6667, "longitude": 71.7500,
        "description": "Home of the Kalash people, known for distinct culture and festivals.",
        "best_season": "May to October", "recommended_days": 2,
        "estimated_budget_per_day": 5500, "activities": "cultural visits,festivals,photography",
        "category": "cultural", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Kumrat Valley", "province": "KPK", "district": "Upper Dir",
        "latitude": 35.4833, "longitude": 72.0000,
        "description": "Dense pine forests and rivers, a less-crowded alternative to Swat.",
        "best_season": "May to September", "recommended_days": 2,
        "estimated_budget_per_day": 6000, "activities": "camping,river visits,hiking",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Malam Jabba", "province": "KPK", "district": "Swat",
        "latitude": 34.8167, "longitude": 72.5667,
        "description": "Ski resort and hill station near Swat, popular in winter.",
        "best_season": "December to February (skiing), June-August (summer)", "recommended_days": 1,
        "estimated_budget_per_day": 7000, "activities": "skiing,chairlift,sightseeing",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Takht-i-Bahi", "province": "KPK", "district": "Mardan",
        "latitude": 34.3167, "longitude": 71.9667,
        "description": "UNESCO World Heritage Buddhist monastery ruins, among the best-preserved in the region.",
        "best_season": "October to March", "recommended_days": 1,
        "estimated_budget_per_day": 3000, "activities": "historical sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },

    # --- Punjab ---
    {
        "name": "Lahore Fort", "province": "Punjab", "district": "Lahore",
        "latitude": 31.5883, "longitude": 74.3142,
        "description": "Mughal-era fort and UNESCO World Heritage Site in the Walled City of Lahore.",
        "best_season": "October to March", "recommended_days": 1,
        "estimated_budget_per_day": 3000, "activities": "historical sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Shalimar Gardens", "province": "Punjab", "district": "Lahore",
        "latitude": 31.5925, "longitude": 74.3806,
        "description": "Mughal-era terraced garden, a UNESCO World Heritage Site.",
        "best_season": "October to March", "recommended_days": 1,
        "estimated_budget_per_day": 2500, "activities": "sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Multan Shrine (Shah Rukn-e-Alam)", "province": "Punjab", "district": "Multan",
        "latitude": 30.1961, "longitude": 71.4694,
        "description": "13th-century Sufi shrine, a landmark of Multan's 'City of Saints' identity.",
        "best_season": "November to February", "recommended_days": 1,
        "estimated_budget_per_day": 3000, "activities": "cultural visits,historical sightseeing",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Murree", "province": "Punjab", "district": "Rawalpindi",
        "latitude": 33.9070, "longitude": 73.3943,
        "description": "Popular hill station near Islamabad, known for pine forests and Mall Road.",
        "best_season": "March to October (also winter for snow)", "recommended_days": 2,
        "estimated_budget_per_day": 6000, "activities": "hiking,shopping,sightseeing",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Rohtas Fort", "province": "Punjab", "district": "Jhelum",
        "latitude": 32.9650, "longitude": 73.5850,
        "description": "16th-century Sher Shah Suri fort, a UNESCO World Heritage Site.",
        "best_season": "October to March", "recommended_days": 1,
        "estimated_budget_per_day": 2500, "activities": "historical sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Katas Raj Temples", "province": "Punjab", "district": "Chakwal",
        "latitude": 32.7742, "longitude": 72.9314,
        "description": "Ancient Hindu temple complex around a sacred pond.",
        "best_season": "October to March", "recommended_days": 1,
        "estimated_budget_per_day": 2500, "activities": "historical sightseeing,cultural visits",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },

    # --- Sindh ---
    {
        "name": "Mohenjo-daro", "province": "Sindh", "district": "Larkana",
        "latitude": 27.3294, "longitude": 68.1378,
        "description": "UNESCO World Heritage archaeological site of the Indus Valley Civilization.",
        "best_season": "November to February", "recommended_days": 1,
        "estimated_budget_per_day": 3500, "activities": "historical sightseeing,museum visit",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Clifton Beach", "province": "Sindh", "district": "Karachi",
        "latitude": 24.8138, "longitude": 66.9930,
        "description": "Karachi's main urban beach, popular for evening visits and camel rides.",
        "best_season": "November to February", "recommended_days": 1,
        "estimated_budget_per_day": 3000, "activities": "beach,sightseeing,food",
        "category": "beaches", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Ranikot Fort", "province": "Sindh", "district": "Jamshoro",
        "latitude": 25.9333, "longitude": 67.9667,
        "description": "One of the world's largest forts by circumference, sometimes called the 'Great Wall of Sindh'.",
        "best_season": "November to February", "recommended_days": 1,
        "estimated_budget_per_day": 4000, "activities": "historical sightseeing,hiking",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Shah Jahan Mosque, Thatta", "province": "Sindh", "district": "Thatta",
        "latitude": 24.7461, "longitude": 67.9219,
        "description": "17th-century mosque famed for its intricate tile work and acoustics.",
        "best_season": "November to February", "recommended_days": 1,
        "estimated_budget_per_day": 3000, "activities": "historical sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Makli Necropolis", "province": "Sindh", "district": "Thatta",
        "latitude": 24.7500, "longitude": 67.9167,
        "description": "One of the largest funerary sites in the world, a UNESCO World Heritage Site.",
        "best_season": "November to February", "recommended_days": 1,
        "estimated_budget_per_day": 3000, "activities": "historical sightseeing,photography",
        "category": "historical", "data_source": "General knowledge — needs verification against Google Maps",
    },

    # --- Balochistan ---
    {
        "name": "Hingol National Park", "province": "Balochistan", "district": "Lasbela",
        "latitude": 25.4667, "longitude": 65.5000,
        "description": "Pakistan's largest national park, known for the Princess of Hope rock formation and coastal desert scenery.",
        "best_season": "November to February", "recommended_days": 2,
        "estimated_budget_per_day": 5500, "activities": "wildlife,sightseeing,hiking",
        "category": "nature", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Ziarat Juniper Forest", "province": "Balochistan", "district": "Ziarat",
        "latitude": 30.3820, "longitude": 67.7250,
        "description": "One of the largest juniper forests in the world, near the historic Quaid-e-Azam Residency.",
        "best_season": "April to October", "recommended_days": 2,
        "estimated_budget_per_day": 5000, "activities": "hiking,sightseeing,historical visit",
        "category": "nature", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Hanna Lake", "province": "Balochistan", "district": "Quetta",
        "latitude": 30.2971, "longitude": 67.1129,
        "description": "Scenic lake near Quetta surrounded by rocky hills, popular for boating.",
        "best_season": "March to October", "recommended_days": 1,
        "estimated_budget_per_day": 4000, "activities": "boating,sightseeing,picnic",
        "category": "nature", "data_source": "General knowledge — needs verification against Google Maps",
    },

    # --- Gilgit-Baltistan (beyond Hunza) ---
    {
        "name": "Skardu (Lower Kachura Lake)", "province": "Gilgit-Baltistan", "district": "Skardu",
        "latitude": 35.4167, "longitude": 75.4167,
        "description": "Gateway to K2 and the Karakoram, with turquoise lakes and dramatic desert-mountain scenery.",
        "best_season": "May to September", "recommended_days": 4,
        "estimated_budget_per_day": 8500, "activities": "sightseeing,boating,hiking",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Deosai National Park", "province": "Gilgit-Baltistan", "district": "Skardu",
        "latitude": 34.8000, "longitude": 75.4000,
        "description": "High-altitude plateau known as the 'Land of Giants', famous for wildflowers and the Himalayan brown bear.",
        "best_season": "June to September", "recommended_days": 2,
        "estimated_budget_per_day": 7500, "activities": "camping,wildlife,photography",
        "category": "nature", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Fairy Meadows", "province": "Gilgit-Baltistan", "district": "Diamer",
        "latitude": 35.3667, "longitude": 74.5833,
        "description": "Grassy meadow with a direct view of Nanga Parbat, reached by jeep and a hiking trail.",
        "best_season": "June to September", "recommended_days": 2,
        "estimated_budget_per_day": 7000, "activities": "trekking,camping,photography",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },
    {
        "name": "Khunjerab Pass", "province": "Gilgit-Baltistan", "district": "Hunza",
        "latitude": 36.8500, "longitude": 75.4167,
        "description": "World's highest paved international border crossing, on the Pakistan-China frontier.",
        "best_season": "May to October (closed in winter)", "recommended_days": 1,
        "estimated_budget_per_day": 6000, "activities": "sightseeing,photography,wildlife (Marco Polo sheep)",
        "category": "mountains", "data_source": "General knowledge — needs verification against Google Maps",
    },

    # --- Islamabad Capital Territory ---
    {
        "name": "Daman-e-Koh", "province": "Islamabad Capital Territory", "district": "Islamabad",
        "latitude": 33.7459, "longitude": 73.0498,
        "description": "Viewpoint in the Margalla Hills overlooking Islamabad, popular for hiking and evening views.",
        "best_season": "Year-round", "recommended_days": 1,
        "estimated_budget_per_day": 2000, "activities": "hiking,sightseeing,photography",
        "category": "nature", "data_source": "General knowledge — needs verification against Google Maps",
    },
]
