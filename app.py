from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_mail import Mail, Message
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, Property, Payment, Issue, Notification
from routes import api
from models import User, Property, Payment, Issue, UserType, PropertyStatus, PaymentStatus, IssueStatus, IssueType, Booking, BookingStatus, NotificationType
from decimal import Decimal
from flasgger import Swagger
import schedule
import time
import threading
import logging
from flask_cors import CORS
import cloudinary
from cloudinary.uploader import upload, destroy
from cloudinary.utils import cloudinary_url
from flask_jwt_extended import create_access_token, JWTManager  


app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'sqlite:///{os.path.join(basedir, "mtaa_heaven.db")}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'  # In production, use environment variable

# Email configuration (mock for now)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with actual email
app.config['MAIL_PASSWORD'] = 'your-password'  # Replace with actual password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'your-cloud-name'),
    api_key=os.getenv('CLOUDINARY_API_KEY', 'your-api-key'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'your-api-secret')
)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)
jwt = JWTManager(app)
swagger = Swagger(app)

CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5174", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
# Register blueprints
# app.register_blueprint(api, url_prefix='/api')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
      return jsonify({'error': 'No input data provided'}), 400
    
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    user_type = data.get('user_type')
    
    password_hash = generate_password_hash(password)
    
    new_user = User(first_name=first_name,last_name=last_name,email=email,password_hash=password_hash,phone=phone,user_type=user_type)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user_id': new_user.id}), 201
  
@app.route('/api/login', methods=['POST'])
def login():
  data = request.get_json()
  email = data.get('email')
  password = data.get('password')
  
  if not email or not password:
    return jsonify({'error': 'Email and password are required'}), 400
  
  user = User.query.filter_by(email=email).first()
  if not user or not check_password_hash(user.password_hash, password):
    return jsonify({'error': 'Invalid email or password'}), 401
  
  token = create_access_token(identity=user.id) 
  return jsonify({'message': 'Login successful','token': token,'user': user.to_dict()}), 200

def send_rent_reminders():
    """Background task to send rent payment reminders"""
    with app.app_context():
        try:
            logging.info("Running rent reminder task...")

            # Get all tenants with active bookings
            active_bookings = Booking.query.filter_by(status=BookingStatus.CONFIRMED).all()

            reminder_count = 0
            for booking in active_bookings:
                tenant = User.query.get(booking.tenant_id)
                property_obj = Property.query.get(booking.property_id)

                if not tenant or not property_obj:
                    continue

                # Check if rent is due soon (within 3 days)
                today = datetime.utcnow().date()
                rent_due_date = booking.end_date.date()

                if rent_due_date <= today + timedelta(days=3) and rent_due_date >= today:
                    # Check if reminder already sent recently (avoid spam)
                    recent_reminder = Notification.query.filter_by(
                        user_id=tenant.id,
                        property_id=property_obj.id,
                        notification_type=NotificationType.RENT_REMINDER
                    ).filter(
                        Notification.created_at >= datetime.utcnow() - timedelta(days=1)
                    ).first()

                    if not recent_reminder:
                        # Create rent reminder notification
                        reminder = Notification(
                            title=f'Rent Due Reminder - {property_obj.title}',
                            message=f'Your rent payment of KES {property_obj.rent_amount} for {property_obj.title} is due on {rent_due_date.strftime("%B %d, %Y")}. Please make payment to avoid late fees.',
                            notification_type=NotificationType.RENT_REMINDER,
                            user_id=tenant.id,
                            property_id=property_obj.id
                        )

                        db.session.add(reminder)
                        db.session.commit()

                        # Mock email sending
                        try:
                            if app.config.get('TESTING'):
                                logging.info(f"Mock rent reminder email sent to {tenant.email}: {reminder.title}")
                            else:
                                msg = Message(reminder.title,
                                            sender=app.config['MAIL_DEFAULT_SENDER'],
                                            recipients=[tenant.email])
                                msg.body = reminder.message
                                mail.send(msg)
                                logging.info(f"Rent reminder email sent to {tenant.email}: {reminder.title}")
                        except Exception as e:
                            logging.error(f"Failed to send rent reminder email to {tenant.email}: {str(e)}")

                        reminder_count += 1

            logging.info(f"Rent reminder task completed. Sent {reminder_count} reminders.")

        except Exception as e:
            logging.error(f"Error in rent reminder task: {str(e)}")

def run_scheduler():
    """Run the background scheduler"""
    # Schedule rent reminders to run daily at 9 AM
    schedule.every().day.at("09:00").do(send_rent_reminders)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Start background scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/')
def index():
    """
    Root endpoint to check if the backend is working.
    ---
    responses:
      200:
        description: Backend is working
        schema:
          type: string
    """
    return "Backend is working!"


@app.route('/api/test', methods=['GET'])
def test():
    """
    Test endpoint for API functionality.
    ---
    responses:
      200:
        description: API is working
        schema:
          type: object
          properties:
            message:
              type: string
              example: "API is working"
    """
    return jsonify({'message': 'API is working'})


