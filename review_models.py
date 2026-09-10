from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class ReviewCreate(BaseModel):
    """
    What the client sends to create a review. Notably absent:
    reviewer_name -- who wrote the review is always taken from the logged-in
    user's JWT (see review_routes.submit_review), never from client input,
    so nobody can post a review under someone else's name.
    """
    destination_name: str = Field(..., min_length=2, max_length=150)
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., min_length=3, max_length=100)
    comment: str = Field(..., min_length=10, max_length=1000)
    visited_month: Optional[str] = Field(None, max_length=50)
    # If this review follows a trip the user planned & saved in this app,
    # pass that trip's id here -- it marks the review as "Verified Trip" and
    # confirms the destination_name matches what they actually planned.
    trip_id: Optional[int] = Field(None)

    @field_validator("rating")
    @classmethod
    def check_rating_range(cls, v):
        if v not in [1, 2, 3, 4, 5]:
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("destination_name", "title", "comment")
    @classmethod
    def strip_text_fields(cls, v):
        if not v.strip():
            raise ValueError("This field cannot be blank")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "destination_name": "Lahore",
                "rating": 5,
                "title": "Incredible food and culture",
                "comment": "Lahore blew me away. The food street at Gawalmandi is something else entirely.",
                "visited_month": "August 2026",
                "trip_id": 42,
            }
        }
    }


class ReviewResponse(BaseModel):
    id: int
    destination_name: str
    reviewer_name: str
    rating: int
    title: str
    comment: str
    visited_month: Optional[str] = None
    created_at: str
    is_verified: bool

    model_config = {"from_attributes": True}


class ReviewSummary(BaseModel):
    destination_name: str
    total_reviews: int
    average_rating: float
    rating_breakdown: dict
    reviews: List[ReviewResponse]


class ReviewDeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_id: int
