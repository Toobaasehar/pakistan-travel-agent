from fastapi import APIRouter, HTTPException, status
from review_models import ReviewCreate, ReviewResponse, ReviewSummary, ReviewDeleteResponse
from reviews import (
    add_review,
    get_reviews_by_destination,
    get_all_reviews,
    get_destination_summary,
    delete_review,
    get_review_by_id
)


router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(review: ReviewCreate):
    try:
        return add_review(review)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/all", response_model=list[ReviewResponse])
async def list_all_reviews(limit: int = 50):
    return get_all_reviews(limit=limit)


@router.get("/{destination_name}/summary", response_model=ReviewSummary)
async def get_reviews_summary(destination_name: str):
    summary = get_destination_summary(destination_name)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No reviews found for '{destination_name}' yet."
        )

    return summary


@router.get("/{destination_name}", response_model=list[ReviewResponse])
async def get_reviews(destination_name: str, limit: int = 20):
    reviews = get_reviews_by_destination(destination_name, limit=limit)

    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No reviews found for '{destination_name}'."
        )

    return reviews


@router.delete("/{review_id}", response_model=ReviewDeleteResponse)
async def remove_review(review_id: int):
    review = get_review_by_id(review_id)

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} does not exist."
        )

    success = delete_review(review_id)

    return ReviewDeleteResponse(
        success=success,
        message="Review deleted successfully." if success else "Delete failed.",
        deleted_id=review_id
    )
