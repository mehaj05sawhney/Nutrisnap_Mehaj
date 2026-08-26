import os
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from .models import CoachMessage, CoachResponse, UserSettings
from .database import get_user_settings, get_all_meals, get_coach_messages, save_coach_message
from .trends import calculate_user_trends
from .gemini_service import genai_client, is_demo_mode

GREETING_PATTERNS = [
    r"^(hi|hello|hey|hola|namaste|greetings)\b",
    r"\bhow are you\b",
    r"\bhow r u\b",
    r"\bhow are u\b",
    r"\bhow's it going\b",
    r"\bwhat's up\b",
    r"\bgood morning\b",
    r"\bgood afternoon\b",
    r"\bgood evening\b",
    r"\bgood day\b"
]

OFF_TOPIC_PATTERNS = [
    r"\bassignment\b", r"\bhomework\b", r"\bessay\b", r"\bexam\b", r"\btest question\b",
    r"\bpython\b", r"\bjavascript\b", r"\bcoding\b", r"\bwrite code\b", r"\bprogramming\b", r"\bsoftware\b",
    r"\bbitcoin\b", r"\bcrypto\b", r"\bstock price\b", r"\binvesting\b", r"\bfinance\b", r"\bmortgage\b",
    r"\bpolitics\b", r"\bpresident\b", r"\belection\b", r"\bgovernment\b", r"\bmilitary\b",
    r"\bcelebrity\b", r"\bgossip\b", r"\bmovie plot\b", r"\bsong lyrics\b",
    r"\bwho is\b", r"\bwho was\b", r"\bcapital of\b", r"\bweather in\b", r"\bflight booking\b"
]

NUTRITION_KEYWORDS = [
    "food", "eat", "meal", "diet", "calorie", "protein", "carb", "fat", "fiber",
    "snack", "breakfast", "lunch", "dinner", "recipe", "cook", "nutrition", "dish",
    "water", "hydrate", "hydration", "vitamin", "mineral", "iron", "calcium", "sodium",
    "potassium", "sugar", "salt", "weight", "loss", "gain", "muscle", "bulk", "cut",
    "workout", "gym", "exercise", "fasting", "gut", "digestion", "bloat", "stomach",
    "metabolism", "health", "roti", "dal", "poha", "paneer", "egg", "chicken", "rice",
    "idli", "dosa", "chole", "rajma", "fruit", "nut", "chocolate", "salmon", "salad",
    "tea", "coffee", "smoothie", "shake", "dairy", "vegan", "vegetarian", "gluten",
    "macro", "micro", "tdee", "bmr", "target", "goal", "hunger", "hungry", "crave", "craving"
]

def sanitize_response_text(text: str) -> str:
    """Removes all markdown bold asterisks ** and cleans text for clean UI output."""
    if not text:
        return ""
    clean = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    clean = clean.replace('**', '')
    return clean.strip()

def is_greeting_only(msg: str) -> bool:
    """Checks if message is primarily a friendly greeting/chit-chat."""
    msg_low = msg.lower().strip()
    for pat in GREETING_PATTERNS:
        if re.search(pat, msg_low):
            if len(msg_low.split()) <= 6 and not any(k in msg_low for k in ["assignment", "code", "python", "stock"]):
                return True
    return False

def is_off_topic_query(msg: str) -> bool:
    """Checks if query is clearly outside the domain of nutrition, diet, health, and fitness."""
    msg_low = msg.lower().strip()
    
    if is_greeting_only(msg):
        return False

    for pat in OFF_TOPIC_PATTERNS:
        if re.search(pat, msg_low):
            if not any(k in msg_low for k in ["diet", "food", "calorie", "protein", "eat", "weight", "meal", "gain", "loss"]):
                return True

    return False

def get_guardrail_refusal_response() -> tuple[str, List[str]]:
    """Returns polite domain boundary refusal without asterisks."""
    text = (
        "Sorry, I can't help with that! I am your NutriSnap AI Nutrition & Culinary Coach, so I specialize exclusively in food, meal planning, dietary macros, recipes, and your health & fitness targets.\n\n"
        "Feel free to ask me anything about your diet, gaining weight/muscle, losing fat, or daily nutrition!"
    )
    chips = ["How can I gain weight?", "Suggest high-protein meals", "What should I eat next?", "Explain my daily targets"]
    return text, chips

