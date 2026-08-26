/**
 * NutriSnap AI - Frontend Application Logic
 * Full API Integration, Additive AI Intelligence, Interactive Food Options Catalog & Auth0
 */

const API_BASE = "";

const todayIsoDate = new Date().toISOString().split('T')[0];
let currentSelectedDate = todayIsoDate;
let currentHistoryFilter = "All";
let currentCatalogCategory = "All";
let selectedSampleImage = "salmon.jpg";
let activeReportMeal = null;
let allFoodOptions = [];
let activeInspectedFood = null;
let inspectorQty = 1.0;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  checkBackendHealth();
  loadFoodCatalog();
  loadDashboard(currentSelectedDate);
  loadSettings();
  initRotatingDeck();
  // Open landing page by default
  navigateTo('landing');
}

// ----------------- NAVIGATION ROUTER -----------------

function navigateTo(viewName) {
  if (viewName === 'landing') {
    document.body.classList.add('on-landing');
    if (typeof startDeckAutoRotation === 'function') {
      startDeckAutoRotation();
    }
  } else {
    document.body.classList.remove('on-landing');
  }

  // Update sidebar active state
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-view") === viewName);
  });

  // Switch visible page view
  document.querySelectorAll(".page-view").forEach(view => {
    view.classList.remove("active");
  });

  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) {
    targetView.classList.add("active");
  }

  // Load contextual data
  if (viewName === "dashboard") {
    loadDashboard(currentSelectedDate);
    loadFoodCatalog();
  } else if (viewName === "history") {
    loadHistory(currentHistoryFilter);
  } else if (viewName === "insights") {
    loadInsights();
  } else if (viewName === "coach") {
    loadCoachChat();
  } else if (viewName === "settings") {
    loadSettings();
  }
}

// ----------------- API / BACKEND CALLS -----------------

async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    const modeBadge = document.getElementById("mode-status-text");
    if (modeBadge) {
      if (data.demo_mode) {
        modeBadge.textContent = "Demo Mode (Active)";
      } else {
        modeBadge.textContent = "Gemini 2.5 Flash (Live)";
      }
    }
  } catch (e) {
    console.warn("Backend health check warning:", e);
  }
}

// ----------------- 1. DASHBOARD LOGIC -----------------

async function loadDashboard(dateStr) {
  currentSelectedDate = dateStr;
  try {
    const res = await fetch(`${API_BASE}/api/dashboard?date=${dateStr}`);
    if (!res.ok) return;
    const data = await res.json();

    renderDashboardOverview(data);
    renderDateSelector(data.available_dates, dateStr);
    renderTodayMeals(data.meals);
  } catch (err) {
    console.error("Failed loading dashboard:", err);
  }
}

function renderDashboardOverview(data) {
  const user = data.user;
  const ov = data.daily_overview;

  // Header Subtitle Date
  const dateObj = new Date(ov.date);
  const dateFormatted = dateObj.toLocaleDateString("en-US", { weekday: 'long', day: 'numeric', month: 'long' });
  const subDateEl = document.getElementById("header-subdate");
  if (subDateEl) subDateEl.textContent = dateFormatted;

  const calGoal = ov.calories_goal || user.daily_calorie_goal || 2400;
  const proGoal = ov.protein_goal || user.daily_protein_goal || 120;
  const carbsGoal = ov.carbs_goal || user.daily_carbs_goal || 250;
  const fatGoal = ov.fat_goal || user.daily_fat_goal || 65;

  // Overview top right pill
  const overviewGoalBadge = document.getElementById("overview-goal-badge");
  if (overviewGoalBadge) overviewGoalBadge.textContent = `Goal: ${calGoal} kcal`;

  // Top Hero Card Values
  document.getElementById("calories-consumed-val").textContent = Math.round(ov.calories_consumed);
  const calGoalEl = document.getElementById("calories-goal-val");
  if (calGoalEl) calGoalEl.textContent = calGoal;
  const calLeftEl = document.getElementById("calories-left-val");
  if (calLeftEl) calLeftEl.textContent = Math.max(0, calGoal - Math.round(ov.calories_consumed));

  // Circular Calorie Gauge
  const circle = document.getElementById("calorie-progress-circle");
  if (circle) {
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const pct = Math.min(100, Math.max(0, (ov.calories_consumed / calGoal) * 100));
    const offset = circumference - (pct / 100) * circumference;
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = offset;
  }

  // Macros (Dynamic from Profile)
  document.getElementById("protein-cur-val").textContent = Math.round(ov.protein_consumed);
  document.getElementById("protein-goal-val").textContent = `/ ${proGoal}g`;
  document.getElementById("protein-bar-fill").style.width = `${Math.min(100, (ov.protein_consumed / proGoal) * 100)}%`;

  document.getElementById("carbs-cur-val").textContent = Math.round(ov.carbs_consumed);
  document.getElementById("carbs-goal-val").textContent = `/ ${carbsGoal}g`;
  document.getElementById("carbs-bar-fill").style.width = `${Math.min(100, (ov.carbs_consumed / carbsGoal) * 100)}%`;

  const fatCur = document.getElementById("fat-cur-val");
  if (fatCur) fatCur.textContent = Math.round(ov.fat_consumed);
  const fatGoalEl = document.getElementById("fat-goal-val");
  if (fatGoalEl) fatGoalEl.textContent = `/ ${fatGoal}g`;
  const fatBar = document.getElementById("fat-bar-fill");
  if (fatBar) fatBar.style.width = `${Math.min(100, (ov.fat_consumed / fatGoal) * 100)}%`;

  // Dynamic Profile-Driven Hero Image & Badge
  const heroPlate = document.getElementById("hero-profile-plate-img");
  const heroBadge = document.getElementById("hero-profile-goal-badge");
  const targetGoal = (user.target_goal || "Muscle Gain").toLowerCase();

  if (heroPlate && heroBadge) {
    if (targetGoal.includes("muscle") || targetGoal.includes("protein")) {
      heroPlate.src = "/assets/paneer_tikka.jpg?v=2026";
      heroBadge.innerHTML = `<span class="pulse-sparkle">✦</span> Muscle Target: High Protein (${proGoal}g)`;
    } else if (targetGoal.includes("fat") || targetGoal.includes("lean") || targetGoal.includes("loss")) {
      heroPlate.src = "/assets/dal.jpg?v=2026";
      heroBadge.innerHTML = `<span class="pulse-sparkle">✦</span> Fat Loss Target: Lean & High Fiber (${calGoal} kcal)`;
    } else if (targetGoal.includes("endurance") || targetGoal.includes("energy")) {
      heroPlate.src = "/assets/dosa.jpg?v=2026";
      heroBadge.innerHTML = `<span class="pulse-sparkle">✦</span> Endurance Target: Sustained Carbs (${carbsGoal}g)`;
    } else {
      heroPlate.src = "/assets/roti.jpg?v=2026";
      heroBadge.innerHTML = `<span class="pulse-sparkle">✦</span> Balanced Nutrition Target (${calGoal} kcal)`;
    }
  }

  // Profile-Aware Dynamic Nutrition Suggestions (Protein, Carbs, Fiber)
  const proLeft = Math.max(0, proGoal - ov.protein_consumed);
  const carbsLeft = Math.max(0, carbsGoal - ov.carbs_consumed);

  let personalizedDesc = "";
  let smartChips = [];

  if (proLeft > 20) {
    personalizedDesc = `For your ${user.weight_kg || 68}kg ${user.target_goal || 'Muscle Gain'} plan, you have ${Math.round(proLeft)}g protein remaining today to hit your ${proGoal}g target:`;
    smartChips = ["Paneer Tikka", "Dal Tadka", "Boiled Eggs", "Chicken Curry"];
  } else if (carbsLeft > 40) {
    personalizedDesc = `You have ${Math.round(carbsLeft)}g complex carbohydrates available for sustained energy and recovery:`;
    smartChips = ["Poha", "Roti", "Idli with Sambhar", "Mixed Fruit Bowl"];
  } else {
    personalizedDesc = `Your daily nutrition is well balanced with your ${user.target_goal || 'Muscle Gain'} targets! Here are healthy pairing suggestions:`;
    smartChips = ["Mixed Fruit Bowl", "Mixed Nuts & Dark Chocolate", "Dal Tadka", "Roti"];
  }

  const patternDescEl = document.getElementById("pattern-desc-text");
  if (patternDescEl) patternDescEl.textContent = personalizedDesc;

  const chipsContainer = document.getElementById("pattern-chips-row");
  if (chipsContainer) {
    chipsContainer.innerHTML = smartChips
      .map(item => `<button class="additive-chip" onclick="quickAddChipItem('${item}')">✦ ${item}</button>`)
      .join("");
  }

  // Update Profile & Goal UI
  updateProfileUI(user);
}

