package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ClassEquipmentRequirement {
    private String classId;
    private String className;
    private int durationMinutes;
    /** equipmentId -> units required (e.g. "TREADMILL" -> 1) */
    private Map<String, Integer> equipmentUnitsRequired;
}
