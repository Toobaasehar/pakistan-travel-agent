# 🇵🇰 Pakistan Travel Agent — Complete v1.1

An AI-powered intelligent trip planner and travel assistant for Pakistan tourism. Featuring real, verified destinations across all 4 provinces (Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan), Gilgit-Baltistan, Azad Kashmir, and Islamabad Capital Territory.

Includes a modern interactive web UI, OpenStreetMap integration, an intelligent tool-calling agent, a ML-based budget/clustering layer, and user accounts (wishlist + saved trips).

---

## 🌟 Key Features

- **Comprehensive Travel Database**: 376+ destinations with coordinates, budget estimates, best seasons, and images.
- **AI Agent Intelligence**: Tool-calling agent (Claude / Groq / rule-based fallback) that searches destinations, plans multi-day itineraries, and calculates live budgets.
- **ML Layer**: Random Forest budget prediction with SHAP explainability, and KMeans clustering for "similar destinations."
- **Live Market Pricing**: Region-aware hotel tiers, route-based transport pricing (Haversine distance between cities), seasonal multipliers, and multi-currency conversion.
- **User Accounts**: Email and phone registration, JWT auth, cloud wishlist, saved trips.
- **Dual Interface**:
  - **FastAPI Web App**: Interactive UI with search, filter by province, dynamic map, and trip planner.
  - **Streamlit App**: Lightweight data-driven exploration dashboard.
- **Automated Testing Suite**: Coverage for tools, ML modules, auth, and API endpoints.

---

## 📁 Project Structure

