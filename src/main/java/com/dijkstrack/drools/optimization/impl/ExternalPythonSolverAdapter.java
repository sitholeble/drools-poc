package com.dijkstrack.drools.optimization.impl;

import com.dijkstrack.drools.optimization.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;

import java.io.IOException;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/**
 * Calls Python scripts (CPLEX/Gurobi/PuLP) via subprocess.
 * Scripts read JSON from stdin and write JSON to stdout.
 * Set optimization.python.path to the repo root or scripts directory.
 */
@Slf4j
public class ExternalPythonSolverAdapter implements OptimizationSolverAdapter {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final String pythonPath;
    private final String pythonExecutable;

    public ExternalPythonSolverAdapter(
            @Value("${optimization.python.path:}") String pythonPath,
            @Value("${optimization.python.executable:python3}") String pythonExecutable) {
        this.pythonPath = pythonPath == null || pythonPath.isBlank() ? "." : pythonPath;
        this.pythonExecutable = pythonExecutable == null ? "python3" : pythonExecutable;
    }

    @Override
    public ClassAllocationResult solveClassAllocation(ClassAllocationRequest request) {
        return runScript("ilp_class_allocation.py", request, ClassAllocationResult.class,
                "class_allocation");
    }

    @Override
    public WorkoutPlanResult solveWorkoutPlan(WorkoutPlanRequest request) {
        return runScript("ilp_workout_plan.py", request, WorkoutPlanResult.class,
                "workout_plan");
    }

    @Override
    public EquipmentSchedulingResult solveEquipmentScheduling(EquipmentSchedulingRequest request) {
        return runScript("ilp_equipment_scheduling.py", request, EquipmentSchedulingResult.class,
                "equipment_scheduling");
    }

    @Override
    public String getSolverName() {
        return "External Python (CPLEX/Gurobi/PuLP)";
    }

    private <Req, Res> Res runScript(String scriptName, Req request, Class<Res> resultType,
                                     String fallbackTag) {
        Path script = Path.of(pythonPath).resolve(scriptName);
        if (!script.toFile().exists()) {
            log.warn("Script not found: {} - returning infeasible", script);
            return buildInfeasibleResult(resultType, fallbackTag);
        }
        try {
            ProcessBuilder pb = new ProcessBuilder(
                    pythonExecutable, script.toAbsolutePath().toString())
                    .redirectInput(ProcessBuilder.Redirect.PIPE)
                    .redirectOutput(ProcessBuilder.Redirect.PIPE)
                    .redirectError(ProcessBuilder.Redirect.PIPE);
            Process p = pb.start();
            objectMapper.writeValue(p.getOutputStream(), request);
            p.getOutputStream().close();
            String out = new String(p.getInputStream().readAllBytes());
            p.waitFor(120, TimeUnit.SECONDS);
            if (p.exitValue() != 0) {
                String err = new String(p.getErrorStream().readAllBytes());
                log.error("Script {} failed: {}", scriptName, err);
                return buildInfeasibleResult(resultType, fallbackTag);
            }
            return objectMapper.readValue(out, resultType);
        } catch (IOException | InterruptedException e) {
            log.error("Running script {} failed", scriptName, e);
            return buildInfeasibleResult(resultType, fallbackTag);
        }
    }

    @SuppressWarnings("unchecked")
    private <Res> Res buildInfeasibleResult(Class<Res> resultType, String tag) {
        if (resultType == ClassAllocationResult.class) {
            return (Res) ClassAllocationResult.builder()
                    .feasible(false)
                    .solverUsed(tag + " (script not run)")
                    .build();
        }
        if (resultType == WorkoutPlanResult.class) {
            return (Res) WorkoutPlanResult.builder()
                    .feasible(false)
                    .solverUsed(tag + " (script not run)")
                    .build();
        }
        if (resultType == EquipmentSchedulingResult.class) {
            return (Res) EquipmentSchedulingResult.builder()
                    .feasible(false)
                    .solverUsed(tag + " (script not run)")
                    .build();
        }
        throw new IllegalArgumentException("Unknown result type: " + resultType);
    }
}
