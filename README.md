# Gym Recommendation System - Drools POC

A comprehensive gym class booking and recommendation system built with **Drools (JBoss Rules Engine)** that implements intelligent business rules for class bookings, personalized recommendations, dynamic pricing, and member management.

## Overview

This system uses Drools to manage complex business logic through declarative rules, making it easy to maintain and extend business policies without code changes. Rules are organized into 11 DRL files covering validation, pricing, recommendations, safety, scheduling, and more.

## Key Features

### **Booking Management**
- Membership validation and expiration checks
- Capacity management and waitlist handling
- Duplicate booking prevention
- Scheduling conflict detection

### **Dynamic Pricing & Discounts**
- **VIP Members**: 20% discount + free classes
- **Students/Seniors**: 15% discount
- **New Members**: 10% discount (first 30 days)
- **Loyalty Rewards**: 5% discount (50+ classes)
- **Time-Based**: Off-peak discounts, early bird bonuses, last-minute surcharges

### **Personalized Recommendations**
- Category-based suggestions (Cardio, Strength, Flexibility, etc.)
- Difficulty progression guidance (Beginner → Intermediate → Advanced)
- Time and instructor preference matching
- Availability-based recommendations

### **Safety & Health Rules**
- Age restrictions for high-intensity classes
- Medical clearance requirements
- Injury recovery recommendations
- Rest day enforcement
- Senior member safety guidelines

### **Time-Based Rules**
- **Off-Peak Discount**: 10% (before 9 AM or after 7 PM weekdays)
- **Early Bird**: 15% discount (book 7+ days in advance)
- **Last Minute**: 20% surcharge (< 4 hours before class)
- **Weekend Premium**: 15% surcharge
- **Morning Bonus**: 5% discount (6-8 AM)

### **Scheduling & Limits**
- Maximum 3 classes per day (5 for VIP members)
- 30-minute minimum gap between classes
- No double booking within 1 hour
- Past class booking prevention

### **Waitlist Management**
- Automatic waitlist when classes are full
- VIP/Premium priority access
- Auto-confirmation when spots open
- Maximum 3 active waitlists per member

### **Cancellation Policy**
- **24+ hours**: Full refund
- **12-24 hours**: 50% refund
- **< 12 hours**: No refund
- **VIP**: Extended window (up to 2 hours before)
- No-show penalties and frequent cancellation fees

### **Referral Program**
- 5% discount per referral (max 20%)
- Milestone bonus: 10% for 5+ referrals
- Automatic credit for referrers

## Rule Categories

The system includes **50+ business rules** organized into 11 categories:

1. **Booking Validation** (`booking-validation.drl`) - 6 rules
2. **Pricing & Discounts** (`pricing-discounts.drl`) - 6 rules
3. **Booking Confirmation** (`booking-confirmation.drl`) - 2 rules
4. **Class Recommendations** (`class-recommendation.drl`) - 8 rules
5. **Difficulty Matching** (`difficulty-matching.drl`) - 5 rules
6. **Time-Based Rules** (`time-based-rules.drl`) - 6 rules
7. **Health & Safety** (`health-safety-rules.drl`) - 8 rules
8. **Scheduling Conflicts** (`scheduling-conflicts.drl`) - 6 rules
9. **Waitlist Management** (`waitlist-management.drl`) - 6 rules
10. **Cancellation Policy** (`cancellation-policy.drl`) - 7 rules
11. **Referral Bonus** (`referral-bonus.drl`) - 3 rules

## Technology Stack

- **Java** - Spring Boot application
- **Drools** - Business Rules Management System (BRMS)
- **Maven** - Dependency management
- **Lombok** - Boilerplate code reduction

## Project Structure

```
src/main/
├── java/com/dijkstrack/drools/
│   ├── config/
│   │   └── DroolsConfig.java          # Drools configuration
│   ├── controller/
│   │   └── BookingController.java     # REST API endpoints
│   ├── model/
│   │   ├── Booking.java               # Booking entity
│   │   ├── BookingRequest.java        # Request wrapper
│   │   ├── GymClass.java              # Class entity
│   │   └── Member.java                # Member entity
│   └── service/
│       └── BookingRulesService.java   # Rules execution service
└── resources/
    └── rules/                         # DRL rule files
        ├── booking-validation.drl
        ├── pricing-discounts.drl
        ├── booking-confirmation.drl
        ├── class-recommendation.drl
        ├── difficulty-matching.drl
        ├── time-based-rules.drl
        ├── health-safety-rules.drl
        ├── scheduling-conflicts.drl
        ├── waitlist-management.drl
        ├── cancellation-policy.drl
        └── referral-bonus.drl
```

## Getting Started

### Prerequisites
- Java 8 or higher
- Maven 3.6+

### Running the Application

```bash
# Build the project
mvn clean install

# Run the application
mvn spring-boot:run
```

### Example API Usage

```bash
# Create a booking request
POST /api/bookings
{
  "member": {
    "memberId": "M001",
    "membershipType": "PREMIUM",
    "totalClassesAttended": 25
  },
  "gymClass": {
    "classId": "C001",
    "className": "Morning Yoga",
    "price": 20.0,
    "difficulty": "BEGINNER"
  }
}
```

## Rule Execution Order

Rules execute based on **salience** (priority):
- **100**: Critical validations (membership, safety, conflicts)
- **90-95**: Important validations
- **80-85**: Business logic restrictions
- **70-75**: Member-specific rules
- **60-65**: Recommendations
- **50-55**: Discounts and pricing
- **40-45**: Waitlist and cancellations
- **30-35**: Logging and information

## Membership Types

- **BASIC**: Limited to 8 classes/month
- **PREMIUM**: Unlimited classes, free classes, priority waitlist
- **VIP**: Unlimited classes, 20% discount, priority booking, extended cancellation
- **STUDENT**: 15% discount
- **SENIOR**: 15% discount
- **CORPORATE**: Corporate membership benefits

## Key Business Rules Highlights

**Validation**: Membership checks, capacity limits, duplicate prevention  
**Pricing**: Dynamic discounts based on membership, time, and loyalty  
**Recommendations**: Personalized class suggestions based on history and preferences  
**Safety**: Age restrictions, medical checks, injury recovery guidance  
**Scheduling**: Conflict prevention, daily limits, time gaps  
**Waitlist**: Automatic management with priority for premium members  
**Cancellation**: Tiered refund policy with VIP benefits  
**Referrals**: Incentive program with milestone rewards  

## Extending the System

To add new rules:

1. Create a new `.drl` file in `src/main/resources/rules/`
2. Add it to `DroolsConfig.java`
3. Follow existing patterns for imports and structure
4. Set appropriate salience values
5. Update documentation

## Documentation

For detailed information about all business rules, see [BUSINESS_RULES_DOCUMENTATION.md](BUSINESS_RULES_DOCUMENTATION.md)

## Best Practices

- Separation of concerns (rules organized by function)
- Salience management for execution order
- Comprehensive validation layers
- Safety-first approach
- Flexible, dynamic pricing
- Fair access with loyalty rewards

## Testing

Recommended testing approach:
- Test each rule category independently
- Test rule interactions (e.g., discount stacking)
- Test edge cases and boundary conditions
- Test with different member types
- Verify salience ordering

## License

This is a proof-of-concept project for demonstrating Drools business rules implementation.

