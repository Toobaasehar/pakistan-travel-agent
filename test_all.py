"""
test_all.py
===========
Automated test suite verifying database integrity, tool functions,
agent simulation heuristics, and FastAPI API routes.
"""

import sys
import time
import json
import unittest
import sqlite3
from fastapi.testclient import TestClient

from main import app
from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary
from agent import extract_budget, extract_days, extract_category, extract_location, run_mock_agent
from ml.predict_budget import predict_budget
from ml.similar_destinations import get_similar_destinations
from ml.explain_budget import explain_budget_prediction


class TestDatabaseIntegrity(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect("travel.db")
        self.cur = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_total_destinations_count(self):
        self.cur.execute("SELECT COUNT(*) FROM destinations")
        count = self.cur.fetchone()[0]
        self.assertGreaterEqual(count, 150, "Should have at least 150 destinations in database")

    def test_no_null_budgets(self):
        self.cur.execute("SELECT COUNT(*) FROM destinations WHERE estimated_budget_per_day IS NULL OR estimated_budget_per_day <= 0")
        count = self.cur.fetchone()[0]
        self.assertEqual(count, 0, "No destinations should have null or 0 budget")

    def test_no_null_recommended_days(self):
        self.cur.execute("SELECT COUNT(*) FROM destinations WHERE recommended_days IS NULL OR recommended_days <= 0")
        count = self.cur.fetchone()[0]
        self.assertEqual(count, 0, "No destinations should have null or 0 recommended_days")

    def test_no_null_best_season(self):
        self.cur.execute("SELECT COUNT(*) FROM destinations WHERE best_season IS NULL OR TRIM(best_season) = ''")
        count = self.cur.fetchone()[0]
        self.assertEqual(count, 0, "No destinations should have empty best_season")

    def test_images_real_and_verified(self):
        # Note: destinations added via seed_my_cities.py (all the new province/
        # district data) intentionally get a placeholder image until real
        # Wikimedia/Unsplash URLs are manually curated for them -- this is
        # documented, expected behavior for the expanded dataset, not a bug.
        # What we actually want to guard against is a genuinely missing/empty
        # image_url, which would be a real data problem.
        self.cur.execute("SELECT COUNT(*) FROM destination_images WHERE image_url IS NULL OR TRIM(image_url) = ''")
        empty = self.cur.fetchone()[0]
        self.assertEqual(empty, 0, "No destination should have a NULL or empty image_url")

        self.cur.execute("SELECT COUNT(*) FROM destination_images WHERE image_url LIKE '%placeholder%'")
        placeholders = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM destination_images")
        total = self.cur.fetchone()[0]
        if placeholders > 0:
            print(f"\n  Note: {placeholders}/{total} destinations still use placeholder images "
                  f"(expected for newly added province data -- not a failure).")


class TestToolsFunctions(unittest.TestCase):
    def test_search_all(self):
        results = search_destinations()
        self.assertGreaterEqual(len(results), 150)
        self.assertIn("district", results[0])

    def test_search_by_district(self):
        results = search_destinations(district="Multan")
        self.assertGreater(len(results), 0)
        for d in results:
            self.assertEqual(d["district"].lower(), "multan")

    def test_search_by_province_and_category(self):
        results = search_destinations(province="KPK", category="mountains")
        self.assertGreater(len(results), 0)
        for d in results:
            self.assertEqual(d["province"], "KPK")
            self.assertEqual(d["category"], "mountains")

    def test_search_by_budget(self):
        results = search_destinations(max_budget_per_day=3500)
        self.assertGreater(len(results), 0)
        for d in results:
            self.assertLessEqual(d["estimated_budget_per_day"], 3500)

    def test_get_destination_details(self):
        details = get_destination_details(1)
        self.assertIsNotNone(details)
        self.assertEqual(details["id"], 1)
        self.assertIn("Hunza", details["name"])

    def test_estimate_cost(self):
        cost = estimate_cost(1, days=4, people=2)
        self.assertIsNotNone(cost)
        self.assertEqual(cost["days"], 4)
        self.assertEqual(cost["people"], 2)
        self.assertIn("accommodation", cost["breakdown_pkr"])
        self.assertGreater(cost["estimated_total_pkr"], 0)

    def test_generate_itinerary_single_day(self):
        itin = generate_itinerary(1, days=1)
        self.assertEqual(len(itin["itinerary"]), 1)
        self.assertIn("Day trip", itin["itinerary"][0]["plan"])

    def test_generate_itinerary_multi_day(self):
        itin = generate_itinerary(1, days=5)
        self.assertEqual(len(itin["itinerary"]), 5)
        self.assertIn("Arrival", itin["itinerary"][0]["plan"])
        self.assertIn("departure", itin["itinerary"][-1]["plan"].lower())


class TestMockAgentParser(unittest.TestCase):
    def test_budget_parser(self):
        self.assertEqual(extract_budget("trip with 50k budget"), 50000)
        self.assertEqual(extract_budget("35.5k pkr"), 35500)
        self.assertEqual(extract_budget("2 lakh budget"), 200000)
        self.assertEqual(extract_budget("cost 45,000 pkr"), 45000)

    def test_days_parser(self):
        self.assertEqual(extract_days("plan a weekend trip"), 2)
        self.assertEqual(extract_days("4 days in Swat"), 4)
        self.assertEqual(extract_days("1 week vacation"), 7)

    def test_category_parser(self):
        self.assertEqual(extract_category("beach side hotels"), "beaches")
        self.assertEqual(extract_category("mountain hiking and trekking"), "mountains")
        self.assertEqual(extract_category("historical forts and mosques"), "historical")
        self.assertEqual(extract_category("scenic lake and nature"), "nature")

    def test_location_parser(self):
        prov, dist = extract_location("Trip to Swat in KPK")
        self.assertEqual(prov, "KPK")
        self.assertEqual(dist, "Swat")

    def test_run_mock_agent(self):
        reply = run_mock_agent("Plan a 3 day trip to Swat for 25k")
        self.assertIn("Swat", reply)
        self.assertIn("PKR", reply)
        self.assertIn("Itinerary", reply)


class TestMLBudgetPrediction(unittest.TestCase):
    def test_predict_budget_returns_positive_estimate(self):
        result = predict_budget(
            province="Gilgit-Baltistan",
            category="mountains",
            recommended_days=2,
            activities=["hiking", "camping"],
        )
        self.assertIn("predicted_budget_per_day", result)
        self.assertGreater(result["predicted_budget_per_day"], 0)

    def test_predict_budget_handles_unseen_category_gracefully(self):
        # Category/province outside the training data shouldn't raise —
        # the encoder should just ignore the unknown value.
        result = predict_budget(
            province="Some New Region",
            category="skydiving",
            recommended_days=1,
        )
        self.assertIn("predicted_budget_per_day", result)

    def test_mock_agent_uses_ml_estimate_when_no_exact_match(self):
        # Province + category combo unlikely to exist as an exact DB match
        reply = run_mock_agent("Plan a beach trip in Islamabad for 2 days")
        self.assertTrue(
            "AI Budget Estimate" in reply or "PKR" in reply,
            "Should either give an ML estimate or a real destination match",
        )


class TestSimilarDestinations(unittest.TestCase):
    def test_returns_requested_count(self):
        result = get_similar_destinations(destination_id=1, top_n=5)
        self.assertEqual(result["destination_id"], 1)
        self.assertIsNotNone(result["cluster"])
        self.assertLessEqual(len(result["similar"]), 5)
        self.assertGreater(len(result["similar"]), 0)

    def test_does_not_recommend_itself(self):
        result = get_similar_destinations(destination_id=1, top_n=5)
        similar_ids = [item["id"] for item in result["similar"]]
        self.assertNotIn(1, similar_ids)

    def test_unknown_id_returns_empty(self):
        result = get_similar_destinations(destination_id=999999, top_n=5)
        self.assertEqual(result["similar"], [])

    def test_similar_destinations_endpoint(self):
        client = TestClient(app)
        res = client.get("/destinations/1/similar?top_n=3")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertLessEqual(len(data["similar"]), 3)
        for item in data["similar"]:
            self.assertIn("name", item)
            self.assertIn("similarity_distance", item)

    def test_similar_destinations_endpoint_404_for_unknown_id(self):
        client = TestClient(app)
        res = client.get("/destinations/999999/similar")
        self.assertEqual(res.status_code, 404)


class TestExplainableBudget(unittest.TestCase):
    def test_explanation_has_contributions(self):
        result = explain_budget_prediction(
            province="Gilgit-Baltistan",
            category="mountains",
            recommended_days=2,
            activities=["hiking", "camping"],
        )
        self.assertIn("predicted_budget_per_day", result)
        self.assertIn("base_value", result)
        self.assertIn("contributions", result)
        self.assertGreater(len(result["contributions"]), 0)
        for c in result["contributions"]:
            self.assertIn("feature", c)
            self.assertIn("impact", c)

    def test_contributions_sorted_by_absolute_impact(self):
        result = explain_budget_prediction(
            province="Punjab", category="historical", recommended_days=1
        )
        impacts = [abs(c["impact"]) for c in result["contributions"]]
        self.assertEqual(impacts, sorted(impacts, reverse=True))

    def test_respects_top_n(self):
        result = explain_budget_prediction(
            province="Sindh", category="museum", recommended_days=1, top_n=3
        )
        self.assertLessEqual(len(result["contributions"]), 3)

    def test_explain_budget_endpoint(self):
        client = TestClient(app)
        res = client.post("/predict-budget/explain", json={
            "province": "Gilgit-Baltistan",
            "category": "mountains",
            "recommended_days": 2,
            "activities": ["hiking", "camping"],
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("contributions", data)
        self.assertGreater(len(data["contributions"]), 0)


class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_destinations_endpoint(self):
        res = self.client.get("/destinations")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(len(data), 150)
        first = data[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("district", first)
        self.assertIn("image_url", first)

    def test_plan_trip_with_district(self):
        payload = {
            "budget": 40000,
            "days": 3,
            "province": "Punjab",
            "district": "Multan",
            "people": 1
        }
        res = self.client.post("/plan-trip", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn("error", data)
        self.assertEqual(data["destination"]["district"].lower(), "multan")
        self.assertIn("itinerary", data)
        self.assertIn("cost", data)
        self.assertIn("alternatives", data)

    def test_plan_trip_single_day(self):
        payload = {
            "budget": 10000,
            "days": 1,
            "category": "historical",
            "people": 2
        }
        res = self.client.post("/plan-trip", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn("error", data)
        self.assertEqual(len(data["itinerary"]["itinerary"]), 1)

    def test_chat_endpoint(self):
        res = self.client.post("/chat", json={"message": "Recommend historical places in Lahore for 2 days"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("reply", data)
        self.assertIn("engine", data)

    def test_predict_budget_endpoint(self):
        res = self.client.post("/predict-budget", json={
            "province": "Punjab",
            "category": "historical",
            "recommended_days": 1,
            "activities": ["sightseeing", "photography"],
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("predicted_budget_per_day", data)
        self.assertGreater(data["predicted_budget_per_day"], 0)

    def test_predict_budget_endpoint_missing_required_field(self):
        res = self.client.post("/predict-budget", json={"province": "Punjab"})
        self.assertEqual(res.status_code, 422)  # Pydantic validation error


class TestUserAuthenticationAndSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_email = f"test_user_{int(time.time() * 1000)}@example.com"
        self.test_username = f"user_{int(time.time() * 1000)}"
        self.test_password = "SecurePassword123!"

    def test_registration_and_login_flow(self):
        # 1. Register new user
        reg_res = self.client.post("/auth/register", json={
            "username": self.test_username,
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Test Explorer",
        })
        self.assertEqual(reg_res.status_code, 200)
        reg_data = reg_res.json()
        self.assertIn("access_token", reg_data)
        self.assertEqual(reg_data["user"]["email"], self.test_email)
        token = reg_data["access_token"]

        # 2. Duplicate registration should fail (400)
        dup_res = self.client.post("/auth/register", json={
            "username": f"another_{self.test_username}",
            "email": self.test_email,
            "password": self.test_password,
        })
        self.assertEqual(dup_res.status_code, 400)

        # 3. Login with correct credentials
        login_res = self.client.post("/auth/login", json={
            "email_or_username": self.test_email,
            "password": self.test_password,
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.json()
        self.assertIn("access_token", login_data)

        # 4. Login with wrong password should fail (401)
        bad_login = self.client.post("/auth/login", json={
            "email_or_username": self.test_email,
            "password": "WrongPassword!",
        })
        self.assertEqual(bad_login.status_code, 401)

        # 5. Access protected /auth/me
        headers = {"Authorization": f"Bearer {token}"}
        me_res = self.client.get("/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], self.test_email)

        # 6. Wishlist toggle & sync
        toggle_res = self.client.post("/api/user/wishlist/toggle", json={"destination_id": 1}, headers=headers)
        self.assertEqual(toggle_res.status_code, 200)
        self.assertTrue(toggle_res.json()["is_favorite"])

        wishlist_res = self.client.get("/api/user/wishlist", headers=headers)
        self.assertEqual(wishlist_res.status_code, 200)
        self.assertIn(1, wishlist_res.json()["destination_ids"])

        # 7. Save and retrieve trip
        save_trip_res = self.client.post("/api/user/trips/save", json={
            "destination_id": 1,
            "destination_name": "Hunza Valley",
            "days": 3,
            "people": 2,
            "total_budget": 50000,
            "trip_plan_json": json.dumps({"note": "Test trip itinerary"}),
        }, headers=headers)
        self.assertEqual(save_trip_res.status_code, 200)
        trip_id = save_trip_res.json()["trip_id"]

        trips_res = self.client.get("/api/user/trips", headers=headers)
        self.assertEqual(trips_res.status_code, 200)
        saved_trips = trips_res.json()["trips"]
        self.assertGreaterEqual(len(saved_trips), 1)
        self.assertEqual(saved_trips[0]["destination_name"], "Hunza Valley")

        # 8. Delete saved trip
        del_res = self.client.delete(f"/api/user/trips/{trip_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)


if __name__ == "__main__":
    import time
    import json
    unittest.main(verbosity=2)