# Project Status

- [x] Phase 1 — FastAPI server runs with CORS & error handling
- [x] Phase 2 — SQLite schema + database working
- [x] Phase 3 — Standalone tool functions (search with district/province/category/budget, cost, itinerary) — tested & verified
- [x] Phase 4 — Claude tool-calling agent built (agent.py) with official Claude 3.5 Haiku model (`claude-3-5-haiku-20241022`), lazy initialization, and safety turn limits. agent_mock.py provides a rich NLP simulation engine with multi-category & budget parsing.
- [x] Phase 5 — Full dataset: 154 destinations across KPK, Punjab, Sindh, Balochistan, Gilgit-Baltistan, Azad Kashmir, and Islamabad Capital Territory with non-null budgets, recommended days, and seasons.
- [x] Phase 5.5 — 100% real, verified Wikimedia Commons photos with proper license & attribution for all 154 destinations.
- [x] Phase 6 — Web UI: Browse (with Province, City, and Category filters + Sorting), Plan a Trip (with city cascade & alternative suggestions), AI Chat, and Wishlist.
- [x] Phase 7 — Leaflet + OpenStreetMap interactive pin view across Pakistan.
- [x] Phase 8 — Comprehensive automated test suite (`test_all.py` — 39 tests passing).
- [x] Phase 9 — Dynamic Live Market Pricing Engine (`live_pricing.py`): Real hotel tiers (budget/standard/luxury), route-based transport modes (private car/mountain jeep/bus/flight), authentic dining rates, seasonal demand multipliers, and multi-currency live conversions (PKR, USD, EUR, GBP, AED, SAR, CAD, AUD).

## Current Architecture
- Database: SQLite `travel.db` containing 154 verified destinations and images.
- Pricing Engine: `live_pricing.py` calibrated with 2026 market rates, real hotel pricing, and dynamic forex rates.
- Backend: FastAPI serving REST API, `/api/pricing/live`, `/api/pricing/currencies`, and responsive frontend at `/`.
- Agent: Dynamic routing in `/chat` (uses Claude when `ANTHROPIC_API_KEY` is configured; automatically falls back to rule-based NLP simulation with live pricing).
- Tests: `python test_all.py` verifies DB integrity, live pricing engine, tools, agent parsing, ML models, and API routes (39 tests passing).
