#!/usr/bin/env python3
"""
Personalized workout plan ILP — CPLEX / Gurobi / PuLP.
Reads WorkoutPlanRequest JSON from stdin, writes WorkoutPlanResult JSON to stdout.
Maximize satisfaction subject to budget, max classes, max duration, diversity bonus.
"""
import json
import sys
import time

def main():
    data = json.load(sys.stdin)
    opts = data.get("classOptions") or []
    prefs = data.get("preferenceScores") or {}
    max_budget = data.get("maxBudget") or 50
    max_classes = data.get("maxClasses") or 3
    max_duration = data.get("maxDurationMinutes") or 150
    diversity_bonus = data.get("diversityBonusPerCategory") or 2.0

    t0 = time.perf_counter()
    result = solve_workout_plan(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus)
    result["solveTimeMs"] = int((time.perf_counter() - t0) * 1000)
    json.dump(result, sys.stdout, indent=0)

def solve_workout_plan(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus):
    if not opts:
        return {"feasible": False, "solverUsed": "none", "recommendedClassIds": [], "categoriesIncluded": []}
    try:
        from docplex.mp.model import Model
        return _solve_docplex(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus)
    except Exception:
        pass
    try:
        import gurobipy as gp
        return _solve_gurobi(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus)
    except Exception:
        pass
    try:
        from pulp import LpMaximize, LpProblem, LpVariable, lpSum
        return _solve_pulp(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus)
    except Exception:
        pass
    return {"feasible": False, "solverUsed": "no solver", "recommendedClassIds": [], "categoriesIncluded": []}

def _solve_docplex(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus):
    from docplex.mp.model import Model
    mdl = Model("workout_plan")
    classes = [c["classId"] for c in opts]
    by_id = {c["classId"]: c for c in opts}
    categories = list({c["category"] for c in opts})
    x = {c: mdl.binary_var(name=f"x_{c}") for c in classes}
    y = {cat: mdl.binary_var(name=f"y_{cat}") for cat in categories}
    # Budget, count, duration
    mdl.add_constraint(mdl.sum(by_id[c]["price"] * x[c] for c in classes) <= max_budget)
    mdl.add_constraint(mdl.sum(x[c] for c in classes) <= max_classes)
    mdl.add_constraint(mdl.sum(by_id[c]["durationMinutes"] * x[c] for c in classes) <= max_duration)
    # One per time slot
    slots = list({c["timeSlotId"] for c in opts})
    for slot in slots:
        in_slot = [c for c in classes if by_id[c]["timeSlotId"] == slot]
        mdl.add_constraint(mdl.sum(x[c] for c in in_slot) <= 1)
    # Link y[cat]
    for cat in categories:
        in_cat = [c for c in classes if by_id[c]["category"] == cat]
        mdl.add_constraint(mdl.sum(x[c] for c in in_cat) >= y[cat])
        mdl.add_constraint(mdl.sum(x[c] for c in in_cat) <= len(in_cat) * y[cat])
    obj = mdl.sum(prefs.get(c, by_id[c].get("preference_score", 1.0) if isinstance(by_id[c].get("preference_score"), (int, float)) else 1.0) * x[c] for c in classes)
    obj = obj + diversity_bonus * mdl.sum(y[cat] for cat in categories)
    mdl.maximize(obj)
    sol = mdl.solve()
    if not sol:
        return {"feasible": False, "solverUsed": "CPLEX (docplex)", "recommendedClassIds": [], "categoriesIncluded": []}
    chosen = [c for c in classes if sol.get_value(x[c]) > 0.5]
    total_price = sum(by_id[c]["price"] for c in chosen)
    total_dur = sum(by_id[c]["durationMinutes"] for c in chosen)
    satisfaction = sum(prefs.get(c, 1.0) for c in chosen) + len({by_id[c]["category"] for c in chosen}) * diversity_bonus
    return {
        "feasible": True,
        "objectiveValue": sol.objective_value,
        "recommendedClassIds": chosen,
        "totalPrice": total_price,
        "totalDurationMinutes": total_dur,
        "satisfactionScore": satisfaction,
        "categoriesIncluded": list({by_id[c]["category"] for c in chosen}),
        "secondBestClassIds": None,
        "solverUsed": "CPLEX (docplex)",
    }

