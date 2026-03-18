package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Time slot for equipment scheduling (e.g. 9:00-10:00).
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EquipmentSlot {
    private String slotId;
    private int dayIndex;
    private int startMinuteOfDay;
    private int durationMinutes;
}
