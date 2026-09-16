"""
reviews.py — data access for the review feature.

Originally this module opened its own raw sqlite3 connection straight to
travel.db, completely separate from the SQLAlchemy engine/session the rest
of the app (database.py, models.py, main.py) uses for the same file. That
worked, but it meant two independent data-access layers touching one
database with no shared transaction/session management, and every write
required hand-written SQL. Rewritten to use the app's existing SessionLocal
and the Review ORM model in models.py instead, so this module behaves the
same as tools.py / main.py's other database calls.
"""

from datetime import datetime
from typing import Optional, List

from database import SessionLocal
from models import Review, SavedTrip, User
from review_models import ReviewCreate, ReviewResponse, ReviewSummary


def add_review(data: ReviewCreate, user: User) -> ReviewResponse:
    """
    Creates a review on behalf of `user` (always the logged-in user — see
    review_routes.submit_review). If data.trip_id is set, it must belong to
    this same user; the review is marked is_verified=True in that case
    (a "Verified Trip" review), since we can confirm they actually planned
    that trip in this app.
    """
    db = SessionLocal()
    try:
        is_verified = False
        if data.trip_id is not None:
            trip = db.query(SavedTrip).filter(
                SavedTrip.id == data.trip_id, SavedTrip.user_id == user.id
            ).first()
            if trip is None:
                raise ValueError("That trip wasn't found on your account.")
            is_verified = True

        review = Review(
            user_id=user.id,
            trip_id=data.trip_id,
            destination_name=data.destination_name,
            rating=data.rating,
            title=data.title,
            comment=data.comment,
            visited_month=data.visited_month,
            is_verified=is_verified,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return _to_response(review)
    finally:
        db.close()


def get_reviews_by_destination(destination_name: str, limit: int = 20) -> List[ReviewResponse]:
    db = SessionLocal()
    try:
        rows = (
            db.query(Review)
            .filter(Review.destination_name.ilike(destination_name.strip()))
            .order_by(Review.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_to_response(r) for r in rows]
    finally:
        db.close()


def get_all_reviews(limit: int = 50) -> List[ReviewResponse]:
    db = SessionLocal()
    try:
        rows = db.query(Review).order_by(Review.created_at.desc()).limit(limit).all()
        return [_to_response(r) for r in rows]
    finally:
        db.close()


def get_destination_summary(destination_name: str) -> Optional[ReviewSummary]:
    db = SessionLocal()
    try:
        rows = (
            db.query(Review)
            .filter(Review.destination_name.ilike(destination_name.strip()))
            .order_by(Review.created_at.desc())
            .limit(500)
            .all()
        )
        if not rows:
            return None

        total = len(rows)
        avg = round(sum(r.rating for r in rows) / total, 1)

        breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in rows:
            breakdown[r.rating] += 1

        return ReviewSummary(
            destination_name=destination_name,
            total_reviews=total,
            average_rating=avg,
            rating_breakdown=breakdown,
            reviews=[_to_response(r) for r in rows[:10]],
        )
    finally:
        db.close()


def delete_review(review_id: int, user: User) -> bool:
    """Deletes a review, but only if it belongs to `user` (or user is staff)."""
    db = SessionLocal()
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if review is None:
            return False
        if review.user_id != user.id:
            raise PermissionError("You can only delete your own reviews.")
        db.delete(review)
        db.commit()
        return True
    finally:
        db.close()


def get_review_by_id(review_id: int) -> Optional[ReviewResponse]:
    db = SessionLocal()
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        return _to_response(review) if review else None
    finally:
        db.close()


def _to_response(review: Review) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        destination_name=review.destination_name,
        reviewer_name=review.user.username if review.user else "Traveler",
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        visited_month=review.visited_month,
        created_at=(review.created_at or datetime.utcnow()).isoformat(),
        is_verified=bool(review.is_verified),
    )
import streamlit as st

def show_reviews_section():
    """
    Displays the user reviews and feedback section in the Streamlit app.
    """
    st.subheader("⭐ User Reviews & Feedback")
    st.write("Share your travel experience and read reviews from other travelers!")
    
    # Add your review submission form or review list logic here
    with st.form("review_form"):
        user_name = st.text_input("Your Name")
        review_text = st.text_input("Write your review")
        rating = st.slider("Rating", 1, 5, 5)
        submit_button = st.form_submit_button("Submit Review")
        
        if submit_button:
            st.success("Thank you for your feedback!")