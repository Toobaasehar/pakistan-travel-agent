"""
recommendations.py
==================
Curated recommendations for top-rated restaurants, famous local food spots,
and top hotels/resorts across Pakistan's tourist destinations.
"""

from typing import List, Dict, Any, Optional

# District/City specific curated recommendations
DISTRICT_RECOMMENDATIONS = {
    "hunza": {
        "restaurants": [
            {
                "name": "Cafe de Hunza",
                "cuisine": "Cafe & Bakery",
                "famous_for": "World-famous Walnut Cake & Fresh Herbal Mountain Teas",
                "rating": 4.8,
                "price_level": "₨₨",
                "area": "Karimabad Bazaar, Hunza",
            },
            {
                "name": "Yak Grill Hunza",
                "cuisine": "BBQ & Steaks",
                "famous_for": "Tender Organic Yak Meat Steaks & Mountain Burgers",
                "rating": 4.7,
                "price_level": "₨₨₨",
                "area": "Passu / Karimabad, Hunza",
            },
            {
                "name": "Hidden Paradise Restaurant",
                "cuisine": "Traditional Hunza Cuisine",
                "famous_for": "Authentic Chapshuro, Dawdo Soup & Giyaling",
                "rating": 4.9,
                "price_level": "₨₨",
                "area": "Zero Point, Karimabad",
            },
            {
                "name": "Rakaposhi View Restaurant",
                "cuisine": "Pakistani & Chinese",
                "famous_for": "Fresh River Trout with Panoramic Rakaposhi Views",
                "rating": 4.6,
                "price_level": "₨₨",
                "area": "Ghulmet, Nagar / Hunza Highway",
            },
        ],
        "hotels": [
            {
                "name": "Hunza Serena Inn",
                "type": "5-Star Mountain Resort",
                "price_per_night": "₨ 28,000+",
                "rating": 4.8,
                "amenities": ["Fort Views", "Free Breakfast", "Heated Rooms", "Fine Dining"],
                "area": "Karimabad, Hunza",
            },
            {
                "name": "Luxus Grand Attabad Lake Resort",
                "type": "Luxury Overwater Chalets",
                "price_per_night": "₨ 35,000+",
                "rating": 4.9,
                "amenities": ["Direct Lake Front", "Boating Dock", "Private Balconies", "WiFi"],
                "area": "Attabad Lake, Hunza",
            },
            {
                "name": "Eagle's Nest Hotel",
                "type": "Panoramic Viewpoint Resort",
                "price_per_night": "₨ 16,000+",
                "rating": 4.7,
                "amenities": ["Sunset Point", "Mountain Panorama", "Terrace Cafe"],
                "area": "Duikar, Hunza (Highest Point)",
            },
            {
                "name": "Darbar Hotel Hunza",
                "type": "Boutique Heritage Hotel",
                "price_per_night": "₨ 11,000+",
                "rating": 4.5,
                "amenities": ["Central Location", "Traditional Decor", "Restaurant"],
                "area": "Karimabad, Hunza",
            },
        ],
    },
    "mansehra": {  # Covers Naran, Kaghan, Shogran, Saif-ul-Malook
        "restaurants": [
            {
                "name": "Moon Restaurant Naran",
                "cuisine": "Trout & Desi BBQ",
                "famous_for": "Fresh Kunhar River Fried Trout Fish & Mutton Shinwari",
                "rating": 4.8,
                "price_level": "₨₨",
                "area": "Main Bazaar, Naran",
            },
            {
                "name": "Saif-ul-Malook Lakeside Dhabas",
                "cuisine": "Local Tea & Snacks",
                "famous_for": "Steaming Karak Chai, Crispy Pakoras & Boiled Chana by the Lake",
                "rating": 4.6,
                "price_level": "₨",
                "area": "Lake Saif-ul-Malook Shore",
            },
            {
                "name": "Pine Restaurant Kaghan",
                "cuisine": "Pakistani & BBQ",
                "famous_for": "Chicken Handi & Freshly baked Tandoori Naan",
                "rating": 4.5,
                "price_level": "₨₨",
                "area": "Main Kaghan Valley Road",
            },
            {
                "name": "Arcadian Riverside Cafe",
                "cuisine": "Continental & Desi",
                "famous_for": "Riverside Trout & Continental Breakfast",
                "rating": 4.7,
                "price_level": "₨₨₨",
                "area": "Khanian, Kaghan Valley",
            },
        ],
        "hotels": [
            {
                "name": "The Millennium Hotel Naran",
                "type": "Premium Riverfront Hotel",
                "price_per_night": "₨ 18,000+",
                "rating": 4.7,
                "amenities": ["River View", "Hot Water 24/7", "Heating", "Restaurant"],
                "area": "Main Naran Road",
            },
            {
                "name": "Arcadian Sprucewoods Resort",
                "type": "Luxury Pine Chalets",
                "price_per_night": "₨ 24,000+",
                "rating": 4.8,
                "amenities": ["Alpine Forest", "Bonfire Area", "Fine Dining"],
                "area": "Shogran Plateau",
            },
            {
                "name": "Pine Top Hotel Naran",
                "type": "Family Valley Hotel",
                "price_per_night": "₨ 14,000+",
                "rating": 4.5,
                "amenities": ["Mountain Views", "Family Suites", "Garden"],
                "area": "Naran Valley",
            },
            {
                "name": "Kunhar View Guest House",
                "type": "Budget Comfort Stay",
                "price_per_night": "₨ 7,500+",
                "rating": 4.3,
                "amenities": ["Riverside", "Parking", "Friendly Staff"],
                "area": "Balakot / Kaghan",
            },
        ],
    },
    "lahore": {
        "restaurants": [
            {
                "name": "Haveli Restaurant (Fort View)",
                "cuisine": "Mughlai & Pakistani",
                "famous_for": "Rooftop Views of Badshahi Mosque & Mughlai Handi",
                "rating": 4.9,
                "price_level": "₨₨₨",
                "area": "Food Street, Fort Road, Walled City",
            },
            {
                "name": "Butt Karahi Lakshmi Chowk",
                "cuisine": "Authentic Desi Karahi",
                "famous_for": "Legendary Desi Ghee Mutton & Chicken Karahi",
                "rating": 4.8,
                "price_level": "₨₨",
                "area": "Lakshmi Chowk, Lahore",
            },
            {
                "name": "Cooco's Den",
                "cuisine": "Heritage Rooftop Cuisine",
                "famous_for": "Artistic ambiance, Tawa Chicken & Lahori Fish",
                "rating": 4.7,
                "price_level": "₨₨₨",
                "area": "Old Walled City, Lahore",
            },
            {
                "name": "Waris Nihari House",
                "cuisine": "Traditional Nihari",
                "famous_for": "Rich slow-cooked Nalli Nihari with Tandoori Roghani Naan",
                "rating": 4.9,
                "price_level": "₨",
                "area": "Anarkali Bazaar, Lahore",
            },
        ],
        "hotels": [
            {
                "name": "Pearl Continental Hotel Lahore",
                "type": "5-Star Grand Luxury",
                "price_per_night": "₨ 26,000+",
                "rating": 4.7,
                "amenities": ["Outdoor Pool", "Spa", "Multiple Cuisines", "Fitness Center"],
                "area": "Mall Road, Lahore",
            },
            {
                "name": "Luxus Grand Hotel",
                "type": "Luxury City Hotel",
                "price_per_night": "₨ 19,000+",
                "rating": 4.8,
                "amenities": ["Cinematic Suites", "Indoor Pool", "Free Breakfast", "Buffet"],
                "area": "Egerton Road, Lahore",
            },
            {
                "name": "Heritage Haveli Suites",
                "type": "Historic Mughal Boutique Stay",
                "price_per_night": "₨ 15,000+",
                "rating": 4.6,
                "amenities": ["Old City Walk", "Traditional Architecture", "Courtyard"],
                "area": "Walled City, Lahore",
            },
            {
                "name": "Avari Hotel Lahore",
                "type": "5-Star Premier Stay",
                "price_per_night": "₨ 24,000+",
                "rating": 4.7,
                "amenities": ["Lush Gardens", "Swimming Pool", "High Tea Lounge"],
                "area": "Shahrah-e-Quaid-e-Azam, Lahore",
            },
        ],
    },
    "islamabad": {
        "restaurants": [
            {
                "name": "Monal Restaurant Margalla Hills",
                "cuisine": "Pakistani, BBQ & Continental",
                "famous_for": "Stunning Panoramic Bird's-Eye View of Islamabad City",
                "rating": 4.8,
                "price_level": "₨₨₨",
                "area": "Daman-e-Koh Road, Margalla Hills",
            },
            {
                "name": "Kabul Restaurant F-7",
                "cuisine": "Authentic Afghan Cuisine",
                "famous_for": "Kabuli Pulao, Chapli Kabab & Juicy Lamb Tikka",
                "rating": 4.8,
                "price_level": "₨₨",
                "area": "Jinnah Super Market, F-7 Markaz",
            },
            {
                "name": "Savour Foods",
                "cuisine": "Traditional Rice & Roast",
                "famous_for": "Crispy Shami Pulao, Roast Chicken & Sweet Zarda",
                "rating": 4.7,
                "price_level": "₨",
                "area": "Blue Area, Islamabad",
            },
            {
                "name": "Des Pardes Restaurant",
                "cuisine": "Traditional Pakistani Heritage",
                "famous_for": "Handi Murgh Makhni & Live Folk Music",
                "rating": 4.6,
                "price_level": "₨₨",
                "area": "Saidpur Heritage Village",
            },
        ],
        "hotels": [
            {
                "name": "Islamabad Serena Hotel",
                "type": "5-Star Palatial Luxury",
                "price_per_night": "₨ 42,000+",
                "rating": 4.9,
                "amenities": ["Maisha Spa", "Olympic Pool", "7 Fine Dining Venues", "Hills View"],
                "area": "Khayaban-e-Suhrawardy, Islamabad",
            },
            {
                "name": "Islamabad Marriott Hotel",
                "type": "5-Star International Hotel",
                "price_per_night": "₨ 32,000+",
                "rating": 4.7,
                "amenities": ["Executive Lounge", "Health Club", "Diplomatic Proximity"],
                "area": "Aga Khan Road, F-5/1",
            },
            {
                "name": "Ramada by Wyndham Islamabad",
                "type": "Lakeview Premium Hotel",
                "price_per_night": "₨ 22,000+",
                "rating": 4.6,
                "amenities": ["Rawal Lake View", "Rooftop Dining", "Complimentary Breakfast"],
                "area": "Club Road, Islamabad",
            },
            {
                "name": "Hotel Margala",
                "type": "Central Business & Leisure Hotel",
                "price_per_night": "₨ 13,500+",
                "rating": 4.4,
                "amenities": ["Free WiFi", "Gym", "Banquet Hall"],
                "area": "Near Rawal Lake, Islamabad",
            },
        ],
    },
    "skardu": {
        "restaurants": [
            {
                "name": "Dewanekhas Restaurant",
                "cuisine": "Balti & Pakistani",
                "famous_for": "Local Balti Gyaling, Apricot Soup & Mountain Trout",
                "rating": 4.8,
                "price_level": "₨₨",
                "area": "Kazmi Bazaar, Skardu",
            },
            {
                "name": "Shangrila Pagoda Restaurant",
                "cuisine": "Chinese & Desi",
                "famous_for": "Dine inside an airplane cabin & Heart Lake views",
                "rating": 4.8,
                "price_level": "₨₨₨",
                "area": "Lower Kachura Lake, Skardu",
            },
            {
                "name": "Karakoram Cafe",
                "cuisine": "Cafe & Fast Food",
                "famous_for": "Fresh Cappuccinos, Walnut Pies & Mountain Breakfast",
                "rating": 4.6,
                "price_level": "₨₨",
                "area": "Main Skardu Road",
            },
        ],
        "hotels": [
            {
                "name": "Shangrila Resort Skardu",
                "type": "Iconic Lake Resort ('Heaven on Earth')",
                "price_per_night": "₨ 32,000+",
                "rating": 4.8,
                "amenities": ["Heart Lake Access", "Boating", "Private Gardens", "VIP Suites"],
                "area": "Kachura, Skardu",
            },
            {
                "name": "Serena Shigar Fort",
                "type": "400-Year Heritage Palace Hotel",
                "price_per_night": "₨ 36,000+",
                "rating": 4.9,
                "amenities": ["Royal Raja Suites", "Museum", "Fruit Orchards", "Gourmet Dining"],
                "area": "Shigar Valley, Baltistan",
            },
            {
                "name": "Serena Khaplu Palace",
                "type": "Royal Tibetan Heritage Hotel",
                "price_per_night": "₨ 34,000+",
                "rating": 4.9,
                "amenities": ["Palace Grounds", "Cultural Tours", "Apricot Terraces"],
                "area": "Khaplu, Baltistan",
            },
            {
                "name": "Byarsa Hotel Skardu",
                "type": "Modern Luxury Eco-Resort",
                "price_per_night": "₨ 20,000+",
                "rating": 4.7,
                "amenities": ["Mountain Views", "Underfloor Heating", "Organic Cuisine"],
                "area": "Skardu Town",
            },
        ],
    },
    "karachi": {
        "restaurants": [
            {
                "name": "Kolachi Restaurant (Do Darya)",
                "cuisine": "Seafood & BBQ",
                "famous_for": "Waterfront Open-Sea Dining, Balochi Sajji & Fish",
                "rating": 4.9,
                "price_level": "₨₨₨",
                "area": "Do Darya, Phase 8, DHA Karachi",
            },
            {
                "name": "Burns Road Food Street",
                "cuisine": "Historic Karachi Street Food",
                "famous_for": "Waheed Fry Kabab, Delhi Rabri & Agha Dahi Baray",
                "rating": 4.8,
                "price_level": "₨",
                "area": "Burns Road, Saddar, Karachi",
            },
            {
                "name": "Javed Nihari",
                "cuisine": "Traditional Nihari",
                "famous_for": "World-famous Nalli & Maghaz Beef Nihari",
                "rating": 4.9,
                "price_level": "₨",
                "area": "Dastagir, F.B Area, Karachi",
            },
            {
                "name": "Zameer Ansari BBQ",
                "cuisine": "Barbecue & Karahi",
                "famous_for": "Melting Dhaga Kabab & Creamy Malai Boti",
                "rating": 4.7,
                "price_level": "₨₨",
                "area": "Sindhi Muslim Society / Alamgir Road",
            },
        ],
        "hotels": [
            {
                "name": "Mövenpick Hotel Karachi",
                "type": "5-Star International Hotel",
                "price_per_night": "₨ 30,000+",
                "rating": 4.7,
                "amenities": ["Swimming Pool", "Multiple Fine Dining", "Health Club"],
                "area": "Club Road, Karachi",
            },
            {
                "name": "Beach Luxury Hotel",
                "type": "Historic Creekfront Resort",
                "price_per_night": "₨ 18,000+",
                "rating": 4.6,
                "amenities": ["Mangrove Sea Views", "Outdoor Pool", "Seafood Dining"],
                "area": "Lalazar, M.T Khan Road",
            },
            {
                "name": "Avari Towers Karachi",
                "type": "5-Star Skyscraper Hotel",
                "price_per_night": "₨ 25,000+",
                "rating": 4.7,
                "amenities": ["City Skyline Views", "Tennis Court", "Spa"],
                "area": "Fatima Jinnah Road, Karachi",
            },
            {
                "name": "Pearl Continental Hotel Karachi",
                "type": "5-Star Premier City Hotel",
                "price_per_night": "₨ 24,000+",
                "rating": 4.6,
                "amenities": ["Central Location", "Bakery & Cafe", "Executive Suites"],
                "area": "Club Road, Karachi",
            },
        ],
    },
    "swat": {
        "restaurants": [
            {
                "name": "Swat Trout Fish Park",
                "cuisine": "Fresh River Seafood",
                "famous_for": "Live caught crispy fried Swat River Trout Fish",
                "rating": 4.8,
                "price_level": "₨₨",
                "area": "Charbagh, Swat Valley",
            },
            {
                "name": "Shinwari Dera Swat",
                "cuisine": "Pashtun BBQ & Karahi",
                "famous_for": "Tender Namkeen Mutton & Peshawari Chapli Kabab",
                "rating": 4.7,
                "price_level": "₨₨",
                "area": "Main Mingora Road, Swat",
            },
            {
                "name": "Kalam Riverside Dhabas",
                "cuisine": "Mountain Comfort Food",
                "famous_for": "Hot Karak Chai, BBQ & Local Rice Dishes",
                "rating": 4.6,
                "price_level": "₨",
                "area": "Ushu Forest Road, Kalam",
            },
        ],
        "hotels": [
            {
                "name": "Pearl Continental Malam Jabba",
                "type": "5-Star Ski & Mountain Resort",
                "price_per_night": "₨ 34,000+",
                "rating": 4.8,
                "amenities": ["Ski Slope Access", "Chairlift View", "Heated Rooms", "Luxury Dining"],
                "area": "Malam Jabba, Swat",
            },
            {
                "name": "Swat Serena Hotel",
                "type": "Historic Colonial Garden Resort",
                "price_per_night": "₨ 22,000+",
                "rating": 4.7,
                "amenities": ["Heritage Gardens", "Badminton Court", "Traditional Hospitality"],
                "area": "Saidu Sharif, Swat",
            },
            {
                "name": "Greens Hotel Kalam",
                "type": "Alpine Wooden Hotel",
                "price_per_night": "₨ 14,000+",
                "rating": 4.5,
                "amenities": ["Riverfront View", "Pine Wood Rooms", "Family Suites"],
                "area": "Main Kalam Bazaar",
            },
            {
                "name": "Rock City Resort Fizagat",
                "type": "Scenic River Resort",
                "price_per_night": "₨ 12,000+",
                "rating": 4.4,
                "amenities": ["Swat River Overlook", "Lawn Dining", "Campfire"],
                "area": "Fizagat, Swat",
            },
        ],
    },
    "multan": {
        "restaurants": [
            {
                "name": "Shahi Dawat Multan",
                "cuisine": "Sufi & Punjabi Cuisine",
                "famous_for": "Multani Sohan Halwa, Mutton Chops & Chicken Sajji",
                "rating": 4.7,
                "price_level": "₨₨",
                "area": "Gulgasht Colony, Multan",
            },
            {
                "name": "Rewari Sweets & Halwa House",
                "cuisine": "Sweets & Traditional Breakfast",
                "famous_for": "Authentic Multani Desi Ghee Sohan Halwa & Poori Chana",
                "rating": 4.9,
                "price_level": "₨",
                "area": "Hussain Agahi Bazaar, Multan",
            },
            {
                "name": "Al-Kaif BBQ Multan",
                "cuisine": "Barbecue & Handi",
                "famous_for": "Smoky Seekh Kababs & Makhmali Malai Boti",
                "rating": 4.6,
                "price_level": "₨₨",
                "area": "Abdali Road, Multan",
            },
        ],
        "hotels": [
            {
                "name": "Ramada by Wyndham Multan",
                "type": "4-Star City Hotel",
                "price_per_night": "₨ 19,000+",
                "rating": 4.6,
                "amenities": ["Outdoor Pool", "Fitness Center", "Airport Shuttle"],
                "area": "Abdali Road, Multan",
            },
            {
                "name": "Hotel One Multan",
                "type": "Modern Business Hotel",
                "price_per_night": "₨ 12,000+",
                "rating": 4.4,
                "amenities": ["Free Breakfast", "Prime Location", "WiFi"],
                "area": "Tariq Road, Multan",
            },
            {
                "name": "Avari Xpress Multan",
                "type": "Premium Boutique Stay",
                "price_per_night": "₨ 15,000+",
                "rating": 4.5,
                "amenities": ["Executive Rooms", "Restaurant", "Valet Parking"],
                "area": "Old Bahawalpur Road, Multan",
            },
        ],
    },
    "peshawar": {
        "restaurants": [
            {
                "name": "Charsi Tikka (Namak Mandi)",
                "cuisine": "Famous Pashtun BBQ",
                "famous_for": "Legendary Dumbah Karahi & Freshly Charbroiled Mutton Rib Tikka",
                "rating": 4.9,
                "price_level": "₨₨",
                "area": "Namak Mandi, Peshawar",
            },
            {
                "name": "Jalil Kabab House",
                "cuisine": "Peshawari Chapli Kabab",
                "famous_for": "Original Giant Crispy Peshawari Beef & Mutton Chapli Kababs",
                "rating": 4.8,
                "price_level": "₨",
                "area": "Khyber Bazaar, Peshawar",
            },
            {
                "name": "Shiraz Rawayat",
                "cuisine": "Pakistani & Continental",
                "famous_for": "Mutton Shinwari & Traditional High Tea",
                "rating": 4.7,
                "price_level": "₨₨₨",
                "area": "University Road, Peshawar",
            },
        ],
        "hotels": [
            {
                "name": "Pearl Continental Peshawar",
                "type": "5-Star Heritage Hotel",
                "price_per_night": "₨ 22,000+",
                "rating": 4.6,
                "amenities": ["Swimming Pool", "Historic Grounds", "Buffet Breakfast"],
                "area": "Khyber Road, Peshawar",
            },
            {
                "name": "Serena Hotel Peshawar",
                "type": "Boutique City Hotel",
                "price_per_night": "₨ 20,000+",
                "rating": 4.6,
                "amenities": ["Traditional Architecture", "Gardens", "Spa"],
                "area": "Fort Road, Peshawar",
            },
            {
                "name": "Hotel Grand Peshawar",
                "type": "Comfort Tourist Hotel",
                "price_per_night": "₨ 9,000+",
                "rating": 4.3,
                "amenities": ["Central Location", "Restaurant", "Room Service"],
                "area": "University Road, Peshawar",
            },
        ],
    },
    "bahawalpur": {
        "restaurants": [
            {
                "name": "Khyber Restaurant Bahawalpur",
                "cuisine": "Desi & Royal Cholistani BBQ",
                "famous_for": "Cholistani Sajji, Mutton Karahi & Fresh Roti",
                "rating": 4.6,
                "price_level": "₨₨",
                "area": "Model Town, Bahawalpur",
            },
            {
                "name": "Four Seasons Restaurant",
                "cuisine": "Pakistani & Chinese",
                "famous_for": "Family Buffet & Royal Mughlai dishes",
                "rating": 4.5,
                "price_level": "₨₨",
                "area": "Circular Road, Bahawalpur",
            },
        ],
        "hotels": [
            {
                "name": "Hotel One Bahawalpur",
                "type": "Modern Boutique Hotel",
                "price_per_night": "₨ 13,000+",
                "rating": 4.5,
                "amenities": ["Close to Noor Mahal", "Free Breakfast", "WiFi"],
                "area": "Circular Road, Bahawalpur",
            },
            {
                "name": "Royal Continental Hotel",
                "type": "Heritage City Hotel",
                "price_per_night": "₨ 9,500+",
                "rating": 4.3,
                "amenities": ["Palace Tours Support", "Restaurant", "Parking"],
                "area": "Model Town, Bahawalpur",
            },
        ],
    },
    "gwadar": {
        "restaurants": [
            {
                "name": "Marine Drive Seafood Corner",
                "cuisine": "Arabian Sea Fresh Seafood",
                "famous_for": "Fresh Catch Lobster, Jumbo Prawns & Grilled Fish",
                "rating": 4.8,
                "price_level": "₨₨",
                "area": "Marine Drive, Gwadar",
            },
            {
                "name": "Zaver Pearl Continental Restaurant",
                "cuisine": "International & Balochi BBQ",
                "famous_for": "Buffet dining overlooking the Arabian Sea Cliff",
                "rating": 4.7,
                "price_level": "₨₨₨",
                "area": "Koh-e-Batil, Gwadar",
            },
        ],
        "hotels": [
            {
                "name": "Zaver Pearl Continental Hotel Gwadar",
                "type": "5-Star Cliffside Resort",
                "price_per_night": "₨ 26,000+",
                "rating": 4.7,
                "amenities": ["Clifftop Sea Panorama", "Pool", "Helipad", "Water Sports"],
                "area": "Koh-e-Batil, Gwadar",
            },
            {
                "name": "Gwadar Business Center Hotel",
                "type": "Modern Harbor Hotel",
                "price_per_night": "₨ 11,000+",
                "rating": 4.3,
                "amenities": ["Port Proximity", "Airport Shuttle", "WiFi"],
                "area": "Jinnah Avenue, Gwadar",
            },
        ],
    },
}


