from database import db
from app import app  # make sure this imports your Flask app
from models import User, Property, UserType, PropertyStatus
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        print("🌱 Seeding users and properties...")

        # ---------------- USERS ----------------
        landlord1 = User(
            email="landlord1@example.com",
            password_hash=generate_password_hash("password123"),
            first_name="James",
            last_name="Mwangi",
            phone="+254700111222",
            user_type=UserType.LANDLORD
        )

        landlord2 = User(
            email="landlord2@example.com",
            password_hash=generate_password_hash("password123"),
            first_name="Alice",
            last_name="Njeri",
            phone="+254711222333",
            user_type=UserType.LANDLORD
        )

        tenant1 = User(
            email="tenant1@example.com",
            password_hash=generate_password_hash("password123"),
            first_name="Brian",
            last_name="Otieno",
            phone="+254722333444",
            user_type=UserType.TENANT
        )

        tenant2 = User(
            email="tenant2@example.com",
            password_hash=generate_password_hash("password123"),
            first_name="Mary",
            last_name="Wambui",
            phone="+254733444555",
            user_type=UserType.TENANT
        )

        db.session.add_all([landlord1, landlord2, tenant1, tenant2])
        db.session.commit()

        print("✅ Users seeded successfully!")

        # ---------------- PROPERTIES ----------------
        property1 = Property(
            title="Modern 2-Bedroom Apartment",
            description="Spacious apartment with a beautiful city view and secure parking.",
            address="123 Riverside Drive",
            city="Nairobi",
            rent_amount=55000.00,
            bedrooms=2,
            bathrooms=2,
            area_sqft=950,
            status=PropertyStatus.AVAILABLE,
            landlord_id=landlord1.id
        )

        property2 = Property(
            title="Cozy Studio Apartment",
            description="Perfect for young professionals. Fully furnished with Wi-Fi.",
            address="456 Westlands Lane",
            city="Nairobi",
            rent_amount=35000.00,
            bedrooms=1,
            bathrooms=1,
            area_sqft=500,
            status=PropertyStatus.OCCUPIED,
            landlord_id=landlord2.id,
            tenant_id=tenant1.id
        )

        property3 = Property(
            title="Luxury Villa with Garden",
            description="5-bedroom villa featuring a pool, garden, and modern finishes.",
            address="789 Karen Avenue",
            city="Nairobi",
            rent_amount=150000.00,
            bedrooms=5,
            bathrooms=4,
            area_sqft=3500,
            status=PropertyStatus.AVAILABLE,
            landlord_id=landlord2.id
        )

        db.session.add_all([property1, property2, property3])
        db.session.commit()

        print("✅ Properties seeded successfully!")
        print("🎉 Seeding completed without dropping any tables.")

if __name__ == "__main__":
    seed_data()