@app.route('/api/properties', methods=['GET'])
def get_properties():
    properties = Property.query.all()

    if not properties:
        return jsonify({'message': 'No properties found'}), 404
    return jsonify({'sucesss': True, 'properties': [prop.to_dict(only=('title',"description", "rent_amount","address", "city","bedrooms","bathrooms","area_sqft", "status")) for prop in properties]})

@app.route('/api/properties/<int:property_id>', methods=['GET'])
def get_property(property_id):
    p = Property.query.get(property_id)

    if not p:
        return jsonify({'message': 'Property not found'}), 404
    return jsonify({'sucesss': True, 'property': p.to_dict(only=('title',"description", "rent_amount","address", "city","bedrooms","bathrooms","area_sqft", "status"))})


# Booking endpoints
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    
    if not data or not all(k in data for k in ['tenant_id', 'property_id', 'start_date', 'end_date']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Check if property exists and is available
        property_obj = Property.query.get(data['property_id'])
        if not property_obj:
            return jsonify({'error': 'Property not found'}), 404
        
        if property_obj.status != PropertyStatus.AVAILABLE:
            return jsonify({'error': 'Property is not available'}), 400
        
        # Check for duplicate bookings (overlapping dates)
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        existing_booking = Booking.query.filter(
            Booking.property_id == data['property_id'],
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.start_date < end_date,
            Booking.end_date > start_date
        ).first()
        
        if existing_booking:
            return jsonify({'error': 'Property already booked for these dates'}), 400
        
        booking = Booking(
            tenant_id=data['tenant_id'],
            property_id=data['property_id'],
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking_id': booking.id,
            'booking': booking.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    user_id = request.args.get('user_id')
    user_type = request.args.get('user_type')
    
    try:
        if user_type == 'tenant':
            bookings = Booking.query.filter_by(tenant_id=user_id).all()
        elif user_type == 'landlord':
            bookings = db.session.query(Booking).join(Property).filter(Property.landlord_id == user_id).all()
        else:
            bookings = Booking.query.all()
        
        return jsonify({
            'success': True,
            'bookings': [booking.to_dict() for booking in bookings]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Payment endpoints
@app.route('/api/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    
    if not data or not all(k in data for k in ['user_id', 'property_id', 'amount', 'due_date']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Verify property and user exist
        property_obj = Property.query.get(data['property_id'])
        user = User.query.get(data['user_id'])
        
        if not property_obj or not user:
            return jsonify({'error': 'Property or user not found'}), 404
        
        due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        
        payment = Payment(
            user_id=data['user_id'],
            property_id=data['property_id'],
            amount=Decimal(str(data['amount'])),
            due_date=due_date,
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment created successfully',
            'payment_id': payment.id,
            'payment': {
                'id': payment.id,
                'amount': str(payment.amount),
                'status': payment.status.value,
                'due_date': payment.due_date.isoformat(),
                'user_id': payment.user_id,
                'property_id': payment.property_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/payments', methods=['GET'])
def get_payments():
    user_id = request.args.get('user_id')
    user_type = request.args.get('user_type')
    
    try:
        if user_type == 'tenant':
            payments = Payment.query.filter_by(user_id=user_id).all()
        elif user_type == 'landlord':
            payments = db.session.query(Payment).join(Property).filter(Property.landlord_id == user_id).all()
        else:
            payments = Payment.query.all()
        
        return jsonify({
            'success': True,
            'payments': [{
                'id': p.id,
                'amount': str(p.amount),
                'status': p.status.value,
                'due_date': p.due_date.isoformat() if p.due_date else None,
                'payment_date': p.payment_date.isoformat() if p.payment_date else None,
                'user_id': p.user_id,
                'property_id': p.property_id,
                'payment_method': p.payment_method,
                'notes': p.notes
            } for p in payments]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/payments/<int:payment_id>', methods=['GET'])
def get_payment_by_id(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        return jsonify({
            'success': True,
            'payment': {
                'id': payment.id,
                'amount': str(payment.amount),
                'status': payment.status.value,
                'due_date': payment.due_date.isoformat() if payment.due_date else None,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'user_id': payment.user_id,
                'property_id': payment.property_id,
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'notes': payment.notes
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Payment not found'}), 404


@app.route('/api/payments/<int:payment_id>/confirm', methods=['PATCH'])
def confirm_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Update payment status
        payment.status = PaymentStatus.COMPLETED
        payment.payment_date = datetime.utcnow()
        
        # Update property status if this is the first confirmed payment
        property_obj = Property.query.get(payment.property_id)
        if property_obj and property_obj.status == PropertyStatus.AVAILABLE:
            property_obj.status = PropertyStatus.OCCUPIED
            property_obj.tenant_id = payment.user_id
        
        # Update related booking status
        booking = Booking.query.filter_by(
            property_id=payment.property_id,
            tenant_id=payment.user_id,
            status=BookingStatus.PENDING
        ).first()
        
        if booking:
            booking.status = BookingStatus.CONFIRMED
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment confirmed and property status updated',
            'payment_status': payment.status.value,
            'property_status': property_obj.status.value if property_obj else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)


