import sqlite3
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .database import get_connection, get_user_settings

def calculate_user_trends(user_id: str = "alex") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    settings = get_user_settings(user_id)
    
    # Fetch all meals for user
    cursor.execute("""
        SELECT meal_date, meal_type, total_calories, total_protein, total_carbohydrates, 
               total_fat, total_fiber, total_sodium, total_calcium, total_iron, total_vitamin_c 
        FROM meals 
        WHERE user_id = ? 
        ORDER BY meal_date ASC
    """, (user_id,))
    rows = cursor.fetchall()
    
    # Fetch unique food count
    cursor.execute("""
        SELECT COUNT(DISTINCT food_id) as unique_foods, COUNT(DISTINCT meal_date) as active_days
        FROM meal_items mi
        JOIN meals m ON mi.meal_id = m.id
        WHERE m.user_id = ?
    """, (user_id,))
    variety_row = cursor.fetchone()
    conn.close()
    
    unique_foods = variety_row["unique_foods"] if variety_row else 0
    active_days = variety_row["active_days"] if variety_row and variety_row["active_days"] > 0 else 1
    
    # Aggregate by date
    daily_stats = {}
    breakfast_fibers = []
    
    for r in rows:
        d = r["meal_date"]
        if d not in daily_stats:
            daily_stats[d] = {
                "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0,
                "fiber": 0.0, "calcium": 0.0, "iron": 0.0, "vitamin_c": 0.0, "meals_count": 0
            }
        daily_stats[d]["calories"] += r["total_calories"]
        daily_stats[d]["protein"] += r["total_protein"]
        daily_stats[d]["carbs"] += r["total_carbohydrates"]
        daily_stats[d]["fat"] += r["total_fat"]
        daily_stats[d]["fiber"] += r["total_fiber"]
        daily_stats[d]["calcium"] += r["total_calcium"]
        daily_stats[d]["iron"] += r["total_iron"]
        daily_stats[d]["vitamin_c"] += r["total_vitamin_c"]
        daily_stats[d]["meals_count"] += 1
        
        if r["meal_type"] == "Breakfast":
            breakfast_fibers.append(r["total_fiber"])
            
    if not rows:
        num_days = 0
        avg_calories = 0.0
        avg_protein = 0.0
        avg_carbs = 0.0
        avg_fat = 0.0
        avg_fiber = 0.0
        avg_calcium = 0.0
        avg_iron = 0.0
        avg_vitamin_c = 0.0
    else:
        num_days = max(1, len(daily_stats))
        avg_calories = sum(d["calories"] for d in daily_stats.values()) / num_days
        avg_protein = sum(d["protein"] for d in daily_stats.values()) / num_days
        avg_carbs = sum(d["carbs"] for d in daily_stats.values()) / num_days
        avg_fat = sum(d["fat"] for d in daily_stats.values()) / num_days
        avg_fiber = sum(d["fiber"] for d in daily_stats.values()) / num_days
        avg_calcium = sum(d["calcium"] for d in daily_stats.values()) / num_days
        avg_iron = sum(d["iron"] for d in daily_stats.values()) / num_days
        avg_vitamin_c = sum(d["vitamin_c"] for d in daily_stats.values()) / num_days
    
    avg_b_fiber = (sum(breakfast_fibers) / len(breakfast_fibers)) if breakfast_fibers else 3.5
    
    # 7-day timeline series for charts
    sorted_dates = sorted(daily_stats.keys())[-7:]
    timeline = [
        {
            "date": d,
            "display_date": datetime.strptime(d, "%Y-%m-%d").strftime("%a %d") if len(d) == 10 else d,
            "calories": round(daily_stats[d]["calories"]),
            "protein": round(daily_stats[d]["protein"], 1),
            "carbs": round(daily_stats[d]["carbs"], 1),
            "fat": round(daily_stats[d]["fat"], 1),
            "fiber": round(daily_stats[d]["fiber"], 1)
        }
        for d in sorted_dates
    ]
    
    # Status badges (Non-restrictive & supportive)
    protein_status = "Optimal" if avg_protein >= settings.daily_protein_goal * 0.8 else "Good Baseline"
    fiber_status = "Steady" if avg_fiber >= settings.daily_fiber_goal * 0.7 else "Additive Growth Opportunity"
    variety_status = "Excellent Variety" if unique_foods >= 10 else "Moderate Diversity"
    
    # Highlighted additive patterns
    pattern_notice = {
        "title": "A PATTERN WE NOTICED",
        "description": "Your recent breakfasts have been relatively low in fibre.",
        "avg_breakfast_fiber": f"{avg_b_fiber:.1f}g",
        "try_adding": ["Fruit", "Oats", "Dal", "Flaxseed"],
        "reasoning": "Adding just 4-6g of fiber at breakfast slows glucose absorption and maintains afternoon focus."
    }
    
    return {
        "summary": {
            "active_tracking_days": num_days,
            "unique_foods_logged": unique_foods,
            "avg_daily_calories": round(avg_calories),
            "avg_daily_protein": round(avg_protein, 1),
            "avg_daily_carbs": round(avg_carbs, 1),
            "avg_daily_fat": round(avg_fat, 1),
            "avg_daily_fiber": round(avg_fiber, 1),
            "avg_calcium_mg": round(avg_calcium, 1),
            "avg_iron_mg": round(avg_iron, 1),
            "avg_vitamin_c_mg": round(avg_vitamin_c, 1),
        },
        "goals": {
            "calories": settings.daily_calorie_goal,
            "protein": settings.daily_protein_goal,
            "carbs": settings.daily_carbs_goal,
            "fat": settings.daily_fat_goal,
            "fiber": settings.daily_fiber_goal,
        },
        "status": {
            "protein": protein_status,
            "fiber": fiber_status,
            "variety": variety_status
        },
        "pattern_notice": pattern_notice,
        "timeline_7d": timeline
    }