def get_ai_coach_response(user_id: str, user_message: str, history: List[CoachMessage] = None) -> CoachResponse:
    settings = get_user_settings(user_id)
    trends = calculate_user_trends(user_id)
    recent_meals = get_all_meals(user_id, limit=10)
    
    # Save user question to DB
    save_coach_message(user_id, "user", user_message)
    
    # 0A. GREETING HANDLER
    if is_greeting_only(user_message):
        name = settings.full_name or "there"
        greeting_text = (
            f"Hello {name}! I'm doing great and happy to assist you today!\n\n"
            f"I'm here to help you optimize your daily nutrition, suggest delicious meal pairings, or tailor your diet for {settings.target_goal or 'your fitness goals'}.\n\n"
            f"What would you like to explore today?"
        )
        greeting_chips = ["How can I gain weight?", "Suggest high-protein meals", "What should I eat for lunch?", "How to boost my fiber?"]
        save_coach_message(user_id, "coach", greeting_text, greeting_chips)
        return CoachResponse(
            response=greeting_text,
            suggested_actions=["Explore high-protein options", "Ask about weight gain or fat loss"],
            additive_focus=["Friendly Greeting", "Nutritional Support"],
            is_demo_mode=is_demo_mode()
        )

    # 0B. STRICT DOMAIN GUARDRAIL CHECK
    if is_off_topic_query(user_message):
        refusal_text, refusal_chips = get_guardrail_refusal_response()
        save_coach_message(user_id, "coach", refusal_text, refusal_chips)
        return CoachResponse(
            response=refusal_text,
            suggested_actions=["Ask about your meal planning", "Ask about protein/carb targets"],
            additive_focus=["Domain Guardrail Active", "Nutritional Wellness"],
            is_demo_mode=is_demo_mode()
        )
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_meals = [m for m in recent_meals if m.meal_date == today_date]
    today_cal = sum(m.total_calories for m in today_meals)
    today_pro = sum(m.total_protein for m in today_meals)
    today_carbs = sum(m.total_carbohydrates for m in today_meals)
    today_fat = sum(m.total_fat for m in today_meals)
    today_fiber = sum(m.total_fiber for m in today_meals)

    pro_left = max(0.0, settings.daily_protein_goal - today_pro)
    carbs_left = max(0.0, settings.daily_carbs_goal - today_carbs)
    fat_left = max(0.0, settings.daily_fat_goal - today_fat)
    cal_left = max(0.0, settings.daily_calorie_goal - today_cal)

    # 1. TRY LIVE GEMINI API IF AVAILABLE
    if not is_demo_mode() and genai_client:
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
        for model_name in models_to_try:
            try:
                model = genai_client.GenerativeModel(model_name)
                meals_summary = "\n".join([
                    f"- {m.meal_date} ({m.meal_type}): {m.title} ({m.total_calories} kcal, {m.total_protein}g protein, {m.total_fiber}g fiber)"
                    for m in recent_meals[:6]
                ]) or "No recent meals logged yet for today."
                
                system_prompt = f"""
                You are NutriSnap AI Coach, an expert clinical & culinary nutrition intelligence powered by Gemini.
                
                FORMATTING RULE: Do NOT use markdown double asterisks (**) in your output text. Keep paragraphs clean and readable with plain bullet points.
                
                STRICT DOMAIN GUARDRAIL:
                You are EXCLUSIVELY a Nutrition & Dietary Wellness AI Coach for NutriSnap.
                You MUST ONLY answer questions related to nutrition, dietary science, food, ingredients, recipes, macros (protein, carbs, fat, fiber), micronutrients (iron, calcium, vitamins), digestion, physical fitness, hydration, and NutriSnap daily targets.
                If the user asks questions outside these health and food topics (e.g. assignments, homework, coding, math, general trivia, politics, finance), you MUST politely refuse with:
                "Sorry, I can't help with that! I am your NutriSnap AI Nutrition Coach, so I specialize exclusively in food, meal planning, and health targets."

                USER PROFILE & BIOMETRIC TARGETS:
                - Name: {settings.full_name} | Age: {settings.age} | Weight: {settings.weight_kg}kg | Height: {settings.height_cm}cm | Gender: {settings.gender}
                - Primary Goal: {settings.target_goal} ({settings.macro_focus_goal})
                - Daily Calorie Target: {settings.daily_calorie_goal} kcal (Remaining Today: {round(cal_left)} kcal)
                - Daily Protein Target: {settings.daily_protein_goal}g (Remaining Today: {round(pro_left, 1)}g)
                - Daily Carbs Target: {settings.daily_carbs_goal}g (Remaining Today: {round(carbs_left, 1)}g)
                - Daily Fat Target: {settings.daily_fat_goal}g | Fiber Target: {settings.daily_fiber_goal}g
                - Dietary Preferences: Vegetarian = {settings.is_vegetarian}, Gluten-Free = {settings.is_gluten_free}
                - Persona/Tone: {settings.coach_tone}

                TODAY'S LOGGED INTAKE:
                - Consumed: {round(today_cal)} kcal | {round(today_pro, 1)}g Protein | {round(today_carbs, 1)}g Carbs | {round(today_fat, 1)}g Fat | {round(today_fiber, 1)}g Fiber
                - Recent Meals:
                {meals_summary}

                FOOD CATALOG OPTIONS AVAILABLE:
                - Roti (120 kcal, 4g Pro, 22g Carbs, 3g Fiber)
                - Dal Tadka (220 kcal, 10g Pro, 28g Carbs, 7g Fiber)
                - Poha (250 kcal, 6g Pro, 38g Carbs, 4g Fiber)
                - Paneer Tikka (310 kcal, 22g Pro, 10g Carbs, 2g Fiber)
                - Chicken Curry (320 kcal, 27g Pro, 9g Carbs, 2g Fiber)
                - Steamed Rice (195 kcal, 4g Pro, 43g Carbs, 0.6g Fiber)
                - Idli with Sambhar (240 kcal, 9g Pro, 40g Carbs, 5g Fiber)
                - Masala Dosa (360 kcal, 8g Pro, 48g Carbs, 4g Fiber)
                - Chole Masala (285 kcal, 12g Pro, 38g Carbs, 10g Fiber)
                - Rajma Masala (260 kcal, 13g Pro, 37g Carbs, 9g Fiber)
                - Boiled Eggs (155 kcal, 13g Pro, 1g Carbs, 0g Fiber)
                - Mixed Fruit Bowl (130 kcal, 2g Pro, 32g Carbs, 5g Fiber)
                - Mixed Nuts & Dark Chocolate (190 kcal, 5g Pro, 13g Carbs, 3g Fiber)
                - Grilled Salmon with Veggies (410 kcal, 34g Pro, 14g Carbs, 5g Fiber)

                CRITICAL GUIDANCE INSTRUCTIONS:
                1. ADDITIVE & CONSTRUCTIVE: Always suggest what wholesome food to ADD to fulfill macro gaps rather than restrictive rules.
                2. ADDRESS THE USER'S EXACT INQUIRY: Answer their specific question directly. If they ask about gaining weight, losing fat, recipes, timing, digestion, workouts, protein sources, or snacks, give specific, actionable advice.
                3. INTEGRATE TARGETS: Mention their active goal ({settings.target_goal}) and remaining macros (e.g. {round(pro_left)}g protein left).
                4. FORMATTING: Provide 2-3 structured paragraphs with bullet points for readability. DO NOT USE ** ASTERISKS.
                5. On the very last line, provide 3 short clickable follow-up prompt chips strictly formatted as:
                CHIPS: ["Option 1", "Option 2", "Option 3"]

                USER INQUIRY: "{user_message}"
                """
                
                res = model.generate_content(system_prompt)
                full_text = res.text.strip()
                
                chips = ["Suggest high-protein options", "How to hit today's targets", "Quick snack pairing"]
                cleaned_text = full_text
                if "CHIPS:" in full_text:
                    parts = full_text.split("CHIPS:")
                    cleaned_text = parts[0].strip()
                    try:
                        chips_raw = parts[1].strip()
                        chips = json.loads(chips_raw)
                    except Exception:
                        pass
                        
                cleaned_text = sanitize_response_text(cleaned_text)
                save_coach_message(user_id, "coach", cleaned_text, chips)
                
                return CoachResponse(
                    response=cleaned_text,
                    suggested_actions=["Pair carbs with plant-based protein & fiber", "Try adding a side of spiced dal or roasted seeds"],
                    additive_focus=["Target Goal Harmony", "Micronutrient Density", "Glycemic Stability"],
                    is_demo_mode=False
                )
            except Exception as e:
                print(f"Gemini model {model_name} error: {e}")
                continue

    # 2. ADVANCED GENERATIVE CONVERSATIONAL NLP ENGINE (SMART FALLBACK)
    response_text, chips = generate_dynamic_coach_response(
        user_message=user_message,
        settings=settings,
        trends=trends,
        today_cal=today_cal,
        today_pro=today_pro,
        today_carbs=today_carbs,
        today_fat=today_fat,
        today_fiber=today_fiber,
        cal_left=cal_left,
        pro_left=pro_left,
        carbs_left=carbs_left,
        fat_left=fat_left
    )

    clean_resp = sanitize_response_text(response_text)
    save_coach_message(user_id, "coach", clean_resp, chips)
    
    return CoachResponse(
        response=clean_resp,
        suggested_actions=["Incorporate an extra serving of plant-based fiber", "Pair vitamin C with whole grains"],
        additive_focus=["Target Goal Harmony", "Steady Satiety", "Micro-nutrient Density"],
        is_demo_mode=True
    )


