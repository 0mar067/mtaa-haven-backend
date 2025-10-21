# mtaa-haven-backend

## API Endpoints

### GET /
- **Description**: Root endpoint to check if the backend is working.
- **Response**: Plain text "Backend is working!"

### GET /api/test
- **Description**: Test endpoint for API functionality.
- **Response**: JSON `{"message": "API is working"}`

### POST /api/test
- **Description**: Test endpoint for POST requests with JSON data.
- **Request Body**: JSON object (required, cannot be empty)
- **Responses**:
  - **200 OK**: `{"received": <data>, "message": "Data received successfully"}`
  - **400 Bad Request**: `{"error": "No JSON data provided"}` or `{"error": "Invalid JSON data"}`

### Error Responses
- **404 Not Found**: For non-existent endpoints
- **405 Method Not Allowed**: For unsupported HTTP methods on existing endpoints
- **400 Bad Request**: For malformed requests

## Setup
1. Create virtual environment: `python3 -m venv venv`
2. Activate virtual environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python app.py`
5. The server will run on http://127.0.0.1:5000

## Testing with curl
- GET root: `curl http://127.0.0.1:5000/`
- GET API test: `curl http://127.0.0.1:5000/api/test`
- POST API test: `curl -X POST http://127.0.0.1:5000/api/test -H "Content-Type: application/json" -d '{"key": "value"}'`