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
from dotenv import load_dotenv

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
from mail_utils import mail, send_welcome_email


load_dotenv()

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'sqlite:///{os.path.join(basedir, "mtaa_heaven.db")}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'  # In production, use environment variable

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'your-cloud-name'),
    api_key=os.getenv('CLOUDINARY_API_KEY', 'your-api-key'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'your-api-secret')
)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail.init_app(app)
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


if __name__ == '__main__':
    app.run(debug=True)


