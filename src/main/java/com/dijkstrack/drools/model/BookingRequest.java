package com.dijkstrack.drools.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Request object for processing bookings through Drools rules engine.
 * Contains member and class information for rule evaluation.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BookingRequest {
    private Member member;
    private GymClass gymClass;
    private Booking booking;
    private LocalDateTime requestDateTime;
    private String validationMessage;
    private Boolean isValid;
    private List<String> firedRules; // Track which rules fired during execution
    
    public BookingRequest(Member member, GymClass gymClass) {
        this.member = member;
        this.gymClass = gymClass;
        this.requestDateTime = LocalDateTime.now();
        this.booking = new Booking();
        this.booking.setMemberId(member.getMemberId());
        this.booking.setClassId(gymClass.getClassId());
        this.booking.setClassDateTime(gymClass.getClassDateTime());
        this.booking.setOriginalPrice(gymClass.getPrice());
        this.booking.setStatus(Booking.BookingStatus.PENDING);
        this.isValid = true;
    }
}


