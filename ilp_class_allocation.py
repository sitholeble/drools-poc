#!/usr/bin/env python3
"""
Class booking allocation ILP — CPLEX / Gurobi / PuLP.
Reads ClassAllocationRequest JSON from stdin, writes ClassAllocationResult JSON to stdout.

Constraints: class capacity, premium access, trainer max sessions per day,
attendance priority. Objective: maximize weighted allocation (fair & optimal).
"""
import json
import sys
import time

def main():
    data = json.load(sys.stdin)
    # Normalize keys (Java sends camelCase)
    slots = data.get("slots") or []
    member_demands = data.get("memberDemands") or []
    trainer_limits = data.get("trainerLimits") or []
    max_per_member = data.get("maxClassesPerMember") or 5

    t0 = time.perf_counter()
    result = solve_allocation(slots, member_demands, trainer_limits, max_per_member)
    result["solveTimeMs"] = int((time.perf_counter() - t0) * 1000)
    json.dump(result, sys.stdout, indent=0)

def solve_allocation(slots, member_demands, trainer_limits, max_per_member):
    if not slots or not member_demands:
        return {"feasible": False, "solverUsed": "none", "allocationsByMember": {}, "allocatedCountByClass": {}}

    try:
        from ortools.sat.python import cp_model
        return _solve_ortools(slots, member_demands, trainer_limits, max_per_member)
    except Exception:
        pass
    try:
        from docplex.mp.model import Model
        return _solve_docplex(slots, member_demands, trainer_limits, max_per_member)
    except Exception:
        pass
    try:
        import gurobipy as gp
        return _solve_gurobi(slots, member_demands, trainer_limits, max_per_member)
    except Exception:
        pass
    try:
        from pulp import LpMaximize, LpProblem, LpVariable, lpSum
        return _solve_pulp(slots, member_demands, trainer_limits, max_per_member)
    except Exception:
        pass
    return {"feasible": False, "solverUsed": "no solver", "allocationsByMember": {}, "allocatedCountByClass": {}}

def _solve_ortools(slots, member_demands, trainer_limits, max_per_member):
    """Google OR-Tools CP-SAT: class capacity, scheduling conflicts, trainer limits, member preferences."""
    from ortools.sat.python import cp_model
    model = cp_model.CpModel()
    slot_ids = [s["classId"] for s in slots]
    member_ids = [m["memberId"] for m in member_demands]
    slot_by_id = {s["classId"]: s for s in slots}

    x = {}
    for d in member_demands:
        m = d["memberId"]
        req = d.get("requestedClassIds") or []
        for c in req:
            slot = slot_by_id.get(c)
            if not slot or (slot.get("requiresPremium") and not d.get("hasPremiumAccess")):
                continue
            x[m, c] = model.NewBoolVar(f"x_{m}_{c}")
    y = {c: model.NewBoolVar(f"y_{c}") for c in slot_ids}

    for s in slots:
        c = s["classId"]
        model.Add(sum(x[m, c] for m in member_ids if (m, c) in x) <= s["capacity"])
    for m in member_ids:
        model.Add(sum(x[m, c] for c in slot_ids if (m, c) in x) <= max_per_member)

    # Scheduling conflict: at most one class per (member, dayIndex)
    day_to_classes = {}
    for s in slots:
        day = s.get("dayIndex", 0)
        day_to_classes.setdefault(day, []).append(s["classId"])
    for m in member_ids:
        for day, classes_on_day in day_to_classes.items():
            model.Add(sum(x[m, c] for c in classes_on_day if (m, c) in x) <= 1)

    for c in slot_ids:
        model.Add(sum(x[m, c] for m in member_ids if (m, c) in x) >= y[c])
    for c in slot_ids:
        model.Add(sum(x[m, c] for m in member_ids if (m, c) in x) <= len(member_ids) * y[c])
    for tl in trainer_limits:
        classes_t = [s["classId"] for s in slots if s.get("trainerId") == tl["trainerId"]]
        model.Add(sum(y[c] for c in classes_t) <= tl["maxSessionsPerDay"])

    # Objective: integer coefficients for CP-SAT
    obj_terms = []
    for d in member_demands:
        m = d["memberId"]
        w = d.get("priorityWeight") or 1.0
        prefs = d.get("preferenceScoreByClass") or {}
        for c in slot_ids:
            if (m, c) in x:
                score = int(1000 * (prefs.get(c, w)))
                obj_terms.append(score * x[m, c])
    model.Maximize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"feasible": False, "solverUsed": "OR-Tools", "allocationsByMember": {}, "allocatedCountByClass": {}}

    allocations = {m: [c for c in slot_ids if (m, c) in x and solver.Value(x[m, c]) == 1] for m in member_ids}
    count_by_class = {c: sum(1 for m in member_ids if (m, c) in x and solver.Value(x[m, c]) == 1) for c in slot_ids}
    obj_val = sum(
        (d.get("preferenceScoreByClass") or {}).get(c, d.get("priorityWeight") or 1.0)
        for d in member_demands for c in slot_ids
        if (d["memberId"], c) in x and solver.Value(x[d["memberId"], c]) == 1
    )
    return {
        "feasible": True,
        "objectiveValue": obj_val,
        "allocationsByMember": allocations,
        "allocatedCountByClass": count_by_class,
        "solverUsed": "OR-Tools",
    }

