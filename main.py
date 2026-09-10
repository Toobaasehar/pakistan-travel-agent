"""
Pakistan Travel Agent — Backend Entry Point
=============================================
Phase 8: Added RAG (Retrieval-Augmented Generation) for semantic knowledge search.

Run with:
    uvicorn main:app --reload
Then open:
    http://127.0.0.1:8000
"""

import os
import json
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from database import engine, get_db, Base
from models import Destination, DestinationImage, User, UserWishlist, SavedTrip
from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary
from recommendations import get_recommendations_for_destination
from agent import run_mock_agent
from ml.predict_budget import predict_budget
from ml.similar_destinations import get_similar_destinations
from ml.explain_budget import explain_budget_prediction
from review_routes import router as reviews_router
from auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
    generate_verification_code,
)

# RAG knowledge base search (Phase 8)
try:
    from rag.rag_tool import search_knowledge_base as rag_search
    _RAG_READY = True
    print("[main] RAG module loaded successfully ✓")
except Exception as _rag_err:
    _RAG_READY = False
    print(f"[main] RAG not available: {_rag_err}")
    def rag_search(query: str, top_k: int = 5) -> dict:
        return {"results": [], "count": 0, "engine": "disabled"}

# Automatically create all database tables (including users, user_wishlists, saved_trips)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pakistan Travel Agent API",
    description="Backend for an AI-powered trip planner for Pakistan tourism.",
    version="1.2.0",
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reviews feature: POST/DELETE require a logged-in user (see review_routes.py)
app.include_router(reviews_router)


@app.on_event("startup")
async def warmup_rag():
    """Pre-warm the RAG index on server startup so the first chat request is fast."""
    if _RAG_READY:
        try:
            import threading
            def _build():
                from rag.retriever import get_retriever
                get_retriever()  # builds/loads index
                print("[main] RAG index ready ✓")
            threading.Thread(target=_build, daemon=True).start()
        except Exception as e:
            print(f"[main] RAG warmup error: {e}")


