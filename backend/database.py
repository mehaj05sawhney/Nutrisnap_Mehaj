import sqlite3
import os
import json
from datetime import datetime, timedelta
import random
from typing import List, Optional, Dict, Any
from .models import UserSettings, MealResponse, LoggedFoodItem, CoachMessage
from .nutrition import nutrition_repo

DB_PATH = os.path.join("/tmp", "nutrisnap.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        full_name TEXT,
        email TEXT,
        avatar_url TEXT,
        age INTEGER DEFAULT 26,
        weight_kg REAL DEFAULT 68.0,
        height_cm REAL DEFAULT 174.0,
        gender TEXT DEFAULT 'Male',
        activity_level TEXT DEFAULT 'Moderate',
        target_goal TEXT DEFAULT 'Muscle Gain',
        daily_calorie_goal INTEGER,
        daily_protein_goal INTEGER,
        daily_carbs_goal INTEGER,
        daily_fat_goal INTEGER,
        daily_fiber_goal INTEGER,
        is_vegetarian INTEGER,
        is_gluten_free INTEGER,
        macro_focus_goal TEXT,
        coach_tone TEXT
    )
    """)

    # Run lightweight schema migrations for existing DBs
    for col, col_type in [
        ("age", "INTEGER DEFAULT 26"),
        ("weight_kg", "REAL DEFAULT 68.0"),
        ("height_cm", "REAL DEFAULT 174.0"),
        ("gender", "TEXT DEFAULT 'Male'"),
        ("activity_level", "TEXT DEFAULT 'Moderate'"),
        ("target_goal", "TEXT DEFAULT 'Muscle Gain'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
        except Exception:
            pass

    # 2. Meals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        meal_type TEXT,
        meal_time TEXT,
        meal_date TEXT,
        title TEXT,
        description TEXT,
        image_url TEXT,
        total_calories REAL,
        total_protein REAL,
        total_carbohydrates REAL,
        total_fat REAL,
        total_fiber REAL,
        total_sugar REAL,
        total_sodium REAL,
        total_calcium REAL,
        total_iron REAL,
        total_vitamin_c REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Meal Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meal_id INTEGER,
        food_id TEXT,
        name TEXT,
        quantity REAL,
        serving_size TEXT,
        calories REAL,
        protein REAL,
        carbohydrates REAL,
        fat REAL,
        fiber REAL,
        sugar REAL,
        sodium REAL,
        calcium REAL,
        iron REAL,
        vitamin_c REAL,
        image TEXT,
        FOREIGN KEY(meal_id) REFERENCES meals(id) ON DELETE CASCADE
    )
    """)

    # 4. Coach Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coach_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        sender TEXT,
        message TEXT,
        timestamp TEXT,
        additive_chips_json TEXT
    )
    """)

    conn.commit()

    # Seed Default User if not exists
    cursor.execute("SELECT * FROM users WHERE id = 'alex'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (
            id, full_name, email, avatar_url, age, weight_kg, height_cm, gender, activity_level, target_goal,
            daily_calorie_goal, daily_protein_goal, daily_carbs_goal, daily_fat_goal, daily_fiber_goal,
            is_vegetarian, is_gluten_free, macro_focus_goal, coach_tone
        ) VALUES (
            'alex', 'John Doe', 'john.doe@example.com', '', 26, 68.0, 174.0, 'Male', 'Moderate', 'Muscle Gain',
            2400, 120, 250, 65, 35,
            1, 0, 'Muscle Gain Plan', 'Scientific & Precise'
        )
        """)
        conn.commit()
    else:
        # Update existing user to John Doe if was Alex Sterling
        cursor.execute("UPDATE users SET full_name = 'John Doe', email = 'john.doe@example.com', gender = 'Male' WHERE id = 'alex' AND full_name = 'Alex Sterling'")
        conn.commit()

    # Clear pre-filled meals so all data starts at 0 until user adds food
    cursor.execute("DELETE FROM meal_items")
    cursor.execute("DELETE FROM meals")
    conn.commit()

    conn.close()