def _solve_docplex(slots, member_demands, trainer_limits, max_per_member):
    from docplex.mp.model import Model
    mdl = Model("class_allocation")
    slot_ids = [s["classId"] for s in slots]
    member_ids = [m["memberId"] for m in member_demands]

    # x[m,c] only for requested and premium-eligible (m,c)
    x = {}
    for d in member_demands:
        m = d["memberId"]
        req = d.get("requestedClassIds") or []
        for c in req:
            slot = next((s for s in slots if s["classId"] == c), None)
            if not slot or (slot.get("requiresPremium") and not d.get("hasPremiumAccess")):
                continue
            x[m, c] = mdl.binary_var(name=f"x_{m}_{c}")
    y = {c: mdl.binary_var(name=f"y_{c}") for c in slot_ids}

    # Capacity
    for s in slots:
        c = s["classId"]
        mdl.add_constraint(mdl.sum(x.get((m, c), 0) for m in member_ids if (m, c) in x) <= s["capacity"])
    # Max per member
    for m in member_ids:
        mdl.add_constraint(mdl.sum(x.get((m, c), 0) for c in slot_ids if (m, c) in x) <= max_per_member)
    # Link y[c] to bookings
    for c in slot_ids:
        mdl.add_constraint(mdl.sum(x.get((m, c), 0) for m in member_ids if (m, c) in x) >= y[c])
        mdl.add_constraint(mdl.sum(x.get((m, c), 0) for m in member_ids if (m, c) in x) <= len(member_ids) * y[c])
    # Trainer limit
    for tl in trainer_limits:
        classes_t = [s["classId"] for s in slots if s.get("trainerId") == tl["trainerId"]]
        mdl.add_constraint(mdl.sum(y[c] for c in classes_t) <= tl["maxSessionsPerDay"])

    obj_terms = []
    for d in member_demands:
        m = d["memberId"]
        w = d.get("priorityWeight") or 1.0
        prefs = d.get("preferenceScoreByClass") or {}
        for c in slot_ids:
            if (m, c) in x:
                obj_terms.append(prefs.get(c, w) * x[m, c])
    mdl.maximize(mdl.sum(obj_terms))
    sol = mdl.solve()
    if not sol:
        return {"feasible": False, "solverUsed": "CPLEX (docplex)", "allocationsByMember": {}, "allocatedCountByClass": {}}
    allocations = {m: [c for c in slot_ids if (m, c) in x and sol.get_value(x[m, c]) > 0.5] for m in member_ids}
    count_by_class = {c: sum(1 for m in member_ids if (m, c) in x and sol.get_value(x[m, c]) > 0.5) for c in slot_ids}
    return {
        "feasible": True,
        "objectiveValue": sol.objective_value,
        "allocationsByMember": allocations,
        "allocatedCountByClass": count_by_class,
        "solverUsed": "CPLEX (docplex)",
    }

