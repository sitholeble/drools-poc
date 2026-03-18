package com.dijkstrack.drools.config;

import com.dijkstrack.drools.optimization.OptimizationSolverAdapter;
import com.dijkstrack.drools.optimization.impl.ExternalPythonSolverAdapter;
import com.dijkstrack.drools.optimization.impl.GreedyFallbackSolverAdapter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

/**
 * Configures which ILP solver adapter to use: "greedy" for in-JVM fallback,
 * otherwise external Python (CPLEX/Gurobi/PuLP) scripts.
 */
@Configuration
public class OptimizationConfig {

    @Bean
    @Primary
    public OptimizationSolverAdapter optimizationSolverAdapter(
            @Value("${optimization.solver:python}") String solver,
            @Value("${optimization.python.path:}") String pythonPath,
            @Value("${optimization.python.executable:python3}") String pythonExecutable) {
        if ("greedy".equalsIgnoreCase(solver)) {
            return new GreedyFallbackSolverAdapter();
        }
        return new ExternalPythonSolverAdapter(pythonPath, pythonExecutable);
    }
}
