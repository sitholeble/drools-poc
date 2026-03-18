package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Input for class booking allocation ILP (CPLEX/Gurobi).
 * <p>
 * You recommend classes (Yoga, HIIT, Strength), but: each class has limited capacity,
 * some members have premium access, trainers have max sessions per day, some members
 * have attendance history priority. This request captures all inputs so the solver
 * can allocate fairly and optimally.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ClassAllocationRequest {
    private List<AllocationSlot> slots;
    private List<MemberDemand> memberDemands;
    private List<TrainerLimit> trainerLimits;
    /** Max classes per member in the window (fairness cap). */
    private int maxClassesPerMember;
}
