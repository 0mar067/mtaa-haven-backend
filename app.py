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
swagger = Swagger(app)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])


# Register blueprints
app.register_blueprint(api, url_prefix='/api')

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


@app.route('/api/test', methods=['POST'])
def test_post():
    """
    Test endpoint for POST requests with JSON data.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          example: {"key": "value"}
    responses:
      200:
        description: Data received successfully
        schema:
          type: object
          properties:
            received:
              type: object
            message:
              type: string
              example: "Data received successfully"
      400:
        description: No JSON data provided or invalid JSON
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        data = request.get_json()
        if data is None or data == {}:
            return jsonify({'error': 'No JSON data provided'}), 400
        return jsonify({
            'received': data,
            'message': 'Data received successfully'
        })
    except Exception:
        return jsonify({'error': 'Invalid JSON data'}), 400

@app.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user (landlord or tenant).
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - first_name
            - last_name
            - user_type
            - password
          properties:
            email:
              type: string
              format: email
              example: "user@example.com"
            first_name:
              type: string
              example: "John"
            last_name:
              type: string
              example: "Doe"
            phone:
              type: string
              example: "+1234567890"
            user_type:
              type: string
              enum: [LANDLORD, TENANT]
              example: "TENANT"
            password:
              type: string
              minLength: 1
              example: "password123"
    responses:
      200:
        description: User registered successfully
        schema:
          type: object
          properties:
            Success:
              type: boolean
              example: true
            user:
              type: object
              properties:
                id:
                  type: integer
                email:
                  type: string
                first_name:
                  type: string
                last_name:
                  type: string
                phone:
                  type: string
                user_type:
                  type: string
      400:
        description: Missing required fields or no data provided
        schema:
          type: object
          properties:
            error:
              type: string
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone = data.get('phone')
    user_type = data.get('user_type')
    password = data.get('password')
    created_at = datetime.utcnow()
    updated_at = datetime.utcnow()

    if not (email and first_name and last_name and user_type and password):
        return jsonify({'error': 'Missing required fields'}), 400

    password_hash = generate_password_hash(password)

    new_user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        user_type=user_type,
        password_hash=password_hash,
        created_at=created_at,
        updated_at=updated_at
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"Success":True, "user": new_user.to_dict()})
    
@app.route('/api/login', methods=['POST'])
def login():
    """
    Login with email and password.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: "user@example.com"
            password:
              type: string
              minLength: 1
              example: "password123"
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            message:
              type: string
              example: "logged in successful"
            user:
              type: object
              properties:
                id:
                  type: integer
                email:
                  type: string
                first_name:
                  type: string
                last_name:
                  type: string
                phone:
                  type: string
                user_type:
                  type: string
      400:
        description: No data provided or missing required fields
        schema:
          type: object
          properties:
            error:
              type: string
      401:
        description: Invalid credentials
        schema:
          type: object
          properties:
            error:
              type: string
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        return jsonify({
            "message": "logged in successful",
            "user": user.to_dict(),
            "token": token
        })
    return jsonify({'error': 'Invalid credentials'}), 401
  
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


if __name__ == '__main__':
    app.run(debug=True)


