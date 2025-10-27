from flask import Blueprint, request, jsonify
from flask_mail import Message
from models import Notification, NotificationType, User, Property, Booking, BookingStatus, Payment, Issue, PropertyStatus, PaymentStatus, IssueStatus, IssueType, UserType, PropertyImage
from database import db
import logging
from datetime import datetime
from decimal import Decimal
import cloudinary.uploader
from PIL import Image
import io

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
    Get properties with optional filtering and search.
    Supports public search (no auth required) and authenticated user-specific filtering.
    ---
    parameters:
      - name: location
        in: query
        type: string
        description: Filter by city (case-insensitive)
      - name: price_min
        in: query
        type: number
        description: Minimum rent amount
      - name: price_max
        in: query
        type: number
        description: Maximum rent amount
      - name: type
        in: query
        type: string
        description: Filter by property type (e.g., hostel, airbnb, apartment)
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
              type:
                type: string
              status:
                type: string
              landlord_id:
                type: integer
              tenant_id:
                type: integer
      404:
        description: No properties found matching the criteria
    """
    try:
        # Check for authentication token
        token = request.headers.get('Authorization')
        current_user = None
        if token:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            try:
                import jwt
                from flask import current_app
                data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                current_user = User.query.get(data['user_id'])
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
                pass  # Treat as unauthenticated

        # Build base query
        query = Property.query

        # Apply user-specific filtering if authenticated
        if current_user:
            if current_user.user_type == UserType.LANDLORD:
                query = query.filter_by(landlord_id=current_user.id)
            else:
                query = query.filter_by(tenant_id=current_user.id)

        # Apply search filters
        location = request.args.get('location')
        price_min = request.args.get('price_min')
        price_max = request.args.get('price_max')
        property_type = request.args.get('type')

        filters_applied = []

        if location:
            query = query.filter(Property.city.ilike(f'%{location}%'))
            filters_applied.append(f"location={location}")

        if price_min:
            try:
                min_price = float(price_min)
                query = query.filter(Property.rent_amount >= min_price)
                filters_applied.append(f"price_min={price_min}")
            except ValueError:
                return jsonify({'error': 'Invalid price_min value'}), 400

        if price_max:
            try:
                max_price = float(price_max)
                query = query.filter(Property.rent_amount <= max_price)
                filters_applied.append(f"price_max={price_max}")
            except ValueError:
                return jsonify({'error': 'Invalid price_max value'}), 400

        if property_type:
            query = query.filter(Property.type.ilike(f'%{property_type}%'))
            filters_applied.append(f"type={property_type}")

        # Log search query
        if filters_applied:
            logging.info(f"Property search query: {'&'.join(filters_applied)}")
        else:
            logging.info("Property search query: no filters applied")

        # Execute query
        properties = query.all()

        # Format response
        result = []
        for p in properties:
            # Get property images
            images = PropertyImage.query.filter_by(property_id=p.id).order_by(PropertyImage.display_order).all()
            image_data = [{
                'id': img.id,
                'image_url': img.image_url,
                'thumbnail_url': img.thumbnail_url,
                'is_primary': img.is_primary
            } for img in images]

            # Get primary image URL and image count
            primary_image = next((img for img in images if img.is_primary), None)
            primary_image_url = primary_image.image_url if primary_image else None
            image_count = len(images)

            # Default amenities if not stored in database
            default_amenities = ['Parking', 'Security', 'Water', 'Electricity']
            if p.type and p.type.lower() in ['apartment', 'house']:
                default_amenities.extend(['WiFi', 'Air Conditioning'])
            elif p.type and p.type.lower() == 'hostel':
                default_amenities.extend(['Shared Kitchen', 'Laundry'])

            prop_dict = {
                'id': p.id,
                'name': p.title,  # Changed from 'title' to 'name' to match frontend
                'description': p.description,
                'address': p.address,
                'location': p.city,  # Changed from 'city' to 'location' to match frontend
                'rent_amount': float(p.rent_amount),
                'bedrooms': p.bedrooms,
                'bathrooms': p.bathrooms,
                'size': p.area_sqft,  # Changed from 'area_sqft' to 'size' to match frontend
                'type': p.type,
                'status': p.status.value,
                'landlord_id': p.landlord_id,
                'tenant_id': p.tenant_id,
                'image': primary_image_url,  # Changed from 'primary_image_url' to 'image' to match frontend
                'image_count': image_count,
                'images': image_data,  # Keep images array as expected by frontend
                'amenities': default_amenities,  # Added amenities field
                'created_at': p.created_at.isoformat(),
                'updated_at': p.updated_at.isoformat()
            }
            result.append(prop_dict)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Error in get_properties: {str(e)}")
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

        # Get property images
        images = PropertyImage.query.filter_by(property_id=property_id).order_by(PropertyImage.display_order).all()
        image_data = [{
            'id': img.id,
            'image_url': img.image_url,
            'thumbnail_url': img.thumbnail_url,
            'is_primary': img.is_primary
        } for img in images]

        # Get primary image URL and image count
        primary_image = next((img for img in images if img.is_primary), None)
        primary_image_url = primary_image.image_url if primary_image else None
        image_count = len(images)

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
            'type': property_obj.type,
            'status': property_obj.status.value,
            'landlord_id': property_obj.landlord_id,
            'tenant_id': property_obj.tenant_id,
            'primary_image_url': primary_image_url,
            'image_count': image_count,
            'images': image_data,
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
            type:
              type: string
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
            type=data.get('type'),
            landlord_id=current_user.id,
            status=PropertyStatus.AVAILABLE
        )

        db.session.add(property_obj)
        db.session.commit()

        # Get property images (should be empty for new property)
        images = PropertyImage.query.filter_by(property_id=property_obj.id).order_by(PropertyImage.display_order).all()
        image_data = [{
            'id': img.id,
            'image_url': img.image_url,
            'thumbnail_url': img.thumbnail_url,
            'is_primary': img.is_primary
        } for img in images]

        # Get primary image URL and image count
        primary_image = next((img for img in images if img.is_primary), None)
        primary_image_url = primary_image.image_url if primary_image else None
        image_count = len(images)

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
                'type': property_obj.type,
                'status': property_obj.status.value,
                'landlord_id': property_obj.landlord_id,
                'tenant_id': property_obj.tenant_id,
                'primary_image_url': primary_image_url,
                'image_count': image_count,
                'images': image_data,
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
            type:
              type: string
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
        for field in ['title', 'description', 'address', 'city', 'bedrooms', 'bathrooms', 'area_sqft', 'type']:
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

        # Get property images
        images = PropertyImage.query.filter_by(property_id=property_id).order_by(PropertyImage.display_order).all()
        image_data = [{
            'id': img.id,
            'image_url': img.image_url,
            'thumbnail_url': img.thumbnail_url,
            'is_primary': img.is_primary
        } for img in images]

        # Get primary image URL and image count
        primary_image = next((img for img in images if img.is_primary), None)
        primary_image_url = primary_image.image_url if primary_image else None
        image_count = len(images)

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
                'type': property_obj.type,
                'status': property_obj.status.value,
                'landlord_id': property_obj.landlord_id,
                'tenant_id': property_obj.tenant_id,
                'primary_image_url': primary_image_url,
                'image_count': image_count,
                'images': image_data,
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
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            data:
              type: object
      403:
        description: Unauthorized access
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      404:
        description: Payment not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
    """
    try:
        payment = Payment.query.get_or_404(payment_id)

        # Check if user has access to this payment
        if payment.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized access to payment'}), 403

        # Get associated booking info if exists
        booking = Booking.query.filter_by(property_id=payment.property_id, tenant_id=payment.user_id).first()

        payment_data = {
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

        if booking:
            payment_data['booking_id'] = booking.id
            payment_data['booking_status'] = booking.status.value

        return jsonify({
            'status': 'success',
            'data': payment_data
        })

    except Exception as e:
        logging.error(f"Error retrieving payment {payment_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Property Image Management endpoints
@api.route('/properties/<int:property_id>/images', methods=['POST'])
@token_required
def upload_property_images(current_user, property_id):
    """
    Upload images for a property (landlords only).
    Supports up to 10 images per property with automatic thumbnail generation.
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: integer
        required: true
      - name: images
        in: formData
        type: file
        required: true
        description: Image files (multiple allowed, max 10 per property)
      - name: is_primary
        in: formData
        type: boolean
        required: false
        description: Set first image as primary (default false)
    responses:
      201:
        description: Images uploaded successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
            data:
              type: object
              properties:
                uploaded_images:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      image_url:
                        type: string
                      thumbnail_url:
                        type: string
                      is_primary:
                        type: boolean
      400:
        description: Invalid file or validation error
      403:
        description: Only property landlords can upload images
      404:
        description: Property not found
    """
    try:
        # Check if property exists and user has access
        property_obj = Property.query.get_or_404(property_id)
        if current_user.user_type != UserType.LANDLORD or property_obj.landlord_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Only property landlords can upload images'}), 403

        # Check current image count
        current_images = PropertyImage.query.filter_by(property_id=property_id).count()
        if current_images >= 10:
            return jsonify({'status': 'error', 'message': 'Maximum 10 images allowed per property'}), 400

        # Get uploaded files
        if 'images' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image files provided'}), 400

        files = request.files.getlist('images')
        if not files or files[0].filename == '':
            return jsonify({'status': 'error', 'message': 'No image files provided'}), 400

        # Validate file count
        available_slots = 10 - current_images
        if len(files) > available_slots:
            return jsonify({'status': 'error', 'message': f'Too many images. Only {available_slots} more images allowed'}), 400

        uploaded_images = []
        is_primary = request.form.get('is_primary', 'false').lower() == 'true'

        for i, file in enumerate(files):
            if file and file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if not file.filename.lower().split('.')[-1] in allowed_extensions:
                    continue  # Skip invalid files

                # Validate file size (max 5MB)
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                if file_size > 5 * 1024 * 1024:  # 5MB
                    continue  # Skip large files

                try:
                    # Process image with Pillow for validation and optimization
                    image = Image.open(file)
                    image.verify()  # Verify it's a valid image
                    file.seek(0)  # Reset file pointer

                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder=f"mtaa_haven/properties/{property_id}",
                        transformation=[
                            {'width': 1200, 'height': 800, 'crop': 'limit'},
                            {'quality': 'auto'}
                        ]
                    )

                    # Generate thumbnail
                    thumbnail_result = cloudinary.uploader.upload(
                        file,
                        folder=f"mtaa_haven/properties/{property_id}/thumbnails",
                        transformation=[
                            {'width': 300, 'height': 200, 'crop': 'fill'},
                            {'quality': 'auto'}
                        ]
                    )

                    # Create database record
                    display_order = current_images + i
                    property_image = PropertyImage(
                        property_id=property_id,
                        image_url=upload_result['secure_url'],
                        thumbnail_url=thumbnail_result['secure_url'],
                        public_id=upload_result['public_id'],
                        is_primary=is_primary and i == 0,  # Only first image can be primary
                        display_order=display_order
                    )

                    db.session.add(property_image)
                    uploaded_images.append({
                        'id': property_image.id,
                        'image_url': property_image.image_url,
                        'thumbnail_url': property_image.thumbnail_url,
                        'is_primary': property_image.is_primary
                    })

                except Exception as upload_error:
                    logging.error(f"Error uploading image {file.filename}: {str(upload_error)}")
                    continue

        db.session.commit()

        if not uploaded_images:
            return jsonify({'status': 'error', 'message': 'No images were successfully uploaded'}), 400

        return jsonify({
            'status': 'success',
            'message': f'Successfully uploaded {len(uploaded_images)} image(s)',
            'data': {
                'uploaded_images': uploaded_images
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in upload_property_images: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Dashboard endpoints
@api.route('/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """
    Get dashboard statistics for landlords.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Dashboard statistics
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            data:
              type: object
              properties:
                properties:
                  type: integer
                  description: Number of properties owned by the landlord
                tenants:
                  type: integer
                  description: Number of tenants renting landlord's properties
                issues:
                  type: integer
                  description: Number of open issues for landlord's properties
                payments:
                  type: integer
                  description: Total number of payments for landlord's properties
      403:
        description: Only landlords can access dashboard stats
    """
    try:
        if current_user.user_type != UserType.LANDLORD:
            return jsonify({'status': 'error', 'message': 'Only landlords can access dashboard statistics'}), 403

        # Get properties count
        properties_count = Property.query.filter_by(landlord_id=current_user.id).count()

        # Get tenants count (unique tenants renting landlord's properties)
        tenants_count = db.session.query(User).join(Property, Property.tenant_id == User.id)\
            .filter(Property.landlord_id == current_user.id)\
            .filter(Property.tenant_id.isnot(None))\
            .distinct().count()

        # Get open issues count
        issues_count = Issue.query.join(Property)\
            .filter(Property.landlord_id == current_user.id)\
            .filter(Issue.status != IssueStatus.RESOLVED)\
            .count()

        # Get payments count
        payments_count = Payment.query.join(Property)\
            .filter(Property.landlord_id == current_user.id)\
            .count()

        return jsonify({
            'status': 'success',
            'data': {
                'properties': properties_count,
                'tenants': tenants_count,
                'issues': issues_count,
                'payments': payments_count
            }
        })

    except Exception as e:
        logging.error(f"Error retrieving dashboard stats: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api.route('/properties/<int:property_id>/images', methods=['GET'])
def get_property_images(property_id):
    """
    Get all images for a property.
    ---
    parameters:
      - name: property_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List of property images
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              image_url:
                type: string
              thumbnail_url:
                type: string
              is_primary:
                type: boolean
              display_order:
                type: integer
      404:
        description: Property not found
    """
    try:
        # Verify property exists
        property_obj = Property.query.get_or_404(property_id)

        images = PropertyImage.query.filter_by(property_id=property_id).order_by(PropertyImage.display_order).all()

        return jsonify([{
            'id': img.id,
            'image_url': img.image_url,
            'thumbnail_url': img.thumbnail_url,
            'is_primary': img.is_primary,
            'display_order': img.display_order,
            'created_at': img.created_at.isoformat()
        } for img in images])

    except Exception as e:
        logging.error(f"Error retrieving property images: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api.route('/properties/<int:property_id>/images/<int:image_id>', methods=['DELETE'])
@token_required
def delete_property_image(current_user, property_id, image_id):
    """
    Delete a specific property image (landlords only).
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: integer
        required: true
      - name: image_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Image deleted successfully
      403:
        description: Only property landlords can delete images
      404:
        description: Property or image not found
    """
    try:
        # Check if property exists and user has access
        property_obj = Property.query.get_or_404(property_id)
        if current_user.user_type != UserType.LANDLORD or property_obj.landlord_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Only property landlords can delete images'}), 403

        # Find the image
        image = PropertyImage.query.filter_by(id=image_id, property_id=property_id).first()
        if not image:
            return jsonify({'status': 'error', 'message': 'Image not found'}), 404

        # Delete from Cloudinary
        try:
            cloudinary.uploader.destroy(image.public_id)
        except Exception as cloud_error:
            logging.warning(f"Failed to delete image from Cloudinary: {str(cloud_error)}")

        # Delete from database
        db.session.delete(image)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Image deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting property image: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api.route('/properties/<int:property_id>/images/<int:image_id>/primary', methods=['PUT'])
@token_required
def set_primary_image(current_user, property_id, image_id):
    """
    Set an image as the primary image for a property (landlords only).
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: integer
        required: true
      - name: image_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Primary image updated successfully
      403:
        description: Only property landlords can set primary images
      404:
        description: Property or image not found
    """
    try:
        # Check if property exists and user has access
        property_obj = Property.query.get_or_404(property_id)
        if current_user.user_type != UserType.LANDLORD or property_obj.landlord_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Only property landlords can set primary images'}), 403

        # Find the image
        image = PropertyImage.query.filter_by(id=image_id, property_id=property_id).first()
        if not image:
            return jsonify({'status': 'error', 'message': 'Image not found'}), 404

        # Remove primary status from all other images
        PropertyImage.query.filter_by(property_id=property_id).update({'is_primary': False})

        # Set this image as primary
        image.is_primary = True
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Primary image updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error setting primary image: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
            - booking_id
            - amount
            - payment_method
          properties:
            booking_id:
              type: integer
            amount:
              type: number
            payment_method:
              type: string
              enum: [mpesa, card, bank_transfer]
            notes:
              type: string
    responses:
      201:
        description: Payment created and confirmed successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
            data:
              type: object
      400:
        description: Missing required fields or invalid data
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      403:
        description: Unauthorized access
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      404:
        description: Booking not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        required_fields = ['booking_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400

        booking_id = data['booking_id']
        amount = data['amount']
        payment_method = data['payment_method']

        # Validate booking exists and user has access
        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return jsonify({'status': 'error', 'message': 'Booking not found'}), 404

        # Check if user is authorized (tenant of the booking or landlord of the property)
        property_obj = Property.query.filter_by(id=booking.property_id).first()
        if not property_obj:
            return jsonify({'status': 'error', 'message': 'Associated property not found'}), 404

        if current_user.user_type == UserType.TENANT and booking.tenant_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized access to booking'}), 403
        if current_user.user_type == UserType.LANDLORD and property_obj.landlord_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized access to booking'}), 403

        # Validate payment amount (should match property rent or be reasonable)
        if amount <= 0:
            return jsonify({'status': 'error', 'message': 'Payment amount must be positive'}), 400

        # Generate transaction ID
        import uuid
        transaction_id = str(uuid.uuid4())[:8].upper()

        # Create payment with current timestamp as payment_date
        payment = Payment(
            amount=Decimal(str(amount)),
            payment_date=datetime.utcnow(),
            due_date=booking.end_date,  # Use booking end date as due date
            payment_method=payment_method,
            transaction_id=transaction_id,
            notes=data.get('notes'),
            user_id=current_user.id,
            property_id=booking.property_id,
            status=PaymentStatus.PENDING
        )

        db.session.add(payment)
        db.session.commit()

        # Mock payment confirmation logic
        # In a real app, this would integrate with payment gateway webhooks
        try:
            # Simulate payment processing delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing

            # Mock confirmation - in real app, this would be done via webhook
            payment.status = PaymentStatus.COMPLETED
            db.session.commit()

            logging.info(f"Payment confirmed: transaction_id={transaction_id}, amount={amount}, method={payment_method}")

            # If this is a tenant payment and booking is pending, confirm the booking and update property status
            if current_user.user_type == UserType.TENANT and booking.status == BookingStatus.PENDING:
                booking.status = BookingStatus.CONFIRMED
                property_obj.status = PropertyStatus.OCCUPIED
                property_obj.tenant_id = current_user.id
                db.session.commit()

                logging.info(f"Booking confirmed and property status updated: booking_id={booking.id}, property_id={property_obj.id}")

        except Exception as confirm_error:
            logging.error(f"Payment confirmation failed: {str(confirm_error)}")
            # Payment stays pending if confirmation fails

        return jsonify({
            'status': 'success',
            'message': 'Payment processed successfully',
            'data': {
                'payment_id': payment.id,
                'transaction_id': transaction_id,
                'status': payment.status.value,
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
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating payment: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
    Get all issues for the current user with role-based filtering.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of issues
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            data:
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
        if current_user.user_type == UserType.LANDLORD:
            # Landlords see all issues for their properties
            issues = Issue.query.join(Property).filter(Property.landlord_id == current_user.id).all()
        else:
            # Tenants see only issues they reported
            issues = Issue.query.filter_by(reporter_id=current_user.id).all()

        issues_data = [{
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
        } for i in issues]

        return jsonify({
            'status': 'success',
            'data': issues_data
        })

    except Exception as e:
        logging.error(f"Error retrieving issues for user {current_user.id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
            priority:
              type: string
              enum: [low, medium, high]
              default: medium
            property_id:
              type: integer
    responses:
      201:
        description: Issue created successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
            data:
              type: object
      400:
        description: Missing required fields or invalid data
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      403:
        description: Unauthorized access - tenant can only report issues for properties they rent
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      404:
        description: Property not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        required_fields = ['title', 'description', 'issue_type', 'property_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400

        # Validate property exists
        property_obj = Property.query.filter_by(id=data['property_id']).first()
        if not property_obj:
            return jsonify({'status': 'error', 'message': 'Property not found'}), 404

        # For tenants: ensure they can only report issues for properties they rent
        if current_user.user_type == UserType.TENANT:
            if property_obj.tenant_id != current_user.id:
                return jsonify({'status': 'error', 'message': 'You can only report issues for properties you rent'}), 403
        # For landlords: ensure they can only receive issues for their properties
        elif current_user.user_type == UserType.LANDLORD:
            if property_obj.landlord_id != current_user.id:
                return jsonify({'status': 'error', 'message': 'Unauthorized access to property'}), 403

        # Validate priority
        priority = data.get('priority', 'medium')
        if priority not in ['low', 'medium', 'high']:
            return jsonify({'status': 'error', 'message': 'Invalid priority. Must be low, medium, or high'}), 400

        issue = Issue(
            title=data['title'],
            description=data['description'],
            issue_type=IssueType(data['issue_type']),
            priority=priority,
            reporter_id=current_user.id,
            property_id=data['property_id'],
            status=IssueStatus.OPEN
        )

        db.session.add(issue)
        db.session.commit()

        logging.info(f"Issue created: reporter_id={current_user.id}, property_id={property_obj.id}, issue_id={issue.id}")

        return jsonify({
            'status': 'success',
            'message': 'Issue created successfully',
            'data': {
                'issue_id': issue.id,
                'issue': {
                    'id': issue.id,
                    'title': issue.title,
                    'description': issue.description,
                    'issue_type': issue.issue_type.value,
                    'priority': issue.priority,
                    'status': issue.status.value,
                    'reporter_id': issue.reporter_id,
                    'property_id': issue.property_id,
                    'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
                    'created_at': issue.created_at.isoformat(),
                    'updated_at': issue.updated_at.isoformat()
                }
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating issue: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api.route('/issues/<int:issue_id>', methods=['PUT'])
@token_required
def update_issue(current_user, issue_id):
    """
    Update an issue status (landlords can update status, tenants can only update their own issues).
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
              enum: [low, medium, high]
    responses:
      200:
        description: Issue updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
            data:
              type: object
      403:
        description: Unauthorized access
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      404:
        description: Issue not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
    """
    try:
        issue = Issue.query.get_or_404(issue_id)

        # Check authorization: tenants can only update their own issues, landlords can update issues for their properties
        if current_user.user_type == UserType.TENANT:
            if issue.reporter_id != current_user.id:
                return jsonify({'status': 'error', 'message': 'You can only update your own issues'}), 403
        else:  # Landlord
            property_obj = Property.query.filter_by(id=issue.property_id, landlord_id=current_user.id).first()
            if not property_obj:
                return jsonify({'status': 'error', 'message': 'Unauthorized access to issue'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Update fields
        for field in ['title', 'description', 'priority']:
            if field in data:
                setattr(issue, field, data[field])

        if 'issue_type' in data:
            try:
                issue.issue_type = IssueType(data['issue_type'])
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid issue_type value'}), 400

        if 'status' in data:
            try:
                old_status = issue.status
                issue.status = IssueStatus(data['status'])
                if issue.status == IssueStatus.RESOLVED and old_status != IssueStatus.RESOLVED:
                    issue.resolved_at = datetime.utcnow()
                    # Create notification for tenant when issue is resolved
                    notification = Notification(
                        title=f'Issue Resolved - {issue.title}',
                        message=f'Your issue "{issue.title}" has been resolved. Please check the details.',
                        notification_type=NotificationType.ISSUE_UPDATE,
                        user_id=issue.reporter_id,
                        property_id=issue.property_id
                    )
                    db.session.add(notification)
                    logging.info(f"Notification created for issue resolution: issue_id={issue.id}")
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid status value'}), 400

        db.session.commit()

        logging.info(f"Issue updated: issue_id={issue.id}, updated_by={current_user.id}")

        return jsonify({
            'status': 'success',
            'message': 'Issue updated successfully',
            'data': {
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
            }
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating issue {issue_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "Booking created successfully"
            data:
              type: object
              properties:
                booking_id:
                  type: integer
                booking:
                  type: object
      400:
        description: Missing required fields or invalid data
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      404:
        description: Tenant or property not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      409:
        description: Property already booked or unavailable
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        tenant_id = data.get('tenant_id')
        property_id = data.get('property_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not all([tenant_id, property_id, start_date_str, end_date_str]):
            return jsonify({'status': 'error', 'message': 'Missing required fields: tenant_id, property_id, start_date, end_date'}), 400

        # Validate tenant exists and is a tenant
        tenant = User.query.filter_by(id=tenant_id, user_type=UserType.TENANT).first()
        if not tenant:
            return jsonify({'status': 'error', 'message': 'Tenant not found or user is not a tenant'}), 404

        # Validate property exists and is available
        property_obj = Property.query.filter_by(id=property_id).first()
        if not property_obj:
            return jsonify({'status': 'error', 'message': 'Property not found'}), 404

        if property_obj.status != PropertyStatus.AVAILABLE:
            return jsonify({'status': 'error', 'message': 'Property is not available for booking'}), 409

        # Check for existing active bookings for this property
        active_booking = Booking.query.filter_by(
            property_id=property_id,
            status=BookingStatus.CONFIRMED
        ).first()
        if active_booking:
            return jsonify({'status': 'error', 'message': 'Property is already booked'}), 409

        # Check for duplicate pending bookings by same tenant
        pending_booking = Booking.query.filter_by(
            tenant_id=tenant_id,
            property_id=property_id,
            status=BookingStatus.PENDING
        ).first()
        if pending_booking:
            return jsonify({'status': 'error', 'message': 'You already have a pending booking for this property'}), 409

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Validate date logic
        if start_date >= end_date:
            return jsonify({'status': 'error', 'message': 'Start date must be before end date'}), 400

        if start_date < datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0):
            return jsonify({'status': 'error', 'message': 'Start date cannot be in the past'}), 400

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

        logging.info(f"Booking created: tenant_id={tenant_id}, property_id={property_id}, booking_id={booking.id}")

        return jsonify({
            'status': 'success',
            'message': 'Booking created successfully',
            'data': {
                'booking_id': booking.id,
                'booking': booking.to_dict()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating booking: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
