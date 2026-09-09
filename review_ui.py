import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"


def stars(rating: int) -> str:
    return "⭐" * rating + "☆" * (5 - rating)


def rating_color(rating: int) -> str:
    if rating >= 4:
        return "#28a745"
    elif rating == 3:
        return "#ffc107"
    return "#dc3545"


def submit_review_tab():
    st.subheader("Write a Review")

    with st.form("review_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            destination = st.text_input("Destination", placeholder="e.g. Lahore, Hunza, Swat")
            name = st.text_input("Your Name", placeholder="e.g. Ahmed")
            visited = st.text_input("When did you visit? (optional)", placeholder="e.g. August 2026")

        with col2:
            rating = st.slider("Rating", min_value=1, max_value=5, value=4)
            st.markdown(f"**Your rating:** {stars(rating)} ({rating}/5)")

        title = st.text_input("Review Title", placeholder="e.g. Best trip of my life!", max_chars=100)
        comment = st.text_area("Your Review", placeholder="Share what you loved, what could be better...", max_chars=1000, height=150)

        submitted = st.form_submit_button("Submit Review", use_container_width=True)

        if submitted:
            if not destination.strip():
                st.error("Please enter a destination.")
            elif not name.strip():
                st.error("Please enter your name.")
            elif not title.strip():
                st.error("Please add a title to your review.")
            elif len(comment.strip()) < 10:
                st.error("Review is too short — add a bit more detail.")
            else:
                payload = {
                    "destination_name": destination.strip(),
                    "reviewer_name": name.strip(),
                    "rating": rating,
                    "title": title.strip(),
                    "comment": comment.strip(),
                    "visited_month": visited.strip() or None
                }

                try:
                    res = requests.post(f"{API_BASE}/reviews/", json=payload, timeout=10)

                    if res.status_code == 201:
                        st.success(f"Thanks, {name}! Your review has been posted.")
                        st.balloons()
                    else:
                        st.error(res.json().get("detail", "Something went wrong."))

                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Make sure the backend is running.")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")


def browse_reviews_tab():
    st.subheader("Browse Destination Reviews")

    col1, col2 = st.columns([3, 1])
    with col1:
        destination = st.text_input("Search destination", placeholder="e.g. Karachi, Gilgit, Lahore", key="browse_dest")
    with col2:
        limit = st.selectbox("Show", [5, 10, 20, 50], index=1)

    if not destination.strip():
        return

    try:
        summary_res = requests.get(f"{API_BASE}/reviews/{destination.strip()}/summary", timeout=10)

        if summary_res.status_code == 200:
            s = summary_res.json()

            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Reviews", s["total_reviews"])
            c2.metric("Average Rating", f"{s['average_rating']} / 5")

            breakdown = s["rating_breakdown"]
            five_star_pct = int((breakdown.get("5", 0) / s["total_reviews"]) * 100) if s["total_reviews"] else 0
            c3.metric("5-Star Reviews", f"{five_star_pct}%")

            st.markdown("**Rating breakdown:**")
            for star in [5, 4, 3, 2, 1]:
                count = breakdown.get(str(star), breakdown.get(star, 0))
                pct = count / s["total_reviews"] if s["total_reviews"] else 0
                bar = "█" * int(pct * 20) + "░" * (20 - int(pct * 20))
                st.markdown(f"{stars(star)} &nbsp; `{count}` &nbsp; {bar} {int(pct * 100)}%", unsafe_allow_html=True)

            st.markdown("---")

        elif summary_res.status_code == 404:
            st.info(f"No reviews for '{destination}' yet. Be the first to write one!")
            return

        reviews_res = requests.get(
            f"{API_BASE}/reviews/{destination.strip()}",
            params={"limit": limit},
            timeout=10
        )

        if reviews_res.status_code == 200:
            for r in reviews_res.json():
                color = rating_color(r["rating"])
                verified = " &nbsp; ✅ Verified" if r.get("is_verified") else ""
                visited_str = f"&nbsp;|&nbsp; 📅 {r['visited_month']}" if r.get("visited_month") else ""

                st.markdown(f"""
                <div style="
                    border: 1px solid #e0e0e0;
                    border-left: 4px solid {color};
                    border-radius: 8px;
                    padding: 14px 18px;
                    margin: 10px 0;
                    background: #fafafa;
                ">
                    <div style="display:flex; justify-content:space-between;">
                        <strong style="color:#2c3e50;">{r['title']}</strong>
                        <span>{stars(r['rating'])}</span>
                    </div>
                    <p style="color:#444; margin:8px 0 4px;">{r['comment']}</p>
                    <small style="color:#888;">
                        👤 {r['reviewer_name']}
                        {visited_str}
                        &nbsp;|&nbsp; 🗓 {r['created_at'][:10]}
                        {verified}
                    </small>
                </div>
                """, unsafe_allow_html=True)

        elif reviews_res.status_code == 404:
            st.info("No reviews found.")

    except requests.exceptions.ConnectionError:
        st.error("Backend not reachable. Is the server running?")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_reviews_section():
    st.title("Reviews & Feedback")
    st.markdown("Real traveler experiences across Pakistan.")

    tab1, tab2 = st.tabs(["Write a Review", "Browse Reviews"])

    with tab1:
        submit_review_tab()

    with tab2:
        browse_reviews_tab()


if __name__ == "__main__":
    show_reviews_section()
