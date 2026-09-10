"""
Database table models.
=========================
Each class here = one database table. SQLAlchemy's ORM lets us work
with rows as Python objects instead of writing raw SQL for every
insert/query — but it's still translating to real SQL underneath.
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    province = Column(String, nullable=False)  # KPK, Punjab, Sindh, Balochistan
    district = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text)
    best_season = Column(String)
    recommended_days = Column(Integer)
    estimated_budget_per_day = Column(Integer)  # PKR, per person, rough estimate
    activities = Column(String)  # comma-separated for v1 simplicity
    category = Column(String)  # mountains, historical, beaches, etc.
    data_source = Column(String)  # e.g. "Verified via Google Maps, Aug 2026"
    last_verified_at = Column(DateTime, server_default=func.now())

    # Relationships
    images = relationship("DestinationImage", back_populates="destination", cascade="all, delete-orphan")
    wishlist_items = relationship("UserWishlist", back_populates="destination", cascade="all, delete-orphan")


class DestinationImage(Base):
    __tablename__ = "destination_images"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    image_url = Column(String, nullable=False)
    source = Column(String)  # e.g. "Wikimedia Commons"
    author = Column(String)
    license = Column(String)  # e.g. "CC BY-SA 4.0"
    attribution = Column(String)

    destination = relationship("Destination", back_populates="images")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    # email is intentionally nullable: /auth/phone-register creates accounts
    # with a phone_number and no email. login() looks a user up by either
    # field, so at least one of email/phone_number should be set in practice.
    email = Column(String(128), unique=True, index=True, nullable=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)
    verification_code_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    wishlist = relationship("UserWishlist", back_populates="user", cascade="all, delete-orphan")
    saved_trips = relationship("SavedTrip", back_populates="user", cascade="all, delete-orphan")


class UserWishlist(Base):
    __tablename__ = "user_wishlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "destination_id", name="uq_user_destination_wishlist"),
    )

    user = relationship("User", back_populates="wishlist")
    destination = relationship("Destination", back_populates="wishlist_items")


class SavedTrip(Base):
    __tablename__ = "saved_trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=True)
    destination_name = Column(String(150), nullable=False)
    days = Column(Integer, nullable=False)
    people = Column(Integer, nullable=False, default=1)
    total_budget = Column(Integer, nullable=False)
    trip_plan_json = Column(Text, nullable=False)  # Serialized plan & cost details
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="saved_trips")
    reviews = relationship("Review", back_populates="trip", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    # Who wrote it -- reviews always require a logged-in user now (no more
    # free-text reviewer_name the client could set to anything).
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Which trip prompted this review, if any. Nullable because a user might
    # still want to review a destination they didn't plan through this app's
    # trip planner (e.g. from the destination page directly).
    trip_id = Column(Integer, ForeignKey("saved_trips.id"), nullable=True, index=True)
    destination_name = Column(String(150), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5, enforced in review_models.ReviewCreate
    title = Column(String(100), nullable=False)
    comment = Column(Text, nullable=False)
    visited_month = Column(String(50), nullable=True)
    is_verified = Column(Boolean, default=False)  # True if trip_id links to a real completed trip
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    trip = relationship("SavedTrip", back_populates="reviews")

