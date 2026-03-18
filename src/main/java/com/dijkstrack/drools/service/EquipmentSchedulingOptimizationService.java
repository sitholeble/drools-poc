package com.dijkstrack.drools.service;

import com.dijkstrack.drools.optimization.*;
import org.springframework.stereotype.Service;

/**
 * Runs equipment usage scheduling ILP (CPLEX/Gurobi): assign classes to time slots
 * so equipment capacity is not exceeded.
 */
@Service
public class EquipmentSchedulingOptimizationService {

    private final OptimizationSolverAdapter solver;

    public EquipmentSchedulingOptimizationService(OptimizationSolverAdapter solver) {
        this.solver = solver;
    }

    public EquipmentSchedulingResult schedule(EquipmentSchedulingRequest request) {
        long start = System.currentTimeMillis();
        EquipmentSchedulingResult result = solver.solveEquipmentScheduling(request);
        return EquipmentSchedulingResult.builder()
                .feasible(result.isFeasible())
                .objectiveValue(result.getObjectiveValue())
                .classToSlot(result.getClassToSlot())
                .slotToClasses(result.getSlotToClasses())
                .solverUsed(result.getSolverUsed())
                .solveTimeMs(System.currentTimeMillis() - start)
                .build();
    }
}
