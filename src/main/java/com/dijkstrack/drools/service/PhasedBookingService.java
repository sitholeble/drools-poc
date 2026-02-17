package com.dijkstrack.drools.service;

import com.dijkstrack.drools.listener.RuleExecutionListener;
import com.dijkstrack.drools.model.BookingRequest;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Service demonstrating Agenda Groups - phased rule execution.
 * Rules are organized into phases: Validation → Pricing → Confirmation
 */
@Service
public class PhasedBookingService {

    private final KieContainer kieContainer;

    @Autowired
    public PhasedBookingService(KieContainer kieContainer) {
        this.kieContainer = kieContainer;
    }

    /**
     * Process booking request using phased execution with Agenda Groups.
     * 
     * Phase 1: VALIDATION - Check if booking is valid
     * Phase 2: PRICING - Apply discounts (only if valid)
     * Phase 3: CONFIRMATION - Confirm booking (only if valid)
     */
    public BookingRequest processBookingWithPhases(BookingRequest request) {
        KieSession kieSession = kieContainer.newKieSession();
        
        // Create and attach rule execution listener
        RuleExecutionListener listener = new RuleExecutionListener();
        kieSession.addEventListener(listener);
        
        try {
            // Insert facts into the session
            kieSession.insert(request);
            kieSession.insert(request.getMember());
            kieSession.insert(request.getGymClass());
            kieSession.insert(request.getBooking());
            
            System.out.println("\n========== PHASED BOOKING PROCESSING ==========");
            
            // ============================================
            // PHASE 1: VALIDATION
            // ============================================
            System.out.println("\n[PHASE 1] Running VALIDATION rules...");
            kieSession.getAgenda().getAgendaGroup("validation").setFocus();
            int validationRulesFired = kieSession.fireAllRules();
            System.out.println("Validation rules fired: " + validationRulesFired);
            
            if (!request.getValid()) {
                System.out.println("Validation failed: " + request.getValidationMessage());
                System.out.println("Skipping pricing and confirmation phases.");
                request.setFiredRules(listener.getFiredRules());
                return request;
            }
            
            System.out.println("Validation passed!");
            
            // ============================================
            // PHASE 2: PRICING
            // ============================================
            System.out.println("\n[PHASE 2] Running PRICING rules...");
            kieSession.getAgenda().getAgendaGroup("pricing").setFocus();
            int pricingRulesFired = kieSession.fireAllRules();
            System.out.println("Pricing rules fired: " + pricingRulesFired);
            System.out.println("Original Price: $" + request.getBooking().getOriginalPrice());
            System.out.println("Discount: $" + (request.getBooking().getDiscount() != null ? request.getBooking().getDiscount() : 0));
            System.out.println("Final Price: $" + request.getBooking().getFinalPrice());
            
            // ============================================
            // PHASE 3: CONFIRMATION
            // ============================================
            System.out.println("\n[PHASE 3] Running CONFIRMATION rules...");
            kieSession.getAgenda().getAgendaGroup("confirmation").setFocus();
            int confirmationRulesFired = kieSession.fireAllRules();
            System.out.println("Confirmation rules fired: " + confirmationRulesFired);
            System.out.println("Booking Status: " + request.getBooking().getStatus());
            
            System.out.println("\n========== PROCESSING COMPLETE ==========");
            System.out.println("Total rules fired: " + (validationRulesFired + pricingRulesFired + confirmationRulesFired));
            
            // Store execution history
            request.setFiredRules(listener.getFiredRules());
            
            return request;
        } finally {
            kieSession.dispose();
        }
    }
}

