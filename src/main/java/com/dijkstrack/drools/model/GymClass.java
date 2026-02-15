package com.dijkstrack.drools.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class GymClass {
    private Long id;
    private String classId;
    private String className;
    private String instructor;
    private LocalDateTime classDateTime;
    private Integer maxCapacity;
    private Integer currentBookings;
    private ClassCategory category;
    private DifficultyLevel difficulty;
    private Double price;
    private Boolean requiresPremium;
    private Boolean isFull;
    private List<Booking> bookings = new ArrayList<>();
    
    public enum ClassCategory {
        CARDIO,      // Running, HIIT, Cycling
        STRENGTH,    // Weight training, Body pump
        FLEXIBILITY, // Yoga, Pilates, Stretching
        SPORTS,      // Boxing, Martial arts
        MIND_BODY    // Meditation, Mindfulness
    }
    
    public enum DifficultyLevel {
        BEGINNER, INTERMEDIATE, ADVANCED, ALL_LEVELS
    }
    
    public void addBooking(Booking booking) {
        this.bookings.add(booking);
        this.currentBookings = (this.currentBookings == null ? 0 : this.currentBookings) + 1;
        if (this.currentBookings >= this.maxCapacity) {
            this.isFull = true;
        }
    }
    
    public boolean hasSpace() {
        return currentBookings < maxCapacity;
    }
    
    public int getAvailableSpots() {
        return maxCapacity - (currentBookings == null ? 0 : currentBookings);
    }
}


