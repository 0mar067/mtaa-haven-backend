#!/usr/bin/env python3
"""
Create test data for booking and payment testing
"""
from app import app, db
from models import User, Property, UserType, PropertyStatus
from werkzeug.security import generate_password_hash

def create_test_data():
    with app.app_context():
        # Create test users
        landlord = User(
            email="landlord@test.com",
            password_hash=generate_password_hash("password123"),
            first_name="John",
            last_name="Landlord",
            phone="+254700000001",
            user_type=UserType.LANDLORD
        )
        
        tenant = User(
            email="tenant@test.com",
            password_hash=generate_password_hash("password123"),
            first_name="Jane",
            last_name="Tenant",
            phone="+254700000002",
            user_type=UserType.TENANT
        )
        
        db.session.add(landlord)
        db.session.add(tenant)
        db.session.commit()
        
        # Create test property
        property1 = Property(
            title="Downtown Apartment",
            description="Modern 2-bedroom apartment in the city center",
            address="123 Main Street",
            city="Nairobi",
            rent_amount=25000.00,
            bedrooms=2,
            bathrooms=1,
            area_sqft=800,
            type="apartment",
            status=PropertyStatus.AVAILABLE,
            landlord_id=landlord.id
        )
        
        property2 = Property(
            title="Student Hostel Room",
            description="Affordable single room for students",
            address="456 University Road",
            city="Nairobi",
            rent_amount=8000.00,
            bedrooms=1,
            bathrooms=1,
            area_sqft=200,
            type="hostel",
            status=PropertyStatus.AVAILABLE,
            landlord_id=landlord.id
        )
        
        db.session.add(property1)
        db.session.add(property2)
        db.session.commit()
        
        print(f"Created test data:")
        print(f"- Landlord ID: {landlord.id}")
        print(f"- Tenant ID: {tenant.id}")
        print(f"- Property 1 ID: {property1.id}")
        print(f"- Property 2 ID: {property2.id}")

if __name__ == "__main__":
    create_test_data()