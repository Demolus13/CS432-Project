# FixIIT - Campus Maintenance Request System

A web application for managing campus maintenance requests. Students can submit maintenance requests, administrators can view and manage them, and technicians can be assigned to resolve issues.

## Project Structure

- `app.py` - Backend API server
- `frontend/app.py` - Frontend Flask application

## Setup and Running

### Backend API

1. Install dependencies:
   ```
   pip install flask flask-cors mysql-connector-python psycopg2-binary bcrypt pyjwt
   ```

2. Run the backend server:
   ```
   python app.py
   ```
   The backend API will run on http://localhost:5000

### Frontend Application

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   pip install flask requests
   ```

3. Run the frontend application:
   ```
   python app.py
   ```
   The frontend will be available at http://localhost:8000

## Features

- User authentication (login/registration)
- Student maintenance request submission
- Admin dashboard for request management
- Technician assignment
- Notification system

## Database

The application uses two MySQL databases:
- `cs432g6` - Main application database
- `cs432cims` - Notifications database

## Login API Example

```json
// Request to /api/auth/login
{
  "user": "username",
  "password": "password123"
}

// Response
{
  "message": "Login successful",
  "username": "username",
  "role": "admin"
}
```
