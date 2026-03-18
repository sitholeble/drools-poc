package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ClassOption {
    private String classId;
    private String className;
    private double price;
    private int durationMinutes;
    private String category;
    private String timeSlotId;
}
