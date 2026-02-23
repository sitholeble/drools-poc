"""
Integer Linear Programming (ILP) for Recommendation System
============================================================

Features:
- Personalization: user-specific preference scores per class
- Diversity: bonus for selecting classes from different categories
- Top-2 plans: best and second-best recommendation sets

Install: pip install pulp
"""

from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus

# ============================================
# PROBLEM DATA
# ============================================

# Available gym classes: price, duration, time_slot, category, default preference_score
CLASSES = {
    "Yoga":     {"price": 15, "duration": 60, "time_slot": "morning",   "category": "mind_body", "preference_score": 8},
    "HIIT":     {"price": 20, "duration": 45, "time_slot": "morning",   "category": "cardio",    "preference_score": 9},
    "Pilates":  {"price": 18, "duration": 60, "time_slot": "afternoon", "category": "mind_body", "preference_score": 7},
    "Spinning": {"price": 22, "duration": 45, "time_slot": "afternoon", "category": "cardio",    "preference_score": 6},
    "Boxing":   {"price": 25, "duration": 60, "time_slot": "evening",   "category": "strength",  "preference_score": 10},
    "Zumba":    {"price": 12, "duration": 45, "time_slot": "evening",   "category": "cardio",    "preference_score": 5},
}

# Default member constraints
MAX_BUDGET = 50
MAX_CLASSES = 3
MAX_DURATION = 150
TIME_SLOTS = ["morning", "afternoon", "evening"]

# Personalization: override scores per user (None = use default from CLASSES)
# Example: this user loves cardio and doesn't care for mind_body
USER_PREFERENCES = {
    "Yoga":     5,
    "HIIT":    10,
    "Pilates":  4,
    "Spinning": 8,
    "Boxing":   7,
    "Zumba":    9,
}
# Set to None to use default CLASSES[c]["preference_score"] for all
# USER_PREFERENCES = None

# Diversity: bonus added to objective for each distinct category in the selection
DIVERSITY_BONUS = 2.0


def get_score(class_name, user_preferences):
    """Preference score for a class: user override or default."""
    if user_preferences and class_name in user_preferences:
        return user_preferences[class_name]
    return CLASSES[class_name]["preference_score"]


def get_categories(classes):
    """Unique categories in class catalog."""
    return list({classes[c]["category"] for c in classes})


def build_problem(classes, user_preferences, max_budget, max_classes, max_duration, diversity_bonus, exclude_set=None):
    """
    Build ILP: maximize (satisfaction + diversity), subject to budget, count, duration, one per slot.
    If exclude_set is given, add constraint so we cannot select exactly that set (for 2nd plan).
    Returns (problem, x, y_cat).
    """
    problem = LpProblem("Gym_Recommendation", LpMaximize)
    x = {c: LpVariable(f"x_{c}", cat="Binary") for c in classes}
    categories = get_categories(classes)
    # y[cat] = 1 if at least one class in category cat is selected
    y = {cat: LpVariable(f"y_{cat}", cat="Binary") for cat in categories}

    # Objective: satisfaction + diversity
    satisfaction = lpSum(get_score(c, user_preferences) * x[c] for c in classes)
    diversity = lpSum(diversity_bonus * y[cat] for cat in categories)
    problem += satisfaction + diversity, "Objective"

    # Constraints
    problem += lpSum(classes[c]["price"] * x[c] for c in classes) <= max_budget, "Budget"
    problem += lpSum(x[c] for c in classes) <= max_classes, "Max_Classes"
    problem += lpSum(classes[c]["duration"] * x[c] for c in classes) <= max_duration, "Max_Duration"

    for slot in TIME_SLOTS:
        in_slot = [c for c in classes if classes[c]["time_slot"] == slot]
        problem += lpSum(x[c] for c in in_slot) <= 1, f"Slot_{slot}"

    # Link y_cat to x: y_cat >= 0 and if any x[c]=1 in cat then y_cat can be 1
    for cat in categories:
        in_cat = [c for c in classes if classes[c]["category"] == cat]
        problem += lpSum(x[c] for c in in_cat) >= y[cat], f"Cat_has_class_{cat}"
        problem += lpSum(x[c] for c in in_cat) <= len(in_cat) * y[cat], f"Cat_upper_{cat}"

    # Exclude previous solution (for top-2)
    if exclude_set:
        # Cannot select exactly this set: sum of (1-x[c]) for c in set + sum of x[c] for c not in set >= 1
        problem += lpSum(1 - x[c] for c in exclude_set) + lpSum(x[c] for c in classes if c not in exclude_set) >= 1, "Exclude_prev"

    return problem, x, y


