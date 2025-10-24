from flask import Flask
from flask_migrate import Migrate
from flask_mail import Mail
import os
from database import db
from models import User, Property, Payment, Issue, Notification
from routes import api

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "mtaa_heaven.db")}'
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
        return jsonify({'received': data, 'message': 'Data received successfully'})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400

if __name__ == '__main__':
    app.run(debug=True)