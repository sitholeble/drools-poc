package com.dijkstrack.drools.optimization.impl;

import com.dijkstrack.drools.optimization.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Greedy fallback when no CPLEX/Gurobi or Python is available.
 * Allocates in priority order; respects capacity and trainer limits but does not optimize globally.
 */
public class GreedyFallbackSolverAdapter implements OptimizationSolverAdapter {

    @Override
    public ClassAllocationResult solveClassAllocation(ClassAllocationRequest request) {
        if (request.getSlots() == null || request.getMemberDemands() == null) {
            return ClassAllocationResult.builder().feasible(false).solverUsed("greedy").build();
        }
        Map<String, Integer> capacityRemaining = request.getSlots().stream()
                .collect(Collectors.toMap(AllocationSlot::getClassId, AllocationSlot::getCapacity, (a, b) -> a));
        Map<String, Integer> trainerSessionsUsed = new HashMap<>();
        List<TrainerLimit> trainerLimits = request.getTrainerLimits() != null ? request.getTrainerLimits() : Collections.emptyList();
        for (TrainerLimit tl : trainerLimits) {
            trainerSessionsUsed.put(tl.getTrainerId(), 0);
        }
        Map<String, List<String>> allocationsByMember = new HashMap<>();
        int maxPerMember = request.getMaxClassesPerMember() <= 0 ? 10 : request.getMaxClassesPerMember();

        List<MemberDemand> sorted = new ArrayList<>(request.getMemberDemands());
        sorted.sort(Comparator.comparingDouble(MemberDemand::getPriorityWeight).reversed());

        for (MemberDemand m : sorted) {
            List<String> myAllocations = allocationsByMember.computeIfAbsent(m.getMemberId(), k -> new ArrayList<>());
            if (myAllocations.size() >= maxPerMember) continue;
            Set<String> requested = m.getRequestedClassIds() != null ? m.getRequestedClassIds() : Set.of();
            for (AllocationSlot slot : request.getSlots()) {
                if (!requested.contains(slot.getClassId())) continue;
                if (slot.isRequiresPremium() && !m.isHasPremiumAccess()) continue;
                if (capacityRemaining.getOrDefault(slot.getClassId(), 0) <= 0) continue;
                Integer used = trainerSessionsUsed.get(slot.getTrainerId());
                if (used != null) {
                    int max = trainerLimits.stream()
                            .filter(t -> t.getTrainerId().equals(slot.getTrainerId()))
                            .mapToInt(TrainerLimit::getMaxSessionsPerDay)
                            .findFirst().orElse(Integer.MAX_VALUE);
                    if (used >= max) continue;
                }
                myAllocations.add(slot.getClassId());
                capacityRemaining.merge(slot.getClassId(), -1, Integer::sum);
                trainerSessionsUsed.merge(slot.getTrainerId(), 1, Integer::sum);
                if (myAllocations.size() >= maxPerMember) break;
            }
        }

        Map<String, Integer> allocatedCountByClass = new HashMap<>();
        for (List<String> list : allocationsByMember.values()) {
            for (String c : list) {
                allocatedCountByClass.merge(c, 1, Integer::sum);
            }
        }

        double obj = 0;
        for (MemberDemand m : request.getMemberDemands()) {
            List<String> list = allocationsByMember.get(m.getMemberId());
            if (list != null && m.getPreferenceScoreByClass() != null) {
                for (String c : list) {
                    obj += m.getPreferenceScoreByClass().getOrDefault(c, 1.0);
                }
            } else if (list != null) {
                obj += list.size() * m.getPriorityWeight();
            }
        }

        return ClassAllocationResult.builder()
                .feasible(true)
                .objectiveValue(obj)
                .allocationsByMember(allocationsByMember)
                .allocatedCountByClass(allocatedCountByClass)
                .solverUsed("greedy")
                .solveTimeMs(0)
                .build();
    }

