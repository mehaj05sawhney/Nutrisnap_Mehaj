# NutriSnap AI 🌿✨
### Multimodal AI Nutrition Tracking, Precision Metabolic Intelligence & Additive Nutrition Coaching

NutriSnap AI is an enterprise-grade, full-stack nutrition intelligence web application built on an **evidence-based, additive nutritional philosophy**. Rather than enforcing restrictive diets, calorie guilt, or static meal plans, NutriSnap AI empowers users to understand what they eat through multimodal vision (**Gemini 2.5 Flash**), natural language parsing, dynamic metabolic profile calibration (**Mifflin-St Jeor Formula**), and an intelligent AI coach equipped with strict nutritional guardrails.

---

## 📑 Table of Contents
1. [Core Features](#-core-features)
2. [Additive Nutrition Philosophy](#-additive-nutrition-philosophy)
3. [System Architecture](#-system-architecture)
4. [Project Directory Structure](#-project-directory-structure)
5. [Setup & Installation Guide](#-setup--installation-guide)
6. [Scientific Formulas & Metabolic Engine](#-scientific-formulas--metabolic-engine)
7. [Food Dataset Specification (`data/foods.csv`)](#-food-dataset-specification-datafoodscsv)
8. [REST API Reference](#-rest-api-reference)
9. [AI Coach & Guardrail System](#-ai-coach--guardrail-system)
10. [Technologies Used](#-technologies-used)

---

## 🌟 Core Features

### 1. 📅 Dynamic 7-Day Rolling Date Engine
- **Always Current**: Automatically synchronizes with the user's real-time date (e.g., today **Aug 26** automatically generates **WED 26 &rarr; WED 2 Sep** with month header **`AUG - SEP, 2026`**).
- **Auto-Rolling**: The 7-to-8 day tracking window rolls forward daily without any hardcoded dates or manual configuration.
- **One-Click Date Navigation**: Switch between days seamlessly to view daily meal logs and consumption progress.

### 2. 🎯 Personalized Metabolic Profile & Goal Engine
- **Clinical Calculation**: Uses the **Mifflin-St Jeor equation** to calculate exact Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) based on **Age**, **Weight ($kg$)**, **Height ($cm$)**, **Gender**, and **Activity Level**.
- **Dynamic Goal Customization**:
  - **Muscle Gain**: Caloric surplus ($+350\text{ kcal}$) with $2.0\text{g}/\text{kg}$ protein for hypertrophy.
  - **Fat Loss / Lean**: Satiating deficit ($-450\text{ kcal}$) with elevated protein ($1.8\text{g}/\text{kg}$) to preserve lean tissue.
  - **Endurance & Energy**: Glycogen-matched energy balance with high complex carbohydrates ($1.6\text{g}/\text{kg}$ protein).
  - **Maintenance**: Balanced metabolic homeostasis ($1.4\text{g}/\text{kg}$ protein).
- **Instant Dashboard Synchronization**: Changing your profile immediately recalculates your daily targets and updates the circular gauge and macro meters in real time.

### 3. 0️⃣ Zero Phantom Data & Real-Time Macro Meters
- **Clean Starting State**: Daily overview starts strictly at **0 kcal consumed** and **0g consumed** until meals are logged.
- **Dynamic Gauges**: Circular SVG gauge and progress bars dynamically display:
  - **Calories**: `0 / [Target] kcal`
  - **Protein**: `0 / [Target]g`
  - **Carbohydrates**: `0 / [Target]g`
  - **Fat**: `0 / [Target]g`

### 4. 🖼️ Profile-Adaptive Hero Plate & Smart Additive Suggestions
- **Dynamic Dish Showcase**: The hero card automatically displays culinary dishes tailored to your active goal:
  - *Muscle Gain* &rarr; Sizzling **Paneer Tikka / Grilled Salmon** (`✦ Muscle Target: High Protein`).
  - *Fat Loss* &rarr; High-fiber **Dal Tadka / Poha** (`✦ Fat Loss Target: Lean & Satiating`).
  - *Endurance* &rarr; Complex carb **Masala Dosa / Idli** (`✦ Endurance Target: Sustained Carbs`).
  - *Maintenance* &rarr; Balanced **Whole Wheat Roti / Fruit Platter**.
- **Context-Aware Suggestions**: The AI suggestions card computes your remaining protein/carb gap and suggests 1-click quick-log additions (*Paneer Tikka, Dal Tadka, Boiled Eggs, Chicken Curry*).

### 5. 🍱 Food Options Catalog & Micronutrient Inspector
- **Authentic Culinary Library**: 14 staple Indian and universal whole foods with authentic 4K culinary photography.
- **Zero Undefined Metrics**: Every catalog card and inspector modal displays full macronutrients (Protein, Carbs, Fat, Fiber) and micronutrients (Calcium, Iron, Vitamin C, Vitamin D, Sodium, Sugar).
- **1-Click Nutrition Inspector**: Interactive modal with portion multiplier stepper ($0.5\times$ to $5.0\times$), meal type selection (*Breakfast, Lunch, Dinner, Snack*), and 1-click diary logging.

### 6. 🤖 Intelligent AI Coach with Gemini & Domain Guardrails
- **Multimodal AI**: Direct Google Gemini SDK integration supporting `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`, and `gemini-pro`.
- **Generative Fallback Engine**: Generates dynamic, context-aware answers analyzing user query, body weight, target goal, consumed macros, and catalog foods.
- **Strict Nutritional Guardrails**: Intercepts off-topic queries (*assignments, coding, math, stocks, politics*) and politely redirects to dietary wellness.
- **Clean Formatting**: Clean, readable output with zero raw markdown asterisks (`**`).
- **One-Click Clear Chat**: Header action button to reset AI conversation history instantly.

### 7. 👤 Dynamic Gender Avatars
- **Male**: Blue human avatar icon (`#3b82f6` with blue glow border).
- **Female**: Pink human avatar icon (`#ec4899` with pink glow border).
- **Non-Binary / Other**: Grey human avatar icon (`#9ca3af` with grey border).

### 8. 📷 Multimodal Vision & Natural Language Meal Logging
- **Snap Meal**: Scan photos of dishes using Gemini Vision with viewfinder HUD, laser animation, and multi-ingredient detection.
- **Natural Language Parsing**: Type everyday phrases (e.g. *"Had 2 rotis and 1 bowl of dal tadka with curd for lunch"*); AI extracts portion sizes, meal types, and exact nutritional metrics.

---

## 🌿 Additive Nutrition Philosophy

NutriSnap AI is built on clinical behavioral nutrition:
1. **Additive, Never Restrictive**: Focuses on what nutrient-dense foods to **ADD** (fiber, lentils, seeds, colorful fruits, protein anchors) rather than eliminating foods.
2. **Zero Guilt & Zero Shame**: No negative labels like "bad foods", "cheat days", or red restriction warnings.
3. **Glycemic Stability & Satiety**: Emphasizes pairing complex carbohydrates with protein and healthy fats for sustained physical energy and cognitive focus.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────────────────────┐
                                  │           Client Web Browser           │
                                  │   (HTML5, Modern CSS3, ES6+ Vanilla)   │
                                  └───────────────────┬────────────────────┘
                                                      │
                                             REST API / JSON / Static
                                                      │
                                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                            FastAPI Backend                                             │
│                                              (Port 8000)                                               │
│                                                                                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐  │
│  │   Dashboard Router   │  │   Food Data Layer    │  │   AI Coach Engine    │  │   Profile Engine   │  │
│  │  (/api/dashboard)    │  │ (/api/food-options)  │  │    (/api/coach)      │  │  (/api/profile/*)  │  │
│  │  Rolling 7-Day Window│  │  data/foods.csv (14) │  │  Guardrails + Models │  │  Mifflin-St Jeor   │  │
│  └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘  └─────────┬──────────┘  │
│             │                         │                         │                        │             │
│             └─────────────────────────┼─────────────────────────┴────────────────────────┘             │
│                                       ▼                                                                │
│                   ┌───────────────────────────────────────┐                                            │
│                   │         SQLite Database Layer         │                                            │
│                   │             (nutrisnap.db)            │                                            │
│                   │  • users (profile, targets, avatar)   │                                            │
│                   │  • meals & meal_items (7-day logs)    │                                            │
│                   │  • coach_messages (chat history)      │                                            │
│                   └───────────────────┬───────────────────┘                                            │
└───────────────────────────────────────┼────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                   ┌────────────────────────────────────────┐
                   │        Google Gemini AI Service        │
                   │  • Gemini 2.5 / 2.0 / 1.5 Flash        │
                   │  • Vision Multimodal Photo Scanning    │
                   │  • Natural Language Meal Parsing       │
                   │  • Intelligent Conversational Coach    │
                   └────────────────────────────────────────┘
```

---

## 📁 Project Directory Structure

```
nutribae/
├── backend/
│   ├── __init__.py          # Python package initializer
│   ├── main.py              # FastAPI server, REST routes, static file mounting
│   ├── models.py            # Pydantic data schemas (User, Meal, Coach, Foods, Profile)
│   ├── database.py          # SQLite schema, migrations, CRUD, and initial setup
│   ├── nutrition.py         # CSV food parser & macro/micronutrient calculation engine
│   ├── gemini_service.py    # Google Gemini Vision & Natural Language parser
│   ├── coach.py             # Additive AI Coach, Guardrail Intent Filter & Generative NLP
│   └── trends.py            # 7-day & 30-day passive trend analytics engine
├── data/
│   └── foods.csv            # Master food dataset (14 staple items with macros & micros)
├── frontend/
│   ├── index.html           # Single-Page Application HTML markup
│   ├── styles.css           # Glassmorphism, dark theme, micro-animations, responsive layout
│   ├── app.js               # Reactive frontend logic, router, modals, API calls
│   └── assets/              # Culinary food photography, backdrops, and avatar icons
│       ├── roti.jpg         # 4K fresh warm Indian chapati/roti stack
│       ├── dal.jpg          # Authentic Dal Tadka with chili-ghee tadka tempering
│       ├── poha.jpg         # Traditional lemon Aloo Poha (Depositphotos)
│       ├── rajma.jpg        # Authentic Rajma Masala bowl (Pexels #12737913)
│       ├── paneer_tikka.jpg # Sizzling paneer tikka cubes
│       ├── chicken_curry.jpg# Rich chicken curry
│       ├── rice.jpg         # Steamed basmati rice
│       ├── idli.jpg         # Steamed idlis with sambhar
│       ├── dosa.jpg         # Crispy masala dosa with chutneys
│       ├── chole.jpg        # Spiced chole masala
│       ├── eggs.jpg         # Boiled eggs
│       ├── fruit_bowl.jpg   # Fresh mixed fruit bowl
│       ├── nuts_choco.jpg   # Mixed nuts & 70% dark chocolate
│       └── salmon.jpg       # Grilled salmon with greens
├── uploads/                 # Storage directory for user-uploaded meal images
├── .env.example             # Environment configuration template
├── requirements.txt         # Python dependencies
└── README.md                # Master project documentation
```

---

## 🚀 Setup & Installation Guide

### 1. Prerequisites
- **Python**: Version `3.10` or higher
- **Package Manager**: `pip`
- **Web Browser**: Chrome, Edge, Firefox, or Safari

### 2. Clone Repository & Navigate
```bash
git clone https://github.com/your-username/nutribae.git
cd nutribae
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to create `.env`:
```bash
cp .env.example .env
```

Edit `.env` to configure your settings:
```env
# Optional: Google Gemini API Key for live vision and AI coaching
# Get your free key at https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Server Host & Port
HOST=127.0.0.1
PORT=8000
```

> **Note**: If `GEMINI_API_KEY` is not provided or expired, NutriSnap AI automatically activates its **Smart Offline Generative Engine**, ensuring all features, food logging, meal inspections, and AI coaching continue working seamlessly.

### 5. Launch the Application
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 6. Access the Application
Open your web browser and navigate to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔬 Scientific Formulas & Metabolic Engine

NutriSnap AI computes nutritional requirements using validated clinical nutrition standards:

### 1. Basal Metabolic Rate (BMR) - Mifflin-St Jeor
$$\text{BMR}_{\text{male}} = 10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age (yr)} + 5$$
$$\text{BMR}_{\text{female}} = 10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age (yr)} - 161$$

### 2. Total Daily Energy Expenditure (TDEE)
$$\text{TDEE} = \text{BMR} \times \text{Activity Multiplier}$$
- **Sedentary / Light**: $1.20$
- **Moderate Activity**: $1.55$
- **High Activity / Athlete**: $1.725$

### 3. Goal-Specific Macronutrient Allocation

| Target Goal | Caloric Target | Protein Target | Fat Target | Carbohydrates Target |
| :--- | :--- | :--- | :--- | :--- |
| **Muscle Gain** | $\text{TDEE} + 350\text{ kcal}$ | $2.0\text{g} \times \text{Weight}_{kg}$ | $25\%$ of Total Calories | Remaining Calories / 4 |
| **Fat Loss / Lean** | $\text{TDEE} - 450\text{ kcal}$ | $1.8\text{g} \times \text{Weight}_{kg}$ | $25\%$ of Total Calories | Remaining Calories / 4 |
| **Endurance & Energy** | $\text{TDEE} + 150\text{ kcal}$ | $1.6\text{g} \times \text{Weight}_{kg}$ | $20\%$ of Total Calories | Remaining Calories / 4 |
| **Maintenance** | $\text{TDEE}$ | $1.4\text{g} \times \text{Weight}_{kg}$ | $25\%$ of Total Calories | Remaining Calories / 4 |

---

## 📊 Food Dataset Specification (`data/foods.csv`)

The food dataset in `data/foods.csv` contains zero undefined values and defines all essential macronutrients and micronutrients:

```csv
id,name,serving_size,category,calories,protein_g,carbs_g,fat_g,fiber_g,sugar_g,sodium_mg,calcium_mg,iron_mg,vitamin_c_mg,vitamin_d_mcg
roti,Roti,1 piece (40g),Grains & Breads,120,4.0,22.0,2.5,3.0,0.5,120,15,1.2,0.0,0.0
dal_tadka,Dal Tadka,1 bowl (150g),Legumes & Pulses,220,10.0,28.0,7.0,7.0,1.2,340,45,2.8,4.5,0.0
poha,Poha,1 medium plate (180g),Breakfast & Grains,250,6.0,38.0,8.0,4.0,2.0,280,30,2.1,8.0,0.0
paneer_tikka,Paneer Tikka,6 cubes (160g),Dairy & Vegetarian,310,22.0,10.0,20.0,2.0,2.5,420,380,1.5,6.0,0.8
chicken_curry,Chicken Curry,1 bowl (200g),Poultry & Meat,320,27.0,9.0,18.0,2.0,1.8,480,35,2.4,5.0,0.6
steamed_rice,Steamed Rice,1 bowl (150g),Grains & Staples,195,4.0,43.0,0.5,0.6,0.1,5,10,0.4,0.0,0.0
idli_sambhar,Idli with Sambhar,2 idlis + 1 cup sambhar (220g),South Indian,240,9.0,40.0,4.5,5.0,3.0,380,50,2.0,6.5,0.0
masala_dosa,Masala Dosa,1 large dosa (200g),South Indian,360,8.0,48.0,15.0,4.0,2.0,650,80,2.0,1.0,0.0
chole_masala,Chole Masala,1 bowl (180g),Legumes & Curries,285,12.0,38.0,9.0,10.0,3.5,460,90,3.6,7.0,0.0
rajma_masala,Rajma Masala,1 bowl (180g),Legumes & Curries,260,13.0,37.0,6.5,9.0,2.8,420,85,3.2,5.5,0.0
boiled_eggs,Boiled Eggs,2 large eggs (100g),Eggs & Poultry,155,13.0,1.0,10.5,0.0,0.6,140,50,1.8,0.0,2.0
mixed_fruit_bowl,Mixed Fruit Bowl,1 bowl (200g),Fresh Fruits,130,2.0,32.0,0.6,5.0,24.0,10,40,0.8,45.0,0.0
nuts_dark_chocolate,Mixed Nuts & Dark Chocolate,1 small handful (35g),Healthy Snacks,190,5.0,13.0,14.0,3.0,7.0,45,60,1.9,0.5,0.0
grilled_salmon,Grilled Salmon with Green Veggies,1 fillet + greens (220g),Fish & Seafood,410,34.0,14.0,22.0,5.0,2.0,360,95,2.1,18.0,11.5
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Backend status, Gemini mode check, and foods count |
| `GET` | `/api/dashboard` | Daily overview, active dates, consumed macros, and logged meals |
| `GET` | `/api/food-options` | Full list of 14 catalog food items with complete nutrients |
| `POST` | `/api/meals/log-item` | Log a specific food item with portion multiplier |
| `POST` | `/api/meals/log-natural` | Natural language meal parsing & logging with Gemini NLP |
| `POST` | `/api/meals/snap-image` | Multimodal photo food scanning with Gemini Vision |
| `DELETE` | `/api/meals/{id}` | Delete a logged meal record |
| `GET` | `/api/trends` | 7-day & 30-day nutrition averages, micronutrients, variety score |
| `POST` | `/api/coach` | Interactive AI Coach conversational guidance |
| `GET` | `/api/coach/history` | Retrieve AI Coach chat messages |
| `POST` | `/api/coach/clear` | Clear AI Coach conversation history |
| `POST` | `/api/profile/calculate-targets` | Calculate BMR, TDEE, and optimal targets |
| `POST` | `/api/profile/save` | Save updated user profile and recalculate dashboard targets |

---

## 🛡️ AI Coach & Guardrail System

The AI Coach features a dual-layer security and intent classification system:

### 1. Guardrail Intent Classification
- **Supported Domains ✅**:
  - Nutrition science, whole foods, recipes, and additive meal pairings.
  - Macronutrients (protein, carbs, fat, fiber) and micronutrients (iron, calcium, vitamins).
  - Fitness goals (weight gain, fat loss, muscle hypertrophy, recovery, digestion).
  - NutriSnap app features, logged meals, and daily targets.
- **Off-Track Queries ⛔**:
  - Homework, school assignments, coding, math, finance, crypto, politics, general trivia.
  - **Refusal Response**:
    > *"Sorry, I can't help with that! I am your NutriSnap AI Nutrition & Culinary Coach, so I specialize exclusively in food, meal planning, dietary macros, recipes, and your health & fitness targets."*

### 2. Conversational Capabilities
- **Friendly Greetings**: Responds warmly to *"Hello"*, *"How are you"*, *"Good morning"* and asks how to help with daily meals.
- **Dynamic Weight Gain / Loss Guidance**: Provides actionable caloric surplus/deficit guidance citing the user's exact body weight, protein target, and food recommendations.

---

## 💻 Technologies Used

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+), [Pydantic v2](https://docs.pydantic.dev/), [Uvicorn](https://www.uvicorn.org/)
- **Database**: SQLite3 (`nutrisnap.db`) with relational meal items & user settings schemas
- **AI & Multimodal**: [Google Generative AI SDK](https://ai.google.dev/) (Gemini 2.5 Flash, 2.0 Flash, 1.5 Flash)
- **Frontend**: Vanilla HTML5, Vanilla CSS3 (Custom Design System, Glassmorphism, Dark Mode), Vanilla JavaScript (ES6+)
- **Typography**: Plus Jakarta Sans, Outfit & Inter (Google Fonts)

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
