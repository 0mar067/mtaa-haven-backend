# Booking & Payment API Documentation

## Overview
This document describes the booking and payment endpoints that maintain data integrity and ensure smooth transactions in the Mtaa Haven property management system.

## Features Implemented

### ✅ Booking Management
- **POST /api/bookings** - Create new bookings with validation
- **GET /api/bookings** - Retrieve bookings by user/landlord
- Property availability validation
- Duplicate booking prevention (overlapping dates)

### ✅ Payment Management  
- **POST /api/payments** - Create payment records
- **GET /api/payments** - Retrieve payments by user/landlord
- **GET /api/payments/<id>** - Get specific payment details
- **PATCH /api/payments/<id>/confirm** - Confirm payment and update property status

### ✅ Data Relationships
- Booking → Payment → Property linking maintained
- Property status updates on payment confirmation
- Booking status updates on payment confirmation

## API Endpoints

### Bookings

#### Create Booking
```http
POST /api/bookings
Content-Type: application/json

{
  "tenant_id": 2,
  "property_id": 1,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z"
}
```

**Validations:**
- Property must exist and be available
- No overlapping bookings for the same property
- Valid date format required

**Response:**
```json
{
  "message": "Booking created successfully",
  "booking_id": 1,
  "booking": {
    "id": 1,
    "tenant_id": 2,
    "property_id": 1,
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59",
    "status": "pending"
  }
}
```

#### Get Bookings
```http
GET /api/bookings?user_id=2&user_type=tenant
GET /api/bookings?user_id=1&user_type=landlord
```

### Payments

#### Create Payment
```http
POST /api/payments
Content-Type: application/json

{
  "user_id": 2,
  "property_id": 1,
  "amount": 25000.00,
  "due_date": "2024-01-31T23:59:59Z",
  "payment_method": "bank_transfer",
  "notes": "Monthly rent payment"
}
```

**Response:**
```json
{
  "message": "Payment created successfully",
  "payment_id": 1,
  "payment": {
    "id": 1,
    "amount": "25000.00",
    "status": "pending",
    "due_date": "2024-01-31T23:59:59",
    "user_id": 2,
    "property_id": 1
  }
}
```

#### Get Payments
```http
GET /api/payments?user_id=2&user_type=tenant
GET /api/payments?user_id=1&user_type=landlord
```

#### Get Specific Payment
```http
GET /api/payments/1
```

#### Confirm Payment
```http
PATCH /api/payments/1/confirm
```

**Response:**
```json
{
  "message": "Payment confirmed and property status updated",
  "payment_status": "completed",
  "property_status": "occupied"
}
```

## Business Logic

### Property Status Updates
When a payment is confirmed:
1. Payment status → `completed`
2. Property status → `occupied` (if previously available)
3. Property tenant_id → payment user_id
4. Related booking status → `confirmed`

### Validation Checks
1. **Property Availability**: Only available properties can be booked
2. **Duplicate Prevention**: No overlapping bookings for same property
3. **Data Integrity**: All foreign keys validated before creation
4. **Date Validation**: Proper ISO format required for dates

### Error Handling
- **400**: Missing required fields, validation errors
- **404**: Property/user not found
- **500**: Server errors with rollback

## Testing

Run the test script to verify functionality:
```bash
python test_booking_payment.py
```

Create test data:
```bash
python create_test_data.py
```

## Database Schema

### Relationships
```
User (1) ←→ (N) Booking ←→ (1) Property
User (1) ←→ (N) Payment ←→ (1) Property
Booking ←→ Payment (via user_id + property_id)
```

### Status Enums
- **BookingStatus**: pending, confirmed, cancelled
- **PaymentStatus**: pending, completed, failed  
- **PropertyStatus**: available, occupied, maintenance

## Security Considerations
- Input validation on all endpoints
- SQL injection prevention via SQLAlchemy ORM
- Transaction rollback on errors
- Proper error messages without sensitive data exposure