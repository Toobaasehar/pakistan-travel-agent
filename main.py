"""
Pakistan Travel Agent — Backend Entry Point
=============================================
Phase 6: now also serves the web UI (static/index.html) and a
/plan-trip endpoint that the frontend calls to get a full trip plan.

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

# Automatically create all database tables (including users, user_wishlists, saved_trips)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pakistan Travel Agent API",
    description="Backend for an AI-powered trip planner for Pakistan tourism.",
    version="1.1.0",
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return {"status": "ok", "version": "1.0.0"}


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


class TripRequest(BaseModel):
    budget: int = Field(..., gt=0, description="Total budget in PKR")
    days: int = Field(..., gt=0, description="Number of trip days")
    category: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    people: int = Field(default=1, gt=0, description="Number of travelers")
    travel_style: Optional[str] = "budget"
    transport_mode: Optional[str] = None
    currency: Optional[str] = "PKR"
    is_local_or_day_trip: Optional[bool] = None


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


# --- Authentication Endpoints ---
@app.post("/auth/register", response_model=TokenResponse)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    existing_username = db.query(User).filter(User.username == req.username.strip()).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="This username is already taken.")
    
    hashed_pw = hash_password(req.password)
    otp_code = generate_verification_code()

    user = User(
        username=req.username.strip(),
        email=req.email.lower().strip(),
        hashed_password=hashed_pw,
        full_name=req.full_name.strip() if req.full_name else req.username.strip(),
        is_verified=False,
        verification_code=otp_code
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"\n========================================\n OTP VERIFICATION CODE FOR {user.email}: {otp_code} \n========================================\n")
    return {"access_token": "pending_verification", "token_type": "bearer", "user": user}


@app.post("/auth/login", response_model=TokenResponse)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates user credentials and issues a signed JWT access token."""
    identifier = req.email_or_username.lower().strip()
    user = db.query(User).filter(
        (User.email == identifier) | (User.username.ilike(identifier))
    ).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is deactivated.",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your email is not verified yet. Please submit your OTP code first."
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


# --- User Data Endpoints (Wishlist & Saved Trips) ---
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
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    has_live_key = (groq_key and groq_key != "your_key_here") or (anthropic_key and anthropic_key != "your_key_here")

    if has_live_key:
        try:
            from agent import run_agent
            reply = run_agent(req.message)
            engine = "groq" if (groq_key and groq_key != "your_key_here") else "claude"
            return {"reply": reply, "engine": engine}
        except Exception as e:
            print(f"[agent fallback] Error with live agent: {e}. Falling back to mock agent.")
            reply = run_mock_agent(req.message)
            return {"reply": reply, "engine": "mock", "notice": f"Fallback to rule engine: {e}"}
    else:
        reply = run_mock_agent(req.message)
        return {"reply": reply, "engine": "mock"}


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
        # Relax budget constraint so user still gets the best destination for their city/interest
        matches = search_destinations(
            province=req.province,
            district=req.district,
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

    # Determine day trip / local resident status
    is_day_trip = (req.days == 1) or bool(req.is_local_or_day_trip)

    # Honor user's travel style or pick best fitting tier
    target_tier = (req.travel_style or "budget").lower().strip()
    cost = estimate_cost(
        chosen_id,
        days=req.days,
        people=req.people,
        travel_style=target_tier,
        transport_mode=req.transport_mode,
        currency=req.currency or "PKR",
        user_budget=req.budget,
        is_local_or_day_trip=is_day_trip,
    )

    # If the user-selected tier exceeds budget, check if a cheaper tier fits nicely
    if cost and cost.get("total_pkr", 0) > req.budget and cost.get("tier_comparisons"):
        tiers_by_price = sorted(
            cost["tier_comparisons"].items(),
            key=lambda kv: kv[1]["total_pkr"],
        )
        for tier_name, tier_data in tiers_by_price:
            if tier_data["total_pkr"] <= req.budget:
                target_tier = tier_name
                cost = estimate_cost(
                    chosen_id,
                    days=req.days,
                    people=req.people,
                    travel_style=target_tier,
                    transport_mode=req.transport_mode,
                    currency=req.currency or "PKR",
                    user_budget=req.budget,
                    is_local_or_day_trip=is_day_trip,
                )
                break

    cost["within_budget"] = bool(cost["total_pkr"] <= req.budget)
    cost["requested_budget"] = req.budget
    cost["savings_pkr"] = max(0, req.budget - cost["total_pkr"])

    itinerary = generate_itinerary(chosen_id, days=req.days)

    dest_row = db.query(Destination).filter(Destination.id == chosen_id).first()
    image_url = None
    image_attribution = None
    if dest_row and dest_row.images:
        first_img = dest_row.images[0]
        image_url = first_img.image_url
        image_attribution = first_img.attribution

    # Alternative destination suggestions matching the same criteria
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

    # ML-based "similar destinations" (KMeans clustering), enriched with
    # display info so the frontend doesn't need a second round-trip.
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
    }


@app.post("/predict-budget")
def predict_budget_endpoint(req: BudgetPredictionRequest):
    """
    ML-based budget-per-day estimate (Random Forest, trained on all 154 destinations)
    for a destination profile that may not exist in the database yet. Lets the
    'Plan a Trip' form give the user a live cost estimate by province/category/duration
    before an exact destination match is found.
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
    Explainable AI (SHAP) breakdown of a budget prediction — shows which
    factors (province, category, duration, activity count) pushed the
    estimate up or down, and by how much. Useful for a "why this estimate?"
    UI element next to the plain /predict-budget number.
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
    ML-based 'similar destinations' recommendation (KMeans clustering on
    province, category, budget, duration, and activity count). Returns the
    closest destinations within the same cluster, with full details attached.
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

@app.post("/auth/verify-otp")
def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    if user.verification_code == otp:
        user.is_verified = True
        user.verification_code = None
        db.commit()
        return {"status": "success", "message": "Email verified successfully! You can now log in."}
    raise HTTPException(status_code=400, detail="Invalid verification code.")

@app.post("/auth/phone-register", response_model=UserResponse)
def phone_register(phone_number: str, username: str, full_name: Optional[str] = None, db: Session = Depends(get_db)):
    existing_phone = db.query(User).filter(User.phone_number == phone_number.strip()).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="This phone number is already registered.")
        user = User(username=username.strip(), phone_number=phone_number.strip(), full_name=full_name if full_name else username, is_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

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

    print("\n>> Starting Pakistan Travel Agent...")
    print(">> Automatically launching http://127.0.0.1:8000 in your browser...\n")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
