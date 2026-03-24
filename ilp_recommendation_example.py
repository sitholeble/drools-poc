"""
Integer Linear Programming (ILP) for Recommendation System
============================================================

Features:
- Personalization: user-specific preference scores per class
- Diversity: bonus for selecting classes from different categories
- Top-2 plans: best and second-best recommendation sets

Install: pip install pulp
"""

import argparse
import json
import time

from pulp import LpMaximize, LpProblem, LpVariable, PULP_CBC_CMD, lpSum, LpStatus

# Quiet CBC so stdout stays clean for `--output-json` and piping.
_CBC = PULP_CBC_CMD(msg=False)

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

# ============================================
# PERSONALIZATION: User-specific preference scores
# ============================================
# Each user has a dict of class_name -> score (1-10). Missing classes use CLASSES default.
# Recommendations maximize that user's total satisfaction.

USER_PROFILES = {
    "default": None,  # Use CLASSES[c]["preference_score"] for everyone
    "cardio_lover": {
        "Yoga":     3, "HIIT":    10, "Pilates":  2, "Spinning": 9, "Boxing":  6, "Zumba":   9,
    },
    "budget_focused": {
        "Yoga":     7, "HIIT":    4, "Pilates":  8, "Spinning": 3, "Boxing":  2, "Zumba":  10,  # Prefers cheaper (Yoga, Zumba)
    },
    "mind_body_fan": {
        "Yoga":    10, "HIIT":    2, "Pilates": 10, "Spinning": 1, "Boxing":  1, "Zumba":   4,
    },
    "mixed": {
        "Yoga":     5, "HIIT":   10, "Pilates":  4, "Spinning": 8, "Boxing":  7, "Zumba":   9,
    },
}

# Which profile to use when running this script (or pass to recommend_for_user)
ACTIVE_USER = "mixed"

# ============================================
# DIVERSITY: Category bonus in the objective
# ============================================
# Each class has a category (e.g. cardio, mind_body, strength). We add a bonus to the
# objective for each distinct category represented in the selected plan, so the solver
# prefers plans that span more categories (variety) when satisfaction is similar.
# Set DIVERSITY_BONUS = 0 to turn off diversity (only maximize satisfaction).

CATEGORIES = ["cardio", "mind_body", "strength"]  # Must match CLASSES[c]["category"]
DIVERSITY_BONUS = 2.0   # Added to objective per category in the plan (e.g. 2 categories -> +4)

# ============================================
# TOP-2 PLANS: Best and second-best alternatives
# ============================================
# We solve the ILP twice:
#   1. First solve: get the best plan (maximize objective, no exclusion).
#   2. Second solve: add a "not this set" constraint so the chosen set cannot be exactly
#      the first plan, then solve again to get the best alternative (second-best plan).
# The exclusion constraint: sum(1 - x[c] for c in plan1) + sum(x[c] for c not in plan1) >= 1
#   forces at least one difference (either drop a class from plan1 or add a class not in plan1).
# So the second solution is a different set of classes with the next-best objective value.
TOP2_ENABLED = True   # Set False to only compute plan 1


def get_preferences_for_user(user_id_or_preferences):
    """
    Resolve user preferences for personalization.
    - str (e.g. 'cardio_lover'): look up in USER_PROFILES; 'default' or missing -> None.
    - dict: use as class_name -> score override.
    - None: use default scores from CLASSES.
    """
    if user_id_or_preferences is None:
        return None
    if isinstance(user_id_or_preferences, dict):
        return user_id_or_preferences
    return USER_PROFILES.get(user_id_or_preferences, USER_PROFILES["default"])


def get_score(class_name, user_preferences):
    """Preference score for a class: user override or default from CLASSES."""
    if user_preferences and class_name in user_preferences:
        return user_preferences[class_name]
    return CLASSES[class_name]["preference_score"]


def get_categories(classes):
    """Unique categories in class catalog."""
    return list({classes[c]["category"] for c in classes})


def get_classes_by_category(classes):
    """Return dict category -> list of class names (for diversity: which classes count toward each category)."""
    by_cat = {}
    for c in classes:
        cat = classes[c]["category"]
        by_cat.setdefault(cat, []).append(c)
    return by_cat


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

    # Exclude previous solution (for top-2 plans)
    if exclude_set:
        # "Not this set": at least one difference from exclude_set.
        # Sum(1-x[c] for c in set) + Sum(x[c] for c not in set) >= 1
        # so we either drop something in the set or pick something outside it.
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
    if categories_used and DIVERSITY_BONUS:
        print(f"  Diversity: {len(categories_used)} categories -> bonus +{len(categories_used) * DIVERSITY_BONUS}")


