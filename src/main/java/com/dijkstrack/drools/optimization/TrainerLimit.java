package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Trainer max sessions per day for ILP constraints.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrainerLimit {
    private String trainerId;
    private int maxSessionsPerDay;
}
