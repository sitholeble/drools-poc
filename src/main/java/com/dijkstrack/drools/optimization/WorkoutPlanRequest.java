package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Input for personalized workout plan ILP (CPLEX/Gurobi).
 * Maximize satisfaction subject to budget, max classes, max duration, diversity.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutPlanRequest {
    private String memberId;
    private double maxBudget;
    private int maxClasses;
    private int maxDurationMinutes;
    /** classId -> (price, durationMin, category, timeSlotId) */
    private List<ClassOption> classOptions;
    /** classId -> preference score (1-10) for this member */
    private Map<String, Double> preferenceScores;
    /** Diversity bonus per distinct category in the plan */
    private double diversityBonusPerCategory;
}
