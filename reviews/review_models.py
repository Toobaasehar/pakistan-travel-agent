from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ReviewCreate(BaseModel):
    destination_name: str = Field(..., min_length=2, max_length=100)
    reviewer_name: str = Field(..., min_length=2, max_length=50)
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., min_length=3, max_length=100)
    comment: str = Field(..., min_length=10, max_length=1000)
    visited_month: Optional[str] = Field(None)

    @field_validator("rating")
    @classmethod
    def check_rating_range(cls, v):
        if v not in [1, 2, 3, 4, 5]:
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("reviewer_name")
    @classmethod
    def strip_reviewer_name(cls, v):
        if not v.strip():
            raise ValueError("Reviewer name cannot be blank")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "destination_name": "Lahore",
                "reviewer_name": "Ahmed",
                "rating": 5,
                "title": "Incredible food and culture",
                "comment": "Lahore blew me away. The food street at Gawalmandi is something else entirely.",
                "visited_month": "August 2026"
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
    visited_month: Optional[str]
    created_at: str
    is_verified: bool

    model_config = {"from_attributes": True}


class ReviewSummary(BaseModel):
    destination_name: str
    total_reviews: int
    average_rating: float
    rating_breakdown: dict
    reviews: list[ReviewResponse]


class ReviewDeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_id: int
