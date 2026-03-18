#!/usr/bin/env python3
"""
Equipment usage scheduling ILP — CPLEX / Gurobi / PuLP.
Reads EquipmentSchedulingRequest JSON from stdin, writes EquipmentSchedulingResult JSON to stdout.
Assign classes to time slots so that for each slot and each equipment type, total units used <= available.
"""
import json
import sys
import time

def main():
    data = json.load(sys.stdin)
    equipment_units = data.get("equipmentTotalUnits") or {}
    slots = data.get("slots") or []
    class_reqs = data.get("classRequirements") or []
    prefs = data.get("classSlotPreferences") or {}

    t0 = time.perf_counter()
    result = solve_equipment(equipment_units, slots, class_reqs, prefs)
    result["solveTimeMs"] = int((time.perf_counter() - t0) * 1000)
    json.dump(result, sys.stdout, indent=0)

def solve_equipment(equipment_units, slots, class_reqs, prefs):
    if not slots or not class_reqs:
        return {"feasible": False, "solverUsed": "none", "classToSlot": {}, "slotToClasses": {}}
    try:
        from docplex.mp.model import Model
        return _solve_docplex(equipment_units, slots, class_reqs, prefs)
    except Exception:
        pass
    try:
        import gurobipy as gp
        return _solve_gurobi(equipment_units, slots, class_reqs, prefs)
    except Exception:
        pass
    try:
        from pulp import LpMaximize, LpProblem, LpVariable, lpSum
        return _solve_pulp(equipment_units, slots, class_reqs, prefs)
    except Exception:
        pass
    return {"feasible": False, "solverUsed": "no solver", "classToSlot": {}, "slotToClasses": {}}

def _solve_docplex(equipment_units, slots, class_reqs, prefs):
    from docplex.mp.model import Model
    mdl = Model("equipment_scheduling")
    slot_ids = [s["slotId"] for s in slots]
    class_ids = [r["classId"] for r in class_reqs]
    req_by_class = {r["classId"]: r for r in class_reqs}
    # x[c,s] = 1 if class c assigned to slot s
    x = {}
    for c in class_ids:
        for s in slot_ids:
            x[c, s] = mdl.binary_var(name=f"x_{c}_{s}")
    # Each class exactly one slot
    for c in class_ids:
        mdl.add_constraint(mdl.sum(x[c, s] for s in slot_ids) == 1)
    # Each slot: for each equipment type, total units used <= available
    for s in slot_ids:
        for eq_id, total in equipment_units.items():
            used = mdl.sum(
                (req_by_class[c].get("equipmentUnitsRequired") or {}).get(eq_id, 0) * x[c, s]
                for c in class_ids
            )
            mdl.add_constraint(used <= total)
    # Optional: prefer slots from classSlotPreferences (soft)
    obj_terms = []
    for c in class_ids:
        preferred = prefs.get(c) or []
        for s in slot_ids:
            if (c, s) in x and s in preferred:
                obj_terms.append(1.0 * x[c, s])
    if obj_terms:
        mdl.maximize(mdl.sum(obj_terms))
    else:
        mdl.maximize(0)  # feasibility only
    sol = mdl.solve()
    if not sol:
        return {"feasible": False, "solverUsed": "CPLEX (docplex)", "classToSlot": {}, "slotToClasses": {}}
    class_to_slot = {c: next(s for s in slot_ids if sol.get_value(x[c, s]) > 0.5) for c in class_ids}
    slot_to_classes = {s: [c for c in class_ids if class_to_slot.get(c) == s] for s in slot_ids}
    return {
        "feasible": True,
        "objectiveValue": sol.objective_value,
        "classToSlot": class_to_slot,
        "slotToClasses": slot_to_classes,
        "solverUsed": "CPLEX (docplex)",
    }

def _solve_gurobi(equipment_units, slots, class_reqs, prefs):
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model("equipment_scheduling")
    slot_ids = [s["slotId"] for s in slots]
    class_ids = [r["classId"] for r in class_reqs]
    req_by_class = {r["classId"]: r for r in class_reqs}
    x = {(c, s): m.addVar(vtype=GRB.BINARY, name=f"x_{c}_{s}") for c in class_ids for s in slot_ids}
    m.update()
    for c in class_ids:
        m.addConstr(gp.quicksum(x[c, s] for s in slot_ids) == 1)
    for s in slot_ids:
        for eq_id, total in equipment_units.items():
            m.addConstr(
                gp.quicksum((req_by_class[c].get("equipmentUnitsRequired") or {}).get(eq_id, 0) * x[c, s] for c in class_ids)
                <= total
            )
    obj = gp.quicksum(x[c, s] for c in class_ids for s in (prefs.get(c) or []) if (c, s) in x)
    m.setObjective(obj, GRB.MAXIMIZE)
    m.optimize()
    if m.Status not in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL) or m.SolCount == 0:
        return {"feasible": False, "solverUsed": "Gurobi", "classToSlot": {}, "slotToClasses": {}}
    class_to_slot = {c: next(s for s in slot_ids if x[c, s].X > 0.5) for c in class_ids}
    slot_to_classes = {s: [c for c in class_ids if class_to_slot.get(c) == s] for s in slot_ids}
    return {
        "feasible": True,
        "objectiveValue": m.ObjVal,
        "classToSlot": class_to_slot,
        "slotToClasses": slot_to_classes,
        "solverUsed": "Gurobi",
    }

def _solve_pulp(equipment_units, slots, class_reqs, prefs):
    from pulp import LpMaximize, LpProblem, LpVariable, lpSum
    prob = LpProblem("equipment_scheduling", LpMaximize)
    slot_ids = [s["slotId"] for s in slots]
    class_ids = [r["classId"] for r in class_reqs]
    req_by_class = {r["classId"]: r for r in class_reqs}
    x = {(c, s): LpVariable(f"x_{c}_{s}", cat="Binary") for c in class_ids for s in slot_ids}
    for c in class_ids:
        prob += lpSum(x[c, s] for s in slot_ids) == 1
    for s in slot_ids:
        for eq_id, total in equipment_units.items():
            prob += lpSum(
                (req_by_class[c].get("equipmentUnitsRequired") or {}).get(eq_id, 0) * x[c, s]
                for c in class_ids
            ) <= total
    prob += lpSum(x[c, s] for c in class_ids for s in (prefs.get(c) or []) if (c, s) in x)
    prob.solve()
    if prob.status != 1:
        return {"feasible": False, "solverUsed": "PuLP", "classToSlot": {}, "slotToClasses": {}}
    class_to_slot = {c: next(s for s in slot_ids if x[c, s].value() and x[c, s].value() > 0.5) for c in class_ids}
    slot_to_classes = {s: [c for c in class_ids if class_to_slot.get(c) == s] for s in slot_ids}
    return {
        "feasible": True,
        "objectiveValue": prob.objective.value(),
        "classToSlot": class_to_slot,
        "slotToClasses": slot_to_classes,
        "solverUsed": "PuLP",
    }

if __name__ == "__main__":
    main()
