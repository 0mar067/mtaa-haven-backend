from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "mtaa_heaven.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models after db initialization
from models import User, Property, Payment, Issue

@app.route('/')
def index():
    return {'message': 'MTAA Heaven Backend API'}

if __name__ == '__main__':
    app.run(debug=True)