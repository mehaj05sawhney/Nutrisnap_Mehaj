import os
import requests

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# 4K Top-view table full of delicious food composition (flatlay dark rustic gourmet feast table)
TOP_VIEW_FOOD_URLS = [
    # Top view flat lay table full of delicious gourmet food dishes
    "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=1920&auto=format&fit=crop&q=85",
    "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1920&auto=format&fit=crop&q=85",
    "https://images.unsplash.com/photo-1544025162-d76694265947?w=1920&auto=format&fit=crop&q=85",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1920&auto=format&fit=crop&q=85"
]

headers = {'User-Agent': 'Mozilla/5.0'}
path = os.path.join(ASSETS_DIR, "hero_table_backdrop.jpg")

# Try to download the best top view gourmet food table
url = "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=1920&auto=format&fit=crop&q=85"
try:
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        with open(path, "wb") as f:
            f.write(r.content)
        print("Downloaded top view table food backdrop successfully.")
except Exception as e:
    print(f"Error: {e}")
