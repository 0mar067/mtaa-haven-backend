from flask import Blueprint, request, jsonify
from flask_mail import Message
from models import Notification, NotificationType, User, Property, Booking, BookingStatus, Payment, Issue, PropertyStatus, PaymentStatus, IssueStatus, IssueType, UserType
from database import db
import logging
from datetime import datetime
from decimal import Decimal

api = Blueprint('api', __name__)


@api.route('/test', methods=['GET'])
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


@api.route('/test', methods=['POST'])
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
        return jsonify({'received': data, 'message': 'Data received successfully'})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400

@api.route('/notifications', methods=['GET'])
def get_notifications():
    """
    Get notifications for the user.
    ---
    responses:
      200:
        description: List of notifications
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              title:
                type: string
              message:
                type: string
              type:
                type: string
              is_read:
                type: boolean
              created_at:
                type: string
                format: date-time
    """
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
    """
    Create a new notification.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "Rent Reminder"
            message:
              type: string
              example: "Your rent is due soon."
            user_id:
              type: integer
              example: 1
            property_id:
              type: integer
            email:
              type: string
              format: email
              example: "tenant@example.com"
    responses:
      201:
        description: Notification created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Notification created and email sent (mock)"
            notification_id:
              type: integer
      400:
        description: No data provided
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
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

        # Send email notification (mock for testing)
        recipient_email = data.get('email', 'tenant@example.com')
        try:
            from flask import current_app
            if current_app.config.get('TESTING'):
                # Mock email sending in tests
                logging.info(f"Mock email sent to {recipient_email}: {notification.title}")
            else:
                msg = Message(notification.title,
                              sender=current_app.config['MAIL_DEFAULT_SENDER'],
                              recipients=[recipient_email])
                msg.body = notification.message
                current_app.extensions['mail'].send(msg)
                logging.info(f"Email sent to {recipient_email}: {notification.title}")
        except Exception as e:
            logging.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return jsonify({'error': 'Failed to send email notification'}), 500

        return jsonify({
            'message': 'Notification created and email sent',
            'notification_id': notification.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Properties CRUD endpoints
def token_required(f):
    from flask import request, jsonify, current_app
    import jwt
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


@api.route('/properties', methods=['GET'])
@token_required
def get_properties(current_user):
    """
    Get all properties for the current user (landlord or tenant).
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of properties
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              title:
                type: string
              description:
                type: string
              address:
                type: string
              city:
                type: string
              rent_amount:
                type: number
              bedrooms:
                type: integer
              bathrooms:
                type: integer
              status:
                type: string
              landlord_id:
                type: integer
              tenant_id:
                type: integer
    """
    try:
        if current_user.user_type == UserType.LANDLORD:
            properties = Property.query.filter_by(landlord_id=current_user.id).all()
        else:
            properties = Property.query.filter_by(tenant_id=current_user.id).all()

        return jsonify([{
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'address': p.address,
            'city': p.city,
            'rent_amount': float(p.rent_amount),
            'bedrooms': p.bedrooms,
            'bathrooms': p.bathrooms,
            'area_sqft': p.area_sqft,
            'status': p.status.value,
            'landlord_id': p.landlord_id,
            'tenant_id': p.tenant_id,
            'created_at': p.created_at.isoformat(),
            'updated_at': p.updated_at.isoformat()
        } for p in properties])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/properties/<int:property_id>', methods=['GET'])
@token_required
def get_property(current_user, property_id):
    """
    Get a specific property by ID.
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Property details
      404:
        description: Property not found
    """
    try:
        property_obj = Property.query.get_or_404(property_id)

        # Check if user has access to this property
        if current_user.user_type == UserType.LANDLORD and property_obj.landlord_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to property'}), 403
        if current_user.user_type == UserType.TENANT and property_obj.tenant_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to property'}), 403

        return jsonify({
            'id': property_obj.id,
            'title': property_obj.title,
            'description': property_obj.description,
            'address': property_obj.address,
            'city': property_obj.city,
            'rent_amount': float(property_obj.rent_amount),
            'bedrooms': property_obj.bedrooms,
            'bathrooms': property_obj.bathrooms,
            'area_sqft': property_obj.area_sqft,
            'status': property_obj.status.value,
            'landlord_id': property_obj.landlord_id,
            'tenant_id': property_obj.tenant_id,
            'created_at': property_obj.created_at.isoformat(),
            'updated_at': property_obj.updated_at.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/properties', methods=['POST'])
@token_required
def create_property(current_user):
    """
    Create a new property (landlords only).
    ---
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - address
            - city
            - rent_amount
            - bedrooms
            - bathrooms
          properties:
            title:
              type: string
            description:
              type: string
            address:
              type: string
            city:
              type: string
            rent_amount:
              type: number
            bedrooms:
              type: integer
            bathrooms:
              type: integer
            area_sqft:
              type: integer
    responses:
      201:
        description: Property created successfully
      400:
        description: Missing required fields
      403:
        description: Only landlords can create properties
    """
    try:
        if current_user.user_type != UserType.LANDLORD:
            return jsonify({'error': 'Only landlords can create properties'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['title', 'address', 'city', 'rent_amount', 'bedrooms', 'bathrooms']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        property_obj = Property(
            title=data['title'],
            description=data.get('description'),
            address=data['address'],
            city=data['city'],
            rent_amount=Decimal(str(data['rent_amount'])),
            bedrooms=data['bedrooms'],
            bathrooms=data['bathrooms'],
            area_sqft=data.get('area_sqft'),
            landlord_id=current_user.id,
            status=PropertyStatus.AVAILABLE
        )

        db.session.add(property_obj)
        db.session.commit()

        return jsonify({
            'message': 'Property created successfully',
            'property_id': property_obj.id,
            'property': {
                'id': property_obj.id,
                'title': property_obj.title,
                'description': property_obj.description,
                'address': property_obj.address,
                'city': property_obj.city,
                'rent_amount': float(property_obj.rent_amount),
                'bedrooms': property_obj.bedrooms,
                'bathrooms': property_obj.bathrooms,
                'area_sqft': property_obj.area_sqft,
                'status': property_obj.status.value,
                'landlord_id': property_obj.landlord_id,
                'tenant_id': property_obj.tenant_id,
                'created_at': property_obj.created_at.isoformat(),
                'updated_at': property_obj.updated_at.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/properties/<int:property_id>', methods=['PUT'])
@token_required
def update_property(current_user, property_id):
    """
    Update a property (landlords only).
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            address:
              type: string
            city:
              type: string
            rent_amount:
              type: number
            bedrooms:
              type: integer
            bathrooms:
              type: integer
            area_sqft:
              type: integer
            status:
              type: string
              enum: [AVAILABLE, OCCUPIED, MAINTENANCE]
    responses:
      200:
        description: Property updated successfully
      403:
        description: Only landlords can update properties
      404:
        description: Property not found
    """
    try:
        property_obj = Property.query.get_or_404(property_id)

        if current_user.user_type != UserType.LANDLORD or property_obj.landlord_id != current_user.id:
            return jsonify({'error': 'Only property landlords can update properties'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update fields
        for field in ['title', 'description', 'address', 'city', 'bedrooms', 'bathrooms', 'area_sqft']:
            if field in data:
                setattr(property_obj, field, data[field])

        if 'rent_amount' in data:
            property_obj.rent_amount = Decimal(str(data['rent_amount']))

        if 'status' in data:
            try:
                property_obj.status = PropertyStatus(data['status'])
            except ValueError:
                return jsonify({'error': 'Invalid status value'}), 400

        db.session.commit()

        return jsonify({
            'message': 'Property updated successfully',
            'property': {
                'id': property_obj.id,
                'title': property_obj.title,
                'description': property_obj.description,
                'address': property_obj.address,
                'city': property_obj.city,
                'rent_amount': float(property_obj.rent_amount),
                'bedrooms': property_obj.bedrooms,
                'bathrooms': property_obj.bathrooms,
                'area_sqft': property_obj.area_sqft,
                'status': property_obj.status.value,
                'landlord_id': property_obj.landlord_id,
                'tenant_id': property_obj.tenant_id,
                'created_at': property_obj.created_at.isoformat(),
                'updated_at': property_obj.updated_at.isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/properties/<int:property_id>', methods=['DELETE'])
@token_required
def delete_property(current_user, property_id):
    """
    Delete a property (landlords only).
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Property deleted successfully
      403:
        description: Only landlords can delete properties
      404:
        description: Property not found
    """
    try:
        property_obj = Property.query.get_or_404(property_id)

        if current_user.user_type != UserType.LANDLORD or property_obj.landlord_id != current_user.id:
            return jsonify({'error': 'Only property landlords can delete properties'}), 403

        db.session.delete(property_obj)
        db.session.commit()

        return jsonify({'message': 'Property deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Payments CRUD endpoints
@api.route('/payments', methods=['GET'])
@token_required
def get_payments(current_user):
    """
    Get all payments for the current user.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of payments
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              amount:
                type: number
              payment_date:
                type: string
                format: date
              due_date:
                type: string
                format: date
              status:
                type: string
              payment_method:
                type: string
              transaction_id:
                type: string
              notes:
                type: string
              user_id:
                type: integer
              property_id:
                type: integer
    """
    try:
        payments = Payment.query.filter_by(user_id=current_user.id).all()

        return jsonify([{
            'id': p.id,
            'amount': float(p.amount),
            'payment_date': p.payment_date.isoformat() if p.payment_date else None,
            'due_date': p.due_date.isoformat(),
            'status': p.status.value,
            'payment_method': p.payment_method,
            'transaction_id': p.transaction_id,
            'notes': p.notes,
            'user_id': p.user_id,
            'property_id': p.property_id,
            'created_at': p.created_at.isoformat(),
            'updated_at': p.updated_at.isoformat()
        } for p in payments])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/payments/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(current_user, payment_id):
    """
    Get a specific payment by ID.
    ---
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Payment details
      404:
        description: Payment not found
    """
    try:
        payment = Payment.query.get_or_404(payment_id)

        # Check if user has access to this payment
        if payment.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to payment'}), 403

        return jsonify({
            'id': payment.id,
            'amount': float(payment.amount),
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'due_date': payment.due_date.isoformat(),
            'status': payment.status.value,
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
            'notes': payment.notes,
            'user_id': payment.user_id,
            'property_id': payment.property_id,
            'created_at': payment.created_at.isoformat(),
            'updated_at': payment.updated_at.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/payments', methods=['POST'])
@token_required
def create_payment(current_user):
    """
    Create a new payment.
    ---
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - amount
            - due_date
            - property_id
          properties:
            amount:
              type: number
            due_date:
              type: string
              format: date
            payment_method:
              type: string
            transaction_id:
              type: string
            notes:
              type: string
            property_id:
              type: integer
    responses:
      201:
        description: Payment created successfully
      400:
        description: Missing required fields or invalid data
      404:
        description: Property not found
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['amount', 'due_date', 'property_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate property exists and user has access
        property_obj = Property.query.filter_by(id=data['property_id']).first()
        if not property_obj:
            return jsonify({'error': 'Property not found'}), 404

        if current_user.user_type == UserType.TENANT and property_obj.tenant_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to property'}), 403
        if current_user.user_type == UserType.LANDLORD and property_obj.landlord_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to property'}), 403

        # Parse due date
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        payment = Payment(
            amount=Decimal(str(data['amount'])),
            due_date=due_date,
            payment_method=data.get('payment_method'),
            transaction_id=data.get('transaction_id'),
            notes=data.get('notes'),
            user_id=current_user.id,
            property_id=data['property_id'],
            status=PaymentStatus.PENDING
        )

        db.session.add(payment)
        db.session.commit()

        return jsonify({
            'message': 'Payment created successfully',
            'payment_id': payment.id,
            'payment': {
                'id': payment.id,
                'amount': float(payment.amount),
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'due_date': payment.due_date.isoformat(),
                'status': payment.status.value,
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'notes': payment.notes,
                'user_id': payment.user_id,
                'property_id': payment.property_id,
                'created_at': payment.created_at.isoformat(),
                'updated_at': payment.updated_at.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/payments/<int:payment_id>', methods=['PUT'])
@token_required
def update_payment(current_user, payment_id):
    """
    Update a payment.
    ---
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            amount:
              type: number
            payment_date:
              type: string
              format: date
            due_date:
              type: string
              format: date
            status:
              type: string
              enum: [PENDING, COMPLETED, FAILED]
            payment_method:
              type: string
            transaction_id:
              type: string
            notes:
              type: string
    responses:
      200:
        description: Payment updated successfully
      403:
        description: Unauthorized access
      404:
        description: Payment not found
    """
    try:
        payment = Payment.query.get_or_404(payment_id)

        if payment.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to payment'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update fields
        if 'amount' in data:
            payment.amount = Decimal(str(data['amount']))

        if 'payment_date' in data:
            try:
                payment.payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid payment_date format. Use YYYY-MM-DD'}), 400

        if 'due_date' in data:
            try:
                payment.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid due_date format. Use YYYY-MM-DD'}), 400

        if 'status' in data:
            try:
                payment.status = PaymentStatus(data['status'])
            except ValueError:
                return jsonify({'error': 'Invalid status value'}), 400

        for field in ['payment_method', 'transaction_id', 'notes']:
            if field in data:
                setattr(payment, field, data[field])

        db.session.commit()

        return jsonify({
            'message': 'Payment updated successfully',
            'payment': {
                'id': payment.id,
                'amount': float(payment.amount),
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'due_date': payment.due_date.isoformat(),
                'status': payment.status.value,
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'notes': payment.notes,
                'user_id': payment.user_id,
                'property_id': payment.property_id,
                'created_at': payment.created_at.isoformat(),
                'updated_at': payment.updated_at.isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/payments/<int:payment_id>', methods=['DELETE'])
@token_required
def delete_payment(current_user, payment_id):
    """
    Delete a payment.
    ---
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Payment deleted successfully
      403:
        description: Unauthorized access
      404:
        description: Payment not found
    """
    try:
        payment = Payment.query.get_or_404(payment_id)

        if payment.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to payment'}), 403

        db.session.delete(payment)
        db.session.commit()

        return jsonify({'message': 'Payment deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Issues CRUD endpoints
@api.route('/issues', methods=['GET'])
@token_required
def get_issues(current_user):
    """
    Get all issues for the current user.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of issues
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              title:
                type: string
              description:
                type: string
              issue_type:
                type: string
              status:
                type: string
              priority:
                type: string
              reporter_id:
                type: integer
              property_id:
                type: integer
              resolved_at:
                type: string
                format: date-time
    """
    try:
        issues = Issue.query.filter_by(reporter_id=current_user.id).all()

        return jsonify([{
            'id': i.id,
            'title': i.title,
            'description': i.description,
            'issue_type': i.issue_type.value,
            'status': i.status.value,
            'priority': i.priority,
            'reporter_id': i.reporter_id,
            'property_id': i.property_id,
            'resolved_at': i.resolved_at.isoformat() if i.resolved_at else None,
            'created_at': i.created_at.isoformat(),
            'updated_at': i.updated_at.isoformat()
        } for i in issues])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/issues/<int:issue_id>', methods=['GET'])
@token_required
def get_issue(current_user, issue_id):
    """
    Get a specific issue by ID.
    ---
    security:
      - Bearer: []
    parameters:
      - name: issue_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Issue details
      404:
        description: Issue not found
    """
    try:
        issue = Issue.query.get_or_404(issue_id)

        # Check if user has access to this issue
        if issue.reporter_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to issue'}), 403

        return jsonify({
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'issue_type': issue.issue_type.value,
            'status': issue.status.value,
            'priority': issue.priority,
            'reporter_id': issue.reporter_id,
            'property_id': issue.property_id,
            'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
            'created_at': issue.created_at.isoformat(),
            'updated_at': issue.updated_at.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/issues', methods=['POST'])
@token_required
def create_issue(current_user):
    """
    Create a new issue.
    ---
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - description
            - issue_type
            - property_id
          properties:
            title:
              type: string
            description:
              type: string
            issue_type:
              type: string
              enum: [MAINTENANCE, DISPUTE]
            property_id:
              type: integer
            priority:
              type: string
    responses:
      201:
        description: Issue created successfully
      400:
        description: Missing required fields or invalid data
      404:
        description: Property not found
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['title', 'description', 'issue_type', 'property_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate property exists and user has access
        property_obj = Property.query.filter_by(id=data['property_id']).first()
        if not property_obj:
            return jsonify({'error': 'Property not found'}), 404

        if current_user.user_type == UserType.TENANT and property_obj.tenant_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to property'}), 403
        if current_user.user_type == UserType.LANDLORD and property_obj.landlord_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to property'}), 403

        # Validate issue type
        try:
            issue_type = IssueType(data['issue_type'])
        except ValueError:
            return jsonify({'error': 'Invalid issue_type value'}), 400

        issue = Issue(
            title=data['title'],
            description=data['description'],
            issue_type=issue_type,
            priority=data.get('priority', 'medium'),
            reporter_id=current_user.id,
            property_id=data['property_id'],
            status=IssueStatus.OPEN
        )

        db.session.add(issue)
        db.session.commit()

        return jsonify({
            'message': 'Issue created successfully',
            'issue_id': issue.id,
            'issue': {
                'id': issue.id,
                'title': issue.title,
                'description': issue.description,
                'issue_type': issue.issue_type.value,
                'status': issue.status.value,
                'priority': issue.priority,
                'reporter_id': issue.reporter_id,
                'property_id': issue.property_id,
                'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
                'created_at': issue.created_at.isoformat(),
                'updated_at': issue.updated_at.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/issues/<int:issue_id>', methods=['PUT'])
@token_required
def update_issue(current_user, issue_id):
    """
    Update an issue.
    ---
    security:
      - Bearer: []
    parameters:
      - name: issue_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            issue_type:
              type: string
              enum: [MAINTENANCE, DISPUTE]
            status:
              type: string
              enum: [OPEN, IN_PROGRESS, RESOLVED]
            priority:
              type: string
    responses:
      200:
        description: Issue updated successfully
      403:
        description: Unauthorized access
      404:
        description: Issue not found
    """
    try:
        issue = Issue.query.get_or_404(issue_id)

        if issue.reporter_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to issue'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update fields
        for field in ['title', 'description', 'priority']:
            if field in data:
                setattr(issue, field, data[field])

        if 'issue_type' in data:
            try:
                issue.issue_type = IssueType(data['issue_type'])
            except ValueError:
                return jsonify({'error': 'Invalid issue_type value'}), 400

        if 'status' in data:
            try:
                issue.status = IssueStatus(data['status'])
                if issue.status == IssueStatus.RESOLVED and not issue.resolved_at:
                    issue.resolved_at = datetime.utcnow()
            except ValueError:
                return jsonify({'error': 'Invalid status value'}), 400

        db.session.commit()

        return jsonify({
            'message': 'Issue updated successfully',
            'issue': {
                'id': issue.id,
                'title': issue.title,
                'description': issue.description,
                'issue_type': issue.issue_type.value,
                'status': issue.status.value,
                'priority': issue.priority,
                'reporter_id': issue.reporter_id,
                'property_id': issue.property_id,
                'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
                'created_at': issue.created_at.isoformat(),
                'updated_at': issue.updated_at.isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/issues/<int:issue_id>', methods=['DELETE'])
@token_required
def delete_issue(current_user, issue_id):
    """
    Delete an issue.
    ---
    security:
      - Bearer: []
    parameters:
      - name: issue_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Issue deleted successfully
      403:
        description: Unauthorized access
      404:
        description: Issue not found
    """
    try:
        issue = Issue.query.get_or_404(issue_id)

        if issue.reporter_id != current_user.id:
            return jsonify({'error': 'Unauthorized access to issue'}), 403

        db.session.delete(issue)
        db.session.commit()

        return jsonify({'message': 'Issue deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/bookings', methods=['POST'])
def create_booking():
    """
    Create a new property booking.
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            tenant_id:
              type: integer
              example: 3
            property_id:
              type: integer
              example: 10
            start_date:
              type: string
              format: date
              example: "2025-10-20"
            end_date:
              type: string
              format: date
              example: "2026-10-20"
    responses:
      201:
        description: Booking created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Booking created successfully"
            booking_id:
              type: integer
            booking:
              type: object
      400:
        description: Missing required fields or invalid data
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: Tenant or property not found
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        tenant_id = data.get('tenant_id')
        property_id = data.get('property_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not all([tenant_id, property_id, start_date_str, end_date_str]):
            return jsonify({'error': 'Missing required fields: tenant_id, property_id, start_date, end_date'}), 400

        # Validate tenant exists and is a tenant
        tenant = User.query.filter_by(id=tenant_id, user_type=UserType.TENANT).first()
        if not tenant:
            return jsonify({'error': 'Tenant not found or user is not a tenant'}), 404

        # Validate property exists and is available
        property_obj = Property.query.filter_by(id=property_id, status=PropertyStatus.AVAILABLE).first()
        if not property_obj:
            return jsonify({'error': 'Property not found or not available'}), 404

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Validate date logic
        if start_date >= end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400

        if start_date < datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0):
            return jsonify({'error': 'Start date cannot be in the past'}), 400

        # Create booking
        booking = Booking(
            tenant_id=tenant_id,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            status=BookingStatus.PENDING
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
        return jsonify({'error': str(e)}), 500
