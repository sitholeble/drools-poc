package com.dijkstrack.drools.controller;

import com.dijkstrack.drools.model.Booking;
import com.dijkstrack.drools.model.BookingRequest;
import com.dijkstrack.drools.model.GymClass;
import com.dijkstrack.drools.model.Member;
import com.dijkstrack.drools.service.BookingRulesService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/bookings")
public class BookingController {

    @Autowired
    private BookingRulesService bookingRulesService;

    @PostMapping("/process")
    public ResponseEntity<Map<String, Object>> processBooking(@RequestBody BookingRequestDTO dto) {
        // Create member from DTO
        Member member = createMemberFromDTO(dto);
        
        // Create gym class from DTO
        GymClass gymClass = createGymClassFromDTO(dto);
        
        // Create booking request
        BookingRequest request = new BookingRequest(member, gymClass);
        
        // Process through rules engine
        BookingRequest processedRequest = bookingRulesService.processBookingRequest(request);
        
        // Build response
        Map<String, Object> response = new HashMap<>();
        response.put("bookingId", processedRequest.getBooking().getBookingId());
        response.put("status", processedRequest.getBooking().getStatus());
        response.put("isValid", processedRequest.getValid());
        response.put("validationMessage", processedRequest.getValidationMessage());
        response.put("originalPrice", processedRequest.getBooking().getOriginalPrice());
        response.put("discount", processedRequest.getBooking().getDiscount());
        response.put("finalPrice", processedRequest.getBooking().getFinalPrice());
        response.put("discountReason", processedRequest.getBooking().getDiscountReason());
        response.put("rejectionReason", processedRequest.getBooking().getRejectionReason());
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/test")
    public ResponseEntity<Map<String, Object>> testBooking() {
        // Create a test member
        Member member = new Member();
        member.setId(1L);
        member.setMemberId("M001");
        member.setName("John Doe");
        member.setEmail("john@example.com");
        member.setMembershipType(Member.MembershipType.PREMIUM);
        member.setMembershipStartDate(LocalDate.now().minusMonths(6));
        member.setMembershipEndDate(LocalDate.now().plusMonths(6));
        member.setTotalClassesAttended(25);
        member.setClassesThisMonth(5);
        member.setIsActive(true);
        member.setIsNewMember(false);
        
        // Create a test class
        GymClass gymClass = new GymClass();
        gymClass.setId(1L);
        gymClass.setClassId("C001");
        gymClass.setClassName("HIIT Cardio");
        gymClass.setInstructor("Jane Smith");
        gymClass.setClassDateTime(LocalDateTime.now().plusHours(3));
        gymClass.setMaxCapacity(20);
        gymClass.setCurrentBookings(15);
        gymClass.setCategory(GymClass.ClassCategory.CARDIO);
        gymClass.setDifficulty(GymClass.DifficultyLevel.INTERMEDIATE);
        gymClass.setPrice(25.0);
        gymClass.setRequiresPremium(false);
        gymClass.setIsFull(false);
        
        // Create booking request
        BookingRequest request = new BookingRequest(member, gymClass);
        
        // Process through rules engine
        BookingRequest processedRequest = bookingRulesService.processBookingRequest(request);
        
        // Build response
        Map<String, Object> response = new HashMap<>();
        response.put("member", member.getMemberId() + " - " + member.getName());
        response.put("membershipType", member.getMembershipType());
        response.put("class", gymClass.getClassName());
        response.put("bookingId", processedRequest.getBooking().getBookingId());
        response.put("status", processedRequest.getBooking().getStatus());
        response.put("isValid", processedRequest.getValid());
        response.put("validationMessage", processedRequest.getValidationMessage());
        response.put("originalPrice", processedRequest.getBooking().getOriginalPrice());
        response.put("discount", processedRequest.getBooking().getDiscount());
        response.put("finalPrice", processedRequest.getBooking().getFinalPrice());
        response.put("discountReason", processedRequest.getBooking().getDiscountReason());
        
        return ResponseEntity.ok(response);
    }

    private Member createMemberFromDTO(BookingRequestDTO dto) {
        Member member = new Member();
        member.setMemberId(dto.getMemberId());
        member.setName(dto.getMemberName());
        member.setEmail(dto.getMemberEmail());
        member.setMembershipType(Member.MembershipType.valueOf(dto.getMembershipType()));
        member.setMembershipStartDate(dto.getMembershipStartDate());
        member.setMembershipEndDate(dto.getMembershipEndDate());
        member.setTotalClassesAttended(dto.getTotalClassesAttended());
        member.setClassesThisMonth(dto.getClassesThisMonth());
        member.setIsActive(dto.getIsActive());
        member.setIsNewMember(dto.getIsNewMember());
        return member;
    }

    private GymClass createGymClassFromDTO(BookingRequestDTO dto) {
        GymClass gymClass = new GymClass();
        gymClass.setClassId(dto.getClassId());
        gymClass.setClassName(dto.getClassName());
        gymClass.setInstructor(dto.getInstructor());
        gymClass.setClassDateTime(dto.getClassDateTime());
        gymClass.setMaxCapacity(dto.getMaxCapacity());
        gymClass.setCurrentBookings(dto.getCurrentBookings());
        gymClass.setCategory(GymClass.ClassCategory.valueOf(dto.getCategory()));
        gymClass.setDifficulty(GymClass.DifficultyLevel.valueOf(dto.getDifficulty()));
        gymClass.setPrice(dto.getPrice());
        gymClass.setRequiresPremium(dto.getRequiresPremium());
        gymClass.setIsFull(dto.getIsFull());
        return gymClass;
    }

    // DTO for request body
    public static class BookingRequestDTO {
        private String memberId;
        private String memberName;
        private String memberEmail;
        private String membershipType;
        private LocalDate membershipStartDate;
        private LocalDate membershipEndDate;
        private Integer totalClassesAttended;
        private Integer classesThisMonth;
        private Boolean isActive;
        private Boolean isNewMember;
        private String classId;
        private String className;
        private String instructor;
        private LocalDateTime classDateTime;
        private Integer maxCapacity;
        private Integer currentBookings;
        private String category;
        private String difficulty;
        private Double price;
        private Boolean requiresPremium;
        private Boolean isFull;

        // Getters and setters
        public String getMemberId() { return memberId; }
        public void setMemberId(String memberId) { this.memberId = memberId; }
        public String getMemberName() { return memberName; }
        public void setMemberName(String memberName) { this.memberName = memberName; }
        public String getMemberEmail() { return memberEmail; }
        public void setMemberEmail(String memberEmail) { this.memberEmail = memberEmail; }
        public String getMembershipType() { return membershipType; }
        public void setMembershipType(String membershipType) { this.membershipType = membershipType; }
        public LocalDate getMembershipStartDate() { return membershipStartDate; }
        public void setMembershipStartDate(LocalDate membershipStartDate) { this.membershipStartDate = membershipStartDate; }
        public LocalDate getMembershipEndDate() { return membershipEndDate; }
        public void setMembershipEndDate(LocalDate membershipEndDate) { this.membershipEndDate = membershipEndDate; }
        public Integer getTotalClassesAttended() { return totalClassesAttended; }
        public void setTotalClassesAttended(Integer totalClassesAttended) { this.totalClassesAttended = totalClassesAttended; }
        public Integer getClassesThisMonth() { return classesThisMonth; }
        public void setClassesThisMonth(Integer classesThisMonth) { this.classesThisMonth = classesThisMonth; }
        public Boolean getIsActive() { return isActive; }
        public void setIsActive(Boolean isActive) { this.isActive = isActive; }
        public Boolean getIsNewMember() { return isNewMember; }
        public void setIsNewMember(Boolean isNewMember) { this.isNewMember = isNewMember; }
        public String getClassId() { return classId; }
        public void setClassId(String classId) { this.classId = classId; }
        public String getClassName() { return className; }
        public void setClassName(String className) { this.className = className; }
        public String getInstructor() { return instructor; }
        public void setInstructor(String instructor) { this.instructor = instructor; }
        public LocalDateTime getClassDateTime() { return classDateTime; }
        public void setClassDateTime(LocalDateTime classDateTime) { this.classDateTime = classDateTime; }
        public Integer getMaxCapacity() { return maxCapacity; }
        public void setMaxCapacity(Integer maxCapacity) { this.maxCapacity = maxCapacity; }
        public Integer getCurrentBookings() { return currentBookings; }
        public void setCurrentBookings(Integer currentBookings) { this.currentBookings = currentBookings; }
        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
        public String getDifficulty() { return difficulty; }
        public void setDifficulty(String difficulty) { this.difficulty = difficulty; }
        public Double getPrice() { return price; }
        public void setPrice(Double price) { this.price = price; }
        public Boolean getRequiresPremium() { return requiresPremium; }
        public void setRequiresPremium(Boolean requiresPremium) { this.requiresPremium = requiresPremium; }
        public Boolean getIsFull() { return isFull; }
        public void setIsFull(Boolean isFull) { this.isFull = isFull; }
    }
}