def seed_7_day_history(conn):
    """Populates strictly 7 days of realistic history (June 19 to June 25, 2026)."""
    cursor = conn.cursor()
    
    # 7-day window dates
    seven_days = [
        "2026-06-19", "2026-06-20", "2026-06-21", "2026-06-22",
        "2026-06-23", "2026-06-24", "2026-06-25"
    ]
    
    # Clear older data to enforce strict 7-day record
    cursor.execute("DELETE FROM meal_items")
    cursor.execute("DELETE FROM meals")
    conn.commit()
    
    for cur_date in seven_days:
        if cur_date == "2026-06-24":
            # WEDNESDAY / ACTIVE REFERENCE DATE (1640 kcal, 85g Protein, 190g Carbs, 52g Fat)
            # Meal 1: Breakfast - Poha
            add_seeded_meal(conn, "alex", "Breakfast", "08:30 AM", cur_date, "Poha", "Flattened rice cooked with onions, peanuts, mustard seeds and mild spices.", "/assets/poha.jpg", [("poha", 1.0)])
            
            # Meal 2: Lunch - Roti + Dal
            add_seeded_meal(conn, "alex", "Lunch", "01:15 PM", cur_date, "Roti + Dal", "2 Whole wheat rotis with a hearty portion of yellow dal tadka and roasted cumin.", "/assets/dal.jpg", [("roti", 2.0), ("dal_tadka", 1.25)])
            
            # Meal 3: Snack - Mixed Nuts & Choc
            add_seeded_meal(conn, "alex", "Snack", "04:30 PM", cur_date, "Mixed Nuts & Choc", "Handful of almonds, walnuts, and 70% dark chocolate chips.", "/assets/nuts_choco.jpg", [("nuts_dark_chocolate", 1.0)])
            
            # Meal 4: Dinner - Paneer Tikka + Steamed Rice
            add_seeded_meal(conn, "alex", "Dinner", "08:15 PM", cur_date, "Paneer + Rice", "Tandoori spiced cottage cheese cubes served with light steamed basmati rice.", "/assets/paneer_tikka.jpg", [("paneer_tikka", 1.5), ("steamed_rice", 1.0)])

        elif cur_date == "2026-06-23":
            # TUESDAY
            add_seeded_meal(conn, "alex", "Breakfast", "09:00 AM", cur_date, "Idli with Sambhar", "Steamed fermented rice cakes with vegetable sambhar.", "/assets/idli.jpg", [("idli_sambhar", 1.2)])
            add_seeded_meal(conn, "alex", "Lunch", "01:00 PM", cur_date, "Roti + Dal", "Whole wheat rotis with comforting dal tadka.", "/assets/dal.jpg", [("roti", 2.0), ("dal_tadka", 1.5)])
            add_seeded_meal(conn, "alex", "Dinner", "07:45 PM", cur_date, "Paneer + Rice", "Char-grilled spiced paneer cubes with basmati rice.", "/assets/paneer_tikka.jpg", [("paneer_tikka", 1.2), ("steamed_rice", 1.0)])

        elif cur_date == "2026-06-22":
            # MONDAY
            add_seeded_meal(conn, "alex", "Breakfast", "08:15 AM", cur_date, "Masala Dosa", "Crispy fermented crepe with spiced potato filling.", "/assets/dosa.jpg", [("masala_dosa", 1.0)])
            add_seeded_meal(conn, "alex", "Lunch", "01:30 PM", cur_date, "Chole with Rice", "Spiced chickpea curry served with basmati rice.", "/assets/chole.jpg", [("chole", 1.2), ("steamed_rice", 1.0)])
            add_seeded_meal(conn, "alex", "Dinner", "08:00 PM", cur_date, "Roti & Dal", "Whole wheat rotis with protein-rich dal.", "/assets/dal.jpg", [("roti", 2.0), ("dal_tadka", 1.0)])

        elif cur_date == "2026-06-21":
            # SUNDAY
            add_seeded_meal(conn, "alex", "Breakfast", "09:30 AM", cur_date, "Mixed Fruit Platter", "Fresh papaya, pomegranate, kiwi, and apple slices.", "/assets/fruit_bowl.jpg", [("mixed_fruit_bowl", 1.5)])
            add_seeded_meal(conn, "alex", "Lunch", "01:45 PM", cur_date, "Rajma Chawal", "Comforting red kidney beans in thick gravy with steamed rice.", "/assets/rajma.jpg", [("rajma", 1.2), ("steamed_rice", 1.0)])
            add_seeded_meal(conn, "alex", "Dinner", "08:30 PM", cur_date, "Grilled Salmon with Veggies", "Omega-3 rich grilled fillet with microgreens.", "/assets/salmon.jpg", [("grilled_salmon", 1.0)])

        elif cur_date == "2026-06-20":
            # SATURDAY
            add_seeded_meal(conn, "alex", "Breakfast", "08:45 AM", cur_date, "Poha", "Warm spiced flattened rice with roasted peanuts.", "/assets/poha.jpg", [("poha", 1.0)])
            add_seeded_meal(conn, "alex", "Lunch", "01:15 PM", cur_date, "Paneer Tikka & Roti", "Tandoori cottage cheese cubes with whole wheat roti.", "/assets/paneer_tikka.jpg", [("paneer_tikka", 1.0), ("roti", 2.0)])
            add_seeded_meal(conn, "alex", "Dinner", "07:30 PM", cur_date, "Dal Tadka & Rice", "Comforting lentil curry with fluffy rice.", "/assets/dal.jpg", [("dal_tadka", 1.2), ("steamed_rice", 1.0)])

        elif cur_date == "2026-06-19":
            # FRIDAY
            add_seeded_meal(conn, "alex", "Breakfast", "08:30 AM", cur_date, "Idli Sambhar", "Light steamed rice cakes with sambhar.", "/assets/idli.jpg", [("idli_sambhar", 1.0)])
            add_seeded_meal(conn, "alex", "Lunch", "12:45 PM", cur_date, "Chole & Roti", "Chickpea curry with wheat rotis.", "/assets/chole.jpg", [("chole", 1.0), ("roti", 2.0)])
            add_seeded_meal(conn, "alex", "Dinner", "08:00 PM", cur_date, "Paneer & Steamed Rice", "Light cottage cheese cubes with rice.", "/assets/paneer_tikka.jpg", [("paneer_tikka", 1.0), ("steamed_rice", 1.0)])

        elif cur_date == "2026-06-25":
            # THURSDAY (Light starter day)
            add_seeded_meal(conn, "alex", "Breakfast", "08:30 AM", cur_date, "Poha", "Light breakfast with peanuts.", "/assets/poha.jpg", [("poha", 1.0)])

    # Ensure coach_messages is fresh with 0 pre-existing chats
    cursor.execute("DELETE FROM coach_messages")
    conn.commit()