function updateProfileUI(user) {
  if (!user) return;

  // Header greeting
  const headerName = document.getElementById("header-user-name");
  if (headerName) headerName.textContent = user.full_name || "John Doe";

  // Gender avatar in Header
  const topAvatar = document.getElementById("header-gender-avatar");
  if (topAvatar) {
    topAvatar.className = `user-gender-avatar ${user.gender ? user.gender.toLowerCase() : 'male'}`;
  }

  // Settings inputs
  const nameInp = document.getElementById("setting-full-name");
  if (nameInp) nameInp.value = user.full_name || "John Doe";
  const emailInp = document.getElementById("setting-email");
  if (emailInp) emailInp.value = user.email || "john.doe@example.com";
  const ageInp = document.getElementById("setting-age");
  if (ageInp) ageInp.value = user.age || 26;
  const weightInp = document.getElementById("setting-weight");
  if (weightInp) weightInp.value = user.weight_kg || 68;
  const heightInp = document.getElementById("setting-height");
  if (heightInp) heightInp.value = user.height_cm || 174;
  const genderInp = document.getElementById("setting-gender");
  if (genderInp) genderInp.value = user.gender || "Male";
  const goalInp = document.getElementById("setting-target-goal");
  if (goalInp) goalInp.value = user.target_goal || "Muscle Gain";

  const settingsAvatar = document.getElementById("settings-gender-avatar");
  if (settingsAvatar) {
    settingsAvatar.className = `user-gender-avatar-large ${user.gender ? user.gender.toLowerCase() : 'male'}`;
  }
}