def _solve_gurobi(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus):
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model("workout_plan")
    classes = [c["classId"] for c in opts]
    by_id = {c["classId"]: c for c in opts}
    categories = list({c["category"] for c in opts})
    x = {c: m.addVar(vtype=GRB.BINARY, name=f"x_{c}") for c in classes}
    y = {cat: m.addVar(vtype=GRB.BINARY, name=f"y_{cat}") for cat in categories}
    m.update()
    m.addConstr(gp.quicksum(by_id[c]["price"] * x[c] for c in classes) <= max_budget)
    m.addConstr(gp.quicksum(x[c] for c in classes) <= max_classes)
    m.addConstr(gp.quicksum(by_id[c]["durationMinutes"] * x[c] for c in classes) <= max_duration)
    slots = list({c["timeSlotId"] for c in opts})
    for slot in slots:
        in_slot = [c for c in classes if by_id[c]["timeSlotId"] == slot]
        m.addConstr(gp.quicksum(x[c] for c in in_slot) <= 1)
    for cat in categories:
        in_cat = [c for c in classes if by_id[c]["category"] == cat]
        m.addConstr(gp.quicksum(x[c] for c in in_cat) >= y[cat])
        m.addConstr(gp.quicksum(x[c] for c in in_cat) <= len(in_cat) * y[cat])
    obj = gp.quicksum(prefs.get(c, 1.0) * x[c] for c in classes) + diversity_bonus * gp.quicksum(y[cat] for cat in categories)
    m.setObjective(obj, GRB.MAXIMIZE)
    m.optimize()
    if m.Status not in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL) or m.SolCount == 0:
        return {"feasible": False, "solverUsed": "Gurobi", "recommendedClassIds": [], "categoriesIncluded": []}
    chosen = [c for c in classes if x[c].X > 0.5]
    return {
        "feasible": True,
        "objectiveValue": m.ObjVal,
        "recommendedClassIds": chosen,
        "totalPrice": sum(by_id[c]["price"] for c in chosen),
        "totalDurationMinutes": sum(by_id[c]["durationMinutes"] for c in chosen),
        "satisfactionScore": sum(prefs.get(c, 1.0) for c in chosen) + len({by_id[c]["category"] for c in chosen}) * diversity_bonus,
        "categoriesIncluded": list({by_id[c]["category"] for c in chosen}),
        "secondBestClassIds": None,
        "solverUsed": "Gurobi",
    }

def _solve_pulp(opts, prefs, max_budget, max_classes, max_duration, diversity_bonus):
    from pulp import LpMaximize, LpProblem, LpVariable, lpSum
    prob = LpProblem("workout_plan", LpMaximize)
    classes = [c["classId"] for c in opts]
    by_id = {c["classId"]: c for c in opts}
    categories = list({c["category"] for c in opts})
    x = {c: LpVariable(f"x_{c}", cat="Binary") for c in classes}
    y = {cat: LpVariable(f"y_{cat}", cat="Binary") for cat in categories}
    prob += lpSum(by_id[c]["price"] * x[c] for c in classes) <= max_budget
    prob += lpSum(x[c] for c in classes) <= max_classes
    prob += lpSum(by_id[c]["durationMinutes"] * x[c] for c in classes) <= max_duration
    for slot in list({c["timeSlotId"] for c in opts}):
        in_slot = [c for c in classes if by_id[c]["timeSlotId"] == slot]
        prob += lpSum(x[c] for c in in_slot) <= 1
    for cat in categories:
        in_cat = [c for c in classes if by_id[c]["category"] == cat]
        prob += lpSum(x[c] for c in in_cat) >= y[cat]
        prob += lpSum(x[c] for c in in_cat) <= len(in_cat) * y[cat]
    prob += lpSum(prefs.get(c, 1.0) * x[c] for c in classes) + diversity_bonus * lpSum(y[cat] for cat in categories)
    prob.solve()
    if prob.status != 1:
        return {"feasible": False, "solverUsed": "PuLP", "recommendedClassIds": [], "categoriesIncluded": []}
    chosen = [c for c in classes if x[c].value() and x[c].value() > 0.5]
    return {
        "feasible": True,
        "objectiveValue": prob.objective.value(),
        "recommendedClassIds": chosen,
        "totalPrice": sum(by_id[c]["price"] for c in chosen),
        "totalDurationMinutes": sum(by_id[c]["durationMinutes"] for c in chosen),
        "satisfactionScore": sum(prefs.get(c, 1.0) for c in chosen) + len({by_id[c]["category"] for c in chosen}) * diversity_bonus,
        "categoriesIncluded": list({by_id[c]["category"] for c in chosen}),
        "secondBestClassIds": None,
        "solverUsed": "PuLP",
    }

if __name__ == "__main__":
    main()
