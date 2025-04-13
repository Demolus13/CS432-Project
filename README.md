# FixIIT API Documentation

This project provides a RESTful API for managing maintenance requests, user authentication, and administrative tasks for the FixIIT system.

## API Endpoints

### 1. Authentication

#### **Login**
- **Endpoint**: `/api/auth/login`
- **Method**: POST
- **Description**: Authenticates a user and returns a session token.
- **Tables Used**: `members`, `Login`
- **Example Request**:
  ```json
  {
    "user": "username",
    "password": "password123"
  }
  ```
- **Example Response**:
  ```json
  {
    "message": "Login successful",
    "username": "username",
    "role": "admin"
  }
  ```

#### **Check Authentication Status**
- **Endpoint**: `/api/auth/status`
- **Method**: GET
- **Description**: Checks if the user is authenticated.
- **Tables Used**: None
- **Example Response**:
  ```json
  {
    "message": "User is authenticated",
    "username": "username",
    "role": "admin",
    "expiry": 1699999999
  }
  ```

---

### 2. User Management (Admin Only)

#### **Add User**
- **Endpoint**: `/api/admin/add-user`
- **Method**: POST
- **Description**: Adds a new user to the system.
- **Tables Used**: `members`, `Login`
- **Example Request**:
  ```json
  {
    "username": "newuser",
    "password": "password123",
    "role": "member",
    "email": "newuser@example.com",
    "session_id": "12345",
    "DoB": "2000-01-01"
  }
  ```
- **Example Response**:
  ```json
  {
    "message": "User added successfully with default login credentials"
  }
  ```

#### **Delete User**
- **Endpoint**: `/api/admin/members/<int:member_id>`
- **Method**: DELETE
- **Description**: Deletes a user and their group mappings.
- **Tables Used**: `members`, `MemberGroupMapping`, `Login`
- **Example Request**:
  ```
  DELETE /api/admin/members/123
  ```
- **Example Response**:
  ```json
  {
    "message": "Member 123 deleted successfully"
  }
  ```

---

### 3. Maintenance Requests

#### **Get Maintenance Requests**
- **Endpoint**: `/api/maintenance/requests`
- **Method**: GET
- **Description**: Retrieves all maintenance requests (admin) or requests for a specific student (member).
- **Tables Used**: `maintenance_requests`, `students`
- **Example Request (Admin)**:
  ```
  GET /api/maintenance/requests
  ```
- **Example Request (Member)**:
  ```
  GET /api/maintenance/requests?student_id=22110087
  ```
- **Example Response**:
  ```json
  [
    {
      "Request_ID": 1,
      "Student_ID": 22110087,
      "Issue_Description": "Leaking water pipe in hostel",
      "Location": "Emiet, E 201",
      "Priority": "High",
      "Submission_Date": "2025-02-25 10:15:00",
      "Status": "submitted",
      "StudentName": "Parth Govale"
    }
  ]
  ```

#### **Create Maintenance Request**
- **Endpoint**: `/api/maintenance/request`
- **Method**: POST
- **Description**: Creates a new maintenance request.
- **Tables Used**: `maintenance_requests`, `notifications`
- **Example Request**:
  ```json
  {
    "student_id": 22110087,
    "issue_description": "Leaking water pipe in hostel",
    "location": "Emiet, E 201",
    "priority": "High"
  }
  ```
- **Example Response**:
  ```json
  {
    "message": "Maintenance request created successfully",
    "request_id": 1
  }
  ```

#### **Get Maintenance Request Details**
- **Endpoint**: `/api/maintenance/request/<int:request_id>`
- **Method**: GET
- **Description**: Retrieves detailed information about a specific maintenance request.
- **Tables Used**: `maintenance_requests`, `students`, `technician_assignments`, `maintenance_logs`, `feedback`
- **Example Request**:
  ```
  GET /api/maintenance/request/1
  ```
- **Example Response**:
  ```json
  {
    "Request_ID": 1,
    "Student_ID": 22110087,
    "Issue_Description": "Leaking water pipe in hostel",
    "Location": "Emiet, E 201",
    "Priority": "High",
    "Submission_Date": "2025-02-25 10:15:00",
    "Status": "submitted",
    "StudentName": "Parth Govale",
    "technician": {
      "Technician_ID": 2,
      "Name": "Sarah Connor",
      "Specialization": "Electrical"
    },
    "logs": [
      {
        "Log_ID": 1,
        "Request_ID": 1,
        "Technician_ID": 2,
        "Status_Update": "Leak detected, fixing underway.",
        "Updated_At": "2025-02-25 11:30:00",
        "TechnicianName": "Sarah Connor"
      }
    ],
    "feedback": {
      "Feedback_ID": 6,
      "Request_ID": 1,
      "Student_ID": 22110087,
      "Rating": 3,
      "Comments": "Plumbing issue fixed, but took longer than expected."
    }
  }
  ```

#### **Update Maintenance Request**
- **Endpoint**: `/api/maintenance/request/<int:request_id>`
- **Method**: PUT
- **Description**: Updates the status of a maintenance request.
- **Tables Used**: `maintenance_requests`, `notifications`
- **Example Request**:
  ```json
  {
    "status": "in_progress"
  }
  ```
- **Example Response**:
  ```json
  {
    "message": "Maintenance request status updated to in_progress"
  }
  ```

---

### 4. Technician Management

#### **Assign Technician**
- **Endpoint**: `/api/maintenance/assign-technician`
- **Method**: POST
- **Description**: Assigns a technician to a maintenance request.
- **Tables Used**: `technician_assignments`, `maintenance_requests`, `work_orders`, `notifications`
- **Example Request**:
  ```json
  {
    "request_id": 1,
    "technician_id": 2
  }
  ```
