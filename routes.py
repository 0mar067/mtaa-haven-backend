from flask import Blueprint, jsonify, request
from database import db
from models import User, Property, Payment, Issue, IssueType, IssueStatus
from werkzeug.security import check_password_hash
from mail_utils import send_welcome_email
import jwt
from datetime import datetime, timedelta
from flask import current_app

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

@api.route('/properties', methods=['POST'])
def create_property():
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'rent', 'location', 'landlord_id']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        prop = Property(
            title=data['title'],
            description=data.get('description', ''),
            rent_amount=data['rent'],
            city=data['location'],
            type=data.get('type'),
            longitude=data.get('longitude'),
            latitude=data.get('latitude'),
            landlord_id=data['landlord_id']
        )
        db.session.add(prop)
        db.session.commit()
        return jsonify({'message': 'Property created', 'id': prop.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api.route('/properties/<int:id>', methods=['PUT'])
def update_property(id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    try:
        prop = Property.query.get_or_404(id)
        if 'title' in data:
            prop.title = data['title']
        if 'description' in data:
            prop.description = data['description']
        if 'rent' in data:
            prop.rent_amount = data['rent']
        if 'location' in data:
            prop.city = data['location']
        if 'type' in data:
            prop.type = data['type']
        if 'longitude' in data:
            prop.longitude = data['longitude']
        if 'latitude' in data:
            prop.latitude = data['latitude']
        db.session.commit()
        return jsonify({'message': 'Property updated', 'id': prop.id}), 200
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
        return jsonify([{'id': p.id, 'title': p.title, 'description': p.description, 'rent': str(p.rent_amount), 'location': p.city, 'type': p.type, 'longitude': p.longitude, 'latitude': p.latitude} for p in props])
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
        issue = Issue(
            title=data.get('title', 'Issue'),
            description=data['description'],
            issue_type=IssueType.MAINTENANCE,
            reporter_id=data['user_id'],
            property_id=data['property_id'],
            status=IssueStatus.OPEN
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

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ['email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        user = User.query.filter_by(email=data['email']).first()
        if user and check_password_hash(user.password_hash, data['password']):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
            send_welcome_email(user)
            return jsonify({'message': 'Logged in & welcome email sent', 'token': token}), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500