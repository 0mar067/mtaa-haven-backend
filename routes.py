from flask import Blueprint, request, jsonify
from flask_mail import Message
from models import Notification, NotificationType, User, Property
from database import db
from app import mail
import logging

api = Blueprint('api', __name__)

@api.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working'})

@api.route('/test', methods=['POST'])
def test_post():
    try:
        data = request.get_json()
        if data is None or data == {}:
            return jsonify({'error': 'No JSON data provided'}), 400
        return jsonify({'received': data, 'message': 'Data received successfully'})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400

@api.route('/notifications', methods=['GET'])
def get_notifications():
    # Mock rent reminders - in a real app, this would query based on user and due dates
    mock_notifications = [
        {
            'id': 1,
            'title': 'Rent Due Reminder',
            'message': 'Your rent payment of KES 25,000 is due on October 31st, 2025.',
            'type': 'rent_reminder',
            'is_read': False,
            'created_at': '2025-10-24T06:00:00Z'
        },
        {
            'id': 2,
            'title': 'Payment Due Soon',
            'message': 'Payment for Property: Downtown Apartment is due in 3 days.',
            'type': 'payment_due',
            'is_read': False,
            'created_at': '2025-10-23T12:00:00Z'
        }
    ]
    return jsonify(mock_notifications)

@api.route('/notifications', methods=['POST'])
def create_notification():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Create notification in database (mock for now)
        notification = Notification(
            title=data.get('title', 'Rent Reminder'),
            message=data.get('message', 'Your rent is due soon.'),
            notification_type=NotificationType.RENT_REMINDER,
            user_id=data.get('user_id', 1),  # Mock user ID
            property_id=data.get('property_id')
        )
        db.session.add(notification)
        db.session.commit()

        # Send email notification (mock - log instead of actual send)
        recipient_email = data.get('email', 'tenant@example.com')
        logging.info(f"Mock email sent to {recipient_email}: {notification.title} - {notification.message}")

        # In a real implementation, uncomment the following:
        # msg = Message(notification.title,
        #               sender=app.config['MAIL_DEFAULT_SENDER'],
        #               recipients=[recipient_email])
        # msg.body = notification.message
        # mail.send(msg)

        return jsonify({
            'message': 'Notification created and email sent (mock)',
            'notification_id': notification.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500