async function saveSettingsForm() {
  const name = document.getElementById("setting-full-name")?.value || "John Doe";
  const email = document.getElementById("setting-email")?.value || "john.doe@example.com";
  const age = parseInt(document.getElementById("setting-age")?.value) || 26;
  const weight_kg = parseFloat(document.getElementById("setting-weight")?.value) || 68.0;
  const height_cm = parseFloat(document.getElementById("setting-height")?.value) || 174.0;
  const gender = document.getElementById("setting-gender")?.value || "Male";
  const target_goal = document.getElementById("setting-target-goal")?.value || "Muscle Gain";

  try {
    const payload = {
      name,
      email,
      age,
      weight_kg,
      height_cm,
      gender,
      activity_level: "Moderate",
      target_goal,
      is_vegetarian: true,
      is_gluten_free: false
    };

    const res = await fetch(`${API_BASE}/api/profile/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const updatedUser = await res.json();
      showNotification(`Profile updated! New Target: ${updatedUser.daily_calorie_goal} kcal (${updatedUser.daily_protein_goal}g Protein)`);
      updateProfileUI(updatedUser);
      await loadDashboard(currentSelectedDate || "2026-06-24");
    }
  } catch (err) {
    console.error("Failed to save profile:", err);
    showNotification("Failed to save profile settings.");
  }
}

function quickAddChipItem(foodName) {
  openDescribeModal();
  insertSampleDescribe(`Add a serving of ${foodName} to my meal`);
}

function renderDateSelector(dates, activeDate) {
  const container = document.getElementById("date-pills-container");
  if (!container || !dates || dates.length === 0) return;

  // Determine dynamic month title for current date range
  const monthTitleEl = document.getElementById("dashboard-month-title");
  if (monthTitleEl && dates.length > 0) {
    const firstDate = new Date(dates[0].full_date);
    const lastDate = new Date(dates[dates.length - 1].full_date);
    const firstMonth = firstDate.toLocaleDateString("en-US", { month: 'long', year: 'numeric' });
    const lastMonth = lastDate.toLocaleDateString("en-US", { month: 'long', year: 'numeric' });

    if (firstMonth === lastMonth) {
      monthTitleEl.textContent = firstMonth.toUpperCase();
    } else {
      const fMon = firstDate.toLocaleDateString("en-US", { month: 'short' }).toUpperCase();
      const lMon = lastDate.toLocaleDateString("en-US", { month: 'short', year: 'numeric' }).toUpperCase();
      monthTitleEl.textContent = `${fMon} - ${lMon}`;
    }
  }

  container.innerHTML = dates.map(d => `
    <button class="date-pill-btn ${d.full_date === activeDate ? 'active' : ''}" onclick="loadDashboard('${d.full_date}')">
      <span class="pill-day">${d.day}</span>
      <span class="pill-num">${d.date}</span>
    </button>
  `).join("");
}

function renderTodayMeals(meals) {
  const container = document.getElementById("today-meals-container");
  if (!container) return;

  if (!meals || meals.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px 20px; background: var(--bg-card); border-radius: var(--radius-xl); border: 1px dashed var(--border-subtle); color: var(--text-muted);">
        <p style="font-size: 1rem; color: #fff; font-weight: 700;">No meals logged for this date yet</p>
        <p style="font-size: 0.85rem; margin-top: 4px;">Choose an item from the Food Options Catalog below, snap a photo, or describe what you ate.</p>
        <div style="display: flex; gap: 12px; justify-content: center; margin-top: 16px;">
          <button class="btn-snap-white" onclick="openDescribeModal()">✍️ Describe Meal</button>
          <button class="btn-landing-primary" style="padding: 8px 18px; font-size: 0.85rem;" onclick="openSnapModal()">📷 Snap Photo</button>
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = meals.map(meal => `
    <div class="meal-card" onclick="openNutritionReport(${meal.id})">
      <div class="meal-thumb-wrap">
        <img src="${meal.image_url || '/assets/roti.jpg'}" alt="${meal.title}" class="meal-thumb-img" onerror="this.src='/assets/roti.jpg'">
      </div>

      <div class="meal-card-details">
        <div class="meal-card-header">
          <span class="meal-type-badge">${meal.meal_type}</span>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="meal-time-text">${meal.meal_time}</span>
            <button class="btn-delete-meal" title="Remove Meal" onclick="deleteMealItem(${meal.id}, event)">🗑️</button>
          </div>
        </div>

        <h4 class="meal-title-text">${meal.title}</h4>
        <p class="meal-desc-text">${meal.description || meal.items.map(i => `${i.quantity}x ${i.name}`).join(", ")}</p>

        <div class="meal-metrics-row">
          <div class="meal-metric-group">
            <div class="metric-stat">
              <span class="val">${Math.round(meal.total_calories)}</span>
              <span class="lbl">kcal</span>
            </div>
            <div class="metric-stat">
              <span class="val">${meal.total_protein}g</span>
              <span class="lbl">Pro</span>
            </div>
            <div class="metric-stat">
              <span class="val">${meal.total_carbohydrates}g</span>
              <span class="lbl">Carbs</span>
            </div>
          </div>

          <div class="meal-arrow-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}

async function deleteMealItem(mealId, event) {
  if (event) event.stopPropagation();
  try {
    const res = await fetch(`${API_BASE}/api/meals/${mealId}`, { method: "DELETE" });
    if (res.ok) {
      showNotification("Meal removed from diary");
      loadDashboard(currentSelectedDate);
      loadHistory(currentHistoryFilter);
    }
  } catch (err) {
    console.error("Failed to delete meal:", err);
  }
}

// ----------------- 2. FOOD OPTIONS CATALOG & INSPECTION -----------------

async function loadFoodCatalog() {
  try {
    const res = await fetch(`${API_BASE}/api/food-options`);
    if (!res.ok) return;
    allFoodOptions = await res.json();
    renderFoodCatalog(currentCatalogCategory);
  } catch (err) {
    console.error("Failed loading food options catalog:", err);
  }
}

function filterFoodCatalog(category) {
  currentCatalogCategory = category;
  document.querySelectorAll(".cat-pill").forEach(pill => {
    pill.classList.toggle("active", pill.textContent.toLowerCase().includes(category.toLowerCase()) || (category === "All" && pill.textContent === "All"));
  });
  renderFoodCatalog(category);
}

function renderFoodCatalog(category) {
  const container = document.getElementById("food-catalog-container");
  if (!container) return;

  let filtered = allFoodOptions;
  if (category === "Protein") {
    filtered = allFoodOptions.filter(f => (f.protein || f.protein_per_serving || 0) >= 10 || (f.category && f.category.includes("Protein")));
  } else if (category === "Grains") {
    filtered = allFoodOptions.filter(f => (f.category && f.category.includes("Grains")) || (f.carbohydrates || f.carbs_per_serving || 0) >= 25);
  } else if (category === "Healthy Fats") {
    filtered = allFoodOptions.filter(f => (f.category && f.category.includes("Fats")) || (f.fat || f.fat_per_serving || 0) >= 10);
  } else if (category === "Antioxidant") {
    filtered = allFoodOptions.filter(f => (f.category && f.category.includes("Antioxidant")) || (f.vitamin_c || f.vitamin_c_mg || 0) >= 10 || (f.fiber || f.fiber_per_serving || 0) >= 4);
  }

  container.innerHTML = filtered.map(item => {
    const fid = item.id || item.food_id;
    const cal = item.calories ?? item.calories_per_serving ?? 0;
    const pro = item.protein ?? item.protein_per_serving ?? 0;
    const carbs = item.carbohydrates ?? item.carbs_per_serving ?? 0;
    const fat = item.fat ?? item.fat_per_serving ?? 0;
    const fib = item.fiber ?? item.fiber_per_serving ?? 0;

    const rawImg = item.image || '/assets/roti.jpg';
    const imgSrc = rawImg.includes('?') ? rawImg : `${rawImg}?v=2026`;

    return `
    <div class="food-catalog-card" onclick="inspectFood('${fid}')">
      <div class="catalog-card-img-wrap">
        <img src="${imgSrc}" alt="${item.name}" class="catalog-card-img" onerror="this.src='/assets/roti.jpg?v=2026'">
        <div class="catalog-card-cal-tag">${Math.round(cal)} kcal</div>
      </div>
      <div class="catalog-card-content">
        <div class="catalog-card-title" title="${item.name}">${item.name}</div>
        <div class="catalog-card-serving">${item.serving_size}</div>
        <div class="catalog-card-macros">
          <span>⚡ ${pro}g Pro</span>
          <span>🌾 ${carbs}g Carbs</span>
          <span>🌿 ${fib}g Fib</span>
        </div>
        <div class="catalog-card-action">
          <span>Inspect Nutrients</span>
          <span>+ Add →</span>
        </div>
      </div>
    </div>
  `;
  }).join("");
}

function inspectFood(foodId) {
  const food = allFoodOptions.find(f => (f.id || f.food_id) === foodId);
  if (!food) return;

  activeInspectedFood = food;
  inspectorQty = 1.0;
  updateInspectorModal();

  document.getElementById("food-inspector-modal").classList.add("active");
}

function closeFoodInspector() {
  document.getElementById("food-inspector-modal").classList.remove("active");
}

function stepInspectorQty(delta) {
  inspectorQty = Math.max(0.5, Math.min(5.0, inspectorQty + delta));
  updateInspectorModal();
}

function updateInspectorModal() {
  if (!activeInspectedFood) return;
  const food = activeInspectedFood;
  const q = inspectorQty;
  const rawImg = food.image || '/assets/roti.jpg';
  const modalImg = rawImg.includes('?') ? rawImg : `${rawImg}?v=2026`;

  const cal = (food.calories ?? food.calories_per_serving ?? 0) * q;
  const pro = (food.protein ?? food.protein_per_serving ?? 0) * q;
  const carbs = (food.carbohydrates ?? food.carbs_per_serving ?? 0) * q;
  const fat = (food.fat ?? food.fat_per_serving ?? 0) * q;
  const fib = (food.fiber ?? food.fiber_per_serving ?? 0) * q;
  const calc = (food.calcium ?? food.calcium_mg ?? 0) * q;
  const fe = (food.iron ?? food.iron_mg ?? 0) * q;
  const vitc = (food.vitamin_c ?? food.vitamin_c_mg ?? 0) * q;
  const sod = (food.sodium ?? food.sodium_mg ?? 0) * q;

  document.getElementById("inspector-food-name").textContent = food.name;
  document.getElementById("inspector-food-img").src = modalImg;
  document.getElementById("inspector-serving-badge").textContent = `${q.toFixed(1)}x Serving (${food.serving_size})`;
  document.getElementById("inspector-calories").textContent = Math.round(cal);
  document.getElementById("inspector-food-desc").textContent = food.category ? `${food.category} Whole Food` : "Nutrient-dense food item.";

  document.getElementById("inspector-protein").textContent = `${(Math.round(pro * 10) / 10).toFixed(1)}g`;
  document.getElementById("inspector-carbs").textContent = `${(Math.round(carbs * 10) / 10).toFixed(1)}g`;
  document.getElementById("inspector-fat").textContent = `${(Math.round(fat * 10) / 10).toFixed(1)}g`;
  document.getElementById("inspector-fiber").textContent = `${(Math.round(fib * 10) / 10).toFixed(1)}g`;

  document.getElementById("inspector-calcium").textContent = `${Math.round(calc)} mg`;
  document.getElementById("inspector-iron").textContent = `${(Math.round(fe * 10) / 10).toFixed(1)} mg`;
  document.getElementById("inspector-vit-c").textContent = `${Math.round(vitc)} mg`;
  document.getElementById("inspector-sodium").textContent = `${Math.round(sod)} mg`;

  document.getElementById("inspector-qty-val").textContent = `${q.toFixed(1)}x`;
}

async function logInspectedFood() {
  if (!activeInspectedFood) return;
  const food = activeInspectedFood;
  const q = inspectorQty;
  const fid = food.id || food.food_id;

  const mealTypeRadio = document.querySelector('input[name="insp_meal_type"]:checked');
  const mealType = mealTypeRadio ? mealTypeRadio.value : "Lunch";

  const btn = document.getElementById("btn-inspector-log");
  btn.disabled = true;
  btn.innerHTML = `<span>Logging...</span>`;

  try {
    const cal = (food.calories ?? food.calories_per_serving ?? 0) * q;
    const pro = (food.protein ?? food.protein_per_serving ?? 0) * q;
    const carbs = (food.carbohydrates ?? food.carbs_per_serving ?? 0) * q;
    const fat = (food.fat ?? food.fat_per_serving ?? 0) * q;
    const fib = (food.fiber ?? food.fiber_per_serving ?? 0) * q;
    const sug = (food.sugar ?? food.sugar_per_serving ?? 0) * q;
    const sod = (food.sodium ?? food.sodium_mg ?? 0) * q;
    const calc = (food.calcium ?? food.calcium_mg ?? 0) * q;
    const fe = (food.iron ?? food.iron_mg ?? 0) * q;
    const vitc = (food.vitamin_c ?? food.vitamin_c_mg ?? 0) * q;

    const loggedItem = {
      food_id: fid,
      name: food.name,
      quantity: q,
      serving_size: `${q.toFixed(1)}x ${food.serving_size}`,
      calories: Math.round(cal),
      protein: Math.round(pro * 10) / 10,
      carbohydrates: Math.round(carbs * 10) / 10,
      fat: Math.round(fat * 10) / 10,
      fiber: Math.round(fib * 10) / 10,
      sugar: Math.round(sug * 10) / 10,
      sodium: Math.round(sod),
      calcium: Math.round(calc),
      iron: Math.round(fe * 10) / 10,
      vitamin_c: Math.round(vitc),
      image: food.image
    };

    const res = await fetch(`${API_BASE}/api/meals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        meal_type: mealType,
        meal_time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        meal_date: currentSelectedDate,
        title: food.name,
        description: `${q.toFixed(1)}x ${food.serving_size}`,
        image_url: food.image,
        items: [loggedItem]
      })
    });

    if (res.ok) {
      showNotification(`Added ${food.name} to ${mealType}!`);
      closeFoodInspector();
      loadDashboard(currentSelectedDate);
      loadHistory(currentHistoryFilter);
    }
  } catch (err) {
    console.error("Failed to log food:", err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡ Log to Daily Diary</span>`;
  }
}

// ----------------- 3. MEALS & HISTORY LOGIC -----------------

async function loadHistory(filterCategory = "All") {
  currentHistoryFilter = filterCategory;

  document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.classList.toggle("active", tab.getAttribute("data-filter") === filterCategory);
  });

  try {
    const url = filterCategory === "All" ? `${API_BASE}/api/meals` : `${API_BASE}/api/meals?category=${filterCategory}`;
    const res = await fetch(url);
    const meals = await res.json();

    const todayStr = new Date().toISOString().split('T')[0];
    const yDate = new Date();
    yDate.setDate(yDate.getDate() - 1);
    const yesterdayStr = yDate.toISOString().split('T')[0];

    const todayMeals = meals.filter(m => m.meal_date === todayStr || m.meal_date === currentSelectedDate);
    const yesterdayMeals = meals.filter(m => m.meal_date === yesterdayStr && m.meal_date !== currentSelectedDate);
    const earlierMeals = meals.filter(m => m.meal_date !== todayStr && m.meal_date !== yesterdayStr && m.meal_date !== currentSelectedDate);

    const todayGrid = document.getElementById("history-today-grid");
    if (todayGrid) {
      if (todayMeals.length === 0) {
        todayGrid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 36px 20px; background: var(--bg-card); border-radius: var(--radius-xl); border: 1px dashed var(--border-subtle); color: var(--text-muted);">
            <p style="font-size: 1rem; color: #fff; font-weight: 700;">No meals logged for today yet</p>
            <p style="font-size: 0.85rem; margin-top: 4px;">Choose an item from the dashboard catalog, snap a photo, or describe your meal.</p>
            <div style="display: flex; gap: 12px; justify-content: center; margin-top: 16px;">
              <button class="btn-landing-primary" style="padding: 8px 18px; font-size: 0.85rem;" onclick="navigateTo('dashboard')">🍱 Food Options Catalog</button>
              <button class="btn-snap-white" onclick="openDescribeModal()">✍️ Describe Meal</button>
            </div>
          </div>
        `;
      } else {
        todayGrid.innerHTML = todayMeals.map(m => `
          <div class="meal-card" onclick="openNutritionReport(${m.id})">
            <div class="meal-thumb-wrap" style="width: 110px; height: 110px;">
              <img src="${m.image_url || '/assets/roti.jpg'}" alt="${m.title}" class="meal-thumb-img" onerror="this.src='/assets/roti.jpg'">
            </div>
            <div class="meal-card-details">
              <div class="meal-card-header">
                <span class="meal-type-badge">${m.meal_type}</span>
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span class="meal-time-text">${m.meal_time}</span>
                  <button class="btn-delete-meal" title="Remove" onclick="deleteMealItem(${m.id}, event)">🗑️</button>
                </div>
              </div>
              <h4 class="meal-title-text">${m.title}</h4>
              <div class="meal-metrics-row" style="margin-top: 14px;">
                <div class="meal-metric-group">
                  <span class="tag-pill">${Math.round(m.total_calories)} kcal</span>
                  <span class="tag-pill" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa;">${m.total_protein}g Protein</span>
                </div>
                <div class="meal-arrow-btn">→</div>
              </div>
            </div>
          </div>
        `).join("");
      }
    }

    const yesterdayList = document.getElementById("history-yesterday-list");
    if (yesterdayList) {
      if (yesterdayMeals.length === 0) {
        yesterdayList.innerHTML = `
          <div style="text-align: center; padding: 24px; color: var(--text-muted); font-size: 0.88rem; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
            No meals logged for yesterday
          </div>
        `;
      } else {
        yesterdayList.innerHTML = yesterdayMeals.map(m => `
          <div class="history-list-item" onclick="openNutritionReport(${m.id})">
            <div class="list-item-left">
              <img src="${m.image_url || '/assets/roti.jpg'}" alt="${m.title}" class="list-item-thumb" onerror="this.src='/assets/roti.jpg'">
              <div>
                <div class="list-item-title">${m.title}</div>
                <div class="list-item-tags">
                  <span class="tag-pill">${m.meal_type}</span>
                  <span style="font-size: 0.75rem; color: var(--text-muted);">${m.description || ''}</span>
                </div>
              </div>
            </div>
            <div class="list-item-right">
              <span class="item-stat-badge">${Math.round(m.total_calories)} kcal</span>
              <span class="item-stat-badge" style="color: #60a5fa;">${m.total_protein}g Pro</span>
              <span class="item-time-stamp">${m.meal_time}</span>
              <button class="btn-delete-meal" onclick="deleteMealItem(${m.id}, event)">🗑️</button>
            </div>
          </div>
        `).join("");
      }
    }

    const earlierList = document.getElementById("history-earlier-list");
    if (earlierList) {
      if (earlierMeals.length === 0) {
        earlierList.innerHTML = `
          <div style="text-align: center; padding: 24px; color: var(--text-muted); font-size: 0.88rem; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
            No earlier meal history
          </div>
        `;
      } else {
        earlierList.innerHTML = earlierMeals.slice(0, 15).map(m => `
          <div class="history-list-item" onclick="openNutritionReport(${m.id})">
            <div class="list-item-left">
              <img src="${m.image_url || '/assets/roti.jpg'}" alt="${m.title}" class="list-item-thumb" onerror="this.src='/assets/roti.jpg'">
              <div>
                <div class="list-item-title">${m.title}</div>
                <div class="list-item-tags">
                  <span class="tag-pill">${m.meal_type}</span>
                  <span style="font-size: 0.75rem; color: var(--text-muted);">${m.meal_date} · ${m.meal_time}</span>
                </div>
              </div>
            </div>
            <div class="list-item-right">
              <span class="item-stat-badge">${Math.round(m.total_calories)} kcal</span>
              <span class="item-stat-badge" style="color: #60a5fa;">${m.total_protein}g Pro</span>
              <button class="btn-delete-meal" onclick="deleteMealItem(${m.id}, event)">🗑️</button>
            </div>
          </div>
        `).join("");
      }
    }

  } catch (err) {
    console.error("Failed loading meals history:", err);
  }
}

async function deleteMealItem(mealId, event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }
  if (!confirm("Are you sure you want to delete this logged meal?")) return;

  try {
    const res = await fetch(`${API_BASE}/api/meals/${mealId}`, {
      method: "DELETE"
    });
    if (res.ok) {
      showNotification("Meal record deleted!");
      loadDashboard(currentSelectedDate);
      loadHistory(currentHistoryFilter);
      loadInsights();
    }
  } catch (err) {
    console.error("Failed to delete meal:", err);
  }
}

function filterHistory(category) {
  loadHistory(category);
}

// ----------------- 4. INSIGHTS & TRENDS LOGIC -----------------

async function loadInsights() {
  try {
    const res = await fetch(`${API_BASE}/api/trends`);
    const data = await res.json();
    const summary = data.summary;
    const status = data.status;

    document.getElementById("trend-avg-cal").innerHTML = `${summary.avg_daily_calories} <span class="unit">kcal</span>`;
    document.getElementById("trend-avg-pro").innerHTML = `${summary.avg_daily_protein} <span class="unit">g</span>`;
    document.getElementById("trend-avg-fib").innerHTML = `${summary.avg_daily_fiber} <span class="unit">g</span>`;
    document.getElementById("trend-variety-num").innerHTML = `${summary.unique_foods_logged} <span class="unit">foods</span>`;

    document.getElementById("trend-pro-status").textContent = status.protein;
    document.getElementById("trend-fib-status").textContent = status.fiber;
    document.getElementById("trend-variety-status").textContent = status.variety;

    // Dynamically populate Key Micronutrients based on user's logged meals
    const calVal = summary.avg_calcium_mg || 0;
    const ironVal = summary.avg_iron_mg || 0;
    const vitcVal = summary.avg_vitamin_c_mg || 0;

    const elCalVal = document.getElementById("micro-calcium-val");
    const elCalBar = document.getElementById("micro-calcium-bar");
    if (elCalVal) elCalVal.textContent = `${calVal} mg / 1000 mg`;
    if (elCalBar) elCalBar.style.width = `${Math.min(100, Math.round((calVal / 1000) * 100))}%`;

    const elIronVal = document.getElementById("micro-iron-val");
    const elIronBar = document.getElementById("micro-iron-bar");
    if (elIronVal) elIronVal.textContent = `${ironVal} mg / 18 mg`;
    if (elIronBar) elIronBar.style.width = `${Math.min(100, Math.round((ironVal / 18) * 100))}%`;

    const elVitcVal = document.getElementById("micro-vitc-val");
    const elVitcBar = document.getElementById("micro-vitc-bar");
    if (elVitcVal) elVitcVal.textContent = `${vitcVal} mg / 90 mg`;
    if (elVitcBar) elVitcBar.style.width = `${Math.min(100, Math.round((vitcVal / 90) * 100))}%`;

    const chartContainer = document.getElementById("trend-bar-chart");
    if (chartContainer && data.timeline_7d) {
      const maxCal = Math.max(...data.timeline_7d.map(t => t.calories), 2400);
      chartContainer.innerHTML = data.timeline_7d.map(d => {
        const heightPct = Math.round((d.calories / maxCal) * 100);
        return `
          <div class="chart-col">
            <div class="chart-bar-wrap" title="${d.display_date}: ${d.calories} kcal">
              <div class="chart-bar-fill" style="height: ${heightPct}%;"></div>
            </div>
            <span class="chart-col-label">${d.display_date}</span>
          </div>
        `;
      }).join("");
    }

  } catch (err) {
    console.error("Failed loading insights:", err);
  }
}

// ----------------- 5. AI COACH CHAT LOGIC -----------------

async function loadCoachChat() {
  const feed = document.getElementById("coach-chat-feed");
  if (!feed) return;

  try {
    const res = await fetch(`${API_BASE}/api/coach/history`);
    const messages = await res.json();

    if (messages && messages.length > 0) {
      feed.innerHTML = "";
      messages.forEach(msg => {
        const chips = msg.additive_chips_json ? JSON.parse(msg.additive_chips_json) : [];
        appendLocalChatMessage(msg.sender, msg.message, chips);
      });
    } else {
      feed.innerHTML = "";
      appendLocalChatMessage(
        "coach",
        "Hi! I am your NutriSnap AI Nutrition & Culinary Coach. I'm ready to help you optimize your daily nutrition, suggest high-protein additions, or analyze your meals according to your target goals.",
        ["How can I gain weight?", "Suggest High-Protein Meals", "What Should I Eat Next?", "How To Boost Fiber?"]
      );
    }
  } catch (err) {
    console.warn("Using default coach welcome:", err);
  }
}

function handleCoachSubmit(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  sendCoachMessage(event);
  return false;
}

async function sendCoachMessage(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  const input = document.getElementById("coach-user-input");
  const msg = input.value.trim();
  if (!msg) return;

  input.value = "";
  appendLocalChatMessage("user", msg);

  // Show typing loader
  const feed = document.getElementById("coach-chat-feed");
  const loadingBubble = document.createElement("div");
  loadingBubble.className = "chat-bubble-wrap coach";
  loadingBubble.id = "coach-loading-bubble";
  loadingBubble.innerHTML = `
    <div class="bubble-avatar-badge coach">✨</div>
    <div class="bubble-content" style="display: flex; gap: 8px; align-items: center;">
      <span class="pulse-dot"></span> <em>NutriSnap AI is analyzing your diet & goals with Gemini...</em>
    </div>
  `;
  feed.appendChild(loadingBubble);
  feed.scrollTop = feed.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/api/coach`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();

    const loader = document.getElementById("coach-loading-bubble");
    if (loader) loader.remove();

    appendLocalChatMessage("coach", data.response, data.suggested_actions);
  } catch (err) {
    const loader = document.getElementById("coach-loading-bubble");
    if (loader) loader.remove();
    appendLocalChatMessage("coach", "I'm analyzing your daily nutrition and profile targets! Try asking about high-protein additions (Dal Tadka, Paneer, Boiled Eggs) or how to boost fiber.");
  }
}

function appendLocalChatMessage(sender, text, chips = []) {
  const feed = document.getElementById("coach-chat-feed");
  if (!feed) return;

  const cleanText = (text || "").replace(/\*\*/g, "");

  const wrap = document.createElement("div");
  wrap.className = `chat-bubble-wrap ${sender}`;

  const isCoach = sender === "coach";
  const avatarHtml = isCoach
    ? `<div class="bubble-avatar-badge coach">✨</div>`
    : `<div class="bubble-avatar-badge user">👤</div>`;

  wrap.innerHTML = `
    ${avatarHtml}
    <div class="bubble-content">
      <div>${cleanText.replace(/\n/g, '<br>')}</div>
      ${chips && chips.length ? `
        <div class="bubble-chips-row">
          ${chips.map(chip => `<button class="bubble-chip-btn" onclick="askCoachChip('${chip}')">✦ ${chip}</button>`).join("")}
        </div>
      ` : ''}
    </div>
  `;
  feed.appendChild(wrap);
  feed.scrollTop = feed.scrollHeight;
}

function askCoachChip(promptText) {
  document.getElementById("coach-user-input").value = promptText;
  sendCoachMessage();
}

async function clearCoachChat() {
  if (!confirm("Are you sure you want to clear your AI Coach conversation?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/coach/clear`, { method: "POST" });
    if (res.ok) {
      showNotification("AI Coach chat history cleared.");
      const feed = document.getElementById("coach-chat-feed");
      if (feed) {
        feed.innerHTML = "";
        appendLocalChatMessage(
          "coach",
          "Hi! Conversation cleared. I'm ready to help you optimize your daily nutrition, suggest high-protein additions, or analyze your meals according to your target goals.",
          ["Suggest High-Protein Meals", "What Should I Eat Next?", "How To Boost Fiber?", "Post-Workout Recovery"]
        );
      }
    }
  } catch (err) {
    console.error("Failed to clear coach chat:", err);
  }
}

// ----------------- 6. SNAP MEAL & FOOD VISION LOGIC -----------------

function openSnapModal() {
  document.getElementById("snap-modal").classList.add("active");
  document.getElementById("scan-results-box").style.display = "none";
  document.getElementById("btn-run-scan").disabled = false;
  document.getElementById("btn-run-scan").innerHTML = `<span>⚡ Scan with Gemini Vision</span>`;
}

function closeSnapModal() {
  document.getElementById("snap-modal").classList.remove("active");
  document.getElementById("scanning-laser").classList.remove("active");
}

function pickSampleDish(imageName) {
  selectedSampleImage = imageName;
  document.getElementById("viewfinder-image").src = `/assets/${imageName}`;
  document.querySelectorAll(".sample-pill").forEach(pill => {
    pill.classList.toggle("active", pill.getAttribute("onclick").includes(imageName));
  });
  document.getElementById("scan-results-box").style.display = "none";
}

function handleImageFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (e) {
    document.getElementById("viewfinder-image").src = e.target.result;
  };
  reader.readAsDataURL(file);
}

async function triggerFoodScan() {
  const laser = document.getElementById("scanning-laser");
  const scanBtn = document.getElementById("btn-run-scan");
  laser.classList.add("active");
  scanBtn.disabled = true;
  scanBtn.innerHTML = `<span>Scanning photo...</span>`;

  const fileInput = document.getElementById("image-file-input");
  const formData = new FormData();

  if (fileInput.files.length > 0) {
    formData.append("file", fileInput.files[0]);
  } else {
    formData.append("sample_name", selectedSampleImage);
  }
  formData.append("meal_date", currentSelectedDate);

  try {
    const res = await fetch(`${API_BASE}/api/analyze-image`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    laser.classList.remove("active");

    const resBox = document.getElementById("scan-results-box");
    resBox.style.display = "block";
    document.getElementById("scan-detected-title").textContent = data.title;
    document.getElementById("scan-detected-cals").textContent = `${Math.round(data.totals.calories)} kcal`;

    document.getElementById("scan-detected-chips").innerHTML = data.detected_foods.map(f => `
      <span class="detected-food-chip">${f.quantity}x ${f.name}</span>
    `).join("");

    document.getElementById("scan-additive-suggestion").innerHTML = `
      <strong>✦ Additive Suggestion:</strong> ${data.additive_suggestions[0] || 'Great balance!'}
    `;

    scanBtn.innerHTML = `<span>✓ Logged to Dashboard!</span>`;
    showNotification(`Successfully logged: ${data.title}`);

    loadDashboard(currentSelectedDate);
    loadHistory(currentHistoryFilter);
    loadInsights();

    setTimeout(() => {
      closeSnapModal();
    }, 1800);

  } catch (err) {
    laser.classList.remove("active");
    scanBtn.disabled = false;
    scanBtn.innerHTML = `<span>Scan Failed. Retry</span>`;
    console.error("Scan error:", err);
  }
}

// ----------------- 7. DESCRIBE MEAL LOGIC -----------------

function openDescribeModal() {
  document.getElementById("describe-modal").classList.add("active");
  document.getElementById("nlp-result-box").style.display = "none";
  document.getElementById("btn-parse-nlp").disabled = false;
  document.getElementById("btn-parse-nlp").innerHTML = `<span>Analyze & Log Meal</span>`;
}

function closeDescribeModal() {
  document.getElementById("describe-modal").classList.remove("active");
}

function insertSampleDescribe(text) {
  document.getElementById("describe-text-input").value = text;
}

async function triggerNaturalLanguageParse() {
  const text = document.getElementById("describe-text-input").value.trim();
  if (!text) {
    showNotification("Please enter what you ate.");
    return;
  }

  const mealTypeRadio = document.querySelector('input[name="describe_meal_type"]:checked');
  const mealType = mealTypeRadio ? mealTypeRadio.value : "Lunch";

  const parseBtn = document.getElementById("btn-parse-nlp");
  parseBtn.disabled = true;
  parseBtn.innerHTML = `<span>Analyzing with Gemini...</span>`;

  try {
    const res = await fetch(`${API_BASE}/api/analyze-food`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: text,
        meal_type: mealType,
        meal_date: currentSelectedDate
      })
    });
    const data = await res.json();

    const resBox = document.getElementById("nlp-result-box");
    resBox.style.display = "block";
    document.getElementById("nlp-result-title").textContent = `${data.title} (${Math.round(data.totals.calories)} kcal)`;

    document.getElementById("nlp-items-list").innerHTML = data.matched_items.map(item => `
      <div class="nlp-item-row">
        <span>${item.serving_size}</span>
        <strong>${item.calories} kcal | ${item.protein}g Pro</strong>
      </div>
    `).join("");

    document.getElementById("nlp-additive-notice").innerHTML = `
      <strong>✦ Additive Recommendation:</strong> ${data.additive_suggestions[0]}
    `;

    parseBtn.innerHTML = `<span>✓ Meal Saved!</span>`;
    showNotification(`Logged ${data.title} to your day!`);
    loadDashboard(currentSelectedDate);
    loadHistory(currentHistoryFilter);
    loadInsights();

    setTimeout(() => {
      closeDescribeModal();
      document.getElementById("describe-text-input").value = "";
    }, 1600);

  } catch (err) {
    parseBtn.disabled = false;
    parseBtn.innerHTML = `<span>Failed. Try Again</span>`;
    console.error("NLP error:", err);
  }
}

// ----------------- 8. NUTRITION REPORT LOGIC -----------------

async function openNutritionReport(mealId) {
  try {
    const res = await fetch(`${API_BASE}/api/nutrition/${mealId}`);
    const meal = await res.json();
    activeReportMeal = meal;

    document.getElementById("report-meal-title").textContent = meal.title;
    document.getElementById("report-meal-time").textContent = `${meal.meal_type} · ${meal.meal_date} · ${meal.meal_time}`;

    const content = document.getElementById("report-modal-content");
    content.innerHTML = `
      <div style="display: flex; gap: 20px; align-items: center; background: var(--bg-card-secondary); padding: 18px; border-radius: var(--radius-lg);">
        <img src="${meal.image_url || '/assets/roti.jpg'}" style="width: 100px; height: 100px; border-radius: var(--radius-md); object-fit: cover;">
        <div>
          <div style="font-size: 1.5rem; font-weight: 800; color: #fff;">${Math.round(meal.total_calories)} <span style="font-size: 0.9rem; color: var(--coral-light);">kcal</span></div>
          <p style="font-size: 0.85rem; color: var(--text-body); margin-top: 4px;">${meal.description || 'Logged dish'}</p>
        </div>
      </div>

      <div>
        <h4 style="font-size: 0.95rem; font-weight: 800; margin-bottom: 12px; color: #fff;">Macronutrient Breakdown</h4>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
          <div class="macro-pill"><span class="macro-name">Protein</span><strong class="macro-cur">${meal.total_protein}g</strong></div>
          <div class="macro-pill"><span class="macro-name">Carbs</span><strong class="macro-cur">${meal.total_carbohydrates}g</strong></div>
          <div class="macro-pill"><span class="macro-name">Fat</span><strong class="macro-cur">${meal.total_fat}g</strong></div>
          <div class="macro-pill"><span class="macro-name">Fiber</span><strong class="macro-cur" style="color: #10b981;">${meal.total_fiber}g</strong></div>
        </div>
      </div>

      <div>
        <h4 style="font-size: 0.95rem; font-weight: 800; margin-bottom: 12px; color: #fff;">Micronutrients & Electrolytes</h4>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 0.85rem;">
          <div class="macro-pill"><span class="macro-name">Sodium</span><strong>${meal.total_sodium} mg</strong></div>
          <div class="macro-pill"><span class="macro-name">Calcium</span><strong>${meal.total_calcium} mg</strong></div>
          <div class="macro-pill"><span class="macro-name">Iron</span><strong>${meal.total_iron} mg</strong></div>
          <div class="macro-pill"><span class="macro-name">Vit C</span><strong>${meal.total_vitamin_c} mg</strong></div>
        </div>
      </div>

      <div>
        <h4 style="font-size: 0.95rem; font-weight: 800; margin-bottom: 8px; color: #fff;">Identified Food Components</h4>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${meal.items.map(item => `
            <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm); font-size: 0.85rem;">
              <span><strong>${item.name}</strong> (${item.serving_size})</span>
              <span>${item.calories} kcal | ${item.protein}g Pro</span>
            </div>
          `).join("")}
        </div>
      </div>
    `;

    document.getElementById("report-modal").classList.add("active");
  } catch (err) {
    console.error("Failed opening report:", err);
  }
}

function closeReportModal() {
  document.getElementById("report-modal").classList.remove("active");
}

function openCoachWithContext() {
  closeReportModal();
  navigateTo('coach');
  if (activeReportMeal) {
    const question = `Can you suggest an additive food to pair with my ${activeReportMeal.title} to improve its fiber and micronutrient density?`;
    setTimeout(() => {
      askCoachChip(question);
    }, 400);
  }
}

// ----------------- 9. SETTINGS & PROFILE LOGIC -----------------

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    const settings = await res.json();

    if (document.getElementById("setting-full-name")) {
      document.getElementById("setting-full-name").value = settings.full_name || "John Doe";
      document.getElementById("setting-email").value = settings.email || "john.doe@example.com";
      if (document.getElementById("setting-age")) document.getElementById("setting-age").value = settings.age || 26;
      if (document.getElementById("setting-weight")) document.getElementById("setting-weight").value = settings.weight_kg || 68.0;
      if (document.getElementById("setting-height")) document.getElementById("setting-height").value = settings.height_cm || 174.0;
      if (document.getElementById("setting-gender")) document.getElementById("setting-gender").value = settings.gender || "Male";
      if (document.getElementById("setting-target-goal")) document.getElementById("setting-target-goal").value = settings.target_goal || "Muscle Gain";
      document.getElementById("setting-is-veg").checked = settings.is_vegetarian;
      document.getElementById("setting-is-gf").checked = settings.is_gluten_free;
      document.getElementById("setting-macro-goal").value = settings.macro_focus_goal || "Balanced Macros (30/40/30)";
    }

    const toneRadio = document.querySelector(`input[name="coach_tone"][value="${settings.coach_tone}"]`);
    if (toneRadio) toneRadio.checked = true;

    const badge = document.getElementById("coach-active-tone-badge");
    if (badge) badge.textContent = settings.coach_tone;

    updateGenderAvatar(settings.gender || "Male");

  } catch (err) {
    console.error("Failed loading settings:", err);
  }
}

