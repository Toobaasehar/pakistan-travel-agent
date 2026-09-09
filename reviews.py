import sqlite3
from datetime import datetime
from typing import Optional
from review_models import ReviewCreate, ReviewResponse, ReviewSummary


DB_PATH = "travel.db"


def create_reviews_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_name  TEXT    NOT NULL,
            reviewer_name     TEXT    NOT NULL,
            rating            INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            title             TEXT    NOT NULL,
            comment           TEXT    NOT NULL,
            visited_month     TEXT,
            created_at        TEXT    NOT NULL,
            is_verified       INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_destination
        ON reviews(destination_name)
    """)

    conn.commit()
    conn.close()


def add_review(data: ReviewCreate) -> ReviewResponse:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO reviews
            (destination_name, reviewer_name, rating, title, comment, visited_month, created_at, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.destination_name.strip(),
        data.reviewer_name.strip(),
        data.rating,
        data.title.strip(),
        data.comment.strip(),
        data.visited_month,
        created_at,
        0
    ))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return ReviewResponse(
        id=new_id,
        destination_name=data.destination_name,
        reviewer_name=data.reviewer_name,
        rating=data.rating,
        title=data.title,
        comment=data.comment,
        visited_month=data.visited_month,
        created_at=created_at,
        is_verified=False
    )


def get_reviews_by_destination(destination_name: str, limit: int = 20) -> list[ReviewResponse]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, destination_name, reviewer_name, rating, title, comment,
               visited_month, created_at, is_verified
        FROM reviews
        WHERE LOWER(destination_name) = LOWER(?)
        ORDER BY created_at DESC
        LIMIT ?
    """, (destination_name, limit))

    rows = cursor.fetchall()
    conn.close()

    return [_row_to_review(row) for row in rows]


def get_all_reviews(limit: int = 50) -> list[ReviewResponse]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, destination_name, reviewer_name, rating, title, comment,
               visited_month, created_at, is_verified
        FROM reviews
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [_row_to_review(row) for row in rows]


def get_destination_summary(destination_name: str) -> Optional[ReviewSummary]:
    reviews = get_reviews_by_destination(destination_name, limit=100)

    if not reviews:
        return None

    total = len(reviews)
    avg = round(sum(r.rating for r in reviews) / total, 1)

    breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        breakdown[r.rating] += 1

    return ReviewSummary(
        destination_name=destination_name,
        total_reviews=total,
        average_rating=avg,
        rating_breakdown=breakdown,
        reviews=reviews[:10]
    )


def delete_review(review_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def get_review_by_id(review_id: int) -> Optional[ReviewResponse]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, destination_name, reviewer_name, rating, title, comment,
               visited_month, created_at, is_verified
        FROM reviews WHERE id = ?
    """, (review_id,))

    row = cursor.fetchone()
    conn.close()

    return _row_to_review(row) if row else None


def _row_to_review(row) -> ReviewResponse:
    return ReviewResponse(
        id=row[0],
        destination_name=row[1],
        reviewer_name=row[2],
        rating=row[3],
        title=row[4],
        comment=row[5],
        visited_month=row[6],
        created_at=row[7],
        is_verified=bool(row[8])
    )
