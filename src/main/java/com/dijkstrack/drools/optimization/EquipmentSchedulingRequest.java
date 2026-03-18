package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Input for equipment usage scheduling ILP (CPLEX/Gurobi).
 * Assign classes (that need equipment) to time slots so equipment capacity is not exceeded.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EquipmentSchedulingRequest {
    /** Equipment ID -> total units available */
    private Map<String, Integer> equipmentTotalUnits;
    /** Slots (time windows) that can host classes */
    private List<EquipmentSlot> slots;
    /** Class ID -> (duration, equipment ID -> units needed) */
    private List<ClassEquipmentRequirement> classRequirements;
    /** Optional: classId -> preferred slot IDs (soft preference in objective) */
    private Map<String, List<String>> classSlotPreferences;
}