async function saveSettingsForm() {
  const full_name = document.getElementById("setting-full-name").value.trim() || "John Doe";
  const email = document.getElementById("setting-email").value.trim() || "john.doe@example.com";
  const age = parseInt(document.getElementById("setting-age")?.value) || 26;
  const weight_kg = parseFloat(document.getElementById("setting-weight")?.value) || 68.0;
  const height_cm = parseFloat(document.getElementById("setting-height")?.value) || 174.0;
  const gender = document.getElementById("setting-gender")?.value || "Male";
  const target_goal = document.getElementById("setting-target-goal")?.value || "Muscle Gain";

  const is_vegetarian = document.getElementById("setting-is-veg").checked;
  const is_gluten_free = document.getElementById("setting-is-gf").checked;
  const macro_focus_goal = document.getElementById("setting-macro-goal").value;
  const coachToneRadio = document.querySelector('input[name="coach_tone"]:checked');
  const coach_tone = coachToneRadio ? coachToneRadio.value : "Scientific & Precise";

  try {
    const res = await fetch(`${API_BASE}/api/profile/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: full_name,
        email: email,
        age: age,
        weight_kg: weight_kg,
        height_cm: height_cm,
        gender: gender,
        target_goal: target_goal,
        activity_level: "Moderate",
        is_vegetarian: is_vegetarian,
        is_gluten_free: is_gluten_free
      })
    });
    const updated = await res.json();
    showNotification(`Settings saved! Goals updated for ${target_goal} (${updated.daily_protein_goal}g Protein).`);

    updateProfileUI(updated);
    updateGenderAvatar(gender);
    loadDashboard(currentSelectedDate);

  } catch (err) {
    console.error("Failed saving settings:", err);
  }
}

function updateGenderAvatar(gender = "Male") {
  const g = (gender || "Male").toLowerCase();
  let colorClass = "male";
  if (g.includes("fem") || g.includes("girl") || g.includes("woman")) {
    colorClass = "female";
  } else if (g.includes("other") || g.includes("non") || g.includes("grey")) {
    colorClass = "grey";
  }

  const headerAvatar = document.getElementById("header-gender-avatar");
  if (headerAvatar) {
    headerAvatar.className = `user-gender-avatar ${colorClass}`;
  }

  const settingsAvatar = document.getElementById("settings-gender-avatar");
  if (settingsAvatar) {
    settingsAvatar.className = `user-gender-avatar-large ${colorClass}`;
  }
}

async function clearHistoryData() {
  if (!confirm("Are you sure you want to clear your food scan history?")) return;
  try {
    await fetch(`${API_BASE}/api/clear-history`, { method: "POST" });
    showNotification("History cleared.");
    loadDashboard(currentSelectedDate);
    loadHistory("All");
  } catch (err) {
    console.error("Clear error:", err);
  }
}

function exportDataJson() {
  window.open(`${API_BASE}/api/export`, "_blank");
}

// ----------------- 10. ROTATING 3D DECK (PRECISION INTELLIGENCE) -----------------

let deckCurrentIndex = 0;
const deckCards = [
  { id: 0, title: "Multimodal Scanner", subtitle: "Instant macro detection from photo", icon: "📷", tag: "AI Vision" },
  { id: 1, title: "Additive Guidance", subtitle: "Stack fiber and micros without restriction", icon: "🌿", tag: "Additive AI" },
  { id: 2, title: "Passive Trends", subtitle: "Longitudinal habits & bioavailability", icon: "📈", tag: "Intelligence" }
];

function initRotatingDeck() {
  const cards = document.querySelectorAll(".deck-card");
  if (!cards.length) return;
  rotateDeckTo(0);
}

function rotateDeckTo(index) {
  deckCurrentIndex = (index + deckCards.length) % deckCards.length;
  const cards = document.querySelectorAll(".deck-card");
  const dots = document.querySelectorAll(".deck-dot");

  cards.forEach(card => {
    const cardIdx = parseInt(card.getAttribute("data-card-index") || "0");
    const diff = (cardIdx - deckCurrentIndex + deckCards.length) % deckCards.length;

    card.classList.remove("pos-active", "pos-next", "pos-back");
    if (diff === 0) {
      card.classList.add("pos-active");
    } else if (diff === 1) {
      card.classList.add("pos-next");
    } else {
      card.classList.add("pos-back");
    }
  });

  dots.forEach((dot, idx) => {
    dot.classList.toggle("active", idx === deckCurrentIndex);
  });
}

function nextDeckCard() {
  rotateDeckTo(deckCurrentIndex + 1);
}

function prevDeckCard() {
  rotateDeckTo(deckCurrentIndex - 1);
}

function showNotification(msg) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<span>✦</span><span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("show");
  }, 50);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

// ----------------- 12. USER PROFILE & NUTRITION GOALS LOGIC -----------------

let currentUserProfile = null;

function openProfileModal() {
  document.getElementById("profile-calculator-modal").classList.add("active");
  triggerLivePlanCalc();
}

function closeProfileModal() {
  document.getElementById("profile-calculator-modal").classList.remove("active");
}

function triggerLivePlanCalc() {
  const age = parseInt(document.getElementById("prof-age").value) || 26;
  const weight = parseFloat(document.getElementById("prof-weight").value) || 68.0;
  const height = parseFloat(document.getElementById("prof-height").value) || 174.0;
  const gender = document.getElementById("prof-gender").value || "Male";
  const goal = document.getElementById("prof-goal").value || "Muscle Gain";
  const activity = document.getElementById("prof-activity").value || "Moderate";

  // 1. BMR (Mifflin-St Jeor)
  const isMale = gender.toLowerCase().startsWith("m");
  const genderOffset = isMale ? 5 : -161;
  const bmr = (10 * weight) + (6.25 * height) - (5 * age) + genderOffset;

  // 2. TDEE Multiplier
  let actFactor = 1.55;
  if (activity.includes("Sedentary")) actFactor = 1.2;
  else if (activity.includes("High")) actFactor = 1.725;

  const tdee = Math.round(bmr * actFactor);

  // 3. Goal Calorie & Protein Adjustments
  let targetCal = tdee;
  let proPerKg = 1.8;
  let rationale = "";

  if (goal.includes("Muscle")) {
    targetCal = tdee + 350;
    proPerKg = 2.0;
    rationale = `Caloric surplus (+350 kcal) and high protein (${proPerKg}g/kg) to maximize muscle protein synthesis and lean tissue accretion.`;
  } else if (goal.includes("Fat") || goal.includes("Lean")) {
    targetCal = Math.max(1400, tdee - 450);
    proPerKg = 1.8;
    rationale = `Moderate caloric deficit (-450 kcal) paired with elevated protein (${proPerKg}g/kg) to preserve lean muscle while accelerating fat loss.`;
  } else if (goal.includes("Endurance")) {
    targetCal = tdee + 150;
    proPerKg = 1.6;
    rationale = `Energy-matched nutrition with sustained carbohydrate availability and ${proPerKg}g/kg protein for glycogen recovery.`;
  } else {
    targetCal = tdee;
    proPerKg = 1.4;
    rationale = `Balanced isocaloric energy maintenance with ${proPerKg}g/kg protein for metabolic health and steady daily energy.`;
  }

  const targetPro = Math.round(weight * proPerKg);
  const targetFat = Math.round((targetCal * 0.25) / 9);
  const targetFiber = Math.round((targetCal / 1000) * 14);
  const targetCarbs = Math.round(Math.max(50, (targetCal - (targetPro * 4) - (targetFat * 9)) / 4));

  // Update Live Preview UI
  document.getElementById("plan-bmr-tdee").textContent = `BMR: ${Math.round(bmr)} kcal · TDEE: ${tdee} kcal`;
  document.getElementById("plan-cal-val").innerHTML = `${targetCal} <span class="p-unit">kcal</span>`;
  document.getElementById("plan-pro-val").innerHTML = `${targetPro}g <span class="p-sub">(${proPerKg}g/kg)</span>`;
  document.getElementById("plan-carbs-val").textContent = `${targetCarbs}g`;
  document.getElementById("plan-fat-val").textContent = `${targetFat}g`;
  document.getElementById("plan-fiber-val").textContent = `${targetFiber}g`;
  document.getElementById("plan-rationale-text").textContent = rationale;
}

async function saveUserProfile() {
  const name = document.getElementById("prof-name").value.trim();
  const email = document.getElementById("prof-email").value.trim();
  const age = parseInt(document.getElementById("prof-age").value) || 26;
  const weight_kg = parseFloat(document.getElementById("prof-weight").value) || 68.0;
  const height_cm = parseFloat(document.getElementById("prof-height").value) || 174.0;
  const gender = document.getElementById("prof-gender").value;
  const target_goal = document.getElementById("prof-goal").value;
  const activity_level = document.getElementById("prof-activity").value;

  const btn = document.getElementById("btn-save-profile");
  btn.disabled = true;
  btn.innerHTML = `<span>Saving Profile...</span>`;

  try {
    const res = await fetch(`${API_BASE}/api/profile/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email,
        age,
        weight_kg,
        height_cm,
        gender,
        target_goal,
        activity_level
      })
    });

    if (res.ok) {
      const updatedUser = await res.json();
      currentUserProfile = updatedUser;
      showNotification(`Profile updated! New Daily Goal: ${updatedUser.daily_calorie_goal} kcal (${updatedUser.daily_protein_goal}g Protein)`);
      closeProfileModal();
      updateProfileUI(updatedUser);
      loadDashboard(currentSelectedDate);
    }
  } catch (err) {
    console.error("Failed to save profile:", err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡ Save Profile & Apply Daily Goals</span>`;
  }
}

function updateProfileUI(user) {
  if (!user) return;
  const headerGreeting = document.getElementById("header-greeting");
  if (headerGreeting && user.full_name) headerGreeting.textContent = `Good evening, ${user.full_name.split(" ")[0]}`;

  const headerTargetTag = document.getElementById("header-user-target-tag");
  if (headerTargetTag) headerTargetTag.textContent = `${user.target_goal || 'Muscle Gain'} · ${user.daily_protein_goal}g Pro`;

  const bannerGoalTitle = document.getElementById("banner-goal-title");
  if (bannerGoalTitle) bannerGoalTitle.textContent = `Target Goal: ${user.target_goal || 'Muscle Gain'}`;

  const bannerGoalSub = document.getElementById("banner-goal-subtitle");
  if (bannerGoalSub) bannerGoalSub.textContent = `Customized for ${user.weight_kg || 68} kg · ${user.daily_calorie_goal} kcal/day · ${user.daily_protein_goal}g Protein`;

  // Sync gender avatar color
  updateGenderAvatar(user.gender || "Male");

  // Sync Form inputs if not currently focused
  if (document.activeElement?.id !== "prof-name" && document.getElementById("prof-name") && user.full_name) {
    document.getElementById("prof-name").value = user.full_name;
    document.getElementById("prof-email").value = user.email || "";
    if (user.age) document.getElementById("prof-age").value = user.age;
    if (user.weight_kg) document.getElementById("prof-weight").value = user.weight_kg;
    if (user.height_cm) document.getElementById("prof-height").value = user.height_cm;
    if (user.gender) document.getElementById("prof-gender").value = user.gender;
    if (user.target_goal) document.getElementById("prof-goal").value = user.target_goal;
    if (user.activity_level) document.getElementById("prof-activity").value = user.activity_level;
  }
}

// ----------------- 3D ROTATING DECK CAROUSEL LOGIC -----------------
let currentDeckIndex = 0;
let deckAutoRotateTimer = null;
const DECK_AUTO_ROTATE_INTERVAL = 3000; // Auto-rotates smoothly every 3 seconds

function initRotatingDeck() {
  const container = document.getElementById("intelligence-deck");
  if (!container) return;

  // Set initial 3D positions
  rotateDeckTo(0);

  // Start smooth auto-rotation
  startDeckAutoRotation();

  // Pause when hovered, resume on mouse leave
  container.addEventListener("mouseenter", stopDeckAutoRotation);
  container.addEventListener("mouseleave", startDeckAutoRotation);
}

function startDeckAutoRotation() {
  stopDeckAutoRotation();
  deckAutoRotateTimer = setInterval(() => {
    nextDeckCard();
  }, DECK_AUTO_ROTATE_INTERVAL);
}

function stopDeckAutoRotation() {
  if (deckAutoRotateTimer) {
    clearInterval(deckAutoRotateTimer);
    deckAutoRotateTimer = null;
  }
}

function rotateDeckTo(targetIndex) {
  const cards = document.querySelectorAll(".deck-card");
  const dots = document.querySelectorAll(".deck-dot");
  if (!cards.length) return;

  const total = cards.length;
  currentDeckIndex = (targetIndex + total) % total;

  cards.forEach((card, idx) => {
    card.classList.remove("active", "next", "prev");
    if (idx === currentDeckIndex) {
      card.classList.add("active");
    } else if (idx === (currentDeckIndex + 1) % total) {
      card.classList.add("next");
    } else {
      card.classList.add("prev");
    }
  });

  dots.forEach((dot, idx) => {
    dot.classList.toggle("active", idx === currentDeckIndex);
  });
}

function nextDeckCard() {
  rotateDeckTo(currentDeckIndex + 1);
}

function prevDeckCard() {
  rotateDeckTo(currentDeckIndex - 1);
}

function scrollToLandingSection(sectionId) {
  const el = document.getElementById(sectionId);
  if (!el) return;

  const navOffset = 80;
  const elementPosition = el.getBoundingClientRect().top;
  const currentScroll = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  const targetTop = elementPosition + currentScroll - navOffset;

  // 1. Smooth scroll window & documentElement
  window.scrollTo({
    top: targetTop,
    behavior: 'smooth'
  });

  // 2. Smooth scroll main-content wrapper if it's the scroll container
  const mainContent = document.querySelector('.main-content');
  if (mainContent) {
    mainContent.scrollTo({
      top: el.offsetTop - navOffset,
      behavior: 'smooth'
    });
  }

  // 3. Standard smooth scrollIntoView
  try {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (e) {}
}

