package com.dijkstrack.drools.service;

import com.dijkstrack.drools.optimization.*;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Builds class allocation request and runs ILP (CPLEX/Gurobi) for fair, optimal booking.
 */
@Service
public class ClassAllocationOptimizationService {

    private final OptimizationSolverAdapter solver;

    public ClassAllocationOptimizationService(OptimizationSolverAdapter solver) {
        this.solver = solver;
    }

    public ClassAllocationResult allocate(ClassAllocationRequest request) {
        long start = System.currentTimeMillis();
        ClassAllocationResult result = solver.solveClassAllocation(request);
        result = ClassAllocationResult.builder()
                .feasible(result.isFeasible())
                .objectiveValue(result.getObjectiveValue())
                .allocationsByMember(result.getAllocationsByMember())
                .allocatedCountByClass(result.getAllocatedCountByClass())
                .solverUsed(result.getSolverUsed())
                .solveTimeMs(System.currentTimeMillis() - start)
                .build();
        return result;
    }

    /**
     * Build request from domain data: slots (from GymClass), members (with premium, attendance), trainer limits.
     */
    public ClassAllocationRequest buildRequest(
            List<AllocationSlot> slots,
            List<MemberDemand> memberDemands,
            List<TrainerLimit> trainerLimits,
            int maxClassesPerMember) {
        return ClassAllocationRequest.builder()
                .slots(slots)
                .memberDemands(memberDemands)
                .trainerLimits(trainerLimits != null ? trainerLimits : List.of())
                .maxClassesPerMember(maxClassesPerMember <= 0 ? 5 : maxClassesPerMember)
                .build();
    }
}
