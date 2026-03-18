package com.dijkstrack.drools.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Gym equipment resource for usage scheduling (ILP).
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Equipment {
    private Long id;
    private String equipmentId;
    private String name;
    /** How many units of this equipment exist (e.g. 10 treadmills). */
    private int totalUnits;
    /** Optional: max concurrent bookings per slot (default = totalUnits). */
    private Integer maxConcurrentBookings;
}
