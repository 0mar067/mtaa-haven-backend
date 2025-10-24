from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_mail import Mail
import os
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import db
from models import User, Property, Payment, Issue, Notification
from routes import api
from models import User, Property, Payment, Issue, UserType, PropertyStatus, PaymentStatus, IssueStatus, IssueType
from datetime import datetime
from decimal import Decimal

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'sqlite:///{os.path.join(basedir, "mtaa_heaven.db")}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

# Email configuration (mock for now)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with actual email
app.config['MAIL_PASSWORD'] = 'your-password'  # Replace with actual password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Register blueprints
app.register_blueprint(api, url_prefix='/api')


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
        return jsonify({
            'received': data,
            'message': 'Data received successfully'
        })
    except Exception:
        return jsonify({'error': 'Invalid JSON data'}), 400

@app.route('/api/register', methods=['POST'])
def register():
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
    data = request.get_json()
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')  
    password = data.get('password')

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    user = User.query.filter_by(email=email).first() or User.query.filter_by(first_name=first_name, last_name=last_name).first()
    if (user and check_password_hash(user.password_hash, password)) or (user.first_name == first_name and user.last_name == last_name and check_password_hash(user.password_hash, password)):
        return jsonify({"message":"logged in successful", "user": user.to_dict()})
    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True)


