package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * One class slot in the allocation window (for ILP).
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AllocationSlot {
    private String classId;
    private String className;
    private String trainerId;
    private int capacity;
    private boolean requiresPremium;
    /** Day index in the window (0 = first day). */
    private int dayIndex;
}
