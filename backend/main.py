import os
import shutil
import json
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .models import (
    UserSettings, MealCreateRequest, MealResponse, LoggedFoodItem,
    AnalyzeFoodTextRequest, AnalyzeFoodResponse, AnalyzeImageResponse,
    CoachRequest, CoachResponse, DashboardResponse, DailyOverview,
    ProfileCalculateRequest, SuggestedNutritionPlan
)
from .database import (
    init_db, get_user_settings, update_user_settings, save_meal_record,
    get_meals_by_date, get_meal_by_id, get_all_meals, get_coach_messages,
    clear_user_history, clear_coach_messages
)
from .nutrition import nutrition_repo
from .gemini_service import (
    parse_natural_language_food, analyze_food_image_gemini, is_demo_mode
)
from .coach import get_ai_coach_response
from .trends import calculate_user_trends

# Initialize SQLite database
init_db()

app = FastAPI(
    title="NutriSnap AI API",
    description="Multimodal AI-Powered Nutrition Tracking & Additive Nutrition Intelligence",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOADS_DIR = os.path.join("/tmp", "nutrisnap_uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ----------------- API ROUTES -----------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "NutriSnap AI",
        "demo_mode": is_demo_mode(),
        "database": "SQLite (nutrisnap.db)",
        "foods_count": len(nutrition_repo.get_all_foods())
    }

@app.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(date: Optional[str] = Query(None)):
    """Returns today's nutrition overview, meal list, calories progress, and active 7-day rolling window."""
    user = get_user_settings("alex")
    
    today_dt = datetime.now().date()
    selected_date = date or today_dt.strftime("%Y-%m-%d")
    
    meals = get_meals_by_date("alex", selected_date)
    
    # Calculate daily totals
    cal_consumed = sum(m.total_calories for m in meals)
    protein_consumed = sum(m.total_protein for m in meals)
    carbs_consumed = sum(m.total_carbohydrates for m in meals)
    fat_consumed = sum(m.total_fat for m in meals)
    fiber_consumed = sum(m.total_fiber for m in meals)
    
    cal_goal = user.daily_calorie_goal
    cal_left = max(0.0, cal_goal - cal_consumed)
    progress_pct = min(100.0, round((cal_consumed / cal_goal) * 100, 1)) if cal_goal > 0 else 0
    
    trends = calculate_user_trends("alex")
    
    overview = DailyOverview(
        date=selected_date,
        calories_consumed=round(cal_consumed),
        calories_goal=cal_goal,
        calories_left=round(cal_left),
        progress_percentage=progress_pct,
        protein_consumed=round(protein_consumed, 1),
        protein_goal=user.daily_protein_goal,
        carbs_consumed=round(carbs_consumed, 1),
        carbs_goal=user.daily_carbs_goal,
        fat_consumed=round(fat_consumed, 1),
        fat_goal=user.daily_fat_goal,
        fiber_consumed=round(fiber_consumed, 1),
        fiber_goal=user.daily_fiber_goal,
        pattern_notice=trends["pattern_notice"]
    )
    
    # Dynamic 8-day rolling window starting from today (e.g. 26 Aug to 2 Sep)
    week_dates = []
    for i in range(8):
        cur_dt = today_dt + timedelta(days=i)
        iso_str = cur_dt.strftime("%Y-%m-%d")
        week_dates.append({
            "day": cur_dt.strftime("%a").upper(),
            "date": cur_dt.strftime("%d").lstrip("0"),
            "full_date": iso_str,
            "is_active": selected_date == iso_str
        })
    
    return DashboardResponse(
        user=user,
        selected_date=selected_date,
        daily_overview=overview,
        meals=meals,
        available_dates=week_dates
    )

@app.get("/api/food-options")
def get_food_options():
    """Returns all available food items with full nutritional breakdown."""
    return nutrition_repo.get_all_foods()

@app.delete("/api/meals/{meal_id}")
def delete_meal(meal_id: int):
    """Deletes a meal from the database."""
    from .database import delete_meal_record
    delete_meal_record(meal_id, "alex")
    return {"status": "success", "deleted_id": meal_id}

@app.get("/api/meals", response_model=List[MealResponse])
def get_meals(category: Optional[str] = Query(None)):
    """Fetch meals with optional filter (All, Breakfast, Lunch, Dinner, Snack)."""
    all_meals = get_all_meals("alex", limit=50)
    if category and category.lower() != "all":
        return [m for m in all_meals if m.meal_type.lower() == category.lower()]
    return all_meals

@app.post("/api/meals", response_model=MealResponse)
def create_meal(payload: MealCreateRequest):
    """Manually log a custom meal."""
    meal_date = payload.meal_date or "2026-06-24"
    meal_time = payload.meal_time or datetime.now().strftime("%I:%M %p")
    title = payload.title or (payload.items[0].name if payload.items else "Custom Meal")
    image_url = payload.image_url or (payload.items[0].image if payload.items else "/assets/roti.jpg")
    
    meal_id = save_meal_record(
        user_id="alex",
        meal_type=payload.meal_type,
        meal_time=meal_time,
        meal_date=meal_date,
        title=title,
        description=payload.description or "",
        image_url=image_url,
        items=payload.items
    )
    meal = get_meal_by_id(meal_id)
    if not meal:
        raise HTTPException(status_code=500, detail="Failed to retrieve created meal.")
    return meal

@app.post("/api/analyze-food", response_model=AnalyzeFoodResponse)
def analyze_food_text(payload: AnalyzeFoodTextRequest):
    """Processes natural language food description via Gemini/Demo parser and saves meal."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
    parse_result = parse_natural_language_food(text, payload.meal_type)
    
    matched_items = []
    for detected in parse_result.detected_foods:
        food = nutrition_repo.match_food(detected.name)
        if food:
            matched_items.append(nutrition_repo.create_logged_item(food, detected.quantity))
            
    # If no match found, fallback to closest staple
    if not matched_items:
        default_food = nutrition_repo.get_all_foods()[0]
        matched_items.append(nutrition_repo.create_logged_item(default_food, 1.0))
        
    totals = nutrition_repo.calculate_totals(matched_items)
    additive = nutrition_repo.get_additive_suggestions(totals, parse_result.meal_type)
    
    meal_date = payload.meal_date or "2026-06-24"
    meal_time = datetime.now().strftime("%I:%M %p")
    
    meal_id = save_meal_record(
        user_id="alex",
        meal_type=parse_result.meal_type,
        meal_time=meal_time,
        meal_date=meal_date,
        title=parse_result.suggested_title,
        description=f"Logged via Natural Language: '{text}'",
        image_url=matched_items[0].image if matched_items else "/assets/roti.jpg",
        items=matched_items
    )
    
    return AnalyzeFoodResponse(
        meal_type=parse_result.meal_type,
        title=parse_result.suggested_title,
        detected_foods=parse_result.detected_foods,
        matched_items=matched_items,
        totals=totals,
        additive_suggestions=additive,
        is_demo_mode=is_demo_mode(),
        saved_meal_id=meal_id
    )

@app.post("/api/analyze-image", response_model=AnalyzeImageResponse)
async def analyze_food_image(
    file: Optional[UploadFile] = File(None),
    sample_name: Optional[str] = Form(None),
    meal_date: Optional[str] = Form(None)
):
    """Processes food photo via Gemini Vision / Demo parser and prepares nutrition report."""
    image_url = "/assets/salmon.jpg"
    image_bytes = None
    
    if file and file.filename:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        dest_path = os.path.join(UPLOADS_DIR, filename)
        image_bytes = await file.read()
        with open(dest_path, "wb") as f:
            f.write(image_bytes)
        image_url = f"/uploads/{filename}"
        parse_result = analyze_food_image_gemini(dest_path, image_bytes)
    elif sample_name:
        image_url = f"/assets/{sample_name}"
        parse_result = analyze_food_image_gemini(sample_name)
    else:
        parse_result = analyze_food_image_gemini("hero_plate.jpg")
        
    matched_items = []
    for detected in parse_result.detected_foods:
        food = nutrition_repo.match_food(detected.name)
        if food:
            matched_items.append(nutrition_repo.create_logged_item(food, detected.quantity))
            
    if not matched_items:
        default_food = nutrition_repo.get_food_by_id("paneer_tikka") or nutrition_repo.get_all_foods()[0]
        matched_items.append(nutrition_repo.create_logged_item(default_food, 1.0))
        
    totals = nutrition_repo.calculate_totals(matched_items)
    additive = nutrition_repo.get_additive_suggestions(totals, parse_result.meal_type)
    
    # Save the scanned meal automatically
    target_date = meal_date or "2026-06-24"
    save_meal_record(
        user_id="alex",
        meal_type=parse_result.meal_type,
        meal_time=datetime.now().strftime("%I:%M %p"),
        meal_date=target_date,
        title=parse_result.suggested_title,
        description="Logged via Multimodal Food Scanner.",
        image_url=image_url,
        items=matched_items
    )
    
    return AnalyzeImageResponse(
        meal_type=parse_result.meal_type,
        title=parse_result.suggested_title,
        description="Vision model identified high-density nutrient markers.",
        image_url=image_url,
        detected_foods=parse_result.detected_foods,
        matched_items=matched_items,
        totals=totals,
        additive_suggestions=additive,
        is_demo_mode=is_demo_mode()
    )

@app.get("/api/nutrition/{meal_id}", response_model=MealResponse)
def get_nutrition_report(meal_id: int):
    """Deep nutrition report for a specific meal."""
    meal = get_meal_by_id(meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal

@app.get("/api/trends")
def get_trends():
    """Returns 30-day nutrition averages, micronutrients, variety score, and patterns."""
    return calculate_user_trends("alex")

@app.post("/api/coach", response_model=CoachResponse)
def chat_with_coach(payload: CoachRequest):
    """Interactive AI Coach endpoint with additive recommendations."""
    return get_ai_coach_response("alex", payload.message, payload.conversation_history)

@app.get("/api/coach/history")
def get_coach_history():
    """Retrieve full conversation history with AI Coach."""
    return get_coach_messages("alex")

@app.post("/api/coach/clear")
def clear_coach_history():
    """Clears all conversation history with AI Coach."""
    clear_coach_messages("alex")
    return {"status": "success", "message": "Chat history cleared."}

@app.get("/api/foods")
def get_foods():
    """Returns all available foods in the nutrition database."""
    return nutrition_repo.get_all_foods()

@app.post("/api/profile/calculate-targets", response_model=SuggestedNutritionPlan)
def calculate_profile_targets(payload: ProfileCalculateRequest):
    """Calculates personalized calorie & macronutrient targets using Mifflin-St Jeor equation."""
    return calculate_nutrition_plan(payload)

@app.post("/api/profile/save", response_model=UserSettings)
def save_user_profile(payload: ProfileCalculateRequest):
    """Calculates optimal targets and saves updated user profile to SQLite."""
    plan = calculate_nutrition_plan(payload)
    settings = UserSettings(
        full_name=payload.name,
        email=payload.email,
        avatar_url="/assets/user_avatar.jpg",
        age=payload.age,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        gender=payload.gender,
        activity_level=payload.activity_level,
        target_goal=payload.target_goal,
        daily_calorie_goal=plan.daily_calorie_goal,
        daily_protein_goal=plan.daily_protein_goal,
        daily_carbs_goal=plan.daily_carbs_goal,
        daily_fat_goal=plan.daily_fat_goal,
        daily_fiber_goal=plan.daily_fiber_goal,
        is_vegetarian=payload.is_vegetarian if payload.is_vegetarian is not None else True,
        is_gluten_free=payload.is_gluten_free if payload.is_gluten_free is not None else False,
        macro_focus_goal=f"{payload.target_goal} Plan",
        coach_tone="Scientific & Precise"
    )
    update_user_settings(settings, "alex")
    return settings

def calculate_nutrition_plan(req: ProfileCalculateRequest) -> SuggestedNutritionPlan:
    is_male = req.gender.lower().startswith("m")
    gender_offset = 5 if is_male else -161
    bmr = (10 * req.weight_kg) + (6.25 * req.height_cm) - (5 * req.age) + gender_offset
    
    act = req.activity_level.lower()
    if "high" in act or "athlete" in act or "very" in act:
        activity_factor = 1.725
    elif "mod" in act or "active" in act:
        activity_factor = 1.55
    else:
        activity_factor = 1.2
        
    tdee = bmr * activity_factor
    
    goal = req.target_goal.lower()
    if "muscle" in goal or "bulk" in goal:
        target_cal = round(tdee + 350)
        pro_per_kg = 2.0
        rationale = f"Caloric surplus (+350 kcal) with {pro_per_kg}g/kg protein to maximize muscle protein synthesis and lean tissue growth without excess fat accumulation."
    elif "fat" in goal or "lean" in goal or "loss" in goal:
        target_cal = round(max(1400, tdee - 450))
        pro_per_kg = 1.8
        rationale = f"Caloric deficit (-450 kcal) with elevated protein ({pro_per_kg}g/kg) to preserve lean muscle tissue while accelerating fat oxidation."
    elif "endurance" in goal or "energy" in goal:
        target_cal = round(tdee + 150)
        pro_per_kg = 1.6
        rationale = f"Energy-matched nutrition with sustained carbohydrate availability and {pro_per_kg}g/kg protein for glycogen recovery."
    else:
        target_cal = round(tdee)
        pro_per_kg = 1.4
        rationale = f"Balanced energy maintenance with {pro_per_kg}g/kg protein for metabolic homeostasis and cellular vitality."
        
    target_protein = round(req.weight_kg * pro_per_kg)
    target_fat = round((target_cal * 0.25) / 9)
    target_fiber = round((target_cal / 1000) * 14)
    protein_cal = target_protein * 4
    fat_cal = target_fat * 9
    target_carbs = round(max(50, (target_cal - protein_cal - fat_cal) / 4))
    
    micros = {
        "Calcium": "1,000 mg",
        "Iron": "14 mg",
        "Vitamin C": "90 mg",
        "Vitamin D": "15 mcg",
        "Fiber": f"{target_fiber}g"
    }
    
    return SuggestedNutritionPlan(
        bmr=round(bmr),
        tdee=round(tdee),
        daily_calorie_goal=target_cal,
        daily_protein_goal=target_protein,
        daily_carbs_goal=target_carbs,
        daily_fat_goal=target_fat,
        daily_fiber_goal=target_fiber,
        protein_per_kg=round(pro_per_kg, 1),
        rationale=rationale,
        key_micronutrients=micros
    )

@app.get("/api/settings", response_model=UserSettings)
def get_settings():
    return get_user_settings("alex")

@app.post("/api/settings", response_model=UserSettings)
def save_settings(settings: UserSettings):
    update_user_settings(settings, "alex")
    return get_user_settings("alex")

@app.post("/api/clear-history")
def clear_history():
    clear_user_history("alex")
    return {"status": "success", "message": "History cleared successfully."}

@app.get("/api/export")
def export_data():
    meals = get_all_meals("alex", limit=500)
    data = [m.model_dump() for m in meals]
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": "attachment; filename=nutrisnap_data.json"}
    )

# Static file mount for assets and uploads
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Mount frontend files
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