def get_solution(classes, x, user_preferences=None):
    """Return (recommended_list, total_price, total_duration, total_score, categories_used)."""
    recommended = [c for c in classes if x[c].value() == 1]
    total_price = sum(classes[c]["price"] for c in recommended)
    total_duration = sum(classes[c]["duration"] for c in recommended)
    total_score = sum(get_score(c, user_preferences) for c in recommended)
    categories_used = list({classes[c]["category"] for c in recommended})
    return recommended, total_price, total_duration, total_score, categories_used


def print_plan(plan_label, recommended, total_price, total_duration, total_score, categories_used, user_preferences=None):
    """Print one plan summary."""
    print(f"\n--- {plan_label} ---")
    if not recommended:
        print("  (No feasible plan)")
        return
    for c in recommended:
        info = CLASSES[c]
        sc = get_score(c, user_preferences)
        print(f"  - {c}: {info['time_slot']}, {info['duration']}min, ${info['price']}, score={sc}, category={info['category']}")
    print(f"  Total: ${total_price}, {total_duration} min, satisfaction={total_score}, categories={categories_used}")


def run_recommendation():
    """Build model, solve for plan 1, then plan 2 (excluding plan 1), and print both."""
    classes = CLASSES
    user_preferences = USER_PREFERENCES  # or None for defaults

    print("=" * 60)
    print("ILP RECOMMENDATION - Personalization + Diversity + Top-2 Plans")
    print("=" * 60)
    print(f"\nBudget: ${MAX_BUDGET}  Max classes: {MAX_CLASSES}  Max duration: {MAX_DURATION} min")
    print(f"Diversity bonus per category: {DIVERSITY_BONUS}")
    print("User preferences: " + ("custom" if user_preferences else "default"))

    # Plan 1
    problem1, x1, y1 = build_problem(
        classes, user_preferences, MAX_BUDGET, MAX_CLASSES, MAX_DURATION, DIVERSITY_BONUS, exclude_set=None
    )
    problem1.solve()

    if problem1.status != 1:
        print("\nNo feasible solution found.")
        return

    rec1, price1, dur1, score1, cat1 = get_solution(classes, x1, user_preferences)
    obj1 = problem1.objective.value()
    print_plan("PLAN 1 (Best)", rec1, price1, dur1, score1, cat1, user_preferences)
    print(f"  Objective (satisfaction + diversity): {obj1}")

    # Plan 2: exclude plan 1
    problem2, x2, y2 = build_problem(
        classes, user_preferences, MAX_BUDGET, MAX_CLASSES, MAX_DURATION, DIVERSITY_BONUS, exclude_set=set(rec1)
    )
    problem2.solve()

    if problem2.status == 1:
        rec2, price2, dur2, score2, cat2 = get_solution(classes, x2, user_preferences)
        obj2 = problem2.objective.value()
        print_plan("PLAN 2 (Second best)", rec2, price2, dur2, score2, cat2, user_preferences)
        print(f"  Objective (satisfaction + diversity): {obj2}")
    else:
        print("\n--- PLAN 2 (Second best) ---")
        print("  No other feasible plan (only one feasible combination).")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_recommendation()
