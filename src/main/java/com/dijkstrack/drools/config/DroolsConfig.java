package com.dijkstrack.drools.config;

import org.kie.api.KieServices;
import org.kie.api.builder.KieBuilder;
import org.kie.api.builder.KieFileSystem;
import org.kie.api.builder.KieModule;
import org.kie.api.runtime.KieContainer;
import org.kie.internal.io.ResourceFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DroolsConfig {

    private static final String RULES_PATH = "rules/";
    private final KieServices kieServices = KieServices.Factory.get();

    @Bean
    public KieContainer kieContainer() {
        KieFileSystem kieFileSystem = kieServices.newKieFileSystem();
        
        // Load all DRL files from resources/rules directory
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "booking-validation.drl"));
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "pricing-discounts.drl"));
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "booking-confirmation.drl"));
        
        // Class recommendation and matching rules
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "class-recommendation.drl"));
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "difficulty-matching.drl"));
        
        // Time-based and scheduling rules
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "time-based-rules.drl"));
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "scheduling-conflicts.drl"));
        
        // Health, safety, and management rules
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "health-safety-rules.drl"));
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "waitlist-management.drl"));
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "cancellation-policy.drl"));
        kieFileSystem.write(ResourceFactory.newClassPathResource(RULES_PATH + "referral-bonus.drl"));
        
        KieBuilder kieBuilder = kieServices.newKieBuilder(kieFileSystem);
        kieBuilder.buildAll();
        
        KieModule kieModule = kieBuilder.getKieModule();
        return kieServices.newKieContainer(kieModule.getReleaseId());
    }
}


