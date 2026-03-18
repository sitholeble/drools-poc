package com.dijkstrack.drools.optimization;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Set;

/**
 * Member demand for allocation: which slots they want, priority, and eligibility.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MemberDemand {
    private String memberId;
    private boolean hasPremiumAccess;
    /**
     * Priority weight (higher = prefer to allocate). E.g. from attendance history.
     */
    private double priorityWeight;
    /** Class IDs this member requested (subset of available slots). */
    private Set<String> requestedClassIds;
    /** Preference score per classId (optional; used in objective). */
    private java.util.Map<String, Double> preferenceScoreByClass;
}
