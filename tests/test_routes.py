import pytest
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Property, Booking, Payment, Issue, UserType, PropertyStatus, BookingStatus, PaymentStatus, IssueStatus, IssueType
from datetime import datetime, timedelta
import jwt


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


@pytest.fixture
def auth_headers(client):
    """Create a test user and return authorization headers"""
    # Create a test user
    user_data = {
        'email': 'testauth@example.com',
        'first_name': 'Test',
        'last_name': 'Auth',
        'user_type': 'LANDLORD',
        'password': 'password123'
    }
    client.post('/api/register', data=json.dumps(user_data), content_type='application/json')

    # Login to get token
    login_data = {'email': 'testauth@example.com', 'password': 'password123'}
    response = client.post('/api/login', data=json.dumps(login_data), content_type='application/json')
    token = json.loads(response.data)['token']

    return {'Authorization': f'Bearer {token}'}


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
    assert 'token' in response_data
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


def test_create_booking_success(client):
    """Test successful booking creation"""
    # Create a landlord first
    landlord_data = {
        'email': 'landlord@example.com',
        'first_name': 'Land',
        'last_name': 'Lord',
        'user_type': 'LANDLORD',
        'password': 'password123'
    }
    client.post('/api/register',
               data=json.dumps(landlord_data),
               content_type='application/json')

    # Create a tenant
    tenant_data = {
        'email': 'tenant@example.com',
        'first_name': 'Ten',
        'last_name': 'Ant',
        'user_type': 'TENANT',
        'password': 'password123'
    }
    tenant_response = client.post('/api/register',
                                 data=json.dumps(tenant_data),
                                 content_type='application/json')
    tenant_id = json.loads(tenant_response.data)['user']['id']

    # Create a property
    landlord = User.query.filter_by(email='landlord@example.com').first()
    property_obj = Property(
        title='Test Property',
        description='A test property',
        address='123 Test St',
        city='Test City',
        rent_amount=25000.00,
        bedrooms=2,
        bathrooms=1,
        landlord_id=landlord.id,
        status=PropertyStatus.AVAILABLE
    )
    db.session.add(property_obj)
    db.session.commit()

    # Create booking
    booking_data = {
        'tenant_id': tenant_id,
        'property_id': property_obj.id,
        'start_date': (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'end_date': (datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d')
    }

    response = client.post('/api/bookings',
                          data=json.dumps(booking_data),
                          content_type='application/json')

    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Booking created successfully' in response_data['message']
    assert 'booking_id' in response_data
    assert 'booking' in response_data


def test_create_booking_missing_fields(client):
    """Test booking creation with missing required fields"""
    data = {
        'tenant_id': 1,
        'property_id': 1
        # Missing start_date and end_date
    }

    response = client.post('/api/bookings',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'Missing required fields' in response_data['error']


def test_create_booking_invalid_tenant(client):
    """Test booking creation with non-existent tenant"""
    data = {
        'tenant_id': 999,
        'property_id': 1,
        'start_date': '2025-10-20',
        'end_date': '2026-10-20'
    }

    response = client.post('/api/bookings',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 404
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'Tenant not found' in response_data['error']


def test_create_booking_invalid_property(client):
    """Test booking creation with non-existent property"""
    # Create a tenant first
    tenant_data = {
        'email': 'tenant2@example.com',
        'first_name': 'Ten2',
        'last_name': 'Ant2',
        'user_type': 'TENANT',
        'password': 'password123'
    }
    tenant_response = client.post('/api/register',
                                 data=json.dumps(tenant_data),
                                 content_type='application/json')
    tenant_id = json.loads(tenant_response.data)['user']['id']

    data = {
        'tenant_id': tenant_id,
        'property_id': 999,
        'start_date': '2025-10-20',
        'end_date': '2026-10-20'
    }

    response = client.post('/api/bookings',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 404
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'Property not found' in response_data['error']


def test_create_booking_invalid_dates(client):
    """Test booking creation with invalid date format"""
    # Create tenant and property first
    tenant_data = {
        'email': 'tenant3@example.com',
        'first_name': 'Ten3',
        'last_name': 'Ant3',
        'user_type': 'TENANT',
        'password': 'password123'
    }
    tenant_response = client.post('/api/register',
                                 data=json.dumps(tenant_data),
                                 content_type='application/json')
    tenant_id = json.loads(tenant_response.data)['user']['id']

    landlord_data = {
        'email': 'landlord2@example.com',
        'first_name': 'Land2',
        'last_name': 'Lord2',
        'user_type': 'LANDLORD',
        'password': 'password123'
    }
    client.post('/api/register',
               data=json.dumps(landlord_data),
               content_type='application/json')

    landlord = User.query.filter_by(email='landlord2@example.com').first()
    property_obj = Property(
        title='Test Property 2',
        description='A test property',
        address='456 Test St',
        city='Test City',
        rent_amount=30000.00,
        bedrooms=3,
        bathrooms=2,
        landlord_id=landlord.id,
        status=PropertyStatus.AVAILABLE
    )
    db.session.add(property_obj)
    db.session.commit()

    data = {
        'tenant_id': tenant_id,
        'property_id': property_obj.id,
        'start_date': 'invalid-date',
        'end_date': '2026-10-20'
    }

    response = client.post('/api/bookings',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'Invalid date format' in response_data['error']


# Properties CRUD tests
def test_get_properties_unauthorized(client):
    """Test getting properties without authentication"""
    response = client.get('/api/properties')
    assert response.status_code == 401


def test_create_property_success(client, auth_headers):
    """Test successful property creation"""
    data = {
        'title': 'Test Property',
        'description': 'A beautiful test property',
        'address': '123 Test Street',
        'city': 'Test City',
        'rent_amount': 25000.00,
        'bedrooms': 2,
        'bathrooms': 1,
        'area_sqft': 1000
    }

    response = client.post('/api/properties',
                          data=json.dumps(data),
                          content_type='application/json',
                          headers=auth_headers)

    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Property created successfully' in response_data['message']
    assert 'property_id' in response_data
    assert 'property' in response_data


def test_create_property_missing_fields(client, auth_headers):
    """Test property creation with missing required fields"""
    data = {
        'title': 'Test Property',
        'description': 'A beautiful test property'
        # Missing required fields
    }

    response = client.post('/api/properties',
                          data=json.dumps(data),
                          content_type='application/json',
                          headers=auth_headers)

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert 'error' in response_data


def test_get_properties_success(client, auth_headers):
    """Test getting properties for authenticated user"""
    response = client.get('/api/properties', headers=auth_headers)

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert isinstance(response_data, list)


def test_update_property_success(client, auth_headers):
    """Test successful property update"""
    # First create a property
    data = {
        'title': 'Test Property',
        'description': 'A beautiful test property',
        'address': '123 Test Street',
        'city': 'Test City',
        'rent_amount': 25000.00,
        'bedrooms': 2,
        'bathrooms': 1
    }

    create_response = client.post('/api/properties',
                                 data=json.dumps(data),
                                 content_type='application/json',
                                 headers=auth_headers)
    property_id = json.loads(create_response.data)['property_id']

    # Update the property
    update_data = {
        'title': 'Updated Test Property',
        'rent_amount': 30000.00
    }

    response = client.put(f'/api/properties/{property_id}',
                         data=json.dumps(update_data),
                         content_type='application/json',
                         headers=auth_headers)

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Property updated successfully' in response_data['message']


def test_delete_property_success(client, auth_headers):
    """Test successful property deletion"""
    # First create a property
    data = {
        'title': 'Test Property',
        'description': 'A beautiful test property',
        'address': '123 Test Street',
        'city': 'Test City',
        'rent_amount': 25000.00,
        'bedrooms': 2,
        'bathrooms': 1
    }

    create_response = client.post('/api/properties',
                                 data=json.dumps(data),
                                 content_type='application/json',
                                 headers=auth_headers)
    property_id = json.loads(create_response.data)['property_id']

    # Delete the property
    response = client.delete(f'/api/properties/{property_id}', headers=auth_headers)

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Property deleted successfully' in response_data['message']


# Payments CRUD tests
def test_create_payment_success(client, auth_headers):
    """Test successful payment creation"""
    # First create a property
    property_data = {
        'title': 'Test Property',
        'description': 'A beautiful test property',
        'address': '123 Test Street',
        'city': 'Test City',
        'rent_amount': 25000.00,
        'bedrooms': 2,
        'bathrooms': 1
    }

    property_response = client.post('/api/properties',
                                   data=json.dumps(property_data),
                                   content_type='application/json',
                                   headers=auth_headers)
    property_id = json.loads(property_response.data)['property_id']

    # Create payment
    payment_data = {
        'amount': 25000.00,
        'due_date': '2025-12-01',
        'property_id': property_id,
        'payment_method': 'M-Pesa',
        'notes': 'Monthly rent'
    }

    response = client.post('/api/payments',
                          data=json.dumps(payment_data),
                          content_type='application/json',
                          headers=auth_headers)

    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Payment created successfully' in response_data['message']


def test_get_payments_success(client, auth_headers):
    """Test getting payments for authenticated user"""
    response = client.get('/api/payments', headers=auth_headers)

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert isinstance(response_data, list)


def test_update_payment_success(client, auth_headers):
    """Test successful payment update"""
    # First create a property and payment
    property_data = {
        'title': 'Test Property',
        'description': 'A beautiful test property',
        'address': '123 Test Street',
        'city': 'Test City',
        'rent_amount': 25000.00,
        'bedrooms': 2,
        'bathrooms': 1
    }

    property_response = client.post('/api/properties',
                                   data=json.dumps(property_data),
                                   content_type='application/json',
                                   headers=auth_headers)
    property_id = json.loads(property_response.data)['property_id']

    payment_data = {
        'amount': 25000.00,
        'due_date': '2025-12-01',
        'property_id': property_id
    }

    create_response = client.post('/api/payments',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=auth_headers)
    payment_id = json.loads(create_response.data)['payment_id']

    # Update payment
    update_data = {
        'status': 'COMPLETED',
        'payment_date': '2025-11-30'
    }

    response = client.put(f'/api/payments/{payment_id}',
                         data=json.dumps(update_data),
                         content_type='application/json',
                         headers=auth_headers)

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Payment updated successfully' in response_data['message']


# Issues CRUD tests
def test_create_issue_success(client, auth_headers):
    """Test successful issue creation"""
    # First create a property
    property_data = {
        'title': 'Test Property',
        'description': 'A beautiful test property',
        'address': '123 Test Street',
        'city': 'Test City',
        'rent_amount': 25000.00,
        'bedrooms': 2,
        'bathrooms': 1
    }

    property_response = client.post('/api/properties',
                                   data=json.dumps(property_data),
                                   content_type='application/json',
                                   headers=auth_headers)
    property_id = json.loads(property_response.data)['property_id']

    # Create issue
    issue_data = {
        'title': 'Leaky faucet',
        'description': 'The kitchen faucet is leaking',
        'issue_type': 'maintenance',
        'property_id': property_id,
        'priority': 'high'
    }

    response = client.post('/api/issues',
                          data=json.dumps(issue_data),
                          content_type='application/json',
                          headers=auth_headers)

    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Issue created successfully' in response_data['message']


def test_get_issues_success(client, auth_headers):
    """Test getting issues for authenticated user"""
    response = client.get('/api/issues', headers=auth_headers)

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'status' in response_data
    assert 'data' in response_data
    assert isinstance(response_data['data'], list)


def test_update_issue_success(client, auth_headers):
    """Test successful issue update"""
    # First create a property and issue
    property_data = {
        'title': 'Test Property',
        'description': 'A beautiful test property',
        'address': '123 Test Street',
        'city': 'Test City',
        'rent_amount': 25000.00,
        'bedrooms': 2,
        'bathrooms': 1
    }

    property_response = client.post('/api/properties',
                                   data=json.dumps(property_data),
                                   content_type='application/json',
                                   headers=auth_headers)
    property_id = json.loads(property_response.data)['property_id']

    issue_data = {
        'title': 'Leaky faucet',
        'description': 'The kitchen faucet is leaking',
        'issue_type': 'maintenance',
        'property_id': property_id
    }

    create_response = client.post('/api/issues',
                                 data=json.dumps(issue_data),
                                 content_type='application/json',
                                 headers=auth_headers)
    issue_id = json.loads(create_response.data)['data']['issue_id']

    # Update issue
    update_data = {
        'status': 'IN_PROGRESS',
        'priority': 'low'
    }

    response = client.put(f'/api/issues/{issue_id}',
                         data=json.dumps(update_data),
                         content_type='application/json',
                         headers=auth_headers)

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Issue updated successfully' in response_data['message']


# Authentication tests
def test_invalid_token(client):
    """Test accessing protected route with invalid token"""
    headers = {'Authorization': 'Bearer invalid-token'}
    response = client.get('/api/properties', headers=headers)

    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert 'error' in response_data


def test_missing_token(client):
    """Test accessing protected route without token"""
    response = client.get('/api/properties')

    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert 'error' in response_data
    assert 'Token is missing' in response_data['error']


# Email integration test
def test_create_notification_email_success(client):
    """Test creating notification with email sending"""
    data = {
        'title': 'Test Notification',
        'message': 'This is a test notification',
        'user_id': 1,
        'property_id': 1,
        'email': 'test@example.com'
    }

    response = client.post('/api/notifications',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'Notification created and email sent' in response_data['message']
