# Pakistan Travel Agent — Complete v1.0

AI-powered trip planner for Pakistan tourism. Real, hand-verified destinations across all 4 provinces + Gilgit-Baltistan + Azad Kashmir + Islamabad, with a responsive web UI, OpenStreetMap Leaflet integration, cost & itinerary engine, AI chat, and automated test suite.

## Project Structure

```
pakistan-travel-agent/
├── main.py                ← FastAPI app: serves the UI, CORS, /chat, and /plan-trip
├── database.py             ← DB connection setup (SQLite)
├── models.py                ← Destination & DestinationImage SQLAlchemy models
├── destinations_data.py     ← Core dataset definitions
├── seed.py                   ← Inserts core dataset into travel.db
├── seed_my_cities.py         ← Ingests all 40+ city JSON files with budgets & weather info
├── tools.py                   ← 4 tool functions: search, details, cost, itinerary
├── agent.py                   ← Live Claude AI agent (Claude 3.5 Haiku tool-calling)
├── agent_mock.py              ← Rule-based NLP simulation engine (no API key required)
├── test_all.py                ← Full automated test suite (23 unit & integration tests)
├── test_tools.py               ← Quick CLI verification for tool functions
├── static/
│   ├── index.html             ← Modern web UI (Browse, Plan, Map, Chat, Wishlist)
│   └── hero.jpg               ← Hero background image
├── data/                      ← Curated city JSON files by province
├── scripts/                   ← Database & image utility scripts
├── requirements.txt           ← Python dependencies
├── .env.example                ← Template for ANTHROPIC_API_KEY
└── .gitignore
```

## Setup & Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv venv
    # Mac/Linux
   .\venv\Scripts\Activate.ps1
   # if u get security policy error ,run this first ,then activate
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
    .\venv\Scripts\Activate.ps1 
# 2. Install dependencies

pip install -r requirements.txt

# 3. Seed database (154 destinations with verified Wikimedia images)
python seed.py
python seed_my_cities.py
python scripts/update_db_data.py
```

## Run the Web App (Automatic Browser Launch)

You can launch the web application with **a single command** and it will **automatically open your browser**:

### Option 1: Standard Web App (FastAPI + HTML5/CSS3)
```bash
python run.py
```
*(Or `python main.py` or `uvicorn main:app --reload`)*
Automatically opens **http://127.0.0.1:8000** in your browser.

### Option 2: Streamlit Interactive App (Python UI)
```bash
streamlit run app_streamlit.py
```
Automatically opens **http://localhost:8501** in your browser.


## Run Automated Tests

```bash
python test_all.py
```

Runs all 23 unit and API integration tests covering database schemas, tool functions, NLP parsers, and FastAPI endpoints.

## Run Terminal AI Agent

```bash
python agent.py          # Real Claude AI reasoning (requires ANTHROPIC_API_KEY in .env)
python agent_mock.py     # Rule-based NLP engine (free, no API key needed)
```

