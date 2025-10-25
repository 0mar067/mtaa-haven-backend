from faker import Faker
from app import app, db
from models import User, Property, Payment, Issue, UserType, PropertyStatus, PaymentStatus, IssueStatus, IssueType
from decimal import Decimal
import random

fake = Faker()

def seed_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create users
        users = []
        for _ in range(20):
            user = User(
                email=fake.email(),
                password_hash=fake.password(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number(),
                user_type=random.choice(list(UserType))
            )
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        
        # Create properties
        landlords = [u for u in users if u.user_type == UserType.LANDLORD]
        tenants = [u for u in users if u.user_type == UserType.TENANT]
        
        properties = []
        for _ in range(15):
            prop = Property(
                title=fake.catch_phrase(),
                description=fake.text(),
                address=fake.address(),
                city=fake.city(),
                rent_amount=Decimal(str(random.randint(500, 3000))),
                bedrooms=random.randint(1, 4),
                bathrooms=random.randint(1, 3),
                area_sqft=random.randint(500, 2500),
                status=random.choice(list(PropertyStatus)),
                landlord_id=random.choice(landlords).id,
                tenant_id=random.choice(tenants).id if random.choice([True, False]) else None
            )
            properties.append(prop)
            db.session.add(prop)
        
        db.session.commit()
        
        # Create payments
        for _ in range(30):
            payment = Payment(
                amount=Decimal(str(random.randint(500, 3000))),
                payment_date=fake.date_time_this_year(),
                due_date=fake.date_time_this_year(),
                status=random.choice(list(PaymentStatus)),
                payment_method=random.choice(['credit_card', 'bank_transfer', 'cash']),
                transaction_id=fake.uuid4(),
                user_id=random.choice(users).id,
                property_id=random.choice(properties).id
            )
            db.session.add(payment)
        
        # Create issues
        for _ in range(25):
            issue = Issue(
                title=fake.sentence(nb_words=4),
                description=fake.text(),
                issue_type=random.choice(list(IssueType)),
                status=random.choice(list(IssueStatus)),
                priority=random.choice(['low', 'medium', 'high']),
                reporter_id=random.choice(users).id,
                property_id=random.choice(properties).id
            )
            db.session.add(issue)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_data()