- **Example Response**:
  ```json
  {
    "message": "Technician assigned successfully"
  }
  ```

#### **Add Technician**
- **Endpoint**: `/api/admin/technicians`
- **Method**: POST
- **Description**: Adds a new technician to the system.
- **Tables Used**: `technicians`
- **Example Request**:
  ```json
  {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "contact_number": "1234567890",
    "specialization": "Plumbing"
  }
  ```
- **Example Response**:
  ```json
  {
    "message": "Technician added successfully",
    "technician_id": 6
  }
  ```

#### **Get Technicians**
- **Endpoint**: `/api/admin/technicians`
- **Method**: GET
- **Description**: Retrieves all technicians.
- **Tables Used**: `technicians`
- **Example Request**:
  ```
  GET /api/admin/technicians
  ```
- **Example Response**:
  ```json
  [
    {
      "Technician_ID": 1,
      "Name": "John Doe",
      "Email": "john.doe@example.com",
      "Contact_Number": "1234567890",
      "Specialization": "Plumbing"
    }
  ]
  ```

---

### 5. Feedback

#### **Submit Feedback**
- **Endpoint**: `/api/maintenance/feedback`
- **Method**: POST
- **Description**: Submits feedback for a completed maintenance request.
- **Tables Used**: `feedback`
- **Example Request**:
  ```json
  {
    "request_id": 1,
    "student_id": 22110087,
    "rating": 5,
    "comments": "Great service!"
  }
  ```
- **Example Response**:
  ```json
  {
    "message": "Feedback submitted successfully"
  }
  ```

---

### 6. Notifications

#### **Get Notifications**
- **Endpoint**: `/api/notifications/<int:student_id>`
- **Method**: GET
- **Description**: Retrieves notifications for a specific student.
- **Tables Used**: `notifications`
- **Example Request**:
  ```
  GET /api/notifications/22110087
  ```
- **Example Response**:
  ```json
  [
    {
      "Notification_ID": 1,
      "Student_ID": 22110087,
      "Message": "Your maintenance request has been submitted.",
      "Sent_At": "2025-02-25 10:16:00"
    }
  ]
  ```

---

### 7. Admin Dashboard

#### **Get Dashboard Data**
- **Endpoint**: `/api/admin/dashboard`
- **Method**: GET
- **Description**: Retrieves summary data for the admin dashboard.
- **Tables Used**: `maintenance_requests`, `technicians`, `technician_assignments`
- **Example Request**:
  ```
  GET /api/admin/dashboard
  ```
- **Example Response**:
  ```json
  {
    "status_counts": [
      {"Status": "submitted", "Count": 2},
      {"Status": "in_progress", "Count": 1}
    ],
    "priority_counts": [
      {"Priority": "High", "Count": 1},
      {"Priority": "Medium", "Count": 2}
    ],
    "recent_requests": [
      {
        "Request_ID": 1,
        "Student_ID": 22110087,
        "Issue_Description": "Leaking water pipe in hostel",
        "Location": "Emiet, E 201",
        "Priority": "High",
        "Submission_Date": "2025-02-25 10:15:00",
        "Status": "submitted",
        "StudentName": "Parth Govale"
      }
    ],
    "technician_workload": [
      {
        "Technician_ID": 2,
        "Name": "Sarah Connor",
        "Specialization": "Electrical",
        "AssignedRequests": 1
      }
    ]
  }
  ```

---

### 8. Database Connection

#### **Test Database Connection**
- **Endpoint**: `/api/db/connection`
- **Method**: GET
- **Description**: Tests the database connection.
- **Tables Used**: None
- **Example Request**:
  ```
  GET /api/db/connection
  ```
- **Example Response**:
  ```json
  {
    "message": "Database connection successful",
    "database": "cs432g6"
  }
  ```

---

### 9. Security Logs

#### **View Security Logs**
- **Endpoint**: `/api/admin/security-logs`
- **Method**: GET
- **Description**: Retrieves recent security logs.
- **Tables Used**: None
- **Example Request**:
  ```
  GET /api/admin/security-logs?lines=50
  ```
- **Example Response**:
  ```json
  {
    "security_logs": [
      "2025-02-25 10:15:00 - WARNING - Unauthorized access attempt detected.",
      "2025-02-25 10:16:00 - ERROR - Database connection failed."
    ],
    "count": 2
  }
  ```

---

### 10. Student Profile

#### **Get Student Details**
- **Endpoint**: `/api/student/<int:student_id>`
- **Method**: GET
- **Description**: Retrieves details of a specific student, including their maintenance requests and notifications.
- **Tables Used**: `students`, `maintenance_requests`, `notifications`
- **Example Request**:
  ```
  GET /api/student/22110087
  ```
- **Example Response**:
  ```json
  {
    "Student_ID": 22110087,
    "Name": "Parth Govale",
    "Email": "parth.govale@iitgn.ac.in",
    "Contact_Number": "9619869044",
    "Age": 20,
    "Image": "Parth.jpg",
    "maintenance_requests": [
      {
        "Request_ID": 1,
        "Issue_Description": "Leaking water pipe in hostel",
        "Location": "Emiet, E 201",
        "Priority": "High",
        "Submission_Date": "2025-02-25 10:15:00",
        "Status": "submitted"
      }
    ],
    "notifications": [
      {
        "Notification_ID": 1,
        "Message": "Your maintenance request has been submitted.",
        "Sent_At": "2025-02-25 10:16:00"
      }
    ]
  }
  ```
