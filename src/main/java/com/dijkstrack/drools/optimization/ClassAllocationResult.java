package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Result of class allocation ILP: who is assigned to which class.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ClassAllocationResult {
    private boolean feasible;
    private double objectiveValue;
    /** memberId -> list of allocated classIds */
    private Map<String, List<String>> allocationsByMember;
    /** classId -> count of allocated members */
    private Map<String, Integer> allocatedCountByClass;
    private String solverUsed;
    private long solveTimeMs;
}
