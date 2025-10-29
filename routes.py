from flask import Blueprint, jsonify, request
from database import db
from models import User, Property, Payment, Issue, UserType, IssueStatus, PaymentStatus
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Mtaa Haven API is running"}), 200

@api.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return jsonify([{'id': u.id, 'name': f"{u.first_name} {u.last_name}", 'email': u.email, 'role': u.user_type.value} for u in users])
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@api.route('/register', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or not all(k in data for k in ['email', 'first_name', 'last_name', 'user_type', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        from werkzeug.security import generate_password_hash
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            user_type=UserType(data['user_type'].upper()),
            password_hash=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created', 'id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api.route('/properties', methods=['POST'])
def create_property():
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'rent', 'location', 'landlord_id']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        prop = Property(
            title=data['title'],
            description=data.get('description', ''),
            address=data.get('address', data['location']),
            city=data['location'],
            rent_amount=data['rent'],
            bedrooms=data.get('bedrooms', 1),
            bathrooms=data.get('bathrooms', 1),
            type=data.get('type'),
            landlord_id=data['landlord_id']
        )
        db.session.add(prop)
        db.session.commit()
        return jsonify({'message': 'Property created', 'id': prop.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api.route('/properties', methods=['GET'])
def get_properties():
    try:
        query = Property.query
        location = request.args.get('location')
        if location:
            query = query.filter(Property.city.ilike(f'%{location}%'))
        price_min = request.args.get('price_min')
        if price_min:
            query = query.filter(Property.rent_amount >= float(price_min))
        price_max = request.args.get('price_max')
        if price_max:
            query = query.filter(Property.rent_amount <= float(price_max))
        type_ = request.args.get('type')
        if type_:
            query = query.filter(Property.type == type_)
        props = query.all()
        return jsonify([{'id': p.id, 'title': p.title, 'description': p.description, 'rent': str(p.rent_amount), 'location': p.city, 'type': p.type} for p in props])
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@api.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    if not data or not all(k in data for k in ['user_id', 'property_id', 'amount']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        pay = Payment(
            user_id=data['user_id'],
            property_id=data['property_id'],
            amount=data['amount']
        )
        db.session.add(pay)
        db.session.commit()
        return jsonify({'message': 'Payment created', 'id': pay.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api.route('/payments/<int:id>', methods=['GET'])
def get_payment(id):
    try:
        pay = Payment.query.get_or_404(id)
        return jsonify({'id': pay.id, 'amount': str(pay.amount), 'status': pay.status.value, 'user_id': pay.user_id, 'property_id': pay.property_id})
    except Exception as e:
        return jsonify({'error': 'Payment not found'}), 404

@api.route('/issues', methods=['POST'])
def create_issue():
    data = request.get_json()
    if not data or not all(k in data for k in ['user_id', 'property_id', 'description']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        from models import IssueType
        issue = Issue(
            title=data.get('title', 'Issue'),
            description=data['description'],
            issue_type=IssueType(data.get('issue_type', 'MAINTENANCE')),
            reporter_id=data['user_id'],
            property_id=data['property_id']
        )
        db.session.add(issue)
        db.session.commit()
        return jsonify({'message': 'Issue created', 'id': issue.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api.route('/issues', methods=['GET'])
def get_issues():
    try:
        issues = Issue.query.all()
        return jsonify([{'id': i.id, 'description': i.description, 'status': i.status.value, 'user_id': i.reporter_id, 'property_id': i.property_id} for i in issues])
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

# Landlord-specific endpoints
@api.route('/properties/landlord/<int:landlord_id>', methods=['GET'])
def get_landlord_properties(landlord_id):
    try:
        properties = Property.query.filter_by(landlord_id=landlord_id).all()
        return jsonify({
            'data': [{
                'id': p.id, 
                'title': p.title, 
                'rent_amount': float(p.rent_amount), 
                'status': p.status.value,
                'city': p.city,
                'bedrooms': p.bedrooms,
                'bathrooms': p.bathrooms
            } for p in properties]
        })
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@api.route('/bookings/landlord/<int:landlord_id>', methods=['GET'])
def get_landlord_bookings(landlord_id):
    try:
        from models import Booking
        bookings = db.session.query(Booking).join(Property).filter(Property.landlord_id == landlord_id).all()
        return jsonify({
            'data': [{
                'id': b.id,
                'property_id': b.property_id,
                'tenant_id': b.tenant_id,
                'start_date': b.start_date.isoformat() if b.start_date else None,
                'end_date': b.end_date.isoformat() if b.end_date else None,
                'status': b.status.value
            } for b in bookings]
        })
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@api.route('/issues/landlord/<int:landlord_id>', methods=['GET'])
def get_landlord_issues(landlord_id):
    try:
        issues = db.session.query(Issue).join(Property).filter(Property.landlord_id == landlord_id).all()
        return jsonify({
            'data': [{
                'id': i.id,
                'title': i.title,
                'description': i.description,
                'status': i.status.value,
                'priority': i.priority,
                'property_id': i.property_id,
                'created_at': i.created_at.isoformat() if i.created_at else None
            } for i in issues]
        })
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@api.route('/issues/<int:issue_id>/resolve', methods=['PATCH'])
def resolve_issue(issue_id):
    try:
        issue = Issue.query.get_or_404(issue_id)
        issue.status = IssueStatus.RESOLVED
        issue.resolved_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Issue resolved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@api.route('/payments/confirm/<int:payment_id>', methods=['PATCH'])
def confirm_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        payment.status = PaymentStatus.COMPLETED
        payment.payment_date = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Payment confirmed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500