```text
pakistan-travel-agent/
├── main.py                ← FastAPI application: REST endpoints (/chat, /plan-trip, /auth/*), CORS, static UI
├── database.py             ← SQLAlchemy database connection and session management (SQLite)
├── models.py                ← Database models (Destination, DestinationImage, User, UserWishlist, SavedTrip)
├── auth.py                   ← Password hashing, JWT issuing/decoding, FastAPI auth dependencies
├── destinations_data.py       ← Core destination records and initial dataset
├── city_coordinates.py         ← City-center lat/long lookup, used by seeding and route-distance pricing
├── recommendations.py           ← Budget-tiered hotel/restaurant/shopping recommendations
├── live_pricing.py                ← Formula-based live pricing engine (hotels, transport, food, activities, FX)
├── seed.py                         ← Database initialization & data seeding script
├── tools.py                         ← Core agent tools: search, details, cost estimation, itinerary builder
├── agent.py                          ← AI agent runner (Groq / Claude / rule-based simulation fallback)
├── run.py                             ← One-click FastAPI launcher (auto-opens browser)
├── app_streamlit.py                    ← Streamlit UI dashboard (talks to the FastAPI backend over HTTP)
├── check_status.py                      ← Debug script: inspect stored image URLs
├── review_models.py                      ← Pydantic schemas for the reviews feature
├── reviews.py                             ← Review data access (SQLAlchemy, uses models.Review)
├── review_routes.py                        ← FastAPI router: POST/DELETE require login, GET is public
├── review_ui.py                             ← Streamlit "Reviews" tab (login-gated writing, open browsing)
├── scripts/
│   └── fetch_real_images.py                   ← Pulls real destination photos from Wikipedia (see setup step 4)
├── test_all.py                           ← Full automated test suite (unit & integration tests)
├── requirements.txt                       ← Project dependencies
├── .env.example                            ← Environment variables template
├── ml/
│   ├── predict_budget.py                    ← ML budget inference + multi-currency conversion
│   ├── explain_budget.py                     ← SHAP explainability for the budget model
│   ├── similar_destinations.py                ← KMeans-based "similar destinations" lookup
│   ├── train_budget_model.py                   ← Trains budget_model.joblib
│   ├── train_clustering.py                       ← Trains clustering_model.joblib
│   ├── budget_model.joblib                         ← Trained regression pipeline (generated)
│   └── clustering_model.joblib                      ← Trained clustering bundle (generated)
├── static/
│   ├── index.html                                    ← Frontend single-page app (Browse, Plan, Map, Chat)
│   └── hero.jpg                                        ← Banner asset
└── data/                                                ← Curated per-district attraction JSON files, one file per city/district, grouped by province/territory folder
    ├── AzadKashmir/            (10 districts)  bagh, bhimber, hattian_bala, haveli, kotli, mirpur, muzaffarabad, neelum_valley, rawalakot, sudhanoti
    ├── Balochistan/            (33 districts)  awaran, barkhan, bolan, chagai, chaman, dera_bugti, duki, gwadar, harnai, jaffarabad, jhal_magsi, kalat, kech, kharan, khuzdar, killa_abdullah, kohlu, lasbela, loralai, mastung, musakhel, nasirabad, nushki, panjgur, pishin, qila_saifullah, quetta, sherani, sibi, sohbatpur, washuk, zhob, ziarat
    ├── GilgitBaltistan/        (10 districts)  astore, diamer, ghanche, ghizer, gilgit, hunza, kharmang, nagar, shigar, skardu
    ├── Islamabad/              (6 files)       islamabad (city overview) + zone_i, zone_ii, zone_iii, zone_iv, zone_v
    ├── KhyberPakhtunkhwa/      (42 districts)  abbottabad, allai, bajaur, bannu, battagram, buner, central_dir, charsadda, chitral, dera_ismail_khan, dir, hangu, haripur, karak, khyber, kohat, kolai_palas, kurram, lakki_marwat, lower_chitral, lower_dir, lower_kohistan, lower_south_waziristan, malakand, mansehra, mardan, mohmand, north_waziristan, nowshera, orakzai, paharpur, peshawar, shangla, swabi, swat, tank, torghar, upper_chitral, upper_dir, upper_kohistan, upper_south_waziristan, upper_swat
    ├── Punjab/                 (36 districts)  attock, bahawalnagar, bahawalpur, bhakkar, chakwal, chiniot, dera_ghazi_khan, faisalabad, gujranwala, gujrat, hafizabad, jhang, jhelum, kasur, khanewal, khushab, lahore, layyah, lodhran, mandi_bahauddin, mianwali, multan, muzaffargarh, nankana_sahib, narowal, okara, pakpattan, rahim_yar_khan, rajanpur, rawalpindi, sahiwal, sargodha, sheikhupura, sialkot, toba_tek_singh, vehari
    └── Sindh/                  (24 districts)  badin, dadu, ghotki, hyderabad, jacobabad, jamshoro, karachi, kashmore, khairpur, larkana, matiari, mirpurkhas, naushahro_feroze, nawabshah, qambar_shahdadkot, sanghar, shikarpur, sujawal, sukkur, tando_allahyar, tando_muhammad_khan, tharparkar, thatta, umerkot
```

