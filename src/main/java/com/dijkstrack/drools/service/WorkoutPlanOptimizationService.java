package com.dijkstrack.drools.service;

import com.dijkstrack.drools.optimization.*;
import org.springframework.stereotype.Service;

/**
 * Runs personalized workout plan ILP (CPLEX/Gurobi): maximize satisfaction
 * subject to budget, max classes, duration, diversity.
 */
@Service
public class WorkoutPlanOptimizationService {

    private final OptimizationSolverAdapter solver;

    public WorkoutPlanOptimizationService(OptimizationSolverAdapter solver) {
        this.solver = solver;
    }

    public WorkoutPlanResult recommend(WorkoutPlanRequest request) {
        long start = System.currentTimeMillis();
        WorkoutPlanResult result = solver.solveWorkoutPlan(request);
        return WorkoutPlanResult.builder()
                .feasible(result.isFeasible())
                .objectiveValue(result.getObjectiveValue())
                .recommendedClassIds(result.getRecommendedClassIds())
                .totalPrice(result.getTotalPrice())
                .totalDurationMinutes(result.getTotalDurationMinutes())
                .satisfactionScore(result.getSatisfactionScore())
                .categoriesIncluded(result.getCategoriesIncluded())
                .secondBestClassIds(result.getSecondBestClassIds())
                .solverUsed(result.getSolverUsed())
                .solveTimeMs(System.currentTimeMillis() - start)
                .build();
    }
}
