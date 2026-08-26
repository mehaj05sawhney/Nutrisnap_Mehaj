import requests
import json

BASE = "http://127.0.0.1:8000"

def test_api():
    print("--- 1. Testing /api/health ---")
    r = requests.get(f"{BASE}/api/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print("Health:", r.json())

    print("\n--- 2. Testing /api/dashboard ---")
    r = requests.get(f"{BASE}/api/dashboard?date=2026-06-24")
    assert r.status_code == 200, f"Dashboard failed: {r.status_code}"
    data = r.json()
    print("Dashboard Cal Consumed:", data["daily_overview"]["calories_consumed"])
    print("Dashboard Meals Count:", len(data["meals"]))

    print("\n--- 3. Testing /api/analyze-food (Natural Language) ---")
    payload = {"text": "I had two rotis and dal for lunch", "meal_type": "Lunch", "meal_date": "2026-06-24"}
    r = requests.post(f"{BASE}/api/analyze-food", json=payload)
    assert r.status_code == 200, f"Analyze food failed: {r.status_code}"
    nl_res = r.json()
    print("NL Result Title:", nl_res["title"])
    print("NL Totals:", nl_res["totals"])
    print("Additive Suggestions:", nl_res["additive_suggestions"])

    print("\n--- 4. Testing /api/analyze-image ---")
    r = requests.post(f"{BASE}/api/analyze-image", data={"sample_name": "salmon.jpg", "meal_date": "2026-06-24"})
    assert r.status_code == 200, f"Analyze image failed: {r.status_code}"
    img_res = r.json()
    print("Image Result Title:", img_res["title"])
    print("Image Result Calories:", img_res["totals"]["calories"])

    print("\n--- 5. Testing /api/trends ---")
    r = requests.get(f"{BASE}/api/trends")
    assert r.status_code == 200, f"Trends failed: {r.status_code}"
    trends = r.json()
    print("Trends 30D Active Days:", trends["summary"]["active_tracking_days"])
    print("Trends Variety:", trends["status"]["variety"])
    print("Trends Pattern:", trends["pattern_notice"]["description"])

    print("\n--- 6. Testing /api/coach ---")
    r = requests.post(f"{BASE}/api/coach", json={"message": "What should I add to my lunch?"})
    assert r.status_code == 200, f"Coach failed: {r.status_code}"
    coach_res = r.json()
    print("Coach Response (first 120 chars):", coach_res["response"][:120], "...")

    print("\n--- 7. Testing /api/settings ---")
    r = requests.get(f"{BASE}/api/settings")
    assert r.status_code == 200, f"Get settings failed: {r.status_code}"
    settings = r.json()
    print("User Name:", settings["full_name"])
    print("Coach Tone:", settings["coach_tone"])

    print("\n ALL API ENDPOINTS PASSED SUCCESSFULLY! ")

if __name__ == "__main__":
    test_api()