> **Coverage note:** every province and territory in Pakistan — Punjab, Sindh, KPK, Balochistan, Gilgit-Baltistan, Azad Kashmir, and Islamabad Capital Territory — now has a JSON file per district, **161 district-level files in total**, seeded via `seed.py`'s `load_city_attractions()`. Every district listed above has a matching entry in `city_coordinates.py`, so `seed.py` won't silently skip any of them (it only skips — with a printed warning — a city JSON whose name isn't found there).

---

## 🖥️ Running the Application

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment variables
```bash
cp .env.example .env
```
Then edit `.env` and set, at minimum:

| Variable | Required? | Notes |
|---|---|---|
| `JWT_SECRET_KEY` | **Yes** | App now refuses to start without it (no hardcoded fallback). Generate one with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GROQ_API_KEY` / `ANTHROPIC_API_KEY` | No | Optional. Without either, the agent runs in rule-based Simulation Mode automatically. |

### 3. Initialize & seed the database
```bash
python seed.py
```
This creates `travel.db`, inserts the curated base destinations from `destinations_data.py`, and imports every city/district JSON file under `data/` — 376+ destinations in total across 161+ cities & districts.

### 4. (Optional) Fetch real destination images
By default, newly seeded destinations get a placeholder image. To replace placeholders with real photos pulled automatically from Wikipedia:
```bash
python scripts/fetch_real_images.py
```
This only touches destinations that still have a placeholder image — it won't overwrite any images you've already curated manually (use `--all` to force a re-fetch of everything, or `--limit 20` to test on a small batch first). Requires internet access. See the script's docstring for the licensing caveat: Wikipedia images are generally reusable, but the exact license varies per image, so spot-check before using any commercially — the same "needs verification" convention used elsewhere in this project's data.

### 5. (Optional) Train the ML models
Only needed if `ml/*.joblib` files aren't already present, or after re-seeding with substantially different data:
```bash
python ml/train_budget_model.py
python ml/train_clustering.py
```

### 6. Run it

**Option 1 — FastAPI web app (recommended)**
```bash
python run.py
# or: uvicorn main:app --reload
```
Open: http://127.0.0.1:8000

**Option 2 — Streamlit dashboard**
```bash
streamlit run app_streamlit.py
```
Open: http://localhost:8501
> The Streamlit app talks to the FastAPI backend over HTTP for all account actions (login, register, delete account) — start `python run.py` first, or set `BACKEND_URL` in your environment if the API isn't running on the default `http://127.0.0.1:8000`.

**Option 3 — Terminal AI agent**
```bash
python agent.py
```

---

## 🧪 Running Tests

```bash
python test_all.py
```
Covers database integrity, tool functions, the mock-agent parser, the ML budget/clustering modules, all FastAPI endpoints, and the full registration → login → wishlist → saved-trips flow.

---

## 🛠️ Changelog / Recent Fixes

A full pass was done across the codebase (backend, ML layer, Streamlit UI, data seeding). Fixed in this pass:

**New since last pass — Reviews feature**
- Added a `Review` table (`models.py`) linked to `User` and, optionally, a specific `SavedTrip` — reviews now always require a logged-in account (`review_routes.py` uses `get_current_user`), replacing an earlier draft that let anyone submit a review under any typed-in name.
- After a user saves a trip plan (`static/index.h
tml`'s "Save Trip to My Profile"), a review prompt now opens automatically, pre-filled with that destination and linked to the trip (`trip_id`) — reviews created this way are marked `is_verified=True` since the backend can confirm the user actually planned that trip.
- New endpoints: `POST /reviews/` (login required), `GET /reviews/{destination_name}`, `GET /reviews/{destination_name}/summary`, `GET /reviews/all`, `DELETE /reviews/{review_id}` (only the review's author can delete it).
- `app_streamlit.py` gained a "⭐ Reviews" tab (`review_ui.py`) — writing a review requires being signed in there too; browsing stays open to everyone.
- Along the way, fixed a pre-existing bug in `app_streamlit.py`'s sidebar: two menu options (`Plan a Trip`, `Browse Destinations`) used different emoji in the `st.sidebar.radio()` list than in their `elif menu == ...` dispatch conditions, so selecting them rendered a blank page. Also removed a stale `!= "pending_verification"` check left over from before registration returned a real token immediately.

**New since last pass — Real destination images**
- Added `scripts/fetch_real_images.py`, which looks up each destination on Wikipedia and replaces its placeholder image with a real photo URL (only touching destinations that are still on the placeholder, unless run with `--all`). See setup step 4 above.

**New since last pass — Simple email/phone registration (no OTP)**
- `main.py` — `/auth/register` and `/auth/phone-register` both create a verified account and return a real, immediately-usable JWT in one step. An earlier version of this project briefly required OTP verification before login (accounts stayed `is_verified=False` until a code was confirmed); that step was deliberately removed to keep registration simple — accounts are now instantly usable, matching how the original UI was designed to behave.
- `main.py` — `/auth/login` matches by email, username, *or* phone number, so phone-registered users can log in with their phone number.
- `static/index.html` — the "Create Account" form now has an Email/Phone toggle so users can register either way from the same modal; registering logs the user in immediately (fixing a real bug where the old code treated the backend's old placeholder `"pending_verification"` string as a valid login token, silently breaking every authenticated request afterward).
- `static/index.html` — added a "🗑️ Delete Account" option to the profile dropdown (the backend endpoint already existed; there was previously no UI for it), with a type-DELETE-to-confirm safeguard since the action is irreversible.

**Correctness bugs**
- `main.py` — `/auth/phone-register` referenced `user` before it was ever assigned (it was defined *inside* an `if` block, after an unconditional `raise`), throwing `NameError` on every successful call. Also silently omitted the required `hashed_password` field, which would have failed with a `NOT NULL` constraint error. Both fixed; the endpoint now requires a `password` and checks for a duplicate username too.
- `app_streamlit.py` — imported `from agent_mock import run_mock_agent`, a module that doesn't exist anywhere in the project (`run_mock_agent` lives in `agent.py`). This broke the AI Chat tab entirely. Fixed the import.
- `app_streamlit.py` — every backend call (login, register, OTP verification, phone registration, account deletion) used the literal, incomplete URL `"http://127.0.0"`. None of these requests could ever have succeeded. Added a `BACKEND_URL` constant and pointed each call at the correct endpoint path.
- `ml/predict_budget.py` vs `ml/explain_budget.py` — the two modules applied the 2,500 PKR/day price floor differently (`predict_budget` floored the number, `explain_budget` didn't), so for cheap category/province combinations the two "budget estimate" and "why this estimate" endpoints could report **different headline numbers** for identical input. Extracted a shared `apply_price_floor()` helper that both now use.

**Security**
- `auth.py` — `JWT_SECRET_KEY` had a hardcoded fallback checked into source control, meaning anyone who reads this repo could forge valid login tokens if the env var wasn't set. The app now raises a clear startup error instead of silently using a known secret.
- `auth.py` — email verification codes were generated with `random.randint`, which is not cryptographically secure. Switched to `secrets.randbelow`.

**Data / logic robustness**
- `seed.py` — duplicate-destination detection used plain substring containment (`short_name in long_name`), which could false-positive on any name over 4 characters (e.g. a hypothetical "Valley" entry would match every "X Valley" already seeded). Now requires the shorter name to make up at least 70% of the longer one.
- `ml/train_clustering.py` — hardcoded `DB_PATH = "travel.db"` as a bare relative path, unlike `train_budget_model.py`'s more robust resolution; would silently fail to find the DB if run from a different working directory. Now resolves the same way `train_budget_model.py` does.
- `ml/explain_budget.py` — used the `list[str] | None` union syntax, which requires Python 3.10+. Replaced with `typing.Optional[List[str]]` for broader compatibility.
- `tools.py` — `estimate_cost()` returned two keys (`total_pkr` and `estimated_total_pkr`) holding the identical value with no indication which was canonical. Documented `total_pkr` as canonical; `estimated_total_pkr` kept only as a backward-compatible alias.
- `models.py` — added a comment clarifying that `User.email` is intentionally nullable (to support the phone-only registration path), rather than leaving it as an unexplained deviation from a stricter original design.

**Known limitations carried forward (not yet fixed, worth tracking)**
- `live_pricing.py`'s `EXCHANGE_RATES` and `ml/predict_budget.py`'s `FX_RATES` are two separately maintained currency tables (now with matching values for shared currencies, including the previously-missing CAD/AUD) — if you update one, update the other, or the formula-based and ML-based price estimates will drift apart again.
- `main.py`'s `/auth/verify-otp` endpoint and `generate_verification_code()` are still present but now unused/orphaned — nothing calls them since registration no longer generates a code. Harmless dead code; remove them, or wire them back in, whichever this project needs later.
- `main.py`'s `/auth/phone-register` takes query parameters rather than a Pydantic request body, unlike every other POST endpoint in the file — inconsistent but functional.
- `reviews.py` opens a new `SessionLocal()` per function call rather than using FastAPI's `Depends(get_db)` pattern the rest of `main.py` uses — works fine, but is a different style from the rest of the codebase; worth unifying if this module grows.
- No automated tests currently cover the Streamlit app, the ML training scripts, `scripts/fetch_real_images.py`, or the reviews feature (only `test_all.py`'s existing coverage applies).