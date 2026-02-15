package com.dijkstrack.drools.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Member {
    private Long id;
    private String memberId;
    private String name;
    private String email;
    private MembershipType membershipType;
    private LocalDate membershipStartDate;
    private LocalDate membershipEndDate;
    private Integer totalClassesAttended;
    private Integer classesThisMonth;
    private Integer membershipDurationDays;
    private Boolean isActive;
    private Boolean isNewMember;
    private List<Booking> bookings = new ArrayList<>();
    private LocalDateTime lastBookingDate;
    
    public enum MembershipType {
        BASIC,        // Limited classes per month
        PREMIUM,      // Unlimited classes
        VIP,          // Unlimited + priority booking
        STUDENT,      // Discounted student rate
        SENIOR,       // Discounted senior rate
        CORPORATE     // Corporate membership
    }
    
    public void addBooking(Booking booking) {
        this.bookings.add(booking);
        this.lastBookingDate = LocalDateTime.now();
    }
    
    public boolean isMembershipValid() {
        if (membershipEndDate == null) {
            return false;
        }
        return LocalDate.now().isBefore(membershipEndDate) || 
               LocalDate.now().isEqual(membershipEndDate);
    }
    
    public int getDaysSinceMembershipStart() {
        if (membershipStartDate == null) {
            return 0;
        }
        return (int) java.time.temporal.ChronoUnit.DAYS.between(membershipStartDate, LocalDate.now());
    }
}


