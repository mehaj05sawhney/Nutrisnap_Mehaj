import os
import requests

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Atmospheric dark culinary background matching the reference hero backdrop
HERO_BG_URL = "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=1920&auto=format&fit=crop&q=85"

headers = {'User-Agent': 'Mozilla/5.0'}
path = os.path.join(ASSETS_DIR, "hero_backdrop.jpg")

try:
    r = requests.get(HERO_BG_URL, headers=headers, timeout=12)
    if r.status_code == 200:
        with open(path, "wb") as f:
            f.write(r.content)
        print("Hero backdrop downloaded successfully.")
except Exception as e:
    print(f"Failed hero backdrop: {e}")
