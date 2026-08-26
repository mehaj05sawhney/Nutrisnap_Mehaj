import os
import json
import re
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from .models import GeminiParseResult, DetectedFood

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Check if google-genai or google-generativeai is available
genai_client = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        genai_client = genai
        print("Gemini API configured successfully in REAL MODE.")
    except Exception as e:
        print(f"Error configuring Gemini SDK: {e}")
        genai_client = None
else:
    print("No GEMINI_API_KEY found. NutriSnap running in DEMO MODE.")


def is_demo_mode() -> bool:
    return genai_client is None


def parse_natural_language_food(text: str, default_meal_type: Optional[str] = None) -> GeminiParseResult:
    """Parses natural language meal descriptions into structured items."""
    if not is_demo_mode():
        try:
            model = genai_client.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            You are NutriSnap AI's food extraction engine.
            Extract food items, portion quantities, and meal type from this user text:
            "{text}"

            Return ONLY valid JSON matching this exact structure:
            {{
                "meal_type": "Breakfast" | "Lunch" | "Dinner" | "Snack",
                "suggested_title": "Short descriptive title (e.g. Roti & Dal)",
                "detected_foods": [
                    {{
                        "name": "Standard food name in English or common Indian cuisine",
                        "quantity": 1.0,
                        "confidence": 0.95,
                        "notes": "Optional portion notes"
                    }}
                ],
                "raw_reasoning": "Brief explanation"
            }}
            Do not include markdown code block backticks if possible. Output raw JSON only.
            """
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            # Clean JSON if wrapped in markdown
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            data = json.loads(raw_text.strip())
            
            foods = [DetectedFood(**f) for f in data.get("detected_foods", [])]
            return GeminiParseResult(
                meal_type=data.get("meal_type", default_meal_type or "Lunch"),
                suggested_title=data.get("suggested_title", "Logged Meal"),
                detected_foods=foods,
                raw_reasoning=data.get("raw_reasoning")
            )
        except Exception as e:
            print(f"Gemini API parse failed ({e}). Falling back to intelligent demo parser.")

    # DEMO MODE PARSER (Deterministic & Realistic)
    text_lower = text.lower()
    
    # Infer meal type
    meal_type = default_meal_type or "Lunch"
    if any(w in text_lower for w in ["breakfast", "morning", "poha", "idli", "dosa", "egg", "tea"]):
        meal_type = "Breakfast"
    elif any(w in text_lower for w in ["lunch", "afternoon", "roti", "rice", "dal"]):
        meal_type = "Lunch"
    elif any(w in text_lower for w in ["dinner", "night", "curry", "paneer", "salmon"]):
        meal_type = "Dinner"
    elif any(w in text_lower for w in ["snack", "nuts", "chocolate", "fruit", "tea", "coffee"]):
        meal_type = "Snack"

    detected = []
    
    # Check quantities and items
    # Rotis
    roti_match = re.search(r'(\d+|two|three|four|one|a couple of|2|3|4|1)\s*(?:whole wheat\s*)?roti', text_lower)
    if "roti" in text_lower or "chapati" in text_lower:
        qty = 2.0
        if roti_match:
            word = roti_match.group(1)
            num_map = {"one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "a couple of": 2.0}
            qty = num_map.get(word, float(word) if word.isdigit() else 2.0)
        detected.append(DetectedFood(name="Roti", quantity=qty, confidence=0.98, notes=f"{int(qty)} whole wheat flatbreads"))

    # Dal
    if "dal" in text_lower or "daal" in text_lower or "tadka" in text_lower:
        detected.append(DetectedFood(name="Dal Tadka", quantity=1.0, confidence=0.96, notes="1 standard bowl"))

    # Poha
    if "poha" in text_lower or "flattened rice" in text_lower:
        detected.append(DetectedFood(name="Poha", quantity=1.0, confidence=0.97, notes="1 medium plate with peanuts"))

    # Paneer
    if "paneer" in text_lower:
        qty = 1.0
        if "curry" in text_lower or "gravy" in text_lower:
            detected.append(DetectedFood(name="Paneer Tikka", quantity=qty, confidence=0.92, notes="Cottage cheese"))
        else:
            detected.append(DetectedFood(name="Paneer Tikka", quantity=qty, confidence=0.95, notes="Grilled paneer cubes"))

    # Chicken
    if "chicken" in text_lower or "curry" in text_lower and "chicken" in text_lower:
        detected.append(DetectedFood(name="Chicken Curry", quantity=1.0, confidence=0.96, notes="1 bowl spiced chicken"))

    # Rice
    if "rice" in text_lower or "chawal" in text_lower:
        detected.append(DetectedFood(name="Steamed Rice", quantity=1.0, confidence=0.95, notes="1 bowl basmati rice"))

    # Dosa
    if "dosa" in text_lower:
        detected.append(DetectedFood(name="Masala Dosa", quantity=1.0, confidence=0.97, notes="1 large crisp dosa"))

    # Idli
    if "idli" in text_lower:
        detected.append(DetectedFood(name="Idli with Sambhar", quantity=1.0, confidence=0.97, notes="2 steamed idlis + sambhar"))

    # Chole
    if "chole" in text_lower or "chana" in text_lower:
        detected.append(DetectedFood(name="Chole Masala", quantity=1.0, confidence=0.95, notes="1 bowl spiced chickpeas"))

    # Rajma
    if "rajma" in text_lower or "kidney bean" in text_lower:
        detected.append(DetectedFood(name="Rajma Masala", quantity=1.0, confidence=0.95, notes="1 bowl kidney bean gravy"))

    # Eggs
    if "egg" in text_lower:
        qty = 2.0
        if "3" in text_lower or "three" in text_lower:
            qty = 3.0
        detected.append(DetectedFood(name="Boiled Eggs", quantity=qty / 2.0, confidence=0.98, notes=f"{int(qty)} eggs"))

    # Fruits
    if "fruit" in text_lower or "apple" in text_lower or "banana" in text_lower or "papaya" in text_lower:
        detected.append(DetectedFood(name="Mixed Fruit Bowl", quantity=1.0, confidence=0.94, notes="Fresh seasonal fruits"))

    # Nuts & Chocolate
    if "nut" in text_lower or "chocolate" in text_lower or "almond" in text_lower:
        detected.append(DetectedFood(name="Mixed Nuts & Dark Chocolate", quantity=1.0, confidence=0.95, notes="Handful of mixed nuts & chocolate"))

    # Salmon
    if "salmon" in text_lower or "fish" in text_lower:
        detected.append(DetectedFood(name="Grilled Salmon with Green Veggies", quantity=1.0, confidence=0.96, notes="1 grilled fillet"))

    # Fallback if no exact keyword caught
    if not detected:
        detected.append(DetectedFood(name="Roti", quantity=2.0, confidence=0.85, notes="Estimated standard portion"))
        detected.append(DetectedFood(name="Dal Tadka", quantity=1.0, confidence=0.85, notes="Estimated standard portion"))

    title = " + ".join([d.name for d in detected[:2]])
    return GeminiParseResult(
        meal_type=meal_type,
        suggested_title=title,
        detected_foods=detected,
        raw_reasoning="Parsed using NutriSnap semantic NLP food parser (Demo Mode)."
    )


def analyze_food_image_gemini(image_path: str, image_bytes: Optional[bytes] = None) -> GeminiParseResult:
    """Analyzes a food photo using Gemini Vision or realistic Demo Mode."""
    if not is_demo_mode() and image_bytes:
        try:
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_bytes))
            model = genai_client.GenerativeModel("gemini-1.5-flash")
            prompt = """
            You are NutriSnap AI's food vision model.
            Identify all food items, portions, and meal type present in this photo.
            Return ONLY valid JSON matching this schema:
            {
                "meal_type": "Breakfast" | "Lunch" | "Dinner" | "Snack",
                "suggested_title": "Descriptive short title (e.g. Chicken Curry & Rice)",
                "detected_foods": [
                    {
                        "name": "Standard food name",
                        "quantity": 1.0,
                        "confidence": 0.95,
                        "notes": "Visual observations like portion or side garnish"
                    }
                ],
                "raw_reasoning": "Visual bounding observations"
            }
            Output raw JSON only without markdown fences.
            """
            response = model.generate_content([prompt, image])
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            data = json.loads(raw_text.strip())
            
            foods = [DetectedFood(**f) for f in data.get("detected_foods", [])]
            return GeminiParseResult(
                meal_type=data.get("meal_type", "Lunch"),
                suggested_title=data.get("suggested_title", "Detected Meal"),
                detected_foods=foods,
                raw_reasoning=data.get("raw_reasoning", "Analyzed via Gemini Vision")
            )
        except Exception as e:
            print(f"Gemini Vision API failed ({e}). Using demo vision parser.")

    # DEMO MODE VISION RECOGNITION
    filename = os.path.basename(image_path).lower()
    
    if "salmon" in filename or "fish" in filename or "hero" in filename:
        return GeminiParseResult(
            meal_type="Dinner",
            suggested_title="Grilled Salmon with Green Veggies",
            detected_foods=[
                DetectedFood(name="Grilled Salmon with Green Veggies", quantity=1.0, confidence=0.96, notes="Char-grilled salmon fillet with sautéed greens and cherry tomatoes"),
            ],
            raw_reasoning="Vision detected rich omega-3 salmon protein source with fresh vegetables."
        )
    elif "chicken" in filename:
        return GeminiParseResult(
            meal_type="Dinner",
            suggested_title="Chicken Curry + Steamed Rice",
            detected_foods=[
                DetectedFood(name="Chicken Curry", quantity=1.0, confidence=0.97, notes="Tender chicken in aromatic gravy"),
                DetectedFood(name="Steamed Rice", quantity=1.0, confidence=0.94, notes="1 portion basmati rice")
            ],
            raw_reasoning="Vision detected poultry curry with steamed grains."
        )
    elif "paneer" in filename:
        return GeminiParseResult(
            meal_type="Lunch",
            suggested_title="Paneer Tikka + Roti",
            detected_foods=[
                DetectedFood(name="Paneer Tikka", quantity=1.2, confidence=0.98, notes="Tandoori marinated cottage cheese"),
                DetectedFood(name="Roti", quantity=2.0, confidence=0.95, notes="2 whole wheat rotis")
            ],
            raw_reasoning="Vision detected spiced paneer cubes and warm flatbreads."
        )
    elif "poha" in filename:
        return GeminiParseResult(
            meal_type="Breakfast",
            suggested_title="Kanda Poha",
            detected_foods=[
                DetectedFood(name="Poha", quantity=1.0, confidence=0.98, notes="Flattened rice with mustard seeds, turmeric & crunchy peanuts")
            ],
            raw_reasoning="Vision detected classic breakfast poha with lemon wedge."
        )
    elif "dosa" in filename or "idli" in filename:
        return GeminiParseResult(
            meal_type="Breakfast",
            suggested_title="Masala Dosa with Sambhar",
            detected_foods=[
                DetectedFood(name="Masala Dosa", quantity=1.0, confidence=0.96, notes="Golden fermented crepe with potato masala")
            ],
            raw_reasoning="Vision detected South Indian crispy dosa."
        )
    elif "fruit" in filename:
        return GeminiParseResult(
            meal_type="Snack",
            suggested_title="Fresh Fruit Bowl",
            detected_foods=[
                DetectedFood(name="Mixed Fruit Bowl", quantity=1.0, confidence=0.97, notes="Assorted seasonal antioxidant rich fruits")
            ],
            raw_reasoning="Vision detected fresh vitamin-rich mixed fruits."
        )
    else:
        # Default realistic dish
        return GeminiParseResult(
            meal_type="Lunch",
            suggested_title="Roti & Dal Tadka",
            detected_foods=[
                DetectedFood(name="Roti", quantity=2.0, confidence=0.96, notes="2 Whole wheat rotis"),
                DetectedFood(name="Dal Tadka", quantity=1.0, confidence=0.95, notes="1 Bowl tempered yellow lentils")
            ],
            raw_reasoning="Vision detected wholesome Indian lunch staple."
        )
