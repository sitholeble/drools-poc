package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

/**
 * Result of equipment scheduling ILP: which class is scheduled in which slot.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EquipmentSchedulingResult {
    private boolean feasible;
    private double objectiveValue;
    /** classId -> slotId */
    private Map<String, String> classToSlot;
    /** slotId -> list of classIds in that slot */
    private Map<String, java.util.List<String>> slotToClasses;
    private String solverUsed;
    private long solveTimeMs;
}