def generate_dynamic_coach_response(
    user_message: str,
    settings: UserSettings,
    trends: Dict[str, Any],
    today_cal: float,
    today_pro: float,
    today_carbs: float,
    today_fat: float,
    today_fiber: float,
    cal_left: float,
    pro_left: float,
    carbs_left: float,
    fat_left: float
) -> tuple[str, List[str]]:
    """Intelligent semantic response generator tailored to user's question, profile metrics, and diet gaps."""
    msg = user_message.lower().strip()
    name = settings.full_name or "there"
    goal = settings.target_goal or "Muscle Gain"
    weight = settings.weight_kg or 68.0
    pro_goal = settings.daily_protein_goal or 120
    cal_goal = settings.daily_calorie_goal or 2400

    # 1. WEIGHT GAIN / BULKING / ADDING LEAN MASS
    if any(k in msg for k in ["gain weight", "gain wieittgh", "bulk", "skinny", "put on mass", "add weight", "surplus"]):
        surplus_target = round(cal_goal + 350)
        text = (
            f"To gain healthy weight and lean muscle for your {weight}kg frame, the golden rule is an additive caloric surplus of +300 to +500 kcal above your maintenance (aim for ~{surplus_target} kcal/day) with {pro_goal}g protein.\n\n"
            f"High-Impact Additive Weight Gain Strategy:\n"
            f"1. Dense Healthy Fats: Add Mixed Nuts & 70% Dark Chocolate (190 kcal) between meals or drizzle an extra spoon of pure ghee/olive oil on your Dal Tadka & Rotis (+120 clean kcal without feeling heavy).\n"
            f"2. Double Up on Protein Anchors: Pair Paneer Tikka (310 kcal, 22g Pro) with Steamed Rice or eat 2-3 Boiled Eggs as snacks.\n"
            f"3. Liquid & Whole Food Nutrition: Drink homemade banana, oats, and peanut butter smoothies between your regular breakfast and lunch.\n"
            f"4. Current Status Today: You have {round(cal_left)} kcal and {round(pro_left)}g protein left to reach your baseline."
        )
        chips = ["High-calorie snack ideas", "Best protein for bulking", "Pre & post workout meals"]

    # 2. WEIGHT LOSS / FAT LOSS / CALORIC DEFICIT
    elif any(k in msg for k in ["fat loss", "weight loss", "lose weight", "cut", "deficit", "lean"]):
        text = (
            f"For sustainable Fat Loss & Lean Definition on your {cal_goal} kcal target:\n\n"
            f"• Additive High-Volume Eating: Keep your regular portions and add fiber-dense whole foods like cucumber salad, sliced tomatoes, or Dal Tadka to increase fullness.\n"
            f"• Preserve Lean Muscle: Maintain your {pro_goal}g protein target so your body burns fat while keeping your active metabolic rate high.\n"
            f"• Remaining Today: You have {round(cal_left)} kcal available to fuel your day."
        )
        chips = ["Low calorie dense snacks", "How much fiber should I eat?", "Best dinner for fat loss"]

    # 3. WHAT SHOULD I EAT / MEAL PLANNING
    elif any(k in msg for k in ["what should i eat", "suggest meal", "what to eat", "next meal", "recommend", "food for today"]):
        if pro_left > 20:
            text = (
                f"For your {weight}kg {goal} plan, you currently have {round(pro_left)}g protein and {round(cal_left)} kcal remaining today.\n\n"
                f"Top Recommendations From Your Food Catalog:\n"
                f"• Paneer Tikka (310 kcal, 22g Protein): Char-grilled cottage cheese cubes provide instant bioavailable protein for muscle recovery.\n"
                f"• Dal Tadka + 2 Rotis (460 kcal, 18g Protein, 13g Fiber): A comforting, satiating pairing rich in complex carbohydrates and iron.\n"
                f"• Chicken Curry or 2 Boiled Eggs (155-320 kcal, 13-27g Protein): High-density complete amino acids."
            )
            chips = ["How to log this meal?", "Snack pairing ideas", "Review my macro progress"]
        else:
            text = (
                f"You are doing great today! You've already reached {round(today_pro)}g / {pro_goal}g protein.\n\n"
                f"To complete your daily energy balance ({round(cal_left)} kcal left), consider:\n"
                f"• Mixed Fruit Bowl (130 kcal, 5g Fiber): Papaya, kiwi, and berries for antioxidant recovery and micronutrients.\n"
                f"• Mixed Nuts & Dark Chocolate (190 kcal): Rich in magnesium, zinc, and healthy fats.\n"
                f"• Poha or Steamed Rice with Sambhar: Light, easy-to-digest complex carbohydrates."
            )
            chips = ["What about hydration?", "Add evening snack", "Check micronutrients"]

    # 4. PROTEIN & MUSCLE GAIN
    elif any(k in msg for k in ["protein", "muscle", "hypertrophy", "amino"]):
        text = (
            f"To support your {goal} target of {pro_goal}g protein daily (~{round(pro_goal/weight, 1)}g per kg bodyweight for your {weight}kg frame):\n\n"
            f"Smart Additive Protein Strategies:\n"
            f"1. Anchor Every Meal with 20-30g Protein: Combine Dal Tadka (10g) with Paneer (22g) or Boiled Eggs (13g).\n"
            f"2. Fortify Breakfast: Stir a spoonful of roasted seeds or 2 boiled eggs alongside your morning Poha (6g) to start the day with 20g+ protein.\n"
            f"3. Current Status: You have {round(pro_left)}g protein remaining for today."
        )
        chips = ["High-protein snacks", "Vegetarian protein sources", "Post-workout timing"]

    # 5. FIBER, GUT HEALTH & DIGESTION
    elif any(k in msg for k in ["fiber", "gut", "digestion", "bloat", "constipat", "microbiome"]):
        text = (
            f"Your daily target is {settings.daily_fiber_goal}g of dietary fiber (consumed today: {round(today_fiber, 1)}g).\n\n"
            f"Easy Additive Ways to Boost Fiber by +10g:\n"
            f"• Add Whole Pulses: A single bowl of Chole Masala or Rajma adds 9-10g of natural prebiotic fiber.\n"
            f"• Add Fresh Fruit Platter: 1 bowl of Mixed Fruit Bowl provides 5g soluble fiber.\n"
            f"• Keep Whole Grains: Pair curries with Whole Wheat Roti (3g fiber) rather than refined flour."
        )
        chips = ["High-fiber breakfast ideas", "Prebiotic foods list", "How fiber stabilizes energy"]

    # 6. WORKOUT / EXERCISE / PRE & POST RECOVERY
    elif any(k in msg for k in ["workout", "gym", "exercise", "training", "pre workout", "post workout", "recovery"]):
        text = (
            f"Nutritional Timing for Your {goal} Goals:\n\n"
            f"• Pre-Workout (60-90 mins before): Eat fast-assimilating complex carbs like Poha or 1 Roti with a touch of honey for optimal glycogen availability.\n"
            f"• Post-Workout (Within 2 hours): Combine 25-35g Protein with carbs (e.g. Paneer Tikka + Steamed Rice or Grilled Salmon / Eggs) to trigger muscle protein synthesis.\n"
            f"• Hydration: Drink 500ml water with a pinch of pink salt and lemon for electrolyte restoration."
        )
        chips = ["Best pre-workout snack", "Post-workout meal ideas", "How much water do I need?"]

    # 7. BREAKFAST / LUNCH / DINNER / SNACKS
    elif any(k in msg for k in ["breakfast", "morning"]):
        text = (
            f"High-Energy Breakfast Blueprint:\n\n"
            f"• Base: Poha (250 kcal, 6g Pro) or Idli with Sambhar (240 kcal, 9g Pro).\n"
            f"• Additive Protein Boost: Add 2 Boiled Eggs (13g Pro) or 50g crumbled paneer.\n"
            f"• Micronutrient Boost: A side of sliced papaya or pomegranate for digestive enzymes and vitamin C."
        )
        chips = ["Lunch ideas", "What should I eat next?", "Quick 5-min breakfast"]

    elif any(k in msg for k in ["lunch", "midday", "afternoon"]):
        text = (
            f"Nutrient-Dense Lunch Blueprint:\n\n"
            f"• Core: 2 Rotis + Dal Tadka (340 kcal, 14g Pro, 10g Fiber) or Rajma Masala with Steamed Rice (455 kcal, 17g Pro).\n"
            f"• Additive Pairing: Sliced cucumber with lemon juice to maximize iron bioavailability from the lentils.\n"
            f"• Outcome: Sustained focus with zero afternoon energy crashes."
        )
        chips = ["Why am I hungry at 4 PM?", "Dinner suggestions", "Healthy snacks"]

    elif any(k in msg for k in ["dinner", "night", "evening"]):
        text = (
            f"Restorative Dinner Blueprint:\n\n"
            f"• Target: You have {round(pro_left)}g Protein and {round(cal_left)} kcal remaining for today.\n"
            f"• Option A (High Protein): Paneer Tikka with 1 Roti and Greens (430 kcal, 26g Pro).\n"
            f"• Option B (Comforting Whole Food): Chole Masala with Light Steamed Rice (480 kcal, 16g Pro, 10g Fiber)."
        )
        chips = ["Light evening snack", "Will late carbs hurt sleep?", "Check my daily total"]

    elif any(k in msg for k in ["snack", "cravings", "evening tea"]):
        text = (
            f"Smart 1-Step Snacks From Your Kitchen:\n\n"
            f"• Mixed Nuts & 70% Dark Chocolate (190 kcal, 5g Pro): Polyphenols and healthy fats for dopamine and steady satiety.\n"
            f"• Roasted Chana / Sprouted Moong: +8g plant-based protein with zero preparation.\n"
            f"• Mixed Fruit Bowl with Chia Seeds: Natural sweetness with 5g fiber."
        )
        chips = ["Best late-night snack", "How to curb sugar cravings", "High-protein snack ideas"]

    # 8. MICRONUTRIENTS, VITAMINS & MINERALS
    elif any(k in msg for k in ["iron", "calcium", "vitamin", "mineral", "sodium", "electrolyte"]):
        text = (
            f"Micronutrient Density Check for {name}:\n\n"
            f"• Iron & Bioavailability: Dal Tadka and Rotis provide non-heme iron. Always squeeze fresh lemon (Vitamin C) on lentils to increase absorption by up to 300%!\n"
            f"• Calcium (1,000 mg target): Paneer Tikka (350mg) and Idli Sambhar provide natural bioavailable calcium for bone and muscle contractile function.\n"
            f"• Vitamin D: Pair meals with brief morning sunlight exposure or fortified foods."
        )
        chips = ["How to increase iron absorption?", "Best calcium sources", "Check my trends"]

    # 9. OPEN HEALTH / RECIPE / MEAL QUERY
    else:
        text = (
            f"Hello {name}! Regarding your question about '{user_message}':\n\n"
            f"From an additive clinical nutrition standpoint for your {goal} plan ({pro_goal}g protein, {cal_goal} kcal target):\n\n"
            f"• Target Alignment: You currently have {round(pro_left)}g protein and {round(cal_left)} kcal left today.\n"
            f"• Recommended Action: Fuel your body with nutrient-dense foods (e.g. lentils, eggs, paneer, whole grains, seeds) to maintain stable glycemic energy and recovery.\n"
            f"• Next Step: What specific meal or recipe can I help you pair next?"
        )
        chips = ["What should I eat next?", "How to hit my protein goal", "Suggest a healthy snack", "Explain my 7-day trends"]

    return text, chips
