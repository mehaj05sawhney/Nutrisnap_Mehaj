from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FoodItemSchema(BaseModel):
    id: str
    name: str
    serving_size: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    sugar: float
    sodium: float
    calcium: float
    iron: float
    vitamin_c: float
    vitamin_d: Optional[float] = 0.0
    category: Optional[str] = "General"
    image: Optional[str] = None
    tags: Optional[List[str]] = []

class LoggedFoodItem(BaseModel):
    food_id: str
    name: str
    quantity: float = 1.0
    serving_size: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    sugar: float
    sodium: float
    calcium: float
    iron: float
    vitamin_c: float
    vitamin_d: Optional[float] = 0.0
    image: Optional[str] = None

class MealCreateRequest(BaseModel):
    meal_type: str = "Lunch" # Breakfast, Lunch, Dinner, Snack
    meal_time: Optional[str] = None # e.g. "12:30 PM"
    meal_date: Optional[str] = None # YYYY-MM-DD
    title: Optional[str] = None
    description: Optional[str] = None
    items: List[LoggedFoodItem]
    image_url: Optional[str] = None

class MealResponse(BaseModel):
    id: int
    user_id: str
    meal_type: str
    meal_time: str
    meal_date: str
    title: str
    description: Optional[str] = ""
    image_url: Optional[str] = None
    total_calories: float
    total_protein: float
    total_carbohydrates: float
    total_fat: float
    total_fiber: float
    total_sugar: float
    total_sodium: float
    total_calcium: float
    total_iron: float
    total_vitamin_c: float
    items: List[LoggedFoodItem]

class AnalyzeFoodTextRequest(BaseModel):
    text: str
    meal_type: Optional[str] = None
    meal_date: Optional[str] = None

class DetectedFood(BaseModel):
    name: str
    quantity: float = 1.0
    confidence: Optional[float] = 0.95
    notes: Optional[str] = None

class GeminiParseResult(BaseModel):
    meal_type: str = "Lunch"
    suggested_title: str
    detected_foods: List[DetectedFood]
    raw_reasoning: Optional[str] = None

class AnalyzeFoodResponse(BaseModel):
    meal_type: str
    title: str
    detected_foods: List[DetectedFood]
    matched_items: List[LoggedFoodItem]
    totals: Dict[str, float]
    additive_suggestions: List[str]
    is_demo_mode: bool = False
    saved_meal_id: Optional[int] = None

class AnalyzeImageResponse(BaseModel):
    meal_type: str
    title: str
    description: str
    image_url: str
    detected_foods: List[DetectedFood]
    matched_items: List[LoggedFoodItem]
    totals: Dict[str, float]
    additive_suggestions: List[str]
    is_demo_mode: bool = False

class CoachMessage(BaseModel):
    sender: str # "user" or "coach"
    message: str
    timestamp: Optional[str] = None
    additive_chips: Optional[List[str]] = []

class CoachRequest(BaseModel):
    message: str
    conversation_history: Optional[List[CoachMessage]] = []

class CoachResponse(BaseModel):
    response: str
    suggested_actions: List[str] = []
    additive_focus: List[str] = []
    is_demo_mode: bool = False

class UserSettings(BaseModel):
    full_name: str = "John Doe"
    email: str = "john.doe@example.com"
    avatar_url: str = ""
    age: int = 26
    weight_kg: float = 68.0
    height_cm: float = 174.0
    gender: str = "Male" # Male, Female, Other
    activity_level: str = "Moderate" # Sedentary, Moderate, Very Active
    target_goal: str = "Muscle Gain" # Muscle Gain, Fat Loss / Lean, Maintenance, Endurance
    daily_calorie_goal: int = 2400
    daily_protein_goal: int = 120
    daily_carbs_goal: int = 250
    daily_fat_goal: int = 65
    daily_fiber_goal: int = 35
    is_vegetarian: bool = True
    is_gluten_free: bool = False
    macro_focus_goal: str = "Muscle Gain Plan"
    coach_tone: str = "Scientific & Precise" # "Scientific & Precise", "Encouraging & Soft", "Direct & Strict"

class ProfileCalculateRequest(BaseModel):
    name: str = "John Doe"
    email: str = "john.doe@example.com"
    age: int = 26
    weight_kg: float = 68.0
    height_cm: float = 174.0
    gender: str = "Male"
    activity_level: str = "Moderate"
    target_goal: str = "Muscle Gain"
    is_vegetarian: Optional[bool] = True
    is_gluten_free: Optional[bool] = False

class SuggestedNutritionPlan(BaseModel):
    bmr: int
    tdee: int
    daily_calorie_goal: int
    daily_protein_goal: int
    daily_carbs_goal: int
    daily_fat_goal: int
    daily_fiber_goal: int
    protein_per_kg: float
    rationale: str
    key_micronutrients: Dict[str, str]

class DailyOverview(BaseModel):
    date: str
    calories_consumed: float
    calories_goal: int
    calories_left: float
    progress_percentage: float
    protein_consumed: float
    protein_goal: int
    carbs_consumed: float
    carbs_goal: int
    fat_consumed: float
    fat_goal: int
    fiber_consumed: float
    fiber_goal: int
    pattern_notice: Dict[str, Any]

class DashboardResponse(BaseModel):
    user: UserSettings
    selected_date: str
    daily_overview: DailyOverview
    meals: List[MealResponse]
    available_dates: List[Dict[str, Any]] # e.g. [{"day": "Mon", "date": "19", "full_date": "2026-06-19", "is_active": False}]
