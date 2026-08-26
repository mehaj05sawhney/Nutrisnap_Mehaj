import os
import json
import csv
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from .models import FoodItemSchema, LoggedFoodItem

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "foods.csv")
JSON_PATH = os.path.join(DATA_DIR, "sample_foods.json")

class NutritionRepository:
    def __init__(self):
        self.foods: Dict[str, FoodItemSchema] = {}
        self.aliases_map: Dict[str, str] = {}
        self.reload()

    def reload(self):
        """Loads food database from data/foods.csv with complete nutrition profile."""
        self.foods.clear()
        self.aliases_map.clear()
        
        image_fallbacks = {
            "roti": "/assets/roti.jpg",
            "dal_tadka": "/assets/dal.jpg",
            "poha": "/assets/poha.jpg",
            "paneer_tikka": "/assets/paneer_tikka.jpg",
            "chicken_curry": "/assets/chicken_curry.jpg",
            "rice": "/assets/rice.jpg",
            "idli": "/assets/idli.jpg",
            "dosa": "/assets/dosa.jpg",
            "chole": "/assets/chole.jpg",
            "rajma": "/assets/rajma.jpg",
            "eggs": "/assets/eggs.jpg",
            "fruit_bowl": "/assets/fruit_bowl.jpg",
            "nuts_choco": "/assets/nuts_choco.jpg",
            "salmon": "/assets/salmon.jpg"
        }

        if os.path.exists(CSV_PATH):
            try:
                with open(CSV_PATH, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        food_id = row["id"].strip().lower()
                        cal = float(row.get("calories", 0))
                        pro = float(row.get("protein_g", row.get("protein", 0)))
                        carb = float(row.get("carbs_g", row.get("carbohydrates", 0)))
                        fat = float(row.get("fat_g", row.get("fat", 0)))
                        fib = float(row.get("fiber_g", row.get("fiber", 0)))
                        sug = float(row.get("sugar_g", row.get("sugar", 0)))
                        sod = float(row.get("sodium_mg", row.get("sodium", 0)))
                        calc = float(row.get("calcium_mg", row.get("calcium", 0)))
                        fe = float(row.get("iron_mg", row.get("iron", 0)))
                        vit_c = float(row.get("vitamin_c_mg", row.get("vitamin_c", 0)))
                        vit_d = float(row.get("vitamin_d_mcg", 0))
                        cat = row.get("category", "General").strip()

                        food = FoodItemSchema(
                            id=food_id,
                            name=row["name"].strip(),
                            serving_size=row["serving_size"].strip(),
                            calories=cal,
                            protein=pro,
                            carbohydrates=carb,
                            fat=fat,
                            fiber=fib,
                            sugar=sug,
                            sodium=sod,
                            calcium=calc,
                            iron=fe,
                            vitamin_c=vit_c,
                            vitamin_d=vit_d,
                            category=cat,
                            image=image_fallbacks.get(food_id, "/assets/roti.jpg"),
                            tags=[cat, food_id]
                        )
                        self.foods[food.id] = food
                        self.aliases_map[food.name.lower().strip()] = food.id
                        self.aliases_map[food.id.lower().strip()] = food.id
            except Exception as e:
                print(f"Error loading {CSV_PATH}: {e}")

    def get_all_foods(self) -> List[FoodItemSchema]:
        return list(self.foods.values())

    def get_food_by_id(self, food_id: str) -> Optional[FoodItemSchema]:
        return self.foods.get(food_id.lower().strip())

    def match_food(self, query: str) -> Optional[FoodItemSchema]:
        """Fuzzy and alias-based food matcher."""
        q = query.lower().strip()
        
        # 1. Exact alias match
        if q in self.aliases_map:
            return self.foods.get(self.aliases_map[q])
            
        # 2. Substring match
        for alias, fid in self.aliases_map.items():
            if alias in q or q in alias:
                return self.foods.get(fid)
                
        # 3. Fuzzy similarity
        best_match = None
        highest_score = 0.0
        for alias, fid in self.aliases_map.items():
            score = SequenceMatcher(None, q, alias).ratio()
            if score > highest_score and score > 0.6:
                highest_score = score
                best_match = self.foods.get(fid)
                
        return best_match

    def create_logged_item(self, food: FoodItemSchema, quantity: float = 1.0) -> LoggedFoodItem:
        q = max(0.25, quantity)
        return LoggedFoodItem(
            food_id=food.id,
            name=food.name,
            quantity=q,
            serving_size=f"{q:g} x {food.serving_size}",
            calories=round(food.calories * q, 1),
            protein=round(food.protein * q, 1),
            carbohydrates=round(food.carbohydrates * q, 1),
            fat=round(food.fat * q, 1),
            fiber=round(food.fiber * q, 1),
            sugar=round(food.sugar * q, 1),
            sodium=round(food.sodium * q, 1),
            calcium=round(food.calcium * q, 1),
            iron=round(food.iron * q, 1),
            vitamin_c=round(food.vitamin_c * q, 1),
            image=food.image
        )

    def calculate_totals(self, items: List[LoggedFoodItem]) -> Dict[str, float]:
        totals = {
            "calories": sum(item.calories for item in items),
            "protein": sum(item.protein for item in items),
            "carbohydrates": sum(item.carbohydrates for item in items),
            "fat": sum(item.fat for item in items),
            "fiber": sum(item.fiber for item in items),
            "sugar": sum(item.sugar for item in items),
            "sodium": sum(item.sodium for item in items),
            "calcium": sum(item.calcium for item in items),
            "iron": sum(item.iron for item in items),
            "vitamin_c": sum(item.vitamin_c for item in items)
        }
        return {k: round(v, 1) for k, v in totals.items()}

    def get_additive_suggestions(self, totals: Dict[str, float], meal_type: str = "Meal") -> List[str]:
        """Additive nutrition philosophy: suggestions of nutrient-dense complements."""
        suggestions = []
        fiber = totals.get("fiber", 0)
        protein = totals.get("protein", 0)
        vitamin_c = totals.get("vitamin_c", 0)

        if fiber < 4.0:
            suggestions.append("Add a side of sliced cucumber, papaya, or flaxseeds to boost daily fiber effortlessly.")
        if protein < 12.0:
            suggestions.append("Pair with roasted paneer cubes, boiled eggs, or a cup of warm spiced dal.")
        if vitamin_c < 10.0:
            suggestions.append("Squeeze half a fresh lemon or add bell pepper slices to enhance iron absorption.")
        if not suggestions:
            suggestions.append("Great balanced meal! Consider a handful of almonds or walnuts for sustained energy.")
            
        return suggestions

nutrition_repo = NutritionRepository()
