import os
import requests

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

IMAGES = {
    # 4K high-contrast gourmet culinary photography
    "landing_food_1.jpg": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=1200&auto=format&fit=crop&q=85", # Vibrant healthy nourish bowl
    "landing_food_2.jpg": "https://images.unsplash.com/photo-1519996529931-28324d5a630e?w=1200&auto=format&fit=crop&q=85", # Exotic fresh 4k fruit antioxidant bowl
    "landing_food_3.jpg": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200&auto=format&fit=crop&q=85", # 4K gourmet sizzling plate
}

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in IMAGES.items():
    path = os.path.join(ASSETS_DIR, name)
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            print(f"Downloaded 4K image: {name}")
    except Exception as e:
        print(f"Failed {name}: {e}")

print("4K images setup completed.")
