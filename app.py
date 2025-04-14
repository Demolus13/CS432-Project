from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from functools import wraps
import mysql.connector
import psycopg2
import bcrypt
import jwt
import datetime
import logging
import hashlib
import traceback
import requests

# Import custom modules
import AddUser
import Login
import UpdateImage

# Helper function to hash a password using MD5.
def hash_password_md5(password):
    return hashlib.md5(password.encode()).hexdigest()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'CS'  # Change this in production

# Enable CORS support for cross-origin requests
CORS(app)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

# Database configurations
project_db_config = {
    "host": "10.0.116.125",  # Only the IP or hostname, no protocol information
    "user": "cs432g6",
    "password": "pZ3nLbKX",  # Use your real password here
    "database": "cs432g6"
}

cism_db_config = {
    "host": "10.0.116.125",
    "user": "cs432g6",
    "password": "pZ3nLbKX",  # Use your real password here
    "database": "cs432cims"
}

# Database connection function; default connects to CISM database.
def get_db_connection(use_cism=True):
    if use_cism:
        return mysql.connector.connect(**cism_db_config)
    else:
        return mysql.connector.connect(**project_db_config)

def log_cims_database_change(session_token, action, table_name, record_id, details, app_config, db_connection_func):
    """
    Log changes to the CIMS database both locally and to server logs.
    Only logs to server if session is valid.
    """
    try:
        # Always log locally
        log_message = f"CIMS DATABASE CHANGE: {action} | Table: {table_name} | Record: {record_id} | {details}"
        logging.info(log_message)

        # Validate session before logging to server
        if not session_token:
            logging.warning(f"Attempted database change without session token: {log_message}")
            return False

        try:
            # Decode the JWT token to verify and get user information
            decoded = jwt.decode(session_token, app_config['SECRET_KEY'], algorithms=["HS256"])
            user_id = decoded.get('session_id')
            username = decoded.get('user')

            # If successful, log to server database
            conn = db_connection_func(False)  # True for CIMS database
            cursor = conn.cursor()

            # Get request IP and user agent if available
            ip_address = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent') if request else None

            # Insert into audit_logs table
            cursor.execute("""
                INSERT INTO audit_logs
                (User_ID, Username, Action, Table_Name, Record_ID, Details, IP_Address, User_Agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                username,
                action,
                table_name,
                str(record_id),
                details,
                ip_address,
                user_agent
            ))

            conn.commit()
            logging.info(f"Server log created for {action} by {username}")
            return True

        except jwt.ExpiredSignatureError:
            logging.warning(f"Expired session attempted database change: {log_message}")
            return False
        except jwt.InvalidTokenError:
            logging.warning(f"Invalid session attempted database change: {log_message}")
            return False

    except Exception as e:
        logging.error(f"Error logging database change: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Role-based access control decorator
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get('session_token')

            # Fallback to Authorization header
            if not token and 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remove the Bearer prefix

            # Fallback to token passed as query parameter
            if not token and 'token' in request.args:
                token = request.args.get('token')

            if not token:
                return jsonify({"error": "Authentication required"}), 401

            try:
                decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                if decoded["role"] not in allowed_roles:
                    logging.warning(
                        f"Access denied: User {decoded['user']} with role {decoded['role']} attempted to access {request.path}"
                    )
                    return jsonify({"error": "Insufficient permissions"}), 403

                request.user = decoded  # Add user info to request context

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Session expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ----------------------- API ROUTES -----------------------

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Hello, you are welcome"}), 200

# ----------------------- AUTHENTICATION -----------------------

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('user')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT ID FROM members WHERE UserName = %s", (username,))
        member = cursor.fetchone()
        if not member:
            return jsonify({"error": "User not found"}), 404

        member_id = member['ID']
        cursor.execute("SELECT Password, Role FROM Login WHERE MemberID = %s", (member_id,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    hashed_password = hashlib.md5(password.encode()).hexdigest()
    if not user or hashed_password != user['Password']:
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        "user": username,
        "role": user['Role'],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "session_id": member_id
    }, app.config['SECRET_KEY'], algorithm="HS256")

    response = make_response(jsonify({
        "message": "Login successful",
        "username": username,
        "role": user['Role']
    }))
    response.set_cookie('session_token', token, max_age=3600, httponly=True)

    # Update session in database using the Login module.
    login_instance = Login.Login(request, get_db_connection(), logging, app.config['SECRET_KEY'])
    login_instance.get_session()
    if login_instance.response:
        return login_instance.response

    return response

@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({"error": "No session found"}), 401

    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Session expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid session token"}), 401

    return jsonify({
        "message": "User is authenticated",
        "username": decoded["user"],
        "role": decoded["role"],
        "expiry": decoded["exp"]
    }), 200

# ----------------------- USER MANAGEMENT (ADMIN) -----------------------

# Helper function to check if any users exist
def any_users_exist():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    except Exception as e:
        logging.error(f"Error checking if users exist: {str(e)}")
        return True  # Assume users exist in case of error

@app.route('/api/admin/add-user', methods=['POST'])
def api_add_user():
    session_id = request.json.get('session_id')

    # Check if this is the first user registration
    is_first_user = not any_users_exist()

    # If it's not the first user, require admin authentication
    if not is_first_user:
        token = request.cookies.get('session_token')

        # Fallback to Authorization header
        if not token and 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove the Bearer prefix

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        try:
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            if decoded["role"] != 'admin':
                logging.warning(
                    f"Access denied: User {decoded['user']} with role {decoded['role']} attempted to add a user"
                )
                return jsonify({"error": "Admin privileges required"}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid session token"}), 401

    # If this is the first user, force the role to be admin
    if is_first_user and request.json:
        request_data = request.json.copy()
        request_data['role'] = 'admin'  # Override role to admin for first user
        request.json = request_data

    # Process the user creation
    out = AddUser.AddUser(request, logging, get_db_connection())

    # Log the change if successful
    token = request.cookies.get('session_token')
    if hasattr(out, 'success') and out.success and hasattr(out, 'member_id') and out.member_id:
        # For first user, we don't have a token yet
        if is_first_user:
            logging.info(f"First admin user created: {out.username}, Email: {out.email}")
        else:
            log_cims_database_change(
                token,
                "INSERT",
                "members",
                out.member_id,
                f"Added new member: {out.username}, Email: {out.email}",
                app.config,
                get_db_connection
            )

    # Create a custom response with the is_first_user flag
    if hasattr(out, 'success') and out.success:
        if hasattr(out, 'message') and isinstance(out.message, dict):
            response_data = out.message
        else:
            response_data = {"message": "User created successfully"}

        # Add the is_first_user flag
        response_data["is_first_user"] = is_first_user

        return jsonify(response_data), 200
    else:
        return out.response()

@app.route('/api/admin/members/<int:member_id>', methods=['DELETE'])
@role_required(['admin'])
def api_delete_member(member_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT GroupID FROM MemberGroupMapping WHERE MemberID = %s", (member_id,))
        group_mappings = cursor.fetchall()

        cursor.execute("SELECT UserName, emailID FROM members WHERE ID = %s", (member_id,))
        member = cursor.fetchone()
        if not member:
            return jsonify({"error": "Member not found"}), 404

        member_name = member[0]
        member_email = member[1]

        if not group_mappings:
            cursor.execute("DELETE FROM Login WHERE MemberID = %s", (str(member_id),))
            cursor.execute("DELETE FROM members WHERE ID = %s", (member_id,))
            conn.commit()

            # Using the correct function name
            token = request.cookies.get('session_token')
            log_cims_database_change(
                token,
                "DELETE",
                "members",
                member_id,
                f"Deleted member: {member_name}, Email: {member_email}",
                app.config,
                get_db_connection
            )
            return jsonify({"message": f"Member {member_id} deleted successfully"}), 200
        else:
            cursor.execute("DELETE FROM MemberGroupMapping WHERE MemberID = %s", (member_id,))
            conn.commit()

            # Using the correct function name
            token = request.cookies.get('session_token')
            log_cims_database_change(
                token,
                "DELETE",
                "MemberGroupMapping",
                member_id,
                f"Removed group mappings for member: {member_name}",
                app.config,
                get_db_connection
            )
            return jsonify({"message": f"Group mappings for member {member_id} were removed successfully"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ----------------------- DATABASE & IMAGE -----------------------

@app.route('/api/db/connection', methods=['GET'])
def api_db_connection_test():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        return jsonify({"message": "Database connection successful", "database": db_name[0]}), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/image/update', methods=['POST'])
def api_update_image():
    return UpdateImage.UpdateImage(request, get_db_connection(), logging).update_image()

# ----------------------- MAINTENANCE REQUESTS -----------------------

@app.route('/api/maintenance/requests', methods=['GET'])
@role_required(['admin', 'student', 'technician'])
def api_get_maintenance_requests():
    try:
        conn = get_db_connection(use_cism=False)  # Use project database
        cursor = conn.cursor(dictionary=True)

        if request.user['role'] == 'admin':
            cursor.execute("""
                SELECT r.*, s.Name as StudentName
                FROM maintenance_requests r
                JOIN students s ON r.Student_ID = s.Student_ID
                ORDER BY r.Submission_Date DESC
            """)
        else:
            student_id = request.args.get('student_id')
            if not student_id:
                return jsonify({"error": "Student ID is required"}), 400

            if 'session_id' in request.user and str(student_id) != str(request.user['session_id']):
                logging.warning(
                    f"Unauthorized access attempt: User {request.user['user']} tried to access requests for student {student_id}"
                )
                return jsonify({"error": "You can only view your own maintenance requests"}), 403

            cursor.execute("""
                SELECT * FROM maintenance_requests
                WHERE Student_ID = %s
                ORDER BY Submission_Date DESC
            """, (student_id,))

        requests_data = cursor.fetchall()
        return jsonify(requests_data), 200

    except Exception as e:
        logging.error(f"Error retrieving maintenance requests: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/maintenance/request', methods=['POST'])
@role_required(['admin', 'student'])
def api_create_maintenance_request():
    try:
        data = request.json
        required_fields = ['student_id', 'issue_description', 'location', 'priority']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        if (request.user['role'] == 'admin' or request.user['role'] == 'student') and 'session_id' in request.user:
            if str(data['student_id']) != str(request.user['session_id']):
                logging.warning(
                    f"Unauthorized request creation attempt: User {request.user['user']} tried to create request for student {data['student_id']}"
                )
                return jsonify({"error": "You can only create maintenance requests for yourself"}), 403

        # Use project database for maintenance request
        conn_project = get_db_connection(use_cism=False)
        cursor_project = conn_project.cursor()
        cursor_project.execute("""
            INSERT INTO maintenance_requests
            (Student_ID, Issue_Description, Location, Priority, Status)
            VALUES (%s, %s, %s, %s, 'submitted')
        """, (
            data['student_id'],
            data['issue_description'],
            data['location'],
            data['priority']
        ))
        request_id = cursor_project.lastrowid
        conn_project.commit()

        # Use CIMS database for notifications
        conn_cims = get_db_connection(use_cism=True)
        cursor_cims = conn_cims.cursor()
        cursor_cims.execute("""
            INSERT INTO G6_notifications
            (Student_ID, Message)
            VALUES (%s, %s)
        """, (
            data['student_id'],
            "Your maintenance request has been submitted successfully."
        ))
        conn_cims.commit()

        return jsonify({
            "message": "Maintenance request created successfully",
            "request_id": request_id
        }), 201

    except Exception as e:
        logging.error(f"Error creating maintenance request: {str(e)}")
        if 'conn_project' in locals():
            conn_project.rollback()
        if 'conn_cims' in locals():
            conn_cims.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor_project' in locals():
            cursor_project.close()
        if 'conn_project' in locals():
            conn_project.close()
        if 'cursor_cims' in locals():
            cursor_cims.close()
        if 'conn_cims' in locals():
            conn_cims.close()

@app.route('/api/maintenance/request/<int:request_id>', methods=['GET'])
@role_required(['admin'])
def api_get_maintenance_request_detail(request_id):
    try:
        conn = get_db_connection(use_cism=False)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, s.Name as StudentName, s.Email as StudentEmail, s.Contact_Number as StudentContact
            FROM maintenance_requests r
            JOIN students s ON r.Student_ID = s.Student_ID
            WHERE r.Request_ID = %s
        """, (request_id,))
        request_data = cursor.fetchone()

        if not request_data:
            return jsonify({"error": "Maintenance request not found"}), 404

        if request.user['role'] == 'admin' and 'session_id' in request.user:
            if str(request_data['Student_ID']) != str(request.user['session_id']):
                logging.warning(
                    f"Unauthorized access attempt: User {request.user['user']} tried to access request {request_id} belonging to student {request_data['Student_ID']}"
                )
                return jsonify({"error": "You can only view your own maintenance requests"}), 403

        cursor.execute("""
            SELECT ta.*, t.Name as TechnicianName, t.Specialization
            FROM technician_assignments ta
            JOIN technicians t ON ta.Technician_ID = t.Technician_ID
            WHERE ta.Request_ID = %s
        """, (request_id,))
        assignment = cursor.fetchone()
        if assignment:
            request_data['technician'] = assignment

        cursor.execute("""
            SELECT ml.*, t.Name as TechnicianName
            FROM maintenance_logs ml
            JOIN technicians t ON ml.Technician_ID = t.Technician_ID
            WHERE ml.Request_ID = %s
            ORDER BY ml.Updated_At DESC
        """, (request_id,))
        logs = cursor.fetchall()
        request_data['logs'] = logs

        cursor.execute("""
            SELECT * FROM feedback
            WHERE Request_ID = %s
        """, (request_id,))
        feedback = cursor.fetchone()
        if feedback:
            request_data['feedback'] = feedback

        return jsonify(request_data), 200

    except Exception as e:
        logging.error(f"Error retrieving maintenance request details: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/maintenance/request/<int:request_id>', methods=['PUT'])
@role_required(['admin', 'technician'])
def api_update_maintenance_request(request_id):
    try:
        data = request.json
        if 'status' not in data:
            return jsonify({"error": "Status field is required"}), 400

        valid_statuses = ['submitted', 'in_progress', 'completed', 'rejected']
        if data['status'] not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

        conn_project = get_db_connection(use_cism=False)
        cursor_project = conn_project.cursor()
        cursor_project.execute("""
            UPDATE maintenance_requests
            SET Status = %s
            WHERE Request_ID = %s
        """, (data['status'], request_id))

        if cursor_project.rowcount == 0:
            return jsonify({"error": "Maintenance request not found"}), 404

        conn_project.commit()
        cursor_project.execute("SELECT Student_ID FROM maintenance_requests WHERE Request_ID = %s", (request_id,))
        student_id = cursor_project.fetchone()[0]

        status_message = {
            'in_progress': "Your maintenance request is now in progress.",
            'completed': "Your maintenance request has been completed.",
            'rejected': "Your maintenance request has been rejected."
        }
        if data['status'] in status_message:
            conn_cims = get_db_connection(use_cism=True)
            cursor_cims = conn_cims.cursor()
            cursor_cims.execute("""
                INSERT INTO G6_notifications
                (Student_ID, Message)
                VALUES (%s, %s)
            """, (student_id, status_message[data['status']]))
            conn_cims.commit()
            cursor_cims.close()
            conn_cims.close()

        return jsonify({"message": f"Maintenance request status updated to {data['status']}"}), 200

    except Exception as e:
        logging.error(f"Error updating maintenance request: {str(e)}")
        if 'conn_project' in locals():
            conn_project.rollback()
        if 'conn_cims' in locals():
            conn_cims.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor_project' in locals():
            cursor_project.close()
        if 'conn_project' in locals():
            conn_project.close()

# ----------------------- TECHNICIAN ASSIGNMENT -----------------------

@app.route('/api/maintenance/assign-technician', methods=['POST'])
@role_required(['admin'])
def api_assign_technician():
    try:
        data = request.json
        required_fields = ['request_id', 'technician_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Use project database for everything except notifications
        conn_project = get_db_connection(use_cism=False)
        cursor_project = conn_project.cursor()
        cursor_project.execute("""
            SELECT Status, Student_ID FROM maintenance_requests
            WHERE Request_ID = %s
        """, (data['request_id'],))
        request_data = cursor_project.fetchone()
        if not request_data:
            return jsonify({"error": "Maintenance request not found"}), 404

        status, student_id = request_data[0], request_data[1]
        if status in ['completed', 'rejected']:
            return jsonify({"error": f"Cannot assign technician to a {status} request"}), 400

        cursor_project.execute("SELECT * FROM technicians WHERE Technician_ID = %s", (data['technician_id'],))
        if not cursor_project.fetchone():
            return jsonify({"error": "Technician not found"}), 404

        cursor_project.execute("""
            SELECT * FROM technician_assignments
            WHERE Request_ID = %s
        """, (data['request_id'],))
        if cursor_project.fetchone():
            cursor_project.execute("""
                UPDATE technician_assignments
                SET Technician_ID = %s, Assigned_Date = CURRENT_TIMESTAMP
                WHERE Request_ID = %s
            """, (data['technician_id'], data['request_id']))
        else:
            cursor_project.execute("""
                INSERT INTO technician_assignments
                (Technician_ID, Request_ID)
                VALUES (%s, %s)
            """, (data['technician_id'], data['request_id']))

        if status == 'submitted':
            cursor_project.execute("""
                UPDATE maintenance_requests
                SET Status = 'in_progress'
                WHERE Request_ID = %s
            """, (data['request_id'],))

        cursor_project.execute("""
            SELECT * FROM work_orders
            WHERE Request_ID = %s
        """, (data['request_id'],))
        if not cursor_project.fetchone():
            cursor_project.execute("""
                INSERT INTO work_orders
                (Request_ID, Technician_ID, Remarks)
                VALUES (%s, %s, 'Technician assigned')
            """, (data['request_id'], data['technician_id']))

        conn_project.commit()

        # Use CIMS database for notifications
        conn_cims = get_db_connection(use_cism=True)
        cursor_cims = conn_cims.cursor()
        cursor_cims.execute("""
            INSERT INTO G6_notifications
            (Student_ID, Message)
            VALUES (%s, %s)
        """, (student_id, "A technician has been assigned to your maintenance request."))
        conn_cims.commit()

        return jsonify({"message": "Technician assigned successfully"}), 200

    except Exception as e:
        logging.error(f"Error assigning technician: {str(e)}")
        if 'conn_project' in locals():
            conn_project.rollback()
        if 'conn_cims' in locals():
            conn_cims.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor_project' in locals():
            cursor_project.close()
        if 'conn_project' in locals():
            conn_project.close()
        if 'cursor_cims' in locals():
            cursor_cims.close()
        if 'conn_cims' in locals():
            conn_cims.close()

# ----------------------- MAINTENANCE LOGS -----------------------

@app.route('/api/maintenance/log', methods=['POST'])
@role_required(['admin'])
def api_add_maintenance_log():
    try:
        data = request.json
        required_fields = ['request_id', 'technician_id', 'status_update']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        conn = get_db_connection(use_cism=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_logs
            (Request_ID, Technician_ID, Status_Update)
            VALUES (%s, %s, %s)
        """, (
            data['request_id'],
            data['technician_id'],
            data['status_update']
        ))
        conn.commit()

        return jsonify({"message": "Maintenance log entry added successfully"}), 201

    except Exception as e:
        logging.error(f"Error adding maintenance log: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ----------------------- FEEDBACK -----------------------

@app.route('/api/maintenance/feedback', methods=['POST'])
@role_required(['student'])
def api_submit_feedback():
    try:
        data = request.json
        required_fields = ['request_id', 'student_id', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        if not isinstance(data['rating'], int) or not (1 <= data['rating'] <= 5):
            return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400

        if 'session_id' in request.user and str(data['student_id']) != str(request.user['session_id']):
            logging.warning(
                f"Unauthorized feedback submission attempt: User {request.user['user']} tried to submit feedback for student {data['student_id']}"
            )
            return jsonify({"error": "You can only submit feedback for your own maintenance requests"}), 403

        conn = get_db_connection(use_cism=False)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Status FROM maintenance_requests
            WHERE Request_ID = %s AND Student_ID = %s
        """, (data['request_id'], data['student_id']))
        request_data = cursor.fetchone()
        if not request_data:
            return jsonify({"error": "Maintenance request not found or doesn't belong to this student"}), 404

        status = request_data[0]
        if status != 'completed':
            return jsonify({"error": "Feedback can only be submitted for completed requests"}), 400

        cursor.execute("""
            SELECT * FROM feedback
            WHERE Request_ID = %s AND Student_ID = %s
        """, (data['request_id'], data['student_id']))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE feedback
                SET Rating = %s, Comments = %s
                WHERE Request_ID = %s AND Student_ID = %s
            """, (
                data['rating'],
                data.get('comments', ''),
                data['request_id'],
                data['student_id']
            ))
        else:
            cursor.execute("""
                INSERT INTO feedback
                (Request_ID, Student_ID, Rating, Comments)
                VALUES (%s, %s, %s, %s)
            """, (
                data['request_id'],
                data['student_id'],
                data['rating'],
                data.get('comments', '')
            ))
        conn.commit()

        return jsonify({"message": "Feedback submitted successfully"}), 200

    except Exception as e:
        logging.error(f"Error submitting feedback: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ----------------------- NOTIFICATIONS -----------------------

@app.route('/api/notifications/<int:student_id>', methods=['GET'])
@role_required(['admin', 'student'])
def api_get_notifications(student_id):
    try:
        if (request.user['role'] == 'admin' or request.user['role'] == 'student') and 'session_id' in request.user:
            if str(student_id) != str(request.user['session_id']):
                logging.warning(
                    f"Unauthorized notification access attempt: User {request.user['user']} tried to access notifications for student {student_id}"
                )
                return jsonify({"error": "You can only view your own notifications"}), 403

        # Use CIMS database for notifications
        conn = get_db_connection(use_cism=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM G6_notifications
            WHERE Student_ID = %s
            ORDER BY Sent_At DESC
        """, (student_id,))
        notifications = cursor.fetchall()
        return jsonify(notifications), 200

    except Exception as e:
        logging.error(f"Error retrieving notifications: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ----------------------- ADMIN DASHBOARD -----------------------

@app.route('/api/admin/dashboard', methods=['GET'])
@role_required(['admin'])
def api_admin_dashboard():
    try:
        conn = get_db_connection(use_cism=False)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT Status, COUNT(*) as Count
            FROM maintenance_requests
            GROUP BY Status
        """)
        status_counts = cursor.fetchall()

        cursor.execute("""
            SELECT Priority, COUNT(*) as Count
            FROM maintenance_requests
            GROUP BY Priority
        """)
        priority_counts = cursor.fetchall()

        cursor.execute("""
            SELECT r.*, s.Name as StudentName
            FROM maintenance_requests r
            JOIN students s ON r.Student_ID = s.Student_ID
            ORDER BY r.Submission_Date DESC
            LIMIT 5
        """)
        recent_requests = cursor.fetchall()

        cursor.execute("""
            SELECT t.Technician_ID, t.Name, t.Specialization,
                   COUNT(ta.Assignment_ID) as AssignedRequests
            FROM technicians t
            LEFT JOIN technician_assignments ta ON t.Technician_ID = ta.Technician_ID
            LEFT JOIN maintenance_requests r ON ta.Request_ID = r.Request_ID AND r.Status != 'completed'
            GROUP BY t.Technician_ID, t.Name, t.Specialization
            ORDER BY AssignedRequests DESC
        """)
        technician_workload = cursor.fetchall()

        return jsonify({
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "recent_requests": recent_requests,
            "technician_workload": technician_workload
        }), 200

    except Exception as e:
        logging.error(f"Error retrieving admin dashboard data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ----------------------- STUDENT AND TECHNICIAN MANAGEMENT -----------------------

@app.route('/api/admin/students', methods=['GET'])
@role_required(['admin'])
def api_get_students():
    try:
        conn = get_db_connection(use_cism=False)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students ORDER BY Name")
        students = cursor.fetchall()
        return jsonify(students), 200

    except Exception as e:
        logging.error(f"Error retrieving students: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/technicians', methods=['GET'])
@role_required(['admin'])
def api_get_technicians():
    try:
        conn = get_db_connection(use_cism=False)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM technicians ORDER BY Name")
        technicians = cursor.fetchall()
        return jsonify(technicians), 200

    except Exception as e:
        logging.error(f"Error retrieving technicians: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/technicians', methods=['POST'])
@role_required(['admin'])
def api_add_technician():
    try:
        data = request.json
        required_fields = ['name', 'email', 'contact_number', 'specialization']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        conn = get_db_connection(use_cism=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM technicians WHERE Email = %s", (data['email'],))
        if cursor.fetchone():
            return jsonify({"error": "A technician with this email already exists"}), 400

        cursor.execute("""
            INSERT INTO technicians
            (Name, Email, Contact_Number, Specialization)
            VALUES (%s, %s, %s, %s)
        """, (
            data['name'],
            data['email'],
            data['contact_number'],
            data['specialization']
        ))
        technician_id = cursor.lastrowid
        conn.commit()
        return jsonify({
            "message": "Technician added successfully",
            "technician_id": technician_id
        }), 201

    except Exception as e:
        logging.error(f"Error adding technician: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ----------------------- SECURITY & LOGGING -----------------------

def log_unauthorized_database_access(action, user_info, error_details):
    try:
        log_message = f"UNAUTHORIZED DATABASE ACCESS: {action} | User: {user_info} | Details: {error_details}"
        logging.warning(log_message)
    except Exception as e:
        logging.error(f"Error logging unauthorized access: {str(e)}")

@app.errorhandler(mysql.connector.Error)
def handle_database_error(error):
    try:
        if "access denied" in str(error).lower() or "permission denied" in str(error).lower():
            user_info = getattr(request, 'user', {}).get('user', 'Unknown')
            log_unauthorized_database_access(f"{request.method} {request.path}", user_info, str(error))
        return jsonify({"error": "Database error occurred"}), 500
    except:
        return jsonify({"error": "An error occurred"}), 500

@app.route('/api/admin/security-logs', methods=['GET'])
@role_required(['admin'])
def api_view_security_logs():
    try:
        lines_count = request.args.get('lines', 100, type=int)
        with open('app.log', 'r') as f:
            all_lines = f.readlines()
            security_logs = [line for line in all_lines if 'UNAUTHORIZED' in line or 'WARNING' in line or 'ERROR' in line]
            recent_logs = security_logs[-lines_count:] if security_logs else []
        return jsonify({
            "security_logs": recent_logs,
            "count": len(recent_logs)
        }), 200

    except Exception as e:
        logging.error(f"Error retrieving security logs: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ----------------------- STUDENT PROFILE -----------------------

@app.route('/api/student/<int:student_id>', methods=['GET'])
@role_required(['admin', 'student'])
def api_get_student_details(student_id):
    try:
        if (request.user['role'] == 'admin' or request.user['role'] == 'student') and 'session_id' in request.user:
            if str(student_id) != str(request.user['session_id']):
                log_unauthorized_database_access(
                    "Attempt to access another student's profile",
                    request.user['user'],
                    f"Attempted to access student ID {student_id}"
                )
                return jsonify({"error": "You can only view your own profile"}), 403

        # Get student details and maintenance requests from project database
        conn_project = get_db_connection(use_cism=False)
        cursor_project = conn_project.cursor(dictionary=True)
        cursor_project.execute("SELECT * FROM students WHERE Student_ID = %s", (student_id,))
        student = cursor_project.fetchone()
        if not student:
            return jsonify({"error": "Student not found"}), 404

        cursor_project.execute("""
            SELECT * FROM maintenance_requests
            WHERE Student_ID = %s
            ORDER BY Submission_Date DESC
        """, (student_id,))
        requests_data = cursor_project.fetchall()
        student['maintenance_requests'] = requests_data
        cursor_project.close()
        conn_project.close()

        # Get notifications from CIMS database
        conn_cims = get_db_connection(use_cism=True)
        cursor_cims = conn_cims.cursor(dictionary=True)
        cursor_cims.execute("""
            SELECT * FROM G6_notifications
            WHERE Student_ID = %s
            ORDER BY Sent_At DESC
        """, (student_id,))
        notifications = cursor_cims.fetchall()
        student['notifications'] = notifications

        return jsonify(student), 200

    except Exception as e:
        logging.error(f"Error retrieving student details: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor_cims' in locals():
            cursor_cims.close()
        if 'conn_cims' in locals():
            conn_cims.close()

# ----------------------- APPLICATION STARTUP -----------------------

if __name__ == '__main__':
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        logging.info(f"Connected to database: {cursor.fetchone()[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"DB connection failed on startup: {e}")

    app.run(debug=True)
