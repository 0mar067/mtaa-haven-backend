import pytest
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_register_success(client):
    """Test successful user registration"""
    data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '+1234567890',
        'user_type': 'TENANT',
        'password': 'password123'
    }

    response = client.post('/api/register',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['Success'] == True
    assert 'user' in response_data
    assert response_data['user']['email'] == 'test@example.com'
    assert response_data['user']['first_name'] == 'John'
    assert response_data['user']['last_name'] == 'Doe'
    assert 'password_hash' not in response_data['user']


def test_register_missing_fields(client):
    """Test registration with missing required fields"""
    data = {
        'email': 'test@example.com',
        'first_name': 'John'
        # Missing last_name, user_type, password
    }

    response = client.post('/api/register',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'Missing required fields' in response_data['error']


def test_login_success(client):
    """Test successful login"""
    # First register a user
    data = {
        'email': 'login@example.com',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'user_type': 'LANDLORD',
        'password': 'password123'
    }
    client.post('/api/register',
               data=json.dumps(data),
               content_type='application/json')

    # Now login
    login_data = {
        'email': 'login@example.com',
        'password': 'password123'
    }

    response = client.post('/api/login',
                          data=json.dumps(login_data),
                          content_type='application/json')

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'logged in successful' in response_data['message']
    assert 'user' in response_data
    assert response_data['user']['email'] == 'login@example.com'


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    }

    response = client.post('/api/login',
                          data=json.dumps(login_data),
                          content_type='application/json')

    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'Invalid credentials' in response_data['error']


def test_get_notifications(client):
    """Test getting notifications"""
    response = client.get('/api/notifications')

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert isinstance(response_data, list)
    # Check that mock notifications are returned
    assert len(response_data) > 0
    assert 'title' in response_data[0]
    assert 'message' in response_data[0]
    assert 'type' in response_data[0]


def test_create_notification_success(client):
    """Test creating a notification"""
    data = {
        'title': 'Test Notification',
        'message': 'This is a test notification',
        'user_id': 1,
        'property_id': 1
    }

    response = client.post('/api/notifications',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'notification_id' in response_data


def test_create_notification_missing_data(client):
    """Test creating notification with missing data"""
    response = client.post('/api/notifications',
                          data=json.dumps({}),
                          content_type='application/json')

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert 'error' in response_data


def test_api_test_get(client):
    """Test GET /api/test endpoint"""
    response = client.get('/api/test')

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['message'] == 'API is working'


def test_api_test_post_success(client):
    """Test POST /api/test endpoint with valid data"""
    data = {'key': 'value', 'number': 42}

    response = client.post('/api/test',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'received' in response_data
    assert response_data['received'] == data
    assert 'message' in response_data


def test_api_test_post_empty_data(client):
    """Test POST /api/test endpoint with empty data"""
    response = client.post('/api/test',
                          data=json.dumps({}),
                          content_type='application/json')

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'No JSON data provided' in response_data['error']
