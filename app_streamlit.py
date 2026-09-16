"""
Pakistan Travel Agent — Streamlit Interface
===========================================
Interactive, full-featured Python dashboard.
Automatically opens in your browser when you run:
    streamlit run app_streamlit.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import requests
from database import SessionLocal
from models import Destination, DestinationImage
from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary
from main import run_mock_agent
from reviews import show_reviews_section

# Base URL of the FastAPI backend (main.py / run.py). All account-related
# actions in this Streamlit app go through the same REST API the web UI uses.
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Page Configuration
st.set_page_config(
    page_title="Discover Pakistan — AI Travel Planner",
    page_icon="🇵🇰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-family: 'Georgia', serif;
        color: #1B3A6B;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #6A5F55;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-amt {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1B3A6B;
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #6C757D;
        text-transform: uppercase;
    }
    .dest-card {
        background: #ffffff;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.04);
    }
    .badge-pill {
        display: inline-block;
        background: #E8F4F8;
        color: #1B3A6B;
        padding: 3px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all_destinations():
    db = SessionLocal()
    try:
        destinations = db.query(Destination).all()
        data = []
        for d in destinations:
            img = d.images[0].image_url if d.images else None
            data.append({
                "id": d.id,
                "name": d.name,
                "province": d.province,
                "district": d.district or "",
                "category": (d.category or "sightseeing").lower(),
                "description": d.description or "",
                "best_season": d.best_season or "Year-round",
                "recommended_days": d.recommended_days or 1,
                "estimated_budget_per_day": d.estimated_budget_per_day or 5000,
                "activities": d.activities or "",
                "latitude": d.latitude,
                "longitude": d.longitude,
                "image_url": img,
            })
        return data
    finally:
        db.close()


all_dests = load_all_destinations()
df_dests = pd.DataFrame(all_dests)

# Sidebar Navigation
st.sidebar.title("🇵🇰 Discover Pakistan")
st.sidebar.caption("AI-Powered Tourism & Trip Planner")
menu = st.sidebar.radio(
    "Navigation",
    ["🔑 Login / Register", "🗺️ Plan a Trip", "🏔️ Browse Destinations", "📍 Interactive Map", "💬 AI Chat Assistant", "⭐ Reviews"]
)

st.sidebar.markdown("---")
if st.sidebar.button("🚨 Wipe Profile & Delete Account"):
    if "access_token" in st.session_state and st.session_state["access_token"]:
        headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
        try:
            res = requests.delete(f"{BACKEND_URL}/user/delete-account", headers=headers)
            if res.status_code == 200:
                st.sidebar.success("Account permanently removed.")
                st.session_state.clear()
                st.rerun()
            else:
                st.sidebar.error("Failed to delete account. Session might have timed out.")
        except Exception:
            st.sidebar.error("Could not connect to the backend server.")
    else:
        st.sidebar.warning("Please sign in first to verify ownership before deletion.")


# -------------------------------------------------------------
# 1. PLAN A TRIP TAB
if menu == "🔑 Login / Register":
    st.markdown('<div class="main-header">Account Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Sign up, verify your email, or manage your travel agent profile.</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Existing User Sign-In", "Create New Account"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Login to Your Travel Dashboard")
            identity = st.text_input("Username or Email Address")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Secure Sign-In"):
                payload = {"email_or_username": identity, "password": password}
                try:
                    res = requests.post(f"{BACKEND_URL}/auth/login", json=payload)
                    if res.status_code == 200:
                        st.session_state["access_token"] = res.json().get("access_token")
                        st.success("Successfully logged in! You can now browse our travel planner system.")
                    else:
                        st.error(res.json().get("detail", "Incorrect credentials or unverified profile account."))
                except Exception:
                    st.error("Could not connect to the backend server. Make sure run.py is running.")

    with tab2:
        reg_type = st.radio("Choose Registration Framework", ["Standard Email Verification", "Mobile Phone Registry"])
        
        if reg_type == "Standard Email Verification":
            with st.form("email_reg_form"):
                u_name = st.text_input("Choose Username*")
                e_mail = st.text_input("Email Address*")
                f_name = st.text_input("Full Name")
                p_word = st.text_input("Choose Password*", type="password")
                if st.form_submit_button("Generate Account OTP"):
                    payload = {"username": u_name, "email": e_mail, "full_name": f_name, "password": p_word}
                    try:
                        res = requests.post(f"{BACKEND_URL}/auth/register", json=payload)
                        if res.status_code == 200:
                            st.info("Registration request created successfully! Check your backend terminal window console to copy your 6-digit verification code.")
                        else:
                            st.error(res.json().get("detail", "Failed to construct profile registry account."))
                    except Exception:
                        st.error("Backend server connection failed.")
                        
            st.markdown("---")
            with st.form("otp_verification_gate"):
                st.subheader("Submit Received Account OTP Code")
                target_email = st.text_input("Confirm Registration Email Address")
                otp_code = st.text_input("6-Digit Code", max_chars=6)
                if st.form_submit_button("Verify & Activate Profile"):
                    try:
                        res = requests.post(f"{BACKEND_URL}/auth/verify-otp", params={"identifier": target_email, "otp": otp_code})
                        if res.status_code == 200:
                            st.success("Verification successful! You can now sign in using the Existing User tab.")
                        else:
                            st.error(res.json().get("detail", "Invalid token code entry values."))
                    except Exception:
                        st.error("Backend server connection failed.")
                        
        elif reg_type == "Mobile Phone Registry":
            with st.form("phone_registration_form"):
                st.subheader("Mobile Verification Registry")
                new_phone = st.text_input("Mobile Number (e.g., +923001234567)")
                phone_username = st.text_input("Username Link")
                phone_fullname = st.text_input("Full Name")
                phone_password = st.text_input("Choose Password*", type="password")
                if st.form_submit_button("Complete Account Form"):
                    params = {"phone_number": new_phone, "username": phone_username, "password": phone_password, "full_name": phone_fullname}
                    try:
                        res = requests.post(f"{BACKEND_URL}/auth/phone-register", params=params)
                        if res.status_code == 200:
                            st.info("Registration request created successfully! Check your backend terminal window console to copy your 6-digit verification code.")
                        else:
                            st.error(res.json().get("detail", "Failed to build target account."))
                    except Exception:
                        st.error("Backend server connection failed.")

            st.markdown("---")
            with st.form("phone_otp_verification_gate"):
                st.subheader("Submit Received Phone OTP Code")
                target_phone = st.text_input("Confirm Registration Phone Number")
                phone_otp_code = st.text_input("6-Digit Code", max_chars=6, key="phone_otp")
                if st.form_submit_button("Verify & Activate Phone Profile"):
                    try:
                        res = requests.post(f"{BACKEND_URL}/auth/verify-otp", params={"identifier": target_phone, "otp": phone_otp_code})
                        if res.status_code == 200:
                            st.success("Verification successful! You can now sign in using the Existing User tab.")
                        else:
                            st.error(res.json().get("detail", "Invalid token code entry values."))
                    except Exception:
                        st.error("Backend server connection failed.")
# -------------------------------------------------------------
elif menu == "🗺️ Plan a Trip":
    st.markdown('<div class="main-header">Plan Your Perfect Pakistan Trip</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Select your preferences below to generate an instant itinerary, cost breakdown, and route.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.4], gap="large")

    with col1:
        st.subheader("Trip Preferences")
        with st.form("plan_trip_form"):
            provinces = ["All Provinces"] + sorted(list(set(df_dests["province"].dropna())))
            selected_prov = st.selectbox("Province", provinces)

            if selected_prov != "All Provinces":
                available_cities = ["All Cities"] + sorted(list(set(df_dests[df_dests["province"] == selected_prov]["district"].dropna())))
            else:
                available_cities = ["All Cities"] + sorted(list(set(df_dests["district"].dropna())))
            
            selected_city = st.selectbox("City / District", available_cities)

            categories = ["All Interests", "mountains", "historical", "nature", "beaches", "cultural", "museum"]
            selected_cat = st.selectbox("Travel Interest", categories)

            days = st.slider("Trip Duration (Days)", min_value=1, max_value=14, value=3)
            people = st.slider("Number of Travelers", min_value=1, max_value=10, value=2)
            total_budget = st.slider("Total Budget (PKR)", min_value=10000, max_value=500000, value=50000, step=5000)

            submitted = st.form_submit_button("Generate Complete Trip Plan", use_container_width=True)

    with col2:
        if submitted:
            prov_param = None if selected_prov == "All Provinces" else selected_prov
            city_param = None if selected_city == "All Cities" else selected_city
            cat_param = None if selected_cat == "All Interests" else selected_cat
            per_day = total_budget // days

            matches = search_destinations(
                province=prov_param,
                district=city_param,
                max_budget_per_day=per_day,
                category=cat_param
            )

            if not matches:
                # Relax budget constraint
                matches = search_destinations(province=prov_param, district=city_param, category=cat_param)

            if not matches:
                st.warning("No destinations matched your exact combination. Try selecting a different city or category.")
            else:
                chosen = matches[0]
                details = get_destination_details(chosen["id"])
                cost = estimate_cost(chosen["id"], days=days, people=people)
                itinerary = generate_itinerary(chosen["id"], days=days)

                # Fetch Image
                db = SessionLocal()
                dest_row = db.query(Destination).filter(Destination.id == chosen["id"]).first()
                img_url = dest_row.images[0].image_url if dest_row and dest_row.images else None
                db.close()

                st.success(f"### Recommended Destination: {chosen['name']}")

                # 1. PHOTO ON TOP
                if img_url and not img_url.startswith("PLACEHOLDER"):
                    st.image(img_url, use_container_width=True, caption=f"{chosen['name']} — {chosen['province']}")

                # 2. DETAILS ON BOTTOM
                st.markdown(f"**Location:** {chosen.get('district', '') + ', ' if chosen.get('district') else ''}{chosen['province']} | **Category:** {chosen.get('category', '').title()}")
                st.write(details.get("description", ""))

                # Quick Info
                q1, q2, q3 = st.columns(3)
                q1.info(f"📅 **Stay:** {details.get('recommended_days', 1)} day(s)")
                q2.info(f"🌤️ **Season:** {details.get('best_season', 'Year-round')}")
                q3.info(f"💰 **Daily/Person:** PKR {details.get('estimated_budget_per_day', 5000):,}")

                # Cost Breakdown (4 Balanced Tiles)
                st.markdown(f"#### 💵 Estimated Cost Breakdown ({days} Days, {people} Traveler{'s' if people > 1 else ''})")
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    st.markdown(f'<div class="metric-card"><div class="metric-lbl">🏨 Accommodation</div><div class="metric-amt">PKR {cost["breakdown_pkr"]["accommodation"]:,}</div></div>', unsafe_allow_html=True)
                with b2:
                    st.markdown(f'<div class="metric-card"><div class="metric-lbl">🍽️ Meals & Food</div><div class="metric-amt">PKR {cost["breakdown_pkr"]["food"]:,}</div></div>', unsafe_allow_html=True)
                with b3:
                    st.markdown(f'<div class="metric-card"><div class="metric-lbl">🎯 Activities</div><div class="metric-amt">PKR {cost["breakdown_pkr"]["activities"]:,}</div></div>', unsafe_allow_html=True)
                with b4:
                    st.markdown(f'<div class="metric-card"><div class="metric-lbl">🚗 Transport</div><div class="metric-amt">PKR {cost["breakdown_pkr"]["transport"]:,}</div></div>', unsafe_allow_html=True)

                st.markdown(f"### 💳 Total Estimated Trip Cost: **PKR {cost['estimated_total_pkr']:,}**")

                # Itinerary
                st.markdown("#### 🗓️ Day-by-Day Itinerary")
                for day in itinerary["itinerary"]:
                    with st.expander(f"Day {day['day']} Plan", expanded=(day['day'] == 1)):
                        st.write(day["plan"])

                # Mini Map
                if details.get("latitude") and details.get("longitude"):
                    st.markdown("#### 📍 Location Map")
                    map_df = pd.DataFrame([{"lat": details["latitude"], "lon": details["longitude"]}])
                    st.map(map_df, zoom=10)
        else:
            st.info("👈 Fill out your preferences on the left and click **'Generate Complete Trip Plan'**.")

# -------------------------------------------------------------
# 2. BROWSE DESTINATIONS TAB
# -------------------------------------------------------------
elif menu == "🏔️ Browse Destinations":
    st.markdown('<div class="main-header">Browse Pakistan Destinations</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Exploring {len(df_dests)} verified landmarks, hill stations, and cultural sites.</div>', unsafe_allow_html=True)

    # Filter Bar
    f1, f2, f3, f4 = st.columns([1.5, 1, 1, 1])
    with f1:
        search_query = st.text_input("🔍 Search landmarks or cities", "")
    with f2:
        prov_filter = st.selectbox("Province", ["All Provinces"] + sorted(list(set(df_dests["province"].dropna()))))
    with f3:
        if prov_filter != "All Provinces":
            city_filter = st.selectbox("City", ["All Cities"] + sorted(list(set(df_dests[df_dests["province"] == prov_filter]["district"].dropna()))))
        else:
            city_filter = st.selectbox("City", ["All Cities"] + sorted(list(set(df_dests["district"].dropna()))))
    with f4:
        sort_by = st.selectbox("Sort By", ["Default", "Budget: Low to High", "Budget: High to Low", "Name (A-Z)", "Recommended Days"])

    # Filtering Logic
    filtered = df_dests.copy()
    if search_query:
        q = search_query.lower()
        filtered = filtered[filtered["name"].str.lower().str.contains(q) | filtered["district"].str.lower().str.contains(q) | filtered["description"].str.lower().str.contains(q)]
    if prov_filter != "All Provinces":
        filtered = filtered[filtered["province"] == prov_filter]
    if city_filter != "All Cities":
        filtered = filtered[filtered["district"] == city_filter]

    # Sorting
    if sort_by == "Budget: Low to High":
        filtered = filtered.sort_values("estimated_budget_per_day", ascending=True)
    elif sort_by == "Budget: High to Low":
        filtered = filtered.sort_values("estimated_budget_per_day", ascending=False)
    elif sort_by == "Name (A-Z)":
        filtered = filtered.sort_values("name", ascending=True)
    elif sort_by == "Recommended Days":
        filtered = filtered.sort_values("recommended_days", ascending=False)

    st.write(f"Showing **{len(filtered)}** destinations")

    # Render Cards in 3 Columns (Photo on top, details on bottom)
    cols = st.columns(3)
    for idx, row in enumerate(filtered.to_dict(orient="records")):
        col = cols[idx % 3]
        with col:
            st.markdown(f"### {row['name']}")
            if row["image_url"]:
                st.image(row["image_url"], use_container_width=True)
            st.markdown(f"**📍 {row['province']}{' · ' + row['district'] if row['district'] else ''}**")
            st.caption(row["description"][:120] + "..." if len(row["description"]) > 120 else row["description"])
            st.markdown(f"📅 **Stay:** {row['recommended_days']} day(s) | 💰 **PKR {row['estimated_budget_per_day']:,}/day**")
            with st.expander("View Full Details"):
                st.write(row["description"])
                st.write(f"**Best Season:** {row['best_season']}")
                st.write(f"**Activities:** {row['activities']}")

# -------------------------------------------------------------
# 3. INTERACTIVE MAP TAB
# -------------------------------------------------------------
elif menu == "📍 Interactive Map":
    st.markdown('<div class="main-header">Interactive Tourism Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Every verified destination plotted with GPS coordinates.</div>', unsafe_allow_html=True)

    map_data = df_dests.dropna(subset=["latitude", "longitude"])[["latitude", "longitude", "name", "province", "category"]]
    map_data = map_data.rename(columns={"latitude": "lat", "longitude": "lon"})
    st.map(map_data, zoom=5)

# -------------------------------------------------------------
# 4. AI CHAT ASSISTANT
# -------------------------------------------------------------
elif menu == "💬 AI Chat Assistant":
    st.markdown('<div class="main-header">AI Travel Consultant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask anything about traveling in Pakistan in natural language.</div>', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! 🇵🇰 I'm your Pakistan Travel Consultant. Tell me where you'd like to go, your budget, or how many days you have!"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_prompt := st.chat_input("e.g. Plan a 3-day family trip to Swat for 30k PKR"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Finding best destinations and calculating costs..."):
                reply = run_mock_agent(user_prompt)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

# -------------------------------------------------------------
# ⭐ REVIEWS
# -------------------------------------------------------------
elif menu == "⭐ Reviews":
    show_reviews_section()
