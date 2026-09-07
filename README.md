# 🇵🇰 Pakistan Travel Agent — Complete v1.0

An AI-powered intelligent trip planner and travel assistant for Pakistan tourism. Featuring real, verified destinations across all 4 provinces (Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan), Gilgit-Baltistan, Azad Kashmir, and Islamabad Capital Territory. 

Includes a modern interactive web UI, OpenStreetMap integration, and an intelligent tool-calling agent.

---

## 🌟 Key Features

- **Comprehensive Travel Database**: 150+ hand-verified destinations with coordinates, budget estimates, best seasons, and Wikimedia images.
- **AI Agent Intelligence**: Powered by tool-calling agents to search destinations, plan multi-day custom itineraries, and calculate travel budgets.
- **Dual Interface**:
  - **FastAPI Web App**: Interactive UI with search, filter by province, dynamic map, and trip planner.
  - **Streamlit App**: Lightweight data-driven exploration dashboard.
- **Interactive OpenStreetMap**: Visual map markers and itinerary routes.
- **Automated Testing Suite**: High test coverage for tools, APIs, and database integrity.

---

## 📁 Project Structure

```text
pakistan-travel-agent/
├── main.py                ← FastAPI application: REST endpoints (/chat, /plan-trip), CORS, static UI
├── database.py            ← SQLAlchemy database connection and session management (SQLite)
├── models.py              ← Database models (Destination, DestinationImage)
├── destinations_data.py   ← Core destination records and initial dataset
├── seed.py                ← Database initialization & data seeding script
├── tools.py               ← Core agent tools: search, details, cost estimation, itinerary builder
├── agent.py               ← AI Agent runner (Claude / LLM integration with tool-calling)
├── run.py                 ← One-click application launcher (auto-opens browser)
├── app_streamlit.py       ← Optional Streamlit UI dashboard
├── test_all.py            ← Full automated test suite (unit & integration tests)
├── requirements.txt       ← Project dependencies
├── .env.example           ← Environment variables template
├── static/
│   ├── index.html         ← Frontend single-page app (Browse, Plan, Map, Chat)
│   └── hero.jpg           ← Banner asset
├── data/                  ← Curated city JSON records organized by province
└── scripts/               ← Database maintenance and image scraping utilities

Running the Application
Option 1: FastAPI Full Web App (Recommended)
Launch with automatic browser opening:

bash

python run.py

2. Install Dependencies
bash


pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file from the provided example:

bash


cp .env.example .env
Add your API key (e.g., ANTHROPIC_API_KEY=your_key_here).

4. Initialize & Seed the Database
Populate travel.db with 150+ verified destinations:

bash


python seed.py
🖥️ Running the Application
Option 1: FastAPI Full Web App (Recommended)
Launch with automatic browser opening:

bash


python run.py
(Alternative: uvicorn main:app --reload)
Open: http://127.0.0.1:8000

Option 2: Streamlit Dashboard
bash


streamlit run app_streamlit.py
Open: http://localhost:8501

Option 3: Terminal AI Agent
Interact with the AI agent directly via CLI:

bash


python agent.py
🧪 Running Tests
Execute the automated test suite to verify database queries, tool parsing, and API endpoints:

bash


python test_all.py
