"""
city_coordinates.py
=============================
Approximate city-center coordinates -- general knowledge, same
"needs verification" caveat your friend used for her own data --
used to give each converted attraction a latitude/longitude, since
your original city JSON files didn't track per-attraction GPS points.

Add new cities here as you add new city JSON files -- seed_all.py
will automatically pick up any city listed here.
"""

CITY_COORDINATES = {
    # Punjab
    "Lahore": (31.5497, 74.3436),
    "Bahawalpur": (29.3956, 71.6836),
    "Multan": (30.1575, 71.5249),
    "Faisalabad": (31.4187, 73.0791),
    "Rawalpindi": (33.5651, 73.0169),
    "Sialkot": (32.4945, 74.5229),
    "Sargodha": (32.0836, 72.6711),
    "Gujranwala": (32.1877, 74.1945),
    "Sheikhupura": (31.7131, 73.9783),
    "Jhelum": (32.9425, 73.7257),
    "Kasur": (31.1156, 74.4502),
    "Vehari": (30.0333, 72.3500),
    "Okara": (30.8100, 73.4467),
    # Sindh
    "Karachi": (24.8607, 67.0011),
    "Hyderabad": (25.3960, 68.3578),
    "Sukkur": (27.7052, 68.8574),
    "Larkana": (27.5590, 68.2123),
    "Nawabshah": (26.2442, 68.4100),
    "Mirpurkhas": (25.5266, 69.0113),
    "Dadu": (26.7308, 67.7750),
    "Badin": (24.6564, 68.8378),
    "Thatta": (24.7461, 67.9247),
    # Khyber Pakhtunkhwa
    "Peshawar": (34.0151, 71.5249),
    "Abbottabad": (34.1463, 73.2114),
    "Mardan": (34.1986, 72.0404),
    "Swat": (34.7717, 72.3604),
    "Chitral": (35.8518, 71.7861),
    "Dir": (35.2065, 71.8757),
    "Kohat": (33.5893, 71.4425),
    "Bannu": (32.9855, 70.6039),
    "Dera Ismail Khan": (31.8314, 70.9020),
    "Nowshera": (34.0153, 71.9747),
    # Balochistan
    "Quetta": (30.1798, 66.9750),
    "Gwadar": (25.1264, 62.3225),
    "Sibi": (29.5439, 67.8778),
    "Zhob": (31.3411, 69.4481),
    "Khuzdar": (27.8069, 66.6161),
    "Loralai": (30.3705, 68.5978),
    # Islamabad
    "Islamabad": (33.6844, 73.0479),
    # Azad Kashmir
    "Muzaffarabad": (34.3700, 73.4711),
    "Rawalakot": (33.8575, 73.7521),
    # Gilgit-Baltistan
    "Gilgit": (35.9221, 74.3087),
    "Skardu": (35.2971, 75.6333),
}