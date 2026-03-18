package com.dijkstrack.drools.optimization;

/**
 * Adapter for ILP solvers (CPLEX, Gurobi, or external script).
 * Implementations can call native APIs or export to LP/MPS and invoke solver CLI.
 */
public interface OptimizationSolverAdapter {

    /**
     * Solve class booking allocation: allocate members to class slots fairly and optimally
     * (capacity, premium, trainer max sessions, attendance priority).
     */
    ClassAllocationResult solveClassAllocation(ClassAllocationRequest request);

    /**
     * Solve personalized workout plan: select classes to maximize satisfaction
     * subject to budget, max classes, duration, diversity.
     */
    WorkoutPlanResult solveWorkoutPlan(WorkoutPlanRequest request);

    /**
     * Solve equipment usage scheduling: assign classes to time slots
     * so equipment capacity is not exceeded.
     */
    EquipmentSchedulingResult solveEquipmentScheduling(EquipmentSchedulingRequest request);

    /** Human-readable name of the solver (e.g. "CPLEX", "Gurobi", "External Python"). */
    String getSolverName();
}
