from flask import Flask, request, jsonify
from flask_migrate import Migrate
import os
from database import db

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'sqlite:///{os.path.join(basedir, "mtaa_heaven.db")}'
)
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
        return jsonify({
            'received': data,
            'message': 'Data received successfully'
        })
    except Exception:
        return jsonify({'error': 'Invalid JSON data'}), 400


if __name__ == '__main__':
    app.run(debug=True)