def get_top2_plans(
    classes,
    user_preferences,
    max_budget,
    max_classes,
    max_duration,
    diversity_bonus,
    top2_enabled=TOP2_ENABLED,
):
    """
    Top-2 plans: solve ILP twice to get best and second-best recommendation sets.

    Step 1: Solve with exclude_set=None -> best plan.
    Step 2: Solve with exclude_set=set(plan1_classes) -> best plan that is not plan1 (second-best).

    Returns:
        (rec1, price1, dur1, score1, obj1, rec2, price2, dur2, score2, obj2)
        where rec2/price2/... can be None if no second feasible plan.
    """
    problem1, x1, _ = build_problem(
        classes, user_preferences, max_budget, max_classes, max_duration, diversity_bonus, exclude_set=None
    )
    problem1.solve(_CBC)
    if problem1.status != 1:
        return None, None, None, None, None, None, None, None, None, None

    rec1, price1, dur1, score1, cat1 = get_solution(classes, x1, user_preferences)
    obj1 = problem1.objective.value()

    if not top2_enabled:
        return rec1, price1, dur1, score1, obj1, None, None, None, None, None

    problem2, x2, _ = build_problem(
        classes, user_preferences, max_budget, max_classes, max_duration, diversity_bonus, exclude_set=set(rec1)
    )
    problem2.solve(_CBC)
    if problem2.status != 1:
        return rec1, price1, dur1, score1, obj1, None, None, None, None, None

    rec2, price2, dur2, score2, cat2 = get_solution(classes, x2, user_preferences)
    obj2 = problem2.objective.value()
    return rec1, price1, dur1, score1, obj1, rec2, price2, dur2, score2, obj2


def recommend_for_user_detailed(
    user_id_or_preferences,
    max_budget=MAX_BUDGET,
    max_classes=MAX_CLASSES,
    max_duration=MAX_DURATION,
    diversity_bonus=DIVERSITY_BONUS,
    top2_enabled=TOP2_ENABLED,
):
    """
    Run personalized recommendation and return a structured result.
    """
    classes = CLASSES
    user_preferences = get_preferences_for_user(user_id_or_preferences)

    rec1, price1, dur1, score1, obj1, rec2, price2, dur2, score2, obj2 = get_top2_plans(
        classes,
        user_preferences,
        max_budget,
        max_classes,
        max_duration,
        diversity_bonus,
        top2_enabled=top2_enabled,
    )

    if rec1 is None:
        return {
            "feasible": False,
            "profile": user_id_or_preferences,
            "top2Enabled": top2_enabled,
            "best": None,
            "second_best": None,
        }

    best_categories = list({classes[c]["category"] for c in rec1})
    best = {
        "recommendedClassIds": rec1,
        "objectiveValue": obj1,
        "totalPrice": price1,
        "totalDurationMinutes": dur1,
        "satisfactionScore": score1,
        "categoriesIncluded": best_categories,
    }

    if rec2 is None:
        return {
            "feasible": True,
            "profile": user_id_or_preferences,
            "top2Enabled": top2_enabled,
            "best": best,
            "second_best": None,
        }

    second_categories = list({classes[c]["category"] for c in rec2})
    second_best = {
        "recommendedClassIds": rec2,
        "objectiveValue": obj2,
        "totalPrice": price2,
        "totalDurationMinutes": dur2,
        "satisfactionScore": score2,
        "categoriesIncluded": second_categories,
    }

    return {
        "feasible": True,
        "profile": user_id_or_preferences,
        "top2Enabled": top2_enabled,
        "best": best,
        "second_best": second_best,
    }


