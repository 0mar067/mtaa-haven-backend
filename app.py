from flask import Flask, request, jsonify
from flask_migrate import Migrate
import os
from database import db
from models import User, Property, Payment, Issue, UserType, PropertyStatus, PaymentStatus, IssueStatus, IssueType
from datetime import datetime
from decimal import Decimal

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "mtaa_heaven.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return "Backend is working!"

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working'})

@app.route('/api/test', methods=['POST'])
def test_post():
    try:
        data = request.get_json()
        if data is None or data == {}:
            return jsonify({'error': 'No JSON data provided'}), 400
        return jsonify({'received': data, 'message': 'Data received successfully'})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400

# Users CRUD
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'email': u.email, 'first_name': u.first_name, 'last_name': u.last_name, 'user_type': u.user_type.value} for u in users])

@app.route('/api/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({'id': user.id, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name, 'phone': user.phone, 'user_type': user.user_type.value})

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(email=data['email'], password_hash=data['password'], first_name=data['first_name'], last_name=data['last_name'], phone=data.get('phone'), user_type=UserType(data['user_type']))
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id}), 201

@app.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        if key == 'user_type':
            setattr(user, key, UserType(value))
        elif hasattr(user, key):
            setattr(user, key, value)
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# Properties CRUD
@app.route('/api/properties', methods=['GET'])
def get_properties():
    properties = Property.query.all()
    return jsonify([{'id': p.id, 'title': p.title, 'address': p.address, 'rent_amount': str(p.rent_amount), 'status': p.status.value} for p in properties])

@app.route('/api/properties/<int:id>', methods=['GET'])
def get_property(id):
    prop = Property.query.get_or_404(id)
    return jsonify({'id': prop.id, 'title': prop.title, 'description': prop.description, 'address': prop.address, 'city': prop.city, 'rent_amount': str(prop.rent_amount), 'bedrooms': prop.bedrooms, 'bathrooms': prop.bathrooms, 'status': prop.status.value, 'landlord_id': prop.landlord_id})

@app.route('/api/properties', methods=['POST'])
def create_property():
    data = request.get_json()
    prop = Property(title=data['title'], description=data.get('description'), address=data['address'], city=data['city'], rent_amount=Decimal(str(data['rent_amount'])), bedrooms=data['bedrooms'], bathrooms=data['bathrooms'], landlord_id=data['landlord_id'])
    db.session.add(prop)
    db.session.commit()
    return jsonify({'id': prop.id}), 201

@app.route('/api/properties/<int:id>', methods=['PUT'])
def update_property(id):
    prop = Property.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        if key == 'status':
            setattr(prop, key, PropertyStatus(value))
        elif key == 'rent_amount':
            setattr(prop, key, Decimal(str(value)))
        elif hasattr(prop, key):
            setattr(prop, key, value)
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/properties/<int:id>', methods=['DELETE'])
def delete_property(id):
    prop = Property.query.get_or_404(id)
    db.session.delete(prop)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# Payments CRUD
@app.route('/api/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.all()
    return jsonify([{'id': p.id, 'amount': str(p.amount), 'payment_date': p.payment_date.isoformat(), 'status': p.status.value, 'user_id': p.user_id, 'property_id': p.property_id} for p in payments])

@app.route('/api/payments/<int:id>', methods=['GET'])
def get_payment(id):
    payment = Payment.query.get_or_404(id)
    return jsonify({'id': payment.id, 'amount': str(payment.amount), 'payment_date': payment.payment_date.isoformat(), 'due_date': payment.due_date.isoformat(), 'status': payment.status.value, 'user_id': payment.user_id, 'property_id': payment.property_id})

@app.route('/api/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    payment = Payment(amount=Decimal(str(data['amount'])), payment_date=datetime.fromisoformat(data['payment_date']), due_date=datetime.fromisoformat(data['due_date']), user_id=data['user_id'], property_id=data['property_id'])
    db.session.add(payment)
    db.session.commit()
    return jsonify({'id': payment.id}), 201

@app.route('/api/payments/<int:id>', methods=['PUT'])
def update_payment(id):
    payment = Payment.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        if key == 'status':
            setattr(payment, key, PaymentStatus(value))
        elif key in ['amount']:
            setattr(payment, key, Decimal(str(value)))
        elif key in ['payment_date', 'due_date']:
            setattr(payment, key, datetime.fromisoformat(value))
        elif hasattr(payment, key):
            setattr(payment, key, value)
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    payment = Payment.query.get_or_404(id)
    db.session.delete(payment)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# Issues CRUD
@app.route('/api/issues', methods=['GET'])
def get_issues():
    issues = Issue.query.all()
    return jsonify([{'id': i.id, 'title': i.title, 'issue_type': i.issue_type.value, 'status': i.status.value, 'reporter_id': i.reporter_id, 'property_id': i.property_id} for i in issues])

@app.route('/api/issues/<int:id>', methods=['GET'])
def get_issue(id):
    issue = Issue.query.get_or_404(id)
    return jsonify({'id': issue.id, 'title': issue.title, 'description': issue.description, 'issue_type': issue.issue_type.value, 'status': issue.status.value, 'priority': issue.priority, 'reporter_id': issue.reporter_id, 'property_id': issue.property_id})

@app.route('/api/issues', methods=['POST'])
def create_issue():
    data = request.get_json()
    issue = Issue(title=data['title'], description=data['description'], issue_type=IssueType(data['issue_type']), reporter_id=data['reporter_id'], property_id=data['property_id'])
    db.session.add(issue)
    db.session.commit()
    return jsonify({'id': issue.id}), 201

@app.route('/api/issues/<int:id>', methods=['PUT'])
def update_issue(id):
    issue = Issue.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        if key == 'status':
            setattr(issue, key, IssueStatus(value))
        elif key == 'issue_type':
            setattr(issue, key, IssueType(value))
        elif hasattr(issue, key):
            setattr(issue, key, value)
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/issues/<int:id>', methods=['DELETE'])
def delete_issue(id):
    issue = Issue.query.get_or_404(id)
    db.session.delete(issue)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

if __name__ == '__main__':
    app.run(debug=True)