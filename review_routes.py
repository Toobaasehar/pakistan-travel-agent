"""
review_routes.py
=================
FastAPI router for the reviews feature.

- GET routes are public (no login required) — anyone can browse reviews.
- POST/DELETE routes require a logged-in user (auth.get_current_user) —
  see reviews.py's add_review()/delete_review() docstrings for why.

Wired into main.py via:
    from review_routes import router as reviews_router
    app.include_router(reviews_router)
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from models import User
from review_models import ReviewCreate, ReviewResponse, ReviewSummary
from auth import get_current_user
import reviews as reviews_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_review(data: ReviewCreate, user: User = Depends(get_current_user)):
    """Create a new review. Requires login. Marked verified if linked to a real trip."""
    try:
        return reviews_service.add_review(data, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ReviewResponse])
def list_all_reviews(limit: int = 50):
    """Public: latest reviews across all destinations."""
    return reviews_service.get_all_reviews(limit=limit)


@router.get("/destination/{destination_name}", response_model=List[ReviewResponse])
def list_reviews_for_destination(destination_name: str, limit: int = 20):
    """Public: list reviews for one specific destination."""
    return reviews_service.get_reviews_by_destination(destination_name, limit=limit)


@router.get("/summary/{destination_name}", response_model=ReviewSummary)
def destination_review_summary(destination_name: str):
    """Public: average rating, rating breakdown, and top reviews for a destination."""
    summary = reviews_service.get_destination_summary(destination_name)
    if summary is None:
        raise HTTPException(status_code=404, detail="No reviews found for this destination.")
    return summary


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int):
    """Public: fetch a single review by its id."""
    review = reviews_service.get_review_by_id(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review


@router.delete("/{review_id}")
def remove_review(review_id: int, user: User = Depends(get_current_user)):
    """Delete a review. Requires login, and you can only delete your own review."""
    try:
        deleted = reviews_service.delete_review(review_id, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found.")
    return {"success": True, "review_id": review_id}
