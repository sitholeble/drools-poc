package com.dijkstrack.drools.service;

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
        
        try {
            // Insert facts into the session
            kieSession.insert(request);
            kieSession.insert(request.getMember());
            kieSession.insert(request.getGymClass());
            kieSession.insert(request.getBooking());
            
            // Fire all rules
            int rulesFired = kieSession.fireAllRules();
            
            System.out.println("Total rules fired: " + rulesFired);
            
            return request;
        } finally {
            kieSession.dispose();
        }
    }
}


