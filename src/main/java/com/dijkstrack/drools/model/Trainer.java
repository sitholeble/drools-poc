package com.dijkstrack.drools.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

/**
 * Trainer (instructor) with max sessions per day for ILP constraints.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Trainer {
    private Long id;
    private String trainerId;
    private String name;
    /** Max classes this trainer can lead per day. */
    private int maxSessionsPerDay;
    /** Class categories this trainer is qualified for. */
    private List<GymClass.ClassCategory> qualifiedCategories = new ArrayList<>();
}
