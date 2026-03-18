package com.dijkstrack.drools.controller;

import com.dijkstrack.drools.optimization.*;
import com.dijkstrack.drools.service.ClassAllocationOptimizationService;
import com.dijkstrack.drools.service.EquipmentSchedulingOptimizationService;
import com.dijkstrack.drools.service.WorkoutPlanOptimizationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST API for ILP-based optimization (CPLEX/Gurobi).
 * 1. Class booking allocation (fair, optimal)
 * 2. Personalized workout plan generation
 * 3. Equipment usage scheduling
 */
@RestController
@RequestMapping("/api/optimization")
public class OptimizationController {

    private final ClassAllocationOptimizationService allocationService;
    private final WorkoutPlanOptimizationService workoutPlanService;
    private final EquipmentSchedulingOptimizationService equipmentSchedulingService;

    public OptimizationController(ClassAllocationOptimizationService allocationService,
                                  WorkoutPlanOptimizationService workoutPlanService,
                                  EquipmentSchedulingOptimizationService equipmentSchedulingService) {
        this.allocationService = allocationService;
        this.workoutPlanService = workoutPlanService;
        this.equipmentSchedulingService = equipmentSchedulingService;
    }

    /**
     * Allocate members to class slots fairly and optimally.
     * Constraints: class capacity, premium access, trainer max sessions per day, attendance priority.
     */
    @PostMapping("/class-allocation")
    public ResponseEntity<ClassAllocationResult> classAllocation(@RequestBody ClassAllocationRequest request) {
        ClassAllocationResult result = allocationService.allocate(request);
        return ResponseEntity.ok(result);
    }

    /**
     * Generate personalized workout plan: maximize satisfaction subject to
     * budget, max classes, max duration, category diversity.
     */
    @PostMapping("/workout-plan")
    public ResponseEntity<WorkoutPlanResult> workoutPlan(@RequestBody WorkoutPlanRequest request) {
        WorkoutPlanResult result = workoutPlanService.recommend(request);
        return ResponseEntity.ok(result);
    }

    /**
     * Schedule classes into time slots so equipment capacity is not exceeded.
     */
    @PostMapping("/equipment-scheduling")
    public ResponseEntity<EquipmentSchedulingResult> equipmentScheduling(@RequestBody EquipmentSchedulingRequest request) {
        EquipmentSchedulingResult result = equipmentSchedulingService.schedule(request);
        return ResponseEntity.ok(result);
    }
}
