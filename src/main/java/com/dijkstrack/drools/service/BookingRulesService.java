package com.dijkstrack.drools.service;

import com.dijkstrack.drools.listener.RuleExecutionListener;
import com.dijkstrack.drools.model.BookingRequest;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class BookingRulesService {

    private final KieContainer kieContainer;

    @Autowired
    public BookingRulesService(KieContainer kieContainer) {
        this.kieContainer = kieContainer;
    }

    public BookingRequest processBookingRequest(BookingRequest request) {
        KieSession kieSession = kieContainer.newKieSession();
        
        // Create and attach rule execution listener for audit trail
        RuleExecutionListener listener = new RuleExecutionListener();
        kieSession.addEventListener(listener);
        
        try {
            // Insert facts into the session
            kieSession.insert(request);
            kieSession.insert(request.getMember());
            kieSession.insert(request.getGymClass());
            kieSession.insert(request.getBooking());
            
            // Fire all rules
            int rulesFired = kieSession.fireAllRules();
            
            // Store execution history in request for audit/debugging
            request.setFiredRules(listener.getFiredRules());
            
            System.out.println("Total rules fired: " + rulesFired);
            System.out.println("Fired rules: " + listener.getFiredRules());
            
            return request;
        } finally {
            kieSession.dispose();
        }
    }
}


