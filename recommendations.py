"""
recommendations.py
==================
Smart, Budget-Aware Recommendations for Hotels, Restaurants, and Shopping Malls.
Automatically filters recommendations according to the user's daily budget:
- Budget Tier (<= 5,000 PKR/day)
- Standard Tier (5,001 - 15,000 PKR/day)
- Luxury Tier (> 15,000 PKR/day)
"""

from typing import List, Dict, Any, Optional

DISTRICT_RECOMMENDATIONS = {
    "hunza": {
        "restaurants": [
            # Budget
            {
                "name": "Hidden Paradise Folk Cafe",
                "cuisine": "Traditional Hunza Cuisine",
                "famous_for": "Affordable Chapshuro, Dawdo Soup & Local Bread",
                "rating": 4.8,
                "price_level": "₨",
                "tier": "budget",
                "area": "Zero Point, Karimabad",
            },
            {
                "name": "Old Hunza Dhaba & Tea House",
                "cuisine": "Local Snacks & Chai",
                "famous_for": "Fresh Namkeen Chai, Boiled Eggs & Parathas",
                "rating": 4.5,
                "price_level": "₨",
                "tier": "budget",
                "area": "Ganish Village Chowk",
            },
            # Standard
            {
                "name": "Cafe de Hunza",
                "cuisine": "Cafe & Bakery",
                "famous_for": "World-famous Walnut Cake & Fresh Herbal Teas",
                "rating": 4.8,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Karimabad Bazaar, Hunza",
            },
            {
                "name": "Rakaposhi View Restaurant",
                "cuisine": "Pakistani & Trout",
                "famous_for": "River Trout with Panoramic Mountain Views",
                "rating": 4.6,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Ghulmet, Nagar / Hunza Highway",
            },
            # Luxury
            {
                "name": "Yak Grill Passu",
                "cuisine": "Premium BBQ & Steaks",
                "famous_for": "Organic Yak Meat Steaks & High-altitude Dining",
                "rating": 4.8,
                "price_level": "₨₨₨",
                "tier": "luxury",
                "area": "Passu, Upper Hunza",
            },
        ],
        "hotels": [
            # Budget (Rs. 3,500 - 6,500)
            {
                "name": "Hunza View Guest House",
                "type": "Budget Tourist Lodge",
                "price_per_night": "₨ 4,500 - 6,000",
                "tier": "budget",
                "rating": 4.4,
                "amenities": ["Clean Rooms", "Hot Water", "Mountain View Terrace"],
                "area": "Aliabad, Hunza",
            },
            {
                "name": "Passu Peak Inn",
                "type": "Economy Family Lodge",
                "price_per_night": "₨ 5,000 - 6,500",
                "tier": "budget",
                "rating": 4.3,
                "amenities": ["Free Parking", "Lawn", "Home-cooked Food"],
                "area": "Passu Village",
            },
            # Standard (Rs. 8,000 - 15,000)
            {
                "name": "Darbar Hotel Hunza",
                "type": "3-Star Heritage Hotel",
                "price_per_night": "₨ 11,000 - 14,000",
                "tier": "standard",
                "rating": 4.5,
                "amenities": ["Central Location", "WiFi", "Restaurant", "Heating"],
                "area": "Karimabad, Hunza",
            },
            {
                "name": "Eagle's Nest Hotel",
                "type": "Panoramic View Resort",
                "price_per_night": "₨ 14,000 - 16,000",
                "tier": "standard",
                "rating": 4.7,
                "amenities": ["Sunset Point", "Mountain Panorama", "Terrace Cafe"],
                "area": "Duikar (Highest Viewpoint)",
            },
            # Luxury (Rs. 25,000+)
            {
                "name": "Hunza Serena Inn",
                "type": "5-Star Luxury Mountain Resort",
                "price_per_night": "₨ 28,000+",
                "tier": "luxury",
                "rating": 4.8,
                "amenities": ["Baltit Fort Views", "Buffet Breakfast", "Fine Dining", "Heated Suites"],
                "area": "Karimabad, Hunza",
            },
            {
                "name": "Luxus Grand Attabad Lake Resort",
                "type": "Ultra-Luxury Lakefront Chalets",
                "price_per_night": "₨ 35,000+",
                "tier": "luxury",
                "rating": 4.9,
                "amenities": ["Direct Lake Front", "Private Balconies", "Boating Dock"],
                "area": "Attabad Lake, Hunza",
            },
        ],
        "shopping_malls": [
            {
                "name": "Karimabad Heritage Bazaar",
                "type": "Traditional Handicraft & Gemstone Market",
                "famous_for": "Authentic Hunza Gemstones (Rubies, Emeralds), Handmade Rugs & Walnut Wood Crafts",
                "rating": 4.8,
                "area": "Main Bazaar, Karimabad, Hunza",
            },
            {
                "name": "Hunza Cultural Craft Center",
                "type": "Women's Artisan Guild & Souvenirs",
                "famous_for": "Hand-embroidered Shawls, Traditional Hunza Caps & Pure Mountain Honey",
                "rating": 4.9,
                "area": "Aliabad / Karimabad, Hunza",
            },
            {
                "name": "Passu Dry Fruit Market",
                "type": "Organic Dry Fruit Market",
                "famous_for": "Fresh Sun-dried Apricots, Walnuts, Almonds & Mountain Herbs",
                "rating": 4.7,
                "area": "Passu, Upper Hunza",
            },
        ],
    },

    "mansehra": {  # Covers Naran, Kaghan, Shogran, Saif-ul-Malook
        "restaurants": [
            # Budget
            {
                "name": "Saif-ul-Malook Lakeside Dhabas",
                "cuisine": "Local Tea & Snacks",
                "famous_for": "Steaming Karak Chai, Crispy Pakoras & Fresh Omelettes",
                "rating": 4.6,
                "price_level": "₨",
                "tier": "budget",
                "area": "Lake Saif-ul-Malook Shore",
            },
            {
                "name": "Madina Hotel & Shinwari Balakot",
                "cuisine": "Local Desi Food",
                "famous_for": "Daal Mash, Mutton Karahi & Roti",
                "rating": 4.4,
                "price_level": "₨",
                "tier": "budget",
                "area": "Main Balakot Bazaar",
            },
            # Standard
            {
                "name": "Moon Restaurant Naran",
                "cuisine": "Trout Fish & Desi BBQ",
                "famous_for": "Fresh Kunhar River Fried Trout & Mutton Karahi",
                "rating": 4.8,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Main Bazaar, Naran",
            },
            {
                "name": "Pine Restaurant Kaghan",
                "cuisine": "Pakistani & BBQ",
                "famous_for": "Chicken Handi & Fresh Tandoori Naan",
                "rating": 4.5,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Main Kaghan Road",
            },
            # Luxury
            {
                "name": "Arcadian Riverside Fine Dining",
                "cuisine": "Continental & Trout",
                "famous_for": "Executive Riverside Grilled Trout & Steaks",
                "rating": 4.7,
                "price_level": "₨₨₨",
                "tier": "luxury",
                "area": "Khanian, Kaghan Valley",
            },
        ],
        "hotels": [
            # Budget (Rs. 4,000 - 7,000)
            {
                "name": "Kunhar View Guest House",
                "type": "Budget Riverside Stay",
                "price_per_night": "₨ 4,500 - 6,500",
                "tier": "budget",
                "rating": 4.3,
                "amenities": ["Riverside Lawn", "Hot Water", "Budget Friendly"],
                "area": "Balakot / Kaghan Road",
            },
            {
                "name": "Al-Saeed Hotel Naran",
                "type": "Economy Family Hotel",
                "price_per_night": "₨ 5,500 - 7,000",
                "tier": "budget",
                "rating": 4.2,
                "amenities": ["Bazaar Proximity", "Free Parking", "Room Service"],
                "area": "Main Bazaar, Naran",
            },
            # Standard (Rs. 9,000 - 15,000)
            {
                "name": "Pine Top Hotel Naran",
                "type": "3-Star Scenic Hotel",
                "price_per_night": "₨ 11,000 - 14,000",
                "tier": "standard",
                "rating": 4.5,
                "amenities": ["Mountain Views", "Heating", "Family Suites", "Restaurant"],
                "area": "Naran Valley",
            },
            {
                "name": "The Millennium Hotel Naran",
                "type": "Riverfront Family Hotel",
                "price_per_night": "₨ 14,000 - 16,000",
                "tier": "standard",
                "rating": 4.6,
                "amenities": ["River View", "Hot Water 24/7", "Power Backup"],
                "area": "Main Naran Road",
            },
            # Luxury (Rs. 22,000+)
            {
                "name": "Arcadian Sprucewoods Resort",
                "type": "Luxury Pine Chalets",
                "price_per_night": "₨ 24,000+",
                "tier": "luxury",
                "rating": 4.8,
                "amenities": ["Alpine Pine Forest", "Bonfire Area", "Fine Dining", "Luxury Chalets"],
                "area": "Shogran Plateau",
            },
        ],
        "shopping_malls": [
            {
                "name": "Naran Main Tourist Bazaar",
                "type": "Tourist Souvenir Market",
                "famous_for": "Hand-woven Woolen Shawls, Mountain Walking Sticks, Dry Fruits & Jackets",
                "rating": 4.6,
                "area": "Main Bazaar, Naran",
            },
            {
                "name": "Kaghan Valley Handicrafts Emporium",
                "type": "Traditional Textile Store",
                "famous_for": "Hand-embroidered Chaddars, Pure Honey & Handmade Wood Carvings",
                "rating": 4.7,
                "area": "Main Road, Kaghan / Balakot",
            },
        ],
    },

    "lahore": {
        "restaurants": [
            # Budget
            {
                "name": "Waris Nihari House",
                "cuisine": "Traditional Lahori Breakfast",
                "famous_for": "Rich Nalli Nihari with Fresh Roghani Naan",
                "rating": 4.9,
                "price_level": "₨",
                "tier": "budget",
                "area": "Anarkali Bazaar, Lahore",
            },
            {
                "name": "Fiqah ki Lassi & Gawalmandi Nashta",
                "cuisine": "Historic Street Nashta",
                "famous_for": "Paira Lassi, Crispy Poori Chana & Halwa",
                "rating": 4.7,
                "price_level": "₨",
                "tier": "budget",
                "area": "Gawalmandi, Lahore",
            },
            # Standard
            {
                "name": "Butt Karahi Lakshmi Chowk",
                "cuisine": "Authentic Desi Karahi",
                "famous_for": "Legendary Desi Ghee Mutton & Chicken Karahi",
                "rating": 4.8,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Lakshmi Chowk, Lahore",
            },
            {
                "name": "Haveli Restaurant (Fort View)",
                "cuisine": "Mughlai & Pakistani",
                "famous_for": "Rooftop Views of Badshahi Mosque & Handi",
                "rating": 4.9,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Food Street, Fort Road, Walled City",
            },
            # Luxury
            {
                "name": "Andaaz Restaurant",
                "cuisine": "Royal Fine Dining",
                "famous_for": "Historic Heritage Rooftop Fine Dining overlooking Badshahi Mosque",
                "rating": 4.8,
                "price_level": "₨₨₨",
                "tier": "luxury",
                "area": "Fort Road Food Street",
            },
        ],
        "hotels": [
            # Budget (Rs. 3,500 - 6,000)
            {
                "name": "Heritage Haveli Tourist Inn",
                "type": "Budget Heritage Stay",
                "price_per_night": "₨ 4,500 - 6,000",
                "tier": "budget",
                "rating": 4.3,
                "amenities": ["Old City Walking Tours", "AC Rooms", "Free WiFi"],
                "area": "Walled City, Lahore",
            },
            {
                "name": "Hotel Gulberg Grand Inn",
                "type": "Economy City Hotel",
                "price_per_night": "₨ 5,000 - 7,000",
                "tier": "budget",
                "rating": 4.2,
                "amenities": ["Near Liberty Market", "Clean Rooms", "24/7 Desk"],
                "area": "Gulberg III, Lahore",
            },
            # Standard (Rs. 8,000 - 15,000)
            {
                "name": "Hotel One Gulberg",
                "type": "3-Star Quality City Hotel",
                "price_per_night": "₨ 11,000 - 14,000",
                "tier": "standard",
                "rating": 4.5,
                "amenities": ["Free Breakfast", "Prime Location", "Gym", "WiFi"],
                "area": "Ali Zeb Road, Gulberg",
            },
            {
                "name": "Luxus Grand Hotel",
                "type": "4-Star Modern Hotel",
                "price_per_night": "₨ 14,000 - 18,000",
                "tier": "standard",
                "rating": 4.7,
                "amenities": ["Indoor Pool", "Free Buffet Breakfast", "Suites"],
                "area": "Egerton Road, Lahore",
            },
            # Luxury (Rs. 25,000+)
            {
                "name": "Pearl Continental Hotel Lahore",
                "type": "5-Star Grand Luxury Hotel",
                "price_per_night": "₨ 26,000+",
                "tier": "luxury",
                "rating": 4.7,
                "amenities": ["Outdoor Pool", "Multiple Fine Dining", "Health Spa", "Executive Suites"],
                "area": "Mall Road, Lahore",
            },
        ],
        "shopping_malls": [
            {
                "name": "Packages Mall Lahore",
                "type": "Mega Shopping Mall",
                "famous_for": "200+ International Brands, Cinepax IMAX & Food Court",
                "rating": 4.8,
                "area": "Walton Road, DHA / Gulberg",
            },
            {
                "name": "Emporium Mall by Nishat",
                "type": "Luxury Multiplex Mall",
                "famous_for": "Universal Cinemas, Ice Rink & Dining Boulevard",
                "rating": 4.8,
                "area": "Johar Town, Lahore",
            },
            {
                "name": "Anarkali Bazaar & Liberty Market",
                "type": "Historic Bargain Bazaar",
                "famous_for": "Silks, Bridal Wear, Khussas & Handcrafted Jewelry",
                "rating": 4.7,
                "area": "Mall Road & Gulberg, Lahore",
            },
        ],
    },

    "swat": {
        "restaurants": [
            # Budget
            {
                "name": "Mingora Chappli Kabab Corner",
                "cuisine": "Pashtun Street Food",
                "famous_for": "Juicy Swati Chappli Kababs with hot Naan & Green Tea",
                "rating": 4.7,
                "price_level": "₨",
                "tier": "budget",
                "area": "New Road, Mingora",
            },
            {
                "name": "Kalam Riverside Dhabas",
                "cuisine": "Local Desi & Tea",
                "famous_for": "Hot Karak Chai, BBQ & Dal Mash by the river",
                "rating": 4.5,
                "price_level": "₨",
                "tier": "budget",
                "area": "Ushu Forest Road, Kalam",
            },
            # Standard
            {
                "name": "Swat Trout Fish Park",
                "cuisine": "Fresh River Seafood",
                "famous_for": "Live caught crispy fried Swat River Trout Fish",
                "rating": 4.8,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Charbagh, Swat Valley",
            },
            {
                "name": "Shinwari Dera Swat",
                "cuisine": "Pashtun BBQ & Karahi",
                "famous_for": "Namkeen Mutton, Dum Pukht & Tikka",
                "rating": 4.7,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Main Mingora Road",
            },
            # Luxury
            {
                "name": "Marco Polo Restaurant Malam Jabba",
                "cuisine": "Continental & Fine Desi",
                "famous_for": "Luxury dining with snow-clad ski slope views",
                "rating": 4.8,
                "price_level": "₨₨₨",
                "tier": "luxury",
                "area": "PC Malam Jabba Resort",
            },
        ],
        "hotels": [
            # Budget (Rs. 3,500 - 6,500)
            {
                "name": "Rock City View Inn",
                "type": "Budget Family Inn",
                "price_per_night": "₨ 4,000 - 6,000",
                "tier": "budget",
                "rating": 4.3,
                "amenities": ["River View", "Hot Water", "Home-style Food"],
                "area": "Fizagat, Swat",
            },
            {
                "name": "Kalam Green Pine Lodge",
                "type": "Economy Wooden Hotel",
                "price_per_night": "₨ 5,000 - 7,000",
                "tier": "budget",
                "rating": 4.2,
                "amenities": ["Pine Forest Walk", "Budget Rooms", "Campfire"],
                "area": "Main Kalam Valley",
            },
            # Standard (Rs. 8,000 - 15,000)
            {
                "name": "Swat Serena Hotel",
                "type": "Historic Colonial Garden Resort",
                "price_per_night": "₨ 15,000 - 18,000",
                "tier": "standard",
                "rating": 4.7,
                "amenities": ["Heritage Gardens", "Tennis Court", "Restaurant"],
                "area": "Saidu Sharif, Swat",
            },
            {
                "name": "Greens Hotel Kalam",
                "type": "3-Star Wooden Hotel",
                "price_per_night": "₨ 10,000 - 13,000",
                "tier": "standard",
                "rating": 4.5,
                "amenities": ["Riverfront", "Wooden Family Suites", "Dining"],
                "area": "Main Kalam Bazaar",
            },
            # Luxury (Rs. 25,000+)
            {
                "name": "Pearl Continental Malam Jabba",
                "type": "5-Star Ski Resort",
                "price_per_night": "₨ 32,000+",
                "tier": "luxury",
                "rating": 4.8,
                "amenities": ["Ski Slope Access", "Chairlift View", "Heated Luxury Rooms"],
                "area": "Malam Jabba Ski Resort",
            },
        ],
        "shopping_malls": [
            {
                "name": "Mingora Central Bazaar",
                "type": "Emerald & Textile Market",
                "famous_for": "Swati Embroidered Shawls, Swat Emeralds & Pure Mountain Honey",
                "rating": 4.8,
                "area": "Main Bazaar, Mingora",
            },
            {
                "name": "Bahrain Riverside Handicraft Market",
                "type": "Woodwork & Crafts",
                "famous_for": "Carved Walnut Furniture, Hand-loomed Blankets & Tribal Jewelry",
                "rating": 4.7,
                "area": "Bahrain, Swat",
            },
        ],
    },

    "islamabad": {
        "restaurants": [
            # Budget
            {
                "name": "Savour Foods Blue Area",
                "cuisine": "Traditional Rice & Chicken Roast",
                "famous_for": "Famous Crispy Shami Pulao with Roast Chicken",
                "rating": 4.8,
                "price_level": "₨",
                "tier": "budget",
                "area": "Blue Area, Islamabad",
            },
            {
                "name": "Cheema & Chattha F-11",
                "cuisine": "Desi Breakfast & Karahi",
                "famous_for": "Puri Chana, Halwa, Paye & Makhni Handi",
                "rating": 4.6,
                "price_level": "₨",
                "tier": "budget",
                "area": "F-11 Markaz, Islamabad",
            },
            # Standard
            {
                "name": "Kabul Restaurant F-7",
                "cuisine": "Authentic Afghan Cuisine",
                "famous_for": "Kabuli Pulao, Chapli Kabab & Lamb Tikka",
                "rating": 4.8,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Jinnah Super, F-7 Markaz",
            },
            {
                "name": "Monal Restaurant Margalla Hills",
                "cuisine": "Pakistani & BBQ",
                "famous_for": "Iconic Panoramic View of the entire Capital City",
                "rating": 4.7,
                "price_level": "₨₨",
                "tier": "standard",
                "area": "Pir Sohawa Road, Margalla Hills",
            },
            # Luxury
            {
                "name": "Wild Rice Restaurant (Serena)",
                "cuisine": "Fine Dining Pan-Asian",
                "famous_for": "Exquisite Thai, Indonesian & Japanese Delicacies",
                "rating": 4.9,
                "price_level": "₨₨₨",
                "tier": "luxury",
                "area": "Serena Hotel, Islamabad",
            },
        ],
        "hotels": [
            # Budget (Rs. 4,000 - 7,000)
            {
                "name": "G-9 Tourist Executive Inn",
                "type": "Economy City Guest House",
                "price_per_night": "₨ 4,500 - 6,500",
                "tier": "budget",
                "rating": 4.3,
                "amenities": ["Metro Bus Access", "WiFi", "AC Rooms"],
                "area": "Sector G-9, Islamabad",
            },
            {
                "name": "Islamabad Residency Inn",
                "type": "Budget Comfort Stay",
                "price_per_night": "₨ 5,500 - 7,500",
                "tier": "budget",
                "rating": 4.2,
                "amenities": ["Free Breakfast", "Parking", "Clean Rooms"],
                "area": "Sector F-10, Islamabad",
            },
            # Standard (Rs. 9,000 - 16,000)
            {
                "name": "Hotel Margala",
                "type": "3-Star Leisure & Business Hotel",
                "price_per_night": "₨ 12,000 - 15,000",
                "tier": "standard",
                "rating": 4.5,
                "amenities": ["Free WiFi", "Gym", "Banquet Hall", "Near Rawal Lake"],
                "area": "Near Rawal Lake, Islamabad",
            },
            {
                "name": "Ramada by Wyndham Islamabad",
                "type": "4-Star Premium Hotel",
                "price_per_night": "₨ 18,000 - 22,000",
                "tier": "standard",
                "rating": 4.6,
                "amenities": ["Lakeview Rooftop Dining", "Pool", "Buffet"],
                "area": "Club Road, Islamabad",
            },
            # Luxury (Rs. 30,000+)
            {
                "name": "Islamabad Serena Hotel",
                "type": "5-Star Palatial Luxury Resort",
                "price_per_night": "₨ 38,000+",
                "tier": "luxury",
                "rating": 4.9,
                "amenities": ["Maisha Spa", "Olympic Pool", "7 Fine Dining Venues", "Diplomatic Security"],
                "area": "Khayaban-e-Suhrawardy, Islamabad",
            },
        ],
        "shopping_malls": [
            {
                "name": "The Centaurus Mall",
                "type": "Iconic Luxury Landmark Mall",
                "famous_for": "4 Floors of Brands, Cinepax Multiplex & International Food Court",
                "rating": 4.8,
                "area": "Jinnah Avenue, Sector F-8",
            },
            {
                "name": "Giga Mall World Trade Center",
                "type": "Mega Shopping & Entertainment Mall",
                "famous_for": "Carrefour, Fun City & Extensive Retail Brands",
                "rating": 4.7,
                "area": "Main GT Road, DHA Phase II",
            },
            {
                "name": "F-7 Jinnah Super & F-6 Super Market",
                "type": "Boutique Craft Hub",
                "famous_for": "Artisan Handicrafts, Brass Antiques, Shawls & Cafes",
                "rating": 4.7,
                "area": "Sector F-7 / F-6",
            },
        ],
    },
}


