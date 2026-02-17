package com.dijkstrack.drools.service;

import com.dijkstrack.drools.model.Booking;
import com.dijkstrack.drools.model.Member;
import com.dijkstrack.drools.model.GymClass;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.kie.api.runtime.rule.QueryResults;
import org.kie.api.runtime.rule.QueryResultsRow;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Service for executing Drools queries to extract information from working memory.
 * Queries allow you to retrieve data without side effects (no rule firing).
 */
@Service
public class BookingQueryService {

    private final KieContainer kieContainer;

    @Autowired
    public BookingQueryService(KieContainer kieContainer) {
        this.kieContainer = kieContainer;
    }

    /**
     * Find all active bookings for a member
     */
    public List<Booking> findActiveBookingsForMember(String memberId) {
        KieSession kieSession = kieContainer.newKieSession();
        List<Booking> bookings = new ArrayList<>();
        
        try {
            // Insert all bookings into working memory
            // In a real scenario, you'd load these from a database
            // For now, this is a template showing how to use queries
            
            QueryResults results = kieSession.getQueryResults(
                "Find Active Bookings for Member", 
                memberId
            );
            
            for (QueryResultsRow row : results) {
                Booking booking = (Booking) row.get("$booking");
                bookings.add(booking);
            }
            
        } finally {
            kieSession.dispose();
        }
        
        return bookings;
    }

    /**
     * Find all bookings with discounts applied
     */
    public List<Booking> findBookingsWithDiscounts() {
        KieSession kieSession = kieContainer.newKieSession();
        List<Booking> bookings = new ArrayList<>();
        
        try {
            QueryResults results = kieSession.getQueryResults("Find Bookings with Discounts");
            
            for (QueryResultsRow row : results) {
                Booking booking = (Booking) row.get("$booking");
                bookings.add(booking);
            }
            
        } finally {
            kieSession.dispose();
        }
        
        return bookings;
    }

    /**
     * Find members eligible for loyalty discount
     */
    public List<Member> findLoyaltyEligibleMembers() {
        KieSession kieSession = kieContainer.newKieSession();
        List<Member> members = new ArrayList<>();
        
        try {
            QueryResults results = kieSession.getQueryResults("Find Loyalty Eligible Members");
            
            for (QueryResultsRow row : results) {
                Member member = (Member) row.get("$member");
                members.add(member);
            }
            
        } finally {
            kieSession.dispose();
        }
        
        return members;
    }

    /**
     * Find bookings in a date range
     */
    public List<Booking> findBookingsInDateRange(LocalDateTime startDate, LocalDateTime endDate) {
        KieSession kieSession = kieContainer.newKieSession();
        List<Booking> bookings = new ArrayList<>();
        
        try {
            QueryResults results = kieSession.getQueryResults(
                "Find Bookings in Date Range",
                startDate,
                endDate
            );
            
            for (QueryResultsRow row : results) {
                Booking booking = (Booking) row.get("$booking");
                bookings.add(booking);
            }
            
        } finally {
            kieSession.dispose();
        }
        
        return bookings;
    }

    /**
     * Count bookings by status
     */
    public long countBookingsByStatus(Booking.BookingStatus status) {
        KieSession kieSession = kieContainer.newKieSession();
        
        try {
            QueryResults results = kieSession.getQueryResults(
                "Count Bookings by Status",
                status
            );
            
            if (results.size() > 0) {
                QueryResultsRow row = results.iterator().next();
                Number count = (Number) row.get("$count");
                return count != null ? count.longValue() : 0;
            }
            
        } finally {
            kieSession.dispose();
        }
        
        return 0;
    }
}

