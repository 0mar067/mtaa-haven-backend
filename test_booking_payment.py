#!/usr/bin/env python3
"""
Test script for booking and payment endpoints
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"

def test_create_booking():
    """Test creating a new booking"""
    booking_data = {
        "tenant_id": 1,
        "property_id": 1,
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
    print(f"Create Booking Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json().get('booking_id')

def test_get_bookings():
    """Test getting bookings"""
    response = requests.get(f"{BASE_URL}/bookings?user_id=1&user_type=tenant")
    print(f"Get Bookings Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_create_payment():
    """Test creating a new payment"""
    payment_data = {
        "user_id": 1,
        "property_id": 1,
        "amount": 25000.00,
        "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "payment_method": "bank_transfer",
        "notes": "Monthly rent payment"
    }
    
    response = requests.post(f"{BASE_URL}/payments", json=payment_data)
    print(f"Create Payment Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json().get('payment_id')

def test_get_payments():
    """Test getting payments"""
    response = requests.get(f"{BASE_URL}/payments?user_id=1&user_type=tenant")
    print(f"Get Payments Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_confirm_payment(payment_id):
    """Test confirming a payment"""
    response = requests.patch(f"{BASE_URL}/payments/{payment_id}/confirm")
    print(f"Confirm Payment Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    print("Testing Booking & Payment Endpoints")
    print("=" * 50)
    
    # Test booking creation
    print("\n1. Testing Booking Creation:")
    booking_id = test_create_booking()
    
    # Test getting bookings
    print("\n2. Testing Get Bookings:")
    test_get_bookings()
    
    # Test payment creation
    print("\n3. Testing Payment Creation:")
    payment_id = test_create_payment()
    
    # Test getting payments
    print("\n4. Testing Get Payments:")
    test_get_payments()
    
    # Test payment confirmation
    if payment_id:
        print(f"\n5. Testing Payment Confirmation (ID: {payment_id}):")
        test_confirm_payment(payment_id)