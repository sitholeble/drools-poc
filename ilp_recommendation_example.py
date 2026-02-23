"""
Integer Linear Programming (ILP) for Recommendation System
============================================================

Problem: Recommend optimal gym classes to a member based on:
- Member preferences (scores for each class)
- Constraints (max classes per day, budget, time slots)

This example uses PuLP library for ILP optimization.

Install: pip install pulp
"""

from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus

# ============================================
# PROBLEM DATA
# ============================================

# Available gym classes with their attributes
classes = {
    "Yoga":     {"price": 15, "duration": 60, "time_slot": "morning",   "preference_score": 8},
    "HIIT":     {"price": 20, "duration": 45, "time_slot": "morning",   "preference_score": 9},
    "Pilates":  {"price": 18, "duration": 60, "time_slot": "afternoon", "preference_score": 7},
    "Spinning": {"price": 22, "duration": 45, "time_slot": "afternoon", "preference_score": 6},
    "Boxing":   {"price": 25, "duration": 60, "time_slot": "evening",   "preference_score": 10},
    "Zumba":    {"price": 12, "duration": 45, "time_slot": "evening",   "preference_score": 5},
}

# Member constraints
MAX_BUDGET = 50          # Maximum spend per day
MAX_CLASSES = 3          # Maximum classes per day
MAX_DURATION = 150       # Maximum total duration (minutes)

# ============================================
# ILP MODEL FORMULATION
# ============================================

# Step 1: Create the optimization problem (Maximize satisfaction)
problem = LpProblem("Gym_Class_Recommendation", LpMaximize)

# Step 2: Create decision variables (binary: 1 = recommend, 0 = don't recommend)
# x[class_name] = 1 if we recommend this class, 0 otherwise
x = {
    class_name: LpVariable(f"select_{class_name}", cat="Binary")
    for class_name in classes
}

# Step 3: Define the objective function (Maximize total preference score)
# Objective: Maximize SUM(preference_score * x[class])
problem += lpSum(
    classes[c]["preference_score"] * x[c] for c in classes
), "Maximize_Satisfaction"

# Step 4: Add constraints

# Constraint 1: Budget constraint (total price <= MAX_BUDGET)
problem += lpSum(
    classes[c]["price"] * x[c] for c in classes
) <= MAX_BUDGET, "Budget_Constraint"

# Constraint 2: Maximum classes constraint
problem += lpSum(x[c] for c in classes) <= MAX_CLASSES, "Max_Classes"

# Constraint 3: Total duration constraint
problem += lpSum(
    classes[c]["duration"] * x[c] for c in classes
) <= MAX_DURATION, "Max_Duration"

# Constraint 4: At most one class per time slot (no overlapping)
time_slots = ["morning", "afternoon", "evening"]
for slot in time_slots:
    classes_in_slot = [c for c in classes if classes[c]["time_slot"] == slot]
    problem += lpSum(x[c] for c in classes_in_slot) <= 1, f"One_Per_Slot_{slot}"

# ============================================
# SOLVE THE PROBLEM
# ============================================

print("=" * 60)
print("ILP RECOMMENDATION SYSTEM - GYM CLASSES")
print("=" * 60)

print("\n--- PROBLEM SETUP ---")
print(f"Budget Limit: ${MAX_BUDGET}")
print(f"Max Classes: {MAX_CLASSES}")
print(f"Max Duration: {MAX_DURATION} minutes")
print(f"Available Classes: {len(classes)}")

# Solve
problem.solve()

# ============================================
# DISPLAY RESULTS
# ============================================

print("\n--- OPTIMIZATION RESULTS ---")
print(f"Status: {LpStatus[problem.status]}")

if problem.status == 1:  # Optimal solution found
    print("\n--- RECOMMENDED CLASSES ---")
    
    total_price = 0
    total_duration = 0
    total_score = 0
    recommended = []
    
    for class_name in classes:
        if x[class_name].value() == 1:
            c = classes[class_name]
            recommended.append(class_name)
            total_price += c["price"]
            total_duration += c["duration"]
            total_score += c["preference_score"]
            print(f"  - {class_name}")
            print(f"      Time: {c['time_slot']}, Duration: {c['duration']}min, Price: ${c['price']}, Score: {c['preference_score']}")
    
    print("\n--- SUMMARY ---")
    print(f"Classes Recommended: {len(recommended)}")
    print(f"Total Price: ${total_price} (Budget: ${MAX_BUDGET})")
    print(f"Total Duration: {total_duration} minutes (Limit: {MAX_DURATION})")
    print(f"Total Satisfaction Score: {total_score}")
    
    print("\n--- NOT RECOMMENDED ---")
    for class_name in classes:
        if x[class_name].value() == 0:
            print(f"  - {class_name} (Score: {classes[class_name]['preference_score']})")
else:
    print("No optimal solution found!")

print("\n" + "=" * 60)


# ============================================
# EXPLANATION OF ILP COMPONENTS
# ============================================

"""
ILP MODEL BREAKDOWN:

1. DECISION VARIABLES (Binary):
   x["Yoga"] = 1 or 0  (recommend or not)
   x["HIIT"] = 1 or 0
   x["Pilates"] = 1 or 0
   ...

2. OBJECTIVE FUNCTION (Maximize):
   Maximize: 8*x["Yoga"] + 9*x["HIIT"] + 7*x["Pilates"] + 6*x["Spinning"] + 10*x["Boxing"] + 5*x["Zumba"]
   
   We want to maximize the total preference score of recommended classes.

3. CONSTRAINTS:
   
   Budget: 15*x["Yoga"] + 20*x["HIIT"] + 18*x["Pilates"] + 22*x["Spinning"] + 25*x["Boxing"] + 12*x["Zumba"] <= 50
   
   Max Classes: x["Yoga"] + x["HIIT"] + x["Pilates"] + x["Spinning"] + x["Boxing"] + x["Zumba"] <= 3
   
   Duration: 60*x["Yoga"] + 45*x["HIIT"] + 60*x["Pilates"] + 45*x["Spinning"] + 60*x["Boxing"] + 45*x["Zumba"] <= 150
   
   Time Slots:
     Morning: x["Yoga"] + x["HIIT"] <= 1
     Afternoon: x["Pilates"] + x["Spinning"] <= 1
     Evening: x["Boxing"] + x["Zumba"] <= 1

4. SOLUTION:
   The solver finds the combination of classes that:
   - Maximizes satisfaction score
   - Stays within budget
   - Respects all constraints
"""