def get_recommendations_for_destination(
    district: Optional[str] = None,
    province: Optional[str] = None,
    category: Optional[str] = None,
    budget_per_day: Optional[int] = 5000,
) -> Dict[str, Any]:
    """
    Returns recommendations strictly filtered according to budget_per_day:
    - budget (daily budget <= 5,500 PKR)
    - standard (daily budget between 5,501 and 16,000 PKR)
    - luxury (daily budget > 16,000 PKR)
    """
    # 1. Determine User Budget Tier
    bpd = budget_per_day or 5000
    if bpd <= 5500:
        target_tier = "budget"
    elif bpd <= 16000:
        target_tier = "standard"
    else:
        target_tier = "luxury"

    # 2. Resolve District
    key = (district or "").lower().strip()
    data = None

    if key in DISTRICT_RECOMMENDATIONS:
        data = DISTRICT_RECOMMENDATIONS[key]
    elif any(k in key for k in ["naran", "kaghan", "saiful", "shogran", "balakot"]):
        data = DISTRICT_RECOMMENDATIONS.get("mansehra")
    elif any(k in key for k in ["karimabad", "passu", "attabad", "nagar", "aliabad"]):
        data = DISTRICT_RECOMMENDATIONS.get("hunza")
    elif any(k in key for k in ["mingora", "malam", "kalam", "bahrain"]):
        data = DISTRICT_RECOMMENDATIONS.get("swat")
    elif any(k in key for k in ["rawalpindi", "margalla", "murree", "bhurban"]):
        data = DISTRICT_RECOMMENDATIONS.get("islamabad")
    elif any(k in key for k in ["lahore", "walled"]):
        data = DISTRICT_RECOMMENDATIONS.get("lahore")

    # If district found, filter by tier!
    if data:
        all_hotels = data.get("hotels", [])
        all_rest = data.get("restaurants", [])
        malls = data.get("shopping_malls", [])

        # Filter hotels matching tier, fallback to standard or all if none
        matching_hotels = [h for h in all_hotels if h.get("tier") == target_tier]
        if not matching_hotels:
            matching_hotels = [h for h in all_hotels if h.get("tier") in ("standard", "budget")]
        if not matching_hotels:
            matching_hotels = all_hotels

        # Filter restaurants matching tier
        matching_rest = [r for r in all_rest if r.get("tier") == target_tier]
        if not matching_rest:
            matching_rest = [r for r in all_rest if r.get("tier") in ("standard", "budget")]
        if not matching_rest:
            matching_rest = all_rest

        return {
            "tier_selected": target_tier,
            "restaurants": matching_rest,
            "hotels": matching_hotels,
            "shopping_malls": malls,
        }

    # 3. Fallback for any unknown city tailored by budget
    city_name = district.title() if district else "Destination"

    if target_tier == "budget":
        fb_hotels = [
            {
                "name": f"{city_name} Economy Tourist Lodge",
                "type": "Budget Comfort Stay",
                "price_per_night": "₨ 4,000 - 5,500",
                "tier": "budget",
                "rating": 4.2,
                "amenities": ["Clean Beds", "Hot Water", "Budget Friendly"],
                "area": f"Main Road / City Center, {city_name}",
            },
            {
                "name": f"{city_name} Family Guest House",
                "type": "Affordable Guest House",
                "price_per_night": "₨ 3,500 - 5,000",
                "tier": "budget",
                "rating": 4.1,
                "amenities": ["Local Host", "Home Food Available"],
                "area": f"Bazaar Area, {city_name}",
            },
        ]
        fb_restaurants = [
            {
                "name": f"{city_name} Famous Shinwari & Karahi Dhaba",
                "cuisine": "Local Desi Street Food",
                "famous_for": "Fresh Chicken Karahi, Daal & Tandoori Naan",
                "rating": 4.6,
                "price_level": "₨",
                "tier": "budget",
                "area": f"Main Food Street, {city_name}",
            },
            {
                "name": f"{city_name} Chai & Nashta Point",
                "cuisine": "Tea & Snacks",
                "famous_for": "Karak Doodh Patti Chai, Parathas & Omelette",
                "rating": 4.5,
                "price_level": "₨",
                "tier": "budget",
                "area": f"City Bazaar, {city_name}",
            },
        ]
    elif target_tier == "standard":
        fb_hotels = [
            {
                "name": f"Hotel One {city_name} / Grand Inn",
                "type": "3-Star Quality City Hotel",
                "price_per_night": "₨ 10,000 - 13,000",
                "tier": "standard",
                "rating": 4.5,
                "amenities": ["Free Breakfast", "AC", "WiFi", "Room Service"],
                "area": f"Central Tourist Area, {city_name}",
            },
            {
                "name": f"{city_name} Continental Hotel",
                "type": "Mid-Range Family Hotel",
                "price_per_night": "₨ 8,500 - 11,000",
                "tier": "standard",
                "rating": 4.4,
                "amenities": ["Parking", "Restaurant", "Family Rooms"],
                "area": f"Civil Lines, {city_name}",
            },
        ]
        fb_restaurants = [
            {
                "name": f"{city_name} Heritage Family Restaurant",
                "cuisine": "Pakistani & BBQ",
                "famous_for": "Chicken Handi, Mutton Karahi & Seekh Kababs",
                "rating": 4.7,
                "price_level": "₨₨",
                "tier": "standard",
                "area": f"Tourist Boulevard, {city_name}",
            },
        ]
    else:  # Luxury
        fb_hotels = [
            {
                "name": f"Serena / PC Resort {city_name}",
                "type": "5-Star Premier Luxury Stay",
                "price_per_night": "₨ 26,000+",
                "tier": "luxury",
                "rating": 4.8,
                "amenities": ["Swimming Pool", "Spa", "Fine Dining", "VIP Suites"],
                "area": f"Club Road, {city_name}",
            }
        ]
        fb_restaurants = [
            {
                "name": f"{city_name} Rooftop Fine Dining",
                "cuisine": "Continental & Multi-Cuisine",
                "famous_for": "Steaks, Seafood & Premium Panoramic Dining",
                "rating": 4.8,
                "price_level": "₨₨₨",
                "tier": "luxury",
                "area": f"High Point / Clifftop, {city_name}",
            }
        ]

    fb_shopping = [
        {
            "name": f"{city_name} Central Heritage Bazaar & Crafts",
            "type": "Traditional Handicraft Market",
            "famous_for": "Authentic Regional Handicrafts, Shawls & Souvenirs",
            "rating": 4.6,
            "area": f"Main Commercial Area, {city_name}",
        },
        {
            "name": f"{city_name} Shopping Mall",
            "type": "Modern Retail Mall",
            "famous_for": "Clothing Brands, Footwear & Accessories",
            "rating": 4.5,
            "area": f"City Center, {city_name}",
        },
    ]

    return {
        "tier_selected": target_tier,
        "restaurants": fb_restaurants,
        "hotels": fb_hotels,
        "shopping_malls": fb_shopping,
    }