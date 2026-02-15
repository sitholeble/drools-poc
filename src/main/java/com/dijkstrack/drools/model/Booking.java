package com.dijkstrack.drools.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Booking {
    private Long id;
    private String bookingId;
    private String memberId;
    private String classId;
    private LocalDateTime bookingDateTime;
    private LocalDateTime classDateTime;
    private BookingStatus status;
    private Double originalPrice;
    private Double finalPrice;
    private Double discount;
    private String discountReason;
    private Boolean isWaitlisted;
    private Integer waitlistPosition;
    private String rejectionReason;
    
    public enum BookingStatus {
        PENDING,      // Being processed by rules
        CONFIRMED,   // Successfully booked
        WAITLISTED,  // Added to waitlist
        REJECTED,    // Booking rejected
        CANCELLED    // Member cancelled
    }
    
    public void applyDiscount(Double discountAmount, String reason) {
        this.discount = discountAmount;
        this.discountReason = reason;
        if (this.originalPrice != null && this.discount != null) {
            this.finalPrice = this.originalPrice - this.discount;
        }
    }
    
    public void confirm() {
        this.status = BookingStatus.CONFIRMED;
        this.isWaitlisted = false;
    }
    
    public void reject(String reason) {
        this.status = BookingStatus.REJECTED;
        this.rejectionReason = reason;
    }
    
    public void waitlist(Integer position) {
        this.status = BookingStatus.WAITLISTED;
        this.isWaitlisted = true;
        this.waitlistPosition = position;
    }
}


