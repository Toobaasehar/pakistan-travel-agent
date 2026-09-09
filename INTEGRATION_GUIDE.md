# Review Feature — Integration Guide

## New Files to Add
Copy these 4 files into your project root:
- `review_models.py`
- `reviews.py`
- `review_routes.py`
- `review_ui.py`

---

## Changes to main.py

Add at the top with your other imports:
```python
from review_routes import router as review_router
from reviews import create_reviews_table
```

Add inside your startup event:
```python
@app.on_event("startup")
async def startup_event():
    create_reviews_table()
```

Register the router (next to your other routers):
```python
app.include_router(review_router)
```

---

## Changes to app_streamlit.py

Add at the top:
```python
from review_ui import show_reviews_section
```

Add a Reviews tab wherever your navigation is:
```python
tab1, tab2, tab3 = st.tabs(["Home", "Destinations", "Reviews"])

with tab3:
    show_reviews_section()
```

---

## API Endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| POST | `/reviews/` | Submit a new review |
| GET | `/reviews/{destination}` | Get reviews for a destination |
| GET | `/reviews/{destination}/summary` | Avg rating + breakdown |
| GET | `/reviews/all` | All reviews (admin use) |
| DELETE | `/reviews/{id}` | Delete a review by ID |

Auto-generated docs available at: `http://127.0.0.1:8000/docs`

---

## Quick Test (after server is running)

```bash
# Submit a review
curl -X POST http://127.0.0.1:8000/reviews/ \
  -H "Content-Type: application/json" \
  -d '{"destination_name":"Lahore","reviewer_name":"Ahmed","rating":5,"title":"Amazing city","comment":"The food and history here is unmatched."}'

# Get reviews
curl http://127.0.0.1:8000/reviews/Lahore

# Get summary
curl http://127.0.0.1:8000/reviews/Lahore/summary
```
