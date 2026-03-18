package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Result of workout plan ILP: recommended class set (and optional second-best).
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutPlanResult {
    private boolean feasible;
    private double objectiveValue;
    private List<String> recommendedClassIds;
    private double totalPrice;
    private int totalDurationMinutes;
    private double satisfactionScore;
    private List<String> categoriesIncluded;
    private List<String> secondBestClassIds;
    private String solverUsed;
    private long solveTimeMs;
}
