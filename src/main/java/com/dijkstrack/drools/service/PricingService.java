package com.dijkstrack.drools.service;

import com.dijkstrack.drools.model.BookingRequest;
import com.dijkstrack.drools.model.GymClass;
import com.dijkstrack.drools.model.Member;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.StatelessKieSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Service demonstrating Stateless Sessions - optimized for read-only operations.
 * 
 * Stateless Sessions are:
 * - Faster (no state maintenance)
 * - Thread-safe (can be used concurrently)
 * - Perfect for calculations and validations
 * - No need to dispose (automatically cleaned up)
 */
@Service
public class PricingService {

    private final KieContainer kieContainer;

    @Autowired
    public PricingService(KieContainer kieContainer) {
        this.kieContainer = kieContainer;
    }

    /**
     * Calculate final price for a booking using Stateless Session.
     * Perfect use case: Input → Process → Output (no state needed)
     * 
     * @param member The member making the booking
     * @param gymClass The class being booked
     * @return Final price after all discounts
     */
    public Double calculatePrice(Member member, GymClass gymClass) {
        // Use StatelessKieSession instead of KieSession
        StatelessKieSession kieSession = kieContainer.newStatelessKieSession();
        
        BookingRequest request = new BookingRequest(member, gymClass);
        
        // Execute rules - no state maintained, automatically cleaned up
        kieSession.execute(request);
        
        return request.getBooking().getFinalPrice();
    }

    /**
     * Validate booking eligibility using Stateless Session.
     * Perfect use case: Check if booking is valid (read-only)
     * 
     * @param member The member
     * @param gymClass The class
     * @return true if booking is valid, false otherwise
     */
    public boolean isValidBooking(Member member, GymClass gymClass) {
        StatelessKieSession kieSession = kieContainer.newStatelessKieSession();
        
        BookingRequest request = new BookingRequest(member, gymClass);
        kieSession.execute(request);
        
        return request.getValid() != null && request.getValid();
    }

    /**
     * Get discount amount for a booking using Stateless Session.
     * Perfect use case: Calculate discount (read-only operation)
     * 
     * @param member The member
     * @param gymClass The class
     * @return Discount amount
     */
    public Double getDiscount(Member member, GymClass gymClass) {
        StatelessKieSession kieSession = kieContainer.newStatelessKieSession();
        
        BookingRequest request = new BookingRequest(member, gymClass);
        kieSession.execute(request);
        
        return request.getBooking().getDiscount() != null 
            ? request.getBooking().getDiscount() 
            : 0.0;
    }

    /**
     * Calculate price for multiple bookings (batch processing).
     * Stateless sessions are perfect for batch operations.
     * 
     * @param requests List of booking requests
     * @return List of final prices
     */
    public java.util.List<Double> calculatePricesBatch(java.util.List<BookingRequest> requests) {
        StatelessKieSession kieSession = kieContainer.newStatelessKieSession();
        
        // Execute all requests in batch - thread-safe and efficient
        kieSession.execute(requests);
        
        return requests.stream()
            .map(req -> req.getBooking().getFinalPrice())
            .collect(java.util.stream.Collectors.toList());
    }
}

