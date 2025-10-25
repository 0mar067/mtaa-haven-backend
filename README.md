# Mtaa Haven Backend

A comprehensive property rental management system built with Flask, providing APIs for landlords, tenants, and property management.

## Features

- **User Management**: Registration and authentication for landlords and tenants
- **Property Management**: CRUD operations for rental properties with image uploads
- **Booking System**: Property booking and rental agreements
- **Payment Processing**: Rent payment tracking and management
- **Issue Tracking**: Maintenance request and dispute management
- **Notifications**: Automated rent reminders and system notifications
- **Image Management**: Cloud-based property image storage with thumbnails

## Authentication & Roles

### User Types
- **LANDLORD**: Can create/manage properties, view tenant information, manage payments
- **TENANT**: Can view rented properties, make payments, submit issues

### Authentication Flow
1. Register with email, password, and user type
2. Login to receive JWT token
3. Include token in `Authorization: Bearer <token>` header for protected routes

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Database
SQLALCHEMY_DATABASE_URI=sqlite:///mtaa_heaven.db

# JWT
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Email (optional - for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Cloudinary (for image uploads)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## API Endpoints

### Authentication

#### POST /api/register
Register a new user (landlord or tenant).
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "user_type": "TENANT",
  "password": "password123"
}
```

#### POST /api/login
Login with email and password.
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Properties

#### GET /api/properties
Get properties with optional filtering. Public access with optional authentication for user-specific filtering.

**Query Parameters:**
- `location`: Filter by city (case-insensitive)
- `price_min`: Minimum rent amount
- `price_max`: Maximum rent amount
- `type`: Filter by property type (hostel, airbnb, apartment)

**Response includes:**
- `primary_image_url`: URL of the primary property image
- `image_count`: Total number of images
- `images`: Array of image objects with URLs and thumbnails

#### POST /api/properties
Create a new property (landlords only).
- **Auth Required**: Bearer token
- **Body**: Property details (title, address, rent_amount, etc.)

#### GET /api/properties/{property_id}
Get specific property details.
- **Auth Required**: Bearer token (user must own or rent the property)

#### PUT /api/properties/{property_id}
Update property (landlords only).
- **Auth Required**: Bearer token

#### DELETE /api/properties/{property_id}
Delete property (landlords only).
- **Auth Required**: Bearer token

### Property Images

#### POST /api/properties/{property_id}/images
Upload images for a property (landlords only).
- **Auth Required**: Bearer token
- **Content-Type**: `multipart/form-data`
- **Files**: `images` (multiple files allowed, max 10 per property)
- **Form Data**: `is_primary` (boolean, optional)

**Supported formats**: png, jpg, jpeg, gif, webp
**Max file size**: 5MB per image
**Automatic thumbnail generation**: 300x200px

#### GET /api/properties/{property_id}/images
Get all images for a property.
- **Response**: Array of image objects with URLs, thumbnails, and metadata

#### DELETE /api/properties/{property_id}/images/{image_id}
Delete a specific property image (landlords only).
- **Auth Required**: Bearer token

#### PUT /api/properties/{property_id}/images/{image_id}/primary
Set an image as the primary image for a property (landlords only).
- **Auth Required**: Bearer token

### Dashboard

#### GET /api/dashboard/stats
Get landlord statistics (landlords only).
- **Auth Required**: Bearer token
```json
{
  "status": "success",
  "data": {
    "properties": 5,
    "tenants": 12,
    "issues": 3,
    "payments": 24
  }
}
```

### Payments

#### GET /api/payments
Get payments for current user.
- **Auth Required**: Bearer token

#### POST /api/payments
Create a new payment.
- **Auth Required**: Bearer token
- **Body**: Payment details (booking_id, amount, payment_method)

### Issues

#### GET /api/issues
Get issues for current user (role-based filtering).
- **Auth Required**: Bearer token

#### POST /api/issues
Create a new issue.
- **Auth Required**: Bearer token

### Bookings

#### POST /api/bookings
Create a new property booking.
- **Body**: Booking details (tenant_id, property_id, start_date, end_date)

### Notifications

#### GET /api/notifications
Get notifications for user.

#### POST /api/notifications
Create a notification (admin/system use).

### Test Endpoints

#### GET /
- **Description**: Root endpoint to check if the backend is working.
- **Response**: Plain text "Backend is working!"

#### GET /api/test
- **Description**: Test endpoint for API functionality.
- **Response**: JSON `{"message": "API is working"}`

#### POST /api/test
- **Description**: Test endpoint for POST requests with JSON data.
- **Request Body**: JSON object (required, cannot be empty)
- **Responses**:
  - **200 OK**: `{"received": <data>, "message": "Data received successfully"}`
  - **400 Bad Request**: `{"error": "No JSON data provided"}` or `{"error": "Invalid JSON data"}`

## Response Structure

All API responses follow a consistent structure:

**Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mtaa-haven-backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with the required variables (see Environment Variables section)

5. **Initialize database**
   ```bash
   export FLASK_APP=app.py
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python app.py
   ```
   The server will run on http://127.0.0.1:5000

## Testing with curl

### Authentication
```bash
# Register
curl -X POST http://127.0.0.1:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"landlord@example.com","first_name":"John","last_name":"Doe","user_type":"LANDLORD","password":"password123"}'

# Login
curl -X POST http://127.0.0.1:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"landlord@example.com","password":"password123"}'
```

### Properties
```bash
# Get properties (public)
curl http://127.0.0.1:5000/api/properties

# Get properties with auth
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://127.0.0.1:5000/api/properties

# Create property
curl -X POST http://127.0.0.1:5000/api/properties \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Beautiful Apartment",
    "address": "123 Main St",
    "city": "Nairobi",
    "rent_amount": 25000,
    "bedrooms": 2,
    "bathrooms": 1
  }'
```

### Image Upload
```bash
# Upload images
curl -X POST http://127.0.0.1:5000/api/properties/1/images \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "images=@property1.jpg" \
  -F "images=@property2.jpg" \
  -F "is_primary=true"
```

### Dashboard
```bash
# Get stats
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://127.0.0.1:5000/api/dashboard/stats
```

## Deployment

The application includes a GitHub Actions workflow (`.github/workflows/backend-ci.yml`) that:
- Installs dependencies
- Runs tests
- Checks routes with `python -m flask routes`
- Deploys to Render on main branch pushes

## Technologies Used

- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Flask-Migrate**: Database migrations
- **PyJWT**: JSON Web Tokens for authentication
- **Flask-Mail**: Email notifications
- **Cloudinary**: Cloud image storage and processing
- **Pillow**: Image processing
- **Flasgger**: API documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.