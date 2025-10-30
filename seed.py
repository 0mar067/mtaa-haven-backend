from database import db
from app import app  # make sure this imports your Flask app
from models import User, Property, Payment, Issue, Notification, Booking, PropertyImage, UserType, PropertyStatus, PaymentStatus, IssueStatus, IssueType, NotificationType, BookingStatus
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

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

        # ---------------- PAYMENTS ----------------
        payment1 = Payment(
            amount=55000.00,
            payment_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            status=PaymentStatus.COMPLETED,
            payment_method="M-Pesa",
            transaction_id="TXN123456789",
            notes="Monthly rent payment",
            user_id=tenant1.id,
            property_id=property2.id
        )

        payment2 = Payment(
            amount=35000.00,
            due_date=datetime.utcnow() + timedelta(days=15),
            status=PaymentStatus.PENDING,
            user_id=tenant1.id,
            property_id=property2.id
        )

        payment3 = Payment(
            amount=150000.00,
            due_date=datetime.utcnow() + timedelta(days=7),
            status=PaymentStatus.PENDING,
            user_id=tenant2.id,
            property_id=property3.id
        )

        db.session.add_all([payment1, payment2, payment3])
        db.session.commit()

        print("✅ Payments seeded successfully!")

        # ---------------- ISSUES ----------------
        issue1 = Issue(
            title="Leaky Faucet in Kitchen",
            description="The kitchen faucet has been leaking for the past week. Needs immediate repair.",
            issue_type=IssueType.MAINTENANCE,
            status=IssueStatus.OPEN,
            priority="high",
            reporter_id=tenant1.id,
            property_id=property2.id
        )

        issue2 = Issue(
            title="Dispute Over Rent Increase",
            description="Landlord increased rent without proper notice. This is unfair.",
            issue_type=IssueType.DISPUTE,
            status=IssueStatus.IN_PROGRESS,
            priority="medium",
            reporter_id=tenant1.id,
            property_id=property2.id
        )

        issue3 = Issue(
            title="Broken Window in Bedroom",
            description="The bedroom window won't close properly. It's letting in cold air.",
            issue_type=IssueType.MAINTENANCE,
            status=IssueStatus.RESOLVED,
            priority="medium",
            reporter_id=tenant2.id,
            property_id=property3.id,
            resolved_at=datetime.utcnow()
        )

        db.session.add_all([issue1, issue2, issue3])
        db.session.commit()

        print("✅ Issues seeded successfully!")

        # ---------------- NOTIFICATIONS ----------------
        notification1 = Notification(
            title="Rent Reminder",
            message="Your rent payment of KES 55,000 is due in 3 days.",
            notification_type=NotificationType.RENT_REMINDER,
            is_read=False,
            user_id=tenant1.id,
            property_id=property2.id
        )

        notification2 = Notification(
            title="Payment Due",
            message="Your payment for Property ID 3 is overdue. Please settle immediately.",
            notification_type=NotificationType.PAYMENT_DUE,
            is_read=False,
            user_id=tenant2.id,
            property_id=property3.id
        )

        notification3 = Notification(
            title="Welcome to Mtaa Haven",
            message="Thank you for joining our platform. We're excited to help you find your perfect home!",
            notification_type=NotificationType.GENERAL,
            is_read=True,
            user_id=landlord1.id
        )

        db.session.add_all([notification1, notification2, notification3])
        db.session.commit()

        print("✅ Notifications seeded successfully!")

        # ---------------- BOOKINGS ----------------
        booking1 = Booking(
            tenant_id=tenant1.id,
            property_id=property1.id,
            start_date=datetime.utcnow() + timedelta(days=30),
            end_date=datetime.utcnow() + timedelta(days=365),
            status=BookingStatus.CONFIRMED
        )

        booking2 = Booking(
            tenant_id=tenant2.id,
            property_id=property3.id,
            start_date=datetime.utcnow() + timedelta(days=60),
            end_date=datetime.utcnow() + timedelta(days=730),
            status=BookingStatus.PENDING
        )

        booking3 = Booking(
            tenant_id=tenant1.id,
            property_id=property3.id,
            start_date=datetime.utcnow() + timedelta(days=14),
            end_date=datetime.utcnow() + timedelta(days=180),
            status=BookingStatus.CANCELLED
        )

        db.session.add_all([booking1, booking2, booking3])
        db.session.commit()

        print("✅ Bookings seeded successfully!")

        # ---------------- PROPERTY IMAGES ----------------
        image1 = PropertyImage(
            property_id=property1.id,
            image_url="https://res.cloudinary.com/demo/image/upload/v1234567890/apartment1_main.jpg",
            thumbnail_url="https://res.cloudinary.com/demo/image/upload/w_200,h_150,c_fill/v1234567890/apartment1_main.jpg",
            public_id="apartment1_main",
            is_primary=True,
            display_order=1
        )

        image2 = PropertyImage(
            property_id=property1.id,
            image_url="https://res.cloudinary.com/demo/image/upload/v1234567890/apartment1_bedroom.jpg",
            thumbnail_url="https://res.cloudinary.com/demo/image/upload/w_200,h_150,c_fill/v1234567890/apartment1_bedroom.jpg",
            public_id="apartment1_bedroom",
            is_primary=False,
            display_order=2
        )

        image3 = PropertyImage(
            property_id=property2.id,
            image_url="https://res.cloudinary.com/demo/image/upload/v1234567890/studio1_main.jpg",
            thumbnail_url="https://res.cloudinary.com/demo/image/upload/w_200,h_150,c_fill/v1234567890/studio1_main.jpg",
            public_id="studio1_main",
            is_primary=True,
            display_order=1
        )

        db.session.add_all([image1, image2, image3])
        db.session.commit()

        print("✅ Property Images seeded successfully!")
        print("🎉 Seeding completed without dropping any tables.")

if __name__ == "__main__":
    seed_data()