def recommend_for_user(
    user_id_or_preferences,
    max_budget=MAX_BUDGET,
    max_classes=MAX_CLASSES,
    max_duration=MAX_DURATION,
    diversity_bonus=DIVERSITY_BONUS,
    top2_enabled=TOP2_ENABLED,
):
    """
    Run personalized recommendation for one user. Returns top-2 plans (best and second-best).

    Args:
        user_id_or_preferences: profile name (str) from USER_PROFILES, or dict of class_name -> score, or None for default.
        max_budget, max_classes, max_duration: optional constraint overrides.
        diversity_bonus: objective diversity bonus per selected category.
        top2_enabled: whether to compute best + second-best.

    Returns:
        (plan1_list, plan1_score, plan2_list, plan2_score) or (plan1, s1, None, None) if no second plan.
    """
    classes = CLASSES
    user_preferences = get_preferences_for_user(user_id_or_preferences)
    result = get_top2_plans(
        classes,
        user_preferences,
        max_budget,
        max_classes,
        max_duration,
        diversity_bonus,
        top2_enabled=top2_enabled,
    )
    rec1, price1, dur1, score1, obj1, rec2, price2, dur2, score2, obj2 = result
    if rec1 is None:
        return None, None, None, None
    return rec1, score1, rec2, score2


def run_recommendation(
    profile=ACTIVE_USER,
    max_budget=MAX_BUDGET,
    max_classes=MAX_CLASSES,
    max_duration=MAX_DURATION,
    diversity_bonus=DIVERSITY_BONUS,
    top2_enabled=TOP2_ENABLED,
):
    """Solve recommendation ILP and print both (if top-2 enabled)."""
    classes = CLASSES
    user_preferences = get_preferences_for_user(profile)
    user_label = profile if isinstance(profile, str) else ("custom" if user_preferences else "default")

    print("=" * 60)
    print("ILP RECOMMENDATION - Personalization + Diversity + Top-2 Plans")
    print("=" * 60)
    print(f"\nBudget: ${max_budget}  Max classes: {max_classes}  Max duration: {max_duration} min")
    print(
        f"Diversity: +{diversity_bonus} per category in plan (categories: {', '.join(get_categories(CLASSES))})"
    )
    print("User (personalization): " + user_label)
    print("Top-2: best plan, then second-best (exclude first set)")

    rec1, price1, dur1, score1, obj1, rec2, price2, dur2, score2, obj2 = get_top2_plans(
        classes,
        user_preferences,
        max_budget,
        max_classes,
        max_duration,
        diversity_bonus,
        top2_enabled=top2_enabled,
    )

    if rec1 is None:
        print("\nNo feasible solution found.")
        print("\n" + "=" * 60)
        return

    cat1 = list({classes[c]["category"] for c in rec1})
    print_plan("PLAN 1 (Best)", rec1, price1, dur1, score1, cat1, user_preferences)
    print(f"  Objective (satisfaction + diversity): {obj1}")

    if rec2 is not None:
        cat2 = list({classes[c]["category"] for c in rec2})
        print_plan("PLAN 2 (Second best)", rec2, price2, dur2, score2, cat2, user_preferences)
        print(f"  Objective (satisfaction + diversity): {obj2}")
    else:
        print("\n--- PLAN 2 (Second best) ---")
        print("  No other feasible plan (only one feasible combination).")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gym recommendation ILP experiment (PuLP).")
    parser.add_argument("--profile", default=ACTIVE_USER, help="Profile key in USER_PROFILES (or 'default').")
    parser.add_argument("--max-budget", type=float, default=MAX_BUDGET)
    parser.add_argument("--max-classes", type=int, default=MAX_CLASSES)
    parser.add_argument("--max-duration", type=float, default=MAX_DURATION)
    parser.add_argument("--diversity-bonus", type=float, default=DIVERSITY_BONUS)
    parser.set_defaults(top2_enabled=TOP2_ENABLED)
    parser.add_argument("--no-top2", dest="top2_enabled", action="store_false", help="Only compute plan 1.")
    parser.add_argument("--output-json", action="store_true", help="Print machine-readable JSON to stdout.")

    args = parser.parse_args()

    if args.output_json:
        t0 = time.perf_counter()
        result = recommend_for_user_detailed(
            user_id_or_preferences=args.profile,
            max_budget=args.max_budget,
            max_classes=args.max_classes,
            max_duration=args.max_duration,
            diversity_bonus=args.diversity_bonus,
            top2_enabled=args.top2_enabled,
        )
        result["runtimeMs"] = int((time.perf_counter() - t0) * 1000)
        print(json.dumps(result, indent=0))
    else:
        run_recommendation(
            profile=args.profile,
            max_budget=args.max_budget,
            max_classes=args.max_classes,
            max_duration=args.max_duration,
            diversity_bonus=args.diversity_bonus,
            top2_enabled=args.top2_enabled,
        )