@app.get("/")
def serve_ui():
    """Serves the web UI as the site's homepage with cache-busting headers."""
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Returns empty 204 to prevent 404 logs from browser icon requests."""
    return Response(status_code=204)


# Mounted at /static for static assets (images, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health_check():
    """Health endpoint for monitoring and uptime checks."""
    return {"status": "ok", "version": "1.2.0", "rag_ready": _RAG_READY}


# ── RAG Endpoint (Phase 8) ────────────────────────────────────────────────────

@app.get("/rag/search")
def rag_search_endpoint(q: str, top_k: int = 5):
    """
    Semantic knowledge base search over Pakistan travel data.
    Returns relevant passages about attractions, weather, history,
    travel tips, food, transport, and more.

    Example: GET /rag/search?q=best+time+to+visit+Hunza&top_k=5
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    top_k = min(max(1, top_k), 10)
    try:
        result = rag_search(query=q.strip(), top_k=top_k)
        return {
            "query": q.strip(),
            "top_k": top_k,
            "engine": result.get("engine", "unknown"),
            "count": result.get("count", 0),
            "results": result.get("results", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search failed: {e}")


# ── Destinations ──────────────────────────────────────────────────────────────

@app.get("/destinations")
def list_destinations(
    province: Optional[str] = None,
    district: Optional[str] = None,
    category: Optional[str] = None,
    max_budget_per_day: Optional[int] = None,
    include_coords: bool = False,
    db: Session = Depends(get_db),
):
    """
    Lists destinations with optional filters — used by Browse, Plan, and Map tabs.
    """
    query = db.query(Destination)
    if province:
        query = query.filter(Destination.province.ilike(f"%{province}%"))
    if district:
        query = query.filter(Destination.district.ilike(f"%{district}%"))
    if category:
        query = query.filter(Destination.category.ilike(f"%{category}%"))
    if max_budget_per_day:
        query = query.filter(Destination.estimated_budget_per_day <= max_budget_per_day)

    results = query.all()
    output = []
    for d in results:
        image_url = None
        image_attribution = None
        if d.images:
            first_img = d.images[0]
            image_url = first_img.image_url
            image_attribution = first_img.attribution

        item = {
            "id": d.id,
            "name": d.name,
            "province": d.province,
            "district": d.district,
            "category": d.category,
            "description": d.description,
            "recommended_days": d.recommended_days,
            "estimated_budget_per_day": d.estimated_budget_per_day,
            "best_season": d.best_season,
            "activities": d.activities,
            "image_url": image_url,
            "image_attribution": image_attribution,
        }
        if include_coords:
            item["latitude"] = d.latitude
            item["longitude"] = d.longitude
        output.append(item)
    return output


# ── Pydantic Models ───────────────────────────────────────────────────────────

class TripRequest(BaseModel):
    budget: int = Field(..., gt=0, description="Total budget in PKR")
    days: int = Field(..., gt=0, description="Number of trip days")
    category: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    people: int = Field(default=1, gt=0, description="Number of travelers")
    from_city: Optional[str] = Field(default=None, description="User's current location, e.g. 'Lahore' -- enables route-based transport pricing")
    include_hotel: bool = Field(default=True, description="False if the user won't be staying overnight (day trip, staying with family, etc.)")
    travel_style: Optional[str] = Field(default=None, description="'budget'/'standard'/'luxury' if the user picked a tier manually; omit to auto-select the best tier that fits their budget")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class BudgetPredictionRequest(BaseModel):
    province: str
    category: str
    recommended_days: int = Field(..., gt=0)
    activities: Optional[List[str]] = None


class WishlistToggleRequest(BaseModel):
    destination_id: int


class WishlistSyncRequest(BaseModel):
    destination_ids: List[int]


class SaveTripRequest(BaseModel):
    destination_id: Optional[int] = None
    destination_name: str
    days: int
    people: int = 1
    total_budget: int
    trip_plan_json: str


# ── Authentication Endpoints ──────────────────────────────────────────────────

@app.post("/auth/register", response_model=TokenResponse)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    existing_username = db.query(User).filter(User.username == req.username.strip()).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="This username is already taken.")

    hashed_pw = hash_password(req.password)

    user = User(
        username=req.username.strip(),
        email=req.email.lower().strip(),
        hashed_password=hashed_pw,
        full_name=req.full_name.strip() if req.full_name else req.username.strip(),
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.post("/auth/login", response_model=TokenResponse)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and issues a signed JWT access token.
    Accepts an email, username, or phone number as the identifier, since
    accounts can be created via either the email or phone registration flow.
    """
    identifier = req.email_or_username.strip()
    user = db.query(User).filter(
        (User.email == identifier.lower())
        | (User.username.ilike(identifier))
        | (User.phone_number == identifier)
    ).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username/phone or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is deactivated.",
        )

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return current_user


# ── User Data Endpoints (Wishlist & Saved Trips) ──────────────────────────────

@app.get("/api/user/wishlist")
def get_user_wishlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns all destination IDs saved in the current user's database wishlist."""
    items = db.query(UserWishlist.destination_id).filter(UserWishlist.user_id == current_user.id).all()
    destination_ids = [item[0] for item in items]
    return {"destination_ids": destination_ids}


@app.post("/api/user/wishlist/toggle")
def toggle_user_wishlist(req: WishlistToggleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggles a destination in or out of the user's cloud wishlist."""
    existing = db.query(UserWishlist).filter(
        UserWishlist.user_id == current_user.id,
        UserWishlist.destination_id == req.destination_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        is_favorite = False
    else:
        new_item = UserWishlist(user_id=current_user.id, destination_id=req.destination_id)
        db.add(new_item)
        db.commit()
        is_favorite = True

    total = db.query(UserWishlist).filter(UserWishlist.user_id == current_user.id).count()
    return {"status": "ok", "is_favorite": is_favorite, "total_favorites": total}


@app.post("/api/user/wishlist/sync")
def sync_user_wishlist(req: WishlistSyncRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Merges local guest favorites into the user's database wishlist on login."""
    existing_items = db.query(UserWishlist.destination_id).filter(UserWishlist.user_id == current_user.id).all()
    existing_ids = {item[0] for item in existing_items}

    added_count = 0
    for dest_id in req.destination_ids:
        if dest_id not in existing_ids:
            dest_exists = db.query(Destination.id).filter(Destination.id == dest_id).first()
            if dest_exists:
                db.add(UserWishlist(user_id=current_user.id, destination_id=dest_id))
                existing_ids.add(dest_id)
                added_count += 1

    if added_count > 0:
        db.commit()

    return {"status": "ok", "destination_ids": list(existing_ids)}


@app.get("/api/user/trips")
def get_user_trips(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches all saved trip itineraries for the logged-in user."""
    trips = db.query(SavedTrip).filter(SavedTrip.user_id == current_user.id).order_by(SavedTrip.created_at.desc()).all()
    result = []
    for t in trips:
        try:
            plan_data = json.loads(t.trip_plan_json)
        except Exception:
            plan_data = {}

        result.append({
            "id": t.id,
            "destination_id": t.destination_id,
            "destination_name": t.destination_name,
            "days": t.days,
            "people": t.people,
            "total_budget": t.total_budget,
            "plan_data": plan_data,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return {"trips": result}


@app.post("/api/user/trips/save")
def save_user_trip(req: SaveTripRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Saves a customized trip plan to the user's account."""
    new_trip = SavedTrip(
        user_id=current_user.id,
        destination_id=req.destination_id,
        destination_name=req.destination_name,
        days=req.days,
        people=req.people,
        total_budget=req.total_budget,
        trip_plan_json=req.trip_plan_json,
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    return {"status": "ok", "message": "Trip saved to your profile!", "trip_id": new_trip.id}


@app.delete("/api/user/trips/{trip_id}")
def delete_user_trip(trip_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deletes a saved trip from the user's account."""
    trip = db.query(SavedTrip).filter(
        SavedTrip.id == trip_id,
        SavedTrip.user_id == current_user.id
    ).first()

    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found.")

    db.delete(trip)
    db.commit()
    return {"status": "ok", "message": "Trip deleted successfully."}


# ── Trip Planning ─────────────────────────────────────────────────────────────

DEFAULT_BUDGETS = {
    "mountains": 7000,
    "historical": 3000,
    "nature": 5000,
    "beaches": 4000,
    "cultural": 5000,
    "museum": 2500,
    "wildlife": 5500,
    "adventure": 6500,
    "sightseeing": 4000,
}


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    AI Chat endpoint — dynamically routes to live AI agent (Groq or Claude)
    if API keys are set, or seamlessly uses the rule-based simulation agent.
    Both modes are enhanced with RAG knowledge base retrieval.
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    has_live_key = (groq_key and groq_key != "your_key_here") or (anthropic_key and anthropic_key != "your_key_here")

    if has_live_key:
        try:
            from agent import run_agent
            reply = run_agent(req.message)
            engine = "groq" if (groq_key and groq_key != "your_key_here") else "claude"
            return {"reply": reply, "engine": engine, "rag_enabled": _RAG_READY}
        except Exception as e:
            print(f"[agent fallback] Error with live agent: {e}. Falling back to mock agent.")
            reply = run_mock_agent(req.message)
            return {"reply": reply, "engine": "mock", "rag_enabled": _RAG_READY, "notice": f"Fallback to rule engine: {e}"}
    else:
        reply = run_mock_agent(req.message)
        return {"reply": reply, "engine": "mock", "rag_enabled": _RAG_READY}


@app.post("/plan-trip")
def plan_trip(req: TripRequest, db: Session = Depends(get_db)):
    """
    The planning endpoint — filters destinations by budget, days, province,
    district (city), and category. Returns primary plan, cost breakdown,
    day-by-day itinerary, and alternative destination options.
    """
    per_day_budget = req.budget // req.days if req.days else None
    matches = search_destinations(
        province=req.province,
        district=req.district,
        max_budget_per_day=per_day_budget,
        category=req.category,
    )
    if not matches:
        return {
            "error": "No destinations matched this criteria. Try selecting a different city, interest, or increasing your budget."
        }

    chosen_id = matches[0]["id"]
    details = get_destination_details(chosen_id)

    # Patch missing budget using defaults if needed
    if not details.get("estimated_budget_per_day"):
        cat = (details.get("category") or "").lower()
        details["estimated_budget_per_day"] = DEFAULT_BUDGETS.get(cat, 5000)

    cost = estimate_cost(
        chosen_id, days=req.days, people=req.people,
        travel_style=req.travel_style or "standard",
        from_city=req.from_city, include_hotel=req.include_hotel,
    )

    if req.travel_style:
        best_tier = req.travel_style
    else:
        best_tier = None
        if cost and cost.get("tier_comparisons"):
            tiers_by_price = sorted(
                cost["tier_comparisons"].items(),
                key=lambda kv: kv[1]["total_pkr"],
            )
            for tier_name, tier_data in reversed(tiers_by_price):
                if tier_data["total_pkr"] <= req.budget:
                    best_tier = tier_name
                    break
            if best_tier is None:
                best_tier = tiers_by_price[0][0]

    if best_tier and best_tier != cost.get("travel_style"):
        cost = estimate_cost(
            chosen_id, days=req.days, people=req.people, travel_style=best_tier,
            from_city=req.from_city, include_hotel=req.include_hotel,
        )

    cost["within_budget"] = bool(cost["total_pkr"] <= req.budget)
    cost["requested_budget"] = req.budget

    itinerary = generate_itinerary(chosen_id, days=req.days)

    dest_row = db.query(Destination).filter(Destination.id == chosen_id).first()
    image_url = None
    image_attribution = None
    if dest_row and dest_row.images:
        first_img = dest_row.images[0]
        image_url = first_img.image_url
        image_attribution = first_img.attribution

    alternatives = []
    for alt in matches[1:4]:
        alternatives.append({
            "id": alt["id"],
            "name": alt["name"],
            "province": alt["province"],
            "district": alt.get("district"),
            "category": alt.get("category"),
            "estimated_budget_per_day": alt.get("estimated_budget_per_day"),
        })

    rec_data = get_recommendations_for_destination(
        district=details.get("district"),
        province=details.get("province"),
        category=details.get("category"),
        budget_per_day=details.get("estimated_budget_per_day"),
    )

    similar_raw = get_similar_destinations(destination_id=chosen_id, top_n=4)
    similar_destinations = []
    for item in similar_raw.get("similar", []):
        sim_dest = db.query(Destination).filter(Destination.id == item["id"]).first()
        if not sim_dest:
            continue
        sim_image = sim_dest.images[0].image_url if sim_dest.images else None
        similar_destinations.append({
            "id": sim_dest.id,
            "name": sim_dest.name,
            "province": sim_dest.province,
            "district": sim_dest.district,
            "category": sim_dest.category,
            "estimated_budget_per_day": sim_dest.estimated_budget_per_day,
            "image_url": sim_image,
        })

    # RAG: Fetch relevant travel knowledge for this destination
    rag_knowledge = []
    try:
        dest_name = details.get("name", "")
        district_name = details.get("district", "")
        rag_query = f"{dest_name} {district_name} travel tips weather attractions"
        rag_result = rag_search(query=rag_query, top_k=4)
        rag_knowledge = rag_result.get("results", [])
    except Exception:
        pass

    return {
        "destination": details,
        "cost": cost,
        "itinerary": itinerary,
        "image_url": image_url,
        "image_attribution": image_attribution,
        "latitude": details.get("latitude"),
        "longitude": details.get("longitude"),
        "alternatives": alternatives,
        "restaurants": rec_data.get("restaurants", []),
        "hotels": rec_data.get("hotels", []),
        "similar_destinations": similar_destinations,
        "rag_knowledge": rag_knowledge,
    }


# ── ML / Budget Prediction ────────────────────────────────────────────────────

@app.post("/predict-budget")
def predict_budget_endpoint(req: BudgetPredictionRequest):
    """
    ML-based budget-per-day estimate (Random Forest, trained on all 154 destinations).
    """
    try:
        return predict_budget(
            province=req.province,
            category=req.category,
            recommended_days=req.recommended_days,
            activities=req.activities,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Budget prediction failed: {e}")


@app.post("/predict-budget/explain")
def explain_budget_endpoint(req: BudgetPredictionRequest):
    """
    Explainable AI (SHAP) breakdown of a budget prediction.
    """
    try:
        return explain_budget_prediction(
            province=req.province,
            category=req.category,
            recommended_days=req.recommended_days,
            activities=req.activities,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {e}")


@app.get("/destinations/{destination_id}/similar")
def get_similar_destinations_endpoint(destination_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    """
    ML-based 'similar destinations' recommendation (KMeans clustering).
    """
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")

    result = get_similar_destinations(destination_id=destination_id, top_n=top_n)

    enriched = []
    for item in result["similar"]:
        sim_dest = db.query(Destination).filter(Destination.id == item["id"]).first()
        if not sim_dest:
            continue
        image_url = None
        if sim_dest.images:
            image_url = sim_dest.images[0].image_url
        enriched.append({
            "id": sim_dest.id,
            "name": sim_dest.name,
            "province": sim_dest.province,
            "district": sim_dest.district,
            "category": sim_dest.category,
            "estimated_budget_per_day": sim_dest.estimated_budget_per_day,
            "image_url": image_url,
            "similarity_distance": item["distance"],
        })

    return {"destination_id": destination_id, "cluster": result["cluster"], "similar": enriched}


@app.get("/destinations/{destination_id}/recommendations")
def get_dest_recommendations(destination_id: int, db: Session = Depends(get_db)):
    """Returns curated restaurant and hotel recommendations for a destination."""
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    return get_recommendations_for_destination(
        district=dest.district,
        province=dest.province,
        category=dest.category,
        budget_per_day=dest.estimated_budget_per_day,
    )


# ── Auth Extras ───────────────────────────────────────────────────────────────

@app.post("/auth/verify-otp")
def verify_otp(identifier: str, otp: str, db: Session = Depends(get_db)):
    """Verifies the 6-digit OTP sent during registration."""
    cleaned = identifier.strip()
    user = db.query(User).filter(
        (User.email == cleaned.lower()) | (User.phone_number == cleaned)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    if user.verification_code == otp:
        user.is_verified = True
        user.verification_code = None
        db.commit()
        return {"status": "success", "message": "Account verified successfully! You can now log in."}
    raise HTTPException(status_code=400, detail="Invalid verification code.")


@app.post("/auth/phone-register", response_model=TokenResponse)
def phone_register(phone_number: str, username: str, password: str, full_name: Optional[str] = None, db: Session = Depends(get_db)):
    """Creates a phone-based account and logs the user in immediately."""
    phone = phone_number.strip()
    existing_phone = db.query(User).filter(User.phone_number == phone).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="This phone number is already registered.")
    existing_username = db.query(User).filter(User.username == username.strip()).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="This username is already taken.")

    user = User(
        username=username.strip(),
        phone_number=phone,
        hashed_password=hash_password(password),
        full_name=full_name if full_name else username.strip(),
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.delete("/user/delete-account")
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current_user)
    db.commit()
    return {"status": "success", "message": "Your profile has been permanently removed."}


if __name__ == "__main__":
    import sys
    import uvicorn
    import webbrowser
    import threading
    import time

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    def open_browser():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8000")

    print("\n>> Starting Pakistan Travel Agent (with RAG)...")
    print(">> Automatically launching http://127.0.0.1:8000 in your browser...\n")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