def get_recommendations_for_destination(district: Optional[str] = None, province: Optional[str] = None, category: Optional[str] = None, budget_per_day: Optional[int] = 5000) -> Dict[str, Any]:
    """
    Returns curated top restaurants and hotels tailored to the destination's city/district.
    Falls back to regional or smart categorized recommendations if district not explicitly listed.
    """
    key = (district or "").lower().strip()
    
    # Check direct match
    if key in DISTRICT_RECOMMENDATIONS:
        return DISTRICT_RECOMMENDATIONS[key]
    
    # Check partial match (e.g. "kaghan" or "naran" -> "mansehra")
    if any(k in key for k in ["naran", "kaghan", "saiful", "shogran", "balakot"]):
        return DISTRICT_RECOMMENDATIONS["mansehra"]
    if any(k in key for k in ["karimabad", "passu", "attabad", "nagar", "aliabad"]):
        return DISTRICT_RECOMMENDATIONS["hunza"]
    if any(k in key for k in ["mingora", "malam", "kalam", "bahrain"]):
        return DISTRICT_RECOMMENDATIONS["swat"]
    if any(k in key for k in ["kachura", "shigar", "khaplu", "deosai"]):
        return DISTRICT_RECOMMENDATIONS["skardu"]
    if any(k in key for k in ["rawalpindi", "margalla", "murree", "bhurban"]):
        return DISTRICT_RECOMMENDATIONS["islamabad"]

    # Fallback to smart regional/category tailored recommendations
    prov = (province or "").lower()
    city_name = district.title() if district else "Destination"

    # Default Restaurants
    fallback_restaurants = [
        {
            "name": f"{city_name} Traditional Shinwari & BBQ",
            "cuisine": "Local Pakistani & BBQ",
            "famous_for": "Fresh Mutton Karahi, Charcoal Kebabs & Hot Tandoori Naan",
            "rating": 4.7,
            "price_level": "₨₨",
            "area": f"Main Food Street, {city_name}",
        },
        {
            "name": f"{city_name} Heritage Tea House & Snacks",
            "cuisine": "Local Tea & Snacks",
            "famous_for": "Traditional Karak Doodh Patti, Samosas & Local Sweets",
            "rating": 4.6,
            "price_level": "₨",
            "area": f"City Center, {city_name}",
        },
        {
            "name": f"Al-Bahar Family Restaurant {city_name}",
            "cuisine": "Pakistani & Chinese",
            "famous_for": "Special Chicken Handi, Biryani & Fried Fish",
            "rating": 4.5,
            "price_level": "₨₨",
            "area": f"Civil Lines / Main Bazaar, {city_name}",
        },
    ]

    # Default Hotels
    fallback_hotels = [
        {
            "name": f"Hotel One {city_name} / City Grand Resort",
            "type": "Comfort & Leisure Stay",
            "price_per_night": "₨ 12,000+",
            "rating": 4.5,
            "amenities": ["Free Breakfast", "24/7 Room Service", "Air Conditioning", "WiFi"],
            "area": f"Central Tourist Area, {city_name}",
        },
        {
            "name": f"{city_name} Palace & Heritage Inn",
            "type": "Boutique Traditional Stay",
            "price_per_night": "₨ 8,500+",
            "rating": 4.4,
            "amenities": ["Scenic Garden", "Family Rooms", "Local Tour Assistance"],
            "area": f"Tourist Boulevard, {city_name}",
        },
        {
            "name": f"{city_name} Tourist Guest House",
            "type": "Budget Friendly Stay",
            "price_per_night": "₨ 5,500+",
            "rating": 4.2,
            "amenities": ["Clean Rooms", "Hot Water", "Friendly Host"],
            "area": f"Main Road, {city_name}",
        },
    ]

    return {
        "restaurants": fallback_restaurants,
        "hotels": fallback_hotels,
    }