def _solve_gurobi(slots, member_demands, trainer_limits, max_per_member):
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model("class_allocation")
    slot_ids = [s["classId"] for s in slots]
    member_ids = [m["memberId"] for m in member_demands]

    x = {}
    for mem in member_ids:
        req = next((d.get("requestedClassIds") or [] for d in member_demands if d["memberId"] == mem), [])
        for c in slot_ids:
            if c in req:
                slot = next(s for s in slots if s["classId"] == c)
                if slot.get("requiresPremium"):
                    if not next((d.get("hasPremiumAccess") for d in member_demands if d["memberId"] == mem), False):
                        continue
                x[mem, c] = m.addVar(vtype=GRB.BINARY, name=f"x_{mem}_{c}")
    y = {c: m.addVar(vtype=GRB.BINARY, name=f"y_{c}") for c in slot_ids}
    m.update()

    for s in slots:
        c = s["classId"]
        m.addConstr(gp.quicksum(x.get((mem, c), 0) for mem in member_ids if (mem, c) in x) <= s["capacity"])
    for mem in member_ids:
        m.addConstr(gp.quicksum(x.get((mem, c), 0) for c in slot_ids if (mem, c) in x) <= max_per_member)
    for c in slot_ids:
        m.addConstr(gp.quicksum(x.get((mem, c), 0) for mem in member_ids if (mem, c) in x) >= y[c])
        m.addConstr(gp.quicksum(x.get((mem, c), 0) for mem in member_ids if (mem, c) in x) <= len(member_ids) * y[c])
    for tl in trainer_limits:
        classes_t = [s["classId"] for s in slots if s.get("trainerId") == tl["trainerId"]]
        m.addConstr(gp.quicksum(y[c] for c in classes_t) <= tl["maxSessionsPerDay"])

    obj = 0
    for d in member_demands:
        mem = d["memberId"]
        w = d.get("priorityWeight") or 1.0
        prefs = d.get("preferenceScoreByClass") or {}
        for c in slot_ids:
            if (mem, c) in x:
                obj += prefs.get(c, w) * x[mem, c]
    m.setObjective(obj, GRB.MAXIMIZE)
    m.optimize()
    if m.Status not in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL) or m.SolCount == 0:
        return {"feasible": False, "solverUsed": "Gurobi", "allocationsByMember": {}, "allocatedCountByClass": {}}
    allocations = {mem: [c for c in slot_ids if (mem, c) in x and x[mem, c].X > 0.5] for mem in member_ids}
    count_by_class = {c: sum(1 for mem in member_ids if (mem, c) in x and x[mem, c].X > 0.5) for c in slot_ids}
    return {
        "feasible": True,
        "objectiveValue": m.ObjVal,
        "allocationsByMember": allocations,
        "allocatedCountByClass": count_by_class,
        "solverUsed": "Gurobi",
    }

def _solve_pulp(slots, member_demands, trainer_limits, max_per_member):
    from pulp import LpMaximize, LpProblem, LpVariable, lpSum
    prob = LpProblem("class_allocation", LpMaximize)
    slot_ids = [s["classId"] for s in slots]
    member_ids = [m["memberId"] for m in member_demands]
    x = {}
    for d in member_demands:
        mem = d["memberId"]
        req = d.get("requestedClassIds") or []
        for c in req:
            slot = next((s for s in slots if s["classId"] == c), None)
            if not slot or (slot.get("requiresPremium") and not d.get("hasPremiumAccess")):
                continue
            x[mem, c] = LpVariable(f"x_{mem}_{c}", cat="Binary")
    y = {c: LpVariable(f"y_{c}", cat="Binary") for c in slot_ids}
    for s in slots:
        c = s["classId"]
        prob += lpSum(x.get((m, c), 0) for m in member_ids if (m, c) in x) <= s["capacity"], f"cap_{c}"
    for m in member_ids:
        prob += lpSum(x.get((m, c), 0) for c in slot_ids if (m, c) in x) <= max_per_member, f"max_{m}"
    for c in slot_ids:
        prob += lpSum(x.get((m, c), 0) for m in member_ids if (m, c) in x) >= y[c], f"link1_{c}"
        prob += lpSum(x.get((m, c), 0) for m in member_ids if (m, c) in x) <= len(member_ids) * y[c], f"link2_{c}"
    for tl in trainer_limits:
        classes_t = [s["classId"] for s in slots if s.get("trainerId") == tl["trainerId"]]
        prob += lpSum(y[c] for c in classes_t) <= tl["maxSessionsPerDay"], f"trainer_{tl['trainerId']}"
    obj = 0
    for d in member_demands:
        mem = d["memberId"]
        w = d.get("priorityWeight") or 1.0
        prefs = d.get("preferenceScoreByClass") or {}
        for c in slot_ids:
            if (mem, c) in x:
                obj += prefs.get(c, w) * x[mem, c]
    prob += obj
    prob.solve()
    if prob.status != 1:
        return {"feasible": False, "solverUsed": "PuLP", "allocationsByMember": {}, "allocatedCountByClass": {}}
    allocations = {mem: [c for c in slot_ids if (mem, c) in x and x[mem, c].value() and x[mem, c].value() > 0.5] for mem in member_ids}
    count_by_class = {c: sum(1 for mem in member_ids if (mem, c) in x and x[mem, c].value() and x[mem, c].value() > 0.5) for c in slot_ids}
    return {
        "feasible": True,
        "objectiveValue": prob.objective.value(),
        "allocationsByMember": allocations,
        "allocatedCountByClass": count_by_class,
        "solverUsed": "PuLP",
    }

if __name__ == "__main__":
    main()
