from flask import Flask
from flask_migrate import Migrate
import os
from database import db
from models import User, Property, Payment, Issue

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

if __name__ == '__main__':
    app.run(debug=True)