def delete_meal_record(meal_id: int, user_id: str = "alex") -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meal_items WHERE meal_id = ?", (meal_id,))
    cursor.execute("DELETE FROM meals WHERE id = ? AND user_id = ?", (meal_id, user_id))
    conn.commit()
    conn.close()
    return True

def add_seeded_meal(conn, user_id: str, meal_type: str, meal_time: str, meal_date: str, title: str, description: str, image_url: str, items_data: List[tuple]):
    logged_items = []
    for food_id, qty in items_data:
        food = nutrition_repo.get_food_by_id(food_id)
        if food:
            logged_items.append(nutrition_repo.create_logged_item(food, qty))
            
    if not logged_items:
        return
        
    totals = nutrition_repo.calculate_totals(logged_items)
    
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO meals (
        user_id, meal_type, meal_time, meal_date, title, description, image_url,
        total_calories, total_protein, total_carbohydrates, total_fat, total_fiber,
        total_sugar, total_sodium, total_calcium, total_iron, total_vitamin_c
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, meal_type, meal_time, meal_date, title, description, image_url,
        totals["calories"], totals["protein"], totals["carbohydrates"], totals["fat"], totals["fiber"],
        totals["sugar"], totals["sodium"], totals["calcium"], totals["iron"], totals["vitamin_c"]
    ))
    meal_id = cursor.lastrowid
    
    for item in logged_items:
        cursor.execute("""
        INSERT INTO meal_items (
            meal_id, food_id, name, quantity, serving_size,
            calories, protein, carbohydrates, fat, fiber,
            sugar, sodium, calcium, iron, vitamin_c, image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meal_id, item.food_id, item.name, item.quantity, item.serving_size,
            item.calories, item.protein, item.carbohydrates, item.fat, item.fiber,
            item.sugar, item.sodium, item.calcium, item.iron, item.vitamin_c, item.image
        ))
    conn.commit()

def get_user_settings(user_id: str = "alex") -> UserSettings:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return UserSettings(
            full_name=row["full_name"],
            email=row["email"],
            avatar_url=row["avatar_url"],
            age=row["age"] if "age" in row.keys() and row["age"] else 26,
            weight_kg=row["weight_kg"] if "weight_kg" in row.keys() and row["weight_kg"] else 68.0,
            height_cm=row["height_cm"] if "height_cm" in row.keys() and row["height_cm"] else 174.0,
            gender=row["gender"] if "gender" in row.keys() and row["gender"] else "Male",
            activity_level=row["activity_level"] if "activity_level" in row.keys() and row["activity_level"] else "Moderate",
            target_goal=row["target_goal"] if "target_goal" in row.keys() and row["target_goal"] else "Muscle Gain",
            daily_calorie_goal=row["daily_calorie_goal"],
            daily_protein_goal=row["daily_protein_goal"],
            daily_carbs_goal=row["daily_carbs_goal"],
            daily_fat_goal=row["daily_fat_goal"],
            daily_fiber_goal=row["daily_fiber_goal"],
            is_vegetarian=bool(row["is_vegetarian"]),
            is_gluten_free=bool(row["is_gluten_free"]),
            macro_focus_goal=row["macro_focus_goal"],
            coach_tone=row["coach_tone"]
        )
    return UserSettings()

def update_user_settings(settings: UserSettings, user_id: str = "alex"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET
        full_name = ?, email = ?,
        age = ?, weight_kg = ?, height_cm = ?, gender = ?, activity_level = ?, target_goal = ?,
        daily_calorie_goal = ?, daily_protein_goal = ?, daily_carbs_goal = ?, daily_fat_goal = ?, daily_fiber_goal = ?,
        is_vegetarian = ?, is_gluten_free = ?, macro_focus_goal = ?, coach_tone = ?
    WHERE id = ?
    """, (
        settings.full_name, settings.email,
        settings.age, settings.weight_kg, settings.height_cm, settings.gender, settings.activity_level, settings.target_goal,
        settings.daily_calorie_goal, settings.daily_protein_goal, settings.daily_carbs_goal, settings.daily_fat_goal, settings.daily_fiber_goal,
        int(settings.is_vegetarian), int(settings.is_gluten_free), settings.macro_focus_goal, settings.coach_tone,
        user_id
    ))
    conn.commit()
    conn.close()