    @Override
    public WorkoutPlanResult solveWorkoutPlan(WorkoutPlanRequest request) {
        if (request.getClassOptions() == null || request.getClassOptions().isEmpty()) {
            return WorkoutPlanResult.builder().feasible(false).solverUsed("greedy").build();
        }
        List<ClassOption> options = new ArrayList<>(request.getClassOptions());
        options.sort((a, b) -> {
            double sa = request.getPreferenceScores() != null ? request.getPreferenceScores().getOrDefault(a.getClassId(), 1.0) : 1.0;
            double sb = request.getPreferenceScores() != null ? request.getPreferenceScores().getOrDefault(b.getClassId(), 1.0) : 1.0;
            return Double.compare(sb, sa);
        });
        List<String> chosen = new ArrayList<>();
        double budget = 0;
        int duration = 0;
        Set<String> categories = new HashSet<>();
        for (ClassOption o : options) {
            if (chosen.size() >= request.getMaxClasses()) break;
            if (budget + o.getPrice() > request.getMaxBudget()) continue;
            if (duration + o.getDurationMinutes() > request.getMaxDurationMinutes()) continue;
            chosen.add(o.getClassId());
            budget += o.getPrice();
            duration += o.getDurationMinutes();
            categories.add(o.getCategory());
        }
        double satisfaction = 0;
        if (request.getPreferenceScores() != null) {
            for (String c : chosen) {
                satisfaction += request.getPreferenceScores().getOrDefault(c, 0.0);
            }
        }
        satisfaction += categories.size() * request.getDiversityBonusPerCategory();

        return WorkoutPlanResult.builder()
                .feasible(true)
                .objectiveValue(satisfaction)
                .recommendedClassIds(chosen)
                .totalPrice(budget)
                .totalDurationMinutes(duration)
                .satisfactionScore(satisfaction)
                .categoriesIncluded(new ArrayList<>(categories))
                .solverUsed("greedy")
                .solveTimeMs(0)
                .build();
    }

    @Override
    public EquipmentSchedulingResult solveEquipmentScheduling(EquipmentSchedulingRequest request) {
        if (request.getSlots() == null || request.getClassRequirements() == null || request.getClassRequirements().isEmpty()) {
            return EquipmentSchedulingResult.builder().feasible(false).solverUsed("greedy").build();
        }
        Map<String, Integer> equipmentAvailable = new HashMap<>(request.getEquipmentTotalUnits() != null ? request.getEquipmentTotalUnits() : Map.of());
        Map<String, String> classToSlot = new HashMap<>();
        Map<String, List<String>> slotToClasses = new HashMap<>();
        for (EquipmentSlot s : request.getSlots()) {
            slotToClasses.put(s.getSlotId(), new ArrayList<>());
        }
        // Per-slot equipment usage: slotId -> (equipmentId -> units used)
        Map<String, Map<String, Integer>> slotEquipmentUsed = new HashMap<>();
        for (EquipmentSlot s : request.getSlots()) {
            slotEquipmentUsed.put(s.getSlotId(), new HashMap<>());
        }
        for (ClassEquipmentRequirement cr : request.getClassRequirements()) {
            Map<String, Integer> need = cr.getEquipmentUnitsRequired() != null ? cr.getEquipmentUnitsRequired() : Map.of();
            boolean placed = false;
            for (EquipmentSlot s : request.getSlots()) {
                boolean fits = true;
                for (Map.Entry<String, Integer> e : need.entrySet()) {
                    int usedInSlot = slotEquipmentUsed.get(s.getSlotId()).getOrDefault(e.getKey(), 0);
                    int total = request.getEquipmentTotalUnits().getOrDefault(e.getKey(), 0);
                    if (usedInSlot + e.getValue() > total) {
                        fits = false;
                        break;
                    }
                }
                if (fits) {
                    classToSlot.put(cr.getClassId(), s.getSlotId());
                    slotToClasses.get(s.getSlotId()).add(cr.getClassId());
                    need.forEach((eqId, units) -> slotEquipmentUsed.get(s.getSlotId()).merge(eqId, units, Integer::sum));
                    placed = true;
                    break;
                }
            }
            if (!placed) {
                return EquipmentSchedulingResult.builder().feasible(false).solverUsed("greedy").build();
            }
        }
        return EquipmentSchedulingResult.builder()
                .feasible(true)
                .classToSlot(classToSlot)
                .slotToClasses(slotToClasses)
                .solverUsed("greedy")
                .solveTimeMs(0)
                .build();
    }

    @Override
    public String getSolverName() {
        return "Greedy (fallback)";
    }
}