def save_meal_record(user_id: str, meal_type: str, meal_time: str, meal_date: str, title: str, description: str, image_url: Optional[str], items: List[LoggedFoodItem]) -> int:
    totals = nutrition_repo.calculate_totals(items)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO meals (
        user_id, meal_type, meal_time, meal_date, title, description, image_url,
        total_calories, total_protein, total_carbohydrates, total_fat, total_fiber,
        total_sugar, total_sodium, total_calcium, total_iron, total_vitamin_c
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, meal_type, meal_time, meal_date, title, description, image_url,
        totals["calories"], totals["protein"], totals["carbohydrates"], totals["fat"], totals["fiber"],
        totals["sugar"], totals["sodium"], totals["calcium"], totals["iron"], totals["vitamin_c"]
    ))
    meal_id = cursor.lastrowid

    for item in items:
        cursor.execute("""
        INSERT INTO meal_items (
            meal_id, food_id, name, quantity, serving_size,
            calories, protein, carbohydrates, fat, fiber,
            sugar, sodium, calcium, iron, vitamin_c, image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meal_id, item.food_id, item.name, item.quantity, item.serving_size,
            item.calories, item.protein, item.carbohydrates, item.fat, item.fiber,
            item.sugar, item.sodium, item.calcium, item.iron, item.vitamin_c, item.image
        ))
    conn.commit()
    conn.close()
    return meal_id

def get_meals_by_date(user_id: str, meal_date: str) -> List[MealResponse]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE user_id = ? AND meal_date = ? ORDER BY id ASC", (user_id, meal_date))
    rows = cursor.fetchall()
    meals = []
    for r in rows:
        cursor.execute("SELECT * FROM meal_items WHERE meal_id = ?", (r["id"],))
        item_rows = cursor.fetchall()
        items = [
            LoggedFoodItem(
                food_id=ir["food_id"],
                name=ir["name"],
                quantity=ir["quantity"],
                serving_size=ir["serving_size"],
                calories=ir["calories"],
                protein=ir["protein"],
                carbohydrates=ir["carbohydrates"],
                fat=ir["fat"],
                fiber=ir["fiber"],
                sugar=ir["sugar"],
                sodium=ir["sodium"],
                calcium=ir["calcium"],
                iron=ir["iron"],
                vitamin_c=ir["vitamin_c"],
                image=ir["image"]
            )
            for ir in item_rows
        ]
        meals.append(MealResponse(
            id=r["id"],
            user_id=r["user_id"],
            meal_type=r["meal_type"],
            meal_time=r["meal_time"],
            meal_date=r["meal_date"],
            title=r["title"],
            description=r["description"] or "",
            image_url=r["image_url"],
            total_calories=r["total_calories"],
            total_protein=r["total_protein"],
            total_carbohydrates=r["total_carbohydrates"],
            total_fat=r["total_fat"],
            total_fiber=r["total_fiber"],
            total_sugar=r["total_sugar"],
            total_sodium=r["total_sodium"],
            total_calcium=r["total_calcium"],
            total_iron=r["total_iron"],
            total_vitamin_c=r["total_vitamin_c"],
            items=items
        ))
    conn.close()
    return meals

def get_meal_by_id(meal_id: int) -> Optional[MealResponse]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE id = ?", (meal_id,))
    r = cursor.fetchone()
    if not r:
        conn.close()
        return None
    cursor.execute("SELECT * FROM meal_items WHERE meal_id = ?", (meal_id,))
    item_rows = cursor.fetchall()
    items = [
        LoggedFoodItem(
            food_id=ir["food_id"],
            name=ir["name"],
            quantity=ir["quantity"],
            serving_size=ir["serving_size"],
            calories=ir["calories"],
            protein=ir["protein"],
            carbohydrates=ir["carbohydrates"],
            fat=ir["fat"],
            fiber=ir["fiber"],
            sugar=ir["sugar"],
            sodium=ir["sodium"],
            calcium=ir["calcium"],
            iron=ir["iron"],
            vitamin_c=ir["vitamin_c"],
            image=ir["image"]
        )
        for ir in item_rows
    ]
    conn.close()
    return MealResponse(
        id=r["id"],
        user_id=r["user_id"],
        meal_type=r["meal_type"],
        meal_time=r["meal_time"],
        meal_date=r["meal_date"],
        title=r["title"],
        description=r["description"] or "",
        image_url=r["image_url"],
        total_calories=r["total_calories"],
        total_protein=r["total_protein"],
        total_carbohydrates=r["total_carbohydrates"],
        total_fat=r["total_fat"],
        total_fiber=r["total_fiber"],
        total_sugar=r["total_sugar"],
        total_sodium=r["total_sodium"],
        total_calcium=r["total_calcium"],
        total_iron=r["total_iron"],
        total_vitamin_c=r["total_vitamin_c"],
        items=items
    )

def get_all_meals(user_id: str = "alex", limit: int = 100) -> List[MealResponse]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE user_id = ? ORDER BY meal_date DESC, id DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    meals = []
    for r in rows:
        cursor.execute("SELECT * FROM meal_items WHERE meal_id = ?", (r["id"],))
        item_rows = cursor.fetchall()
        items = [
            LoggedFoodItem(
                food_id=ir["food_id"],
                name=ir["name"],
                quantity=ir["quantity"],
                serving_size=ir["serving_size"],
                calories=ir["calories"],
                protein=ir["protein"],
                carbohydrates=ir["carbohydrates"],
                fat=ir["fat"],
                fiber=ir["fiber"],
                sugar=ir["sugar"],
                sodium=ir["sodium"],
                calcium=ir["calcium"],
                iron=ir["iron"],
                vitamin_c=ir["vitamin_c"],
                image=ir["image"]
            )
            for ir in item_rows
        ]
        meals.append(MealResponse(
            id=r["id"],
            user_id=r["user_id"],
            meal_type=r["meal_type"],
            meal_time=r["meal_time"],
            meal_date=r["meal_date"],
            title=r["title"],
            description=r["description"] or "",
            image_url=r["image_url"],
            total_calories=r["total_calories"],
            total_protein=r["total_protein"],
            total_carbohydrates=r["total_carbohydrates"],
            total_fat=r["total_fat"],
            total_fiber=r["total_fiber"],
            total_sugar=r["total_sugar"],
            total_sodium=r["total_sodium"],
            total_calcium=r["total_calcium"],
            total_iron=r["total_iron"],
            total_vitamin_c=r["total_vitamin_c"],
            items=items
        ))
    conn.close()
    return meals

def get_coach_messages(user_id: str = "alex") -> List[CoachMessage]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coach_messages WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    messages = []
    for r in rows:
        chips = []
        if r["additive_chips_json"]:
            try:
                chips = json.loads(r["additive_chips_json"])
            except:
                pass
        messages.append(CoachMessage(
            sender=r["sender"],
            message=r["message"],
            timestamp=r["timestamp"],
            additive_chips=chips
        ))
    return messages

def save_coach_message(user_id: str, sender: str, message: str, chips: List[str] = []):
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now().strftime("%I:%M %p")
    cursor.execute("""
    INSERT INTO coach_messages (user_id, sender, message, timestamp, additive_chips_json)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, sender, message, ts, json.dumps(chips)))
    conn.commit()
    conn.close()

def clear_user_history(user_id: str = "alex"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM meal_items")
    conn.commit()
    conn.close()

def clear_coach_messages(user_id: str = "alex"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM coach_messages WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
