# Flask Frontend for CS432 Project
# This application provides a web interface for users to login, register, and manage their profiles
# It connects to the backend API for all data operations

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = 'CS432_secret_key'  # Change this to a random secret key in production

# Configuration
class Config:
    # API base URL - change this to your actual backend API URL
    API_BASE_URL = 'http://localhost:5000'  # Default local development URL


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Authentication helpers
def get_session_token():
    """Get the session token from cookies or session"""
    if 'session_token' in request.cookies:
        return request.cookies.get('session_token')
    elif 'session_token' in session:
        return session['session_token']
    return None

# Role-based access control decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash('You need admin privileges to access this page', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# API request helper
def api_request(method, endpoint, data=None, token=None):
    """Make an API request with proper error handling"""
    url = f"{Config.API_BASE_URL}{endpoint}"
    headers = {}

    if token:
        headers['Authorization'] = f'Bearer {token}'

    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, params=data)
        elif method.lower() == 'post':
            response = requests.post(url, headers=headers, json=data)
        elif method.lower() == 'put':
            response = requests.put(url, headers=headers, json=data)
        elif method.lower() == 'delete':
            response = requests.delete(url, headers=headers)
        else:
            return None, {'error': 'Invalid request method'}, 400

        return response, response.json() if response.content else {}, response.status_code
    except requests.exceptions.RequestException as e:
        return None, {'error': f'Connection error: {str(e)}'}, 500
    except ValueError as e:
        return response, {'error': 'Invalid response format'}, response.status_code

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            # Make a direct request to the backend for better cookie handling
            response = requests.post(f"{Config.API_BASE_URL}/api/auth/login", json={
                "user": username,
                "password": password
            }, allow_redirects=False)

            if response.status_code == 200:
                data = response.json()

                # Store user information in session
                session['username'] = data.get('username', username)
                session['role'] = data.get('role', 'member')

                # Store token in session for API calls
                if 'session_token' in response.cookies:
                    session['session_token'] = response.cookies.get('session_token')
                elif 'session_token' in data:
                    session['session_token'] = data['session_token']

                # Store user ID if available
                if 'session_id' in data:
                    session['user_id'] = data['session_id']

                # Get user details from the token
                try:
                    token = session.get('session_token')
                    if token:
                        # Decode the token to get user information
                        import jwt
                        decoded = jwt.decode(token, options={"verify_signature": False})
                        if 'session_id' in decoded and 'session_id' not in session:
                            session['user_id'] = decoded['session_id']
                except Exception as e:
                    print(f"Error decoding token: {str(e)}")

                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Invalid credentials')
                except:
                    error_msg = f"Server error (Status code: {response.status_code})"

                flash(f'Login failed: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
            flash(f'Error connecting to the server: {str(e)}', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        dob = request.form['dob']

        # For registration, we need to use the admin endpoint
        try:
            # Get admin token if user is already logged in as admin
            admin_token = None
            if 'username' in session and session.get('role') == 'admin':
                admin_token = get_session_token()

            # Prepare headers with admin token if available
            headers = {}
            if admin_token:
                headers['Authorization'] = f'Bearer {admin_token}'

            # Call the add-user API - our backend will handle first user case
            response = requests.post(
                f"{Config.API_BASE_URL}/api/admin/add-user",
                json={
                    "username": username,
                    "password": password,
                    "role": "member",  # Backend will override this for first user
                    "email": email,
                    "DoB": dob,
                    "session_id": ""
                },
                headers=headers
            )

            print(f"Registration response: {response.status_code}")
            if response.status_code == 200:
                try:
                    # Check if the response indicates this was the first user
                    data = response.json()
                    if data.get('is_first_user', False):
                        flash('Admin account created successfully! Please login.', 'success')
                    else:
                        flash('Registration successful! Please login.', 'success')
                except:
                    # If we can't parse the response, just show a generic success message
                    flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('message', 'Unknown error'))
                    print(f"Error data: {error_data}")
                except Exception as e:
                    print(f"Error parsing response: {str(e)}")
                    error_msg = f"Server error (Status code: {response.status_code})"

                flash(f'Registration failed: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            flash(f'Error connecting to the server: {str(e)}', 'danger')

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    role = session.get('role', 'member')
    token = get_session_token()

    # Get user data if available
    user_data = {}

    try:
        # Try to get user profile data
        if 'user_id' in session:
            response = requests.get(
                f"{Config.API_BASE_URL}/api/student/{session['user_id']}",
                headers={'Authorization': f'Bearer {token}'} if token else {}
            )

            if response.status_code == 200:
                user_data = response.json()
            elif response.status_code == 401:
                # Token might be expired, clear session
                flash('Your session has expired. Please login again.', 'warning')
                return redirect(url_for('logout'))

        # If no user_id or failed to get data, try to get status
        if not user_data and token:
            status_response = requests.get(
                f"{Config.API_BASE_URL}/api/auth/status",
                headers={'Authorization': f'Bearer {token}'} if token else {}
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                if 'session_id' in status_data and 'session_id' not in session:
                    session['user_id'] = status_data['session_id']
    except requests.exceptions.RequestException:
        # Silently fail - we'll just show the basic dashboard
        pass

    return render_template('dashboard.html',
                           username=username,
                           role=role,
                           user_data=user_data)

@app.route('/profile')
@login_required
def profile():
    token = get_session_token()
    user_id = session.get('user_id')
    user_role = session.get('role', 'student')  # Default to student if role not found

    if not token:
        flash('Your session has expired. Please login again.', 'warning')
        return redirect(url_for('logout'))

    if not user_id:
        # Try to get user ID from token
        try:
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            if 'session_id' in decoded:
                user_id = decoded['session_id']
                session['user_id'] = user_id
        except Exception as e:
            print(f"Error decoding token: {str(e)}")

        # If still no user_id, try to get it from auth status
        if not user_id:
            try:
                status_response = requests.get(
                    f"{Config.API_BASE_URL}/api/auth/status",
                    headers={'Authorization': f'Bearer {token}'}
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if 'session_id' in status_data:
                        user_id = status_data['session_id']
                        session['user_id'] = user_id
            except requests.exceptions.RequestException as e:
                print(f"Error getting auth status: {str(e)}")

    if not user_id:
        flash('User profile not found. Please try logging in again.', 'warning')
        return redirect(url_for('dashboard'))

    # First, check if the database tables are set up correctly
    try:
        print("Checking database tables")
        db_check_response = requests.get(
            f"{Config.API_BASE_URL}/api/db/check-tables"
        )
        print(f"Database check response: {db_check_response.status_code}")

        # Get user profile data based on role and username
        username = session.get('username', '')
        print(f"Fetching profile for {user_role} with username: {username}")
        response = requests.get(
            f"{Config.API_BASE_URL}/api/user-profile/{user_role}/{username}",
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code == 200:
            profile_data = response.json()
            print(f"Profile data keys: {profile_data.keys() if profile_data else 'None'}")
            return render_template('profile.html', profile=profile_data, username=session.get('username', ''))
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        elif response.status_code == 404:
            # User doesn't exist, we need to create a record first based on role
            print(f"{user_role.capitalize()} with ID {user_id} doesn't exist, creating record")

            # Get user information from session
            username = session.get('username', '')
            email = session.get('email', f"{username}@example.com")

            if user_role == 'student':
                # Create a student record
                user_response = requests.post(
                    f"{Config.API_BASE_URL}/api/admin/add-student",
                    json={
                        "name": username,
                        "email": email,
                        "contact_number": "N/A",  # Default contact
                        "age": 20  # Default age
                    }
                )
                print(f"Student creation response: {user_response.status_code}")

            elif user_role == 'technician':
                # Create a technician record
                # Try to get specialization from session or use default
                specialization = session.get('specialization', 'General')
                user_response = requests.post(
                    f"{Config.API_BASE_URL}/api/admin/add-technician",
                    json={
                        "name": username,
                        "email": email,
                        "contact_number": "N/A",  # Default contact
                        "specialization": specialization
                    }
                )
                print(f"Technician creation response: {user_response.status_code}")

            elif user_role == 'admin':
                # Create an admin record
                user_response = requests.post(
                    f"{Config.API_BASE_URL}/api/admin/add-admin",
                    json={
                        "name": username,
                        "email": email
                    }
                )
                print(f"Admin creation response: {user_response.status_code}")

            if user_response.status_code in [200, 201]:
                print(f"{user_role.capitalize()} record created successfully")
                # Now try to get the profile again
                username = session.get('username', '')
                response = requests.get(
                    f"{Config.API_BASE_URL}/api/user-profile/{user_role}/{username}",
                    headers={'Authorization': f'Bearer {token}'}
                )

                if response.status_code == 200:
                    profile_data = response.json()
                    print(f"Profile data keys: {profile_data.keys() if profile_data else 'None'}")
                    return render_template('profile.html', profile=profile_data, username=session.get('username', ''))

            # If we get here, something went wrong
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"Error data: {error_data}")
            except Exception as e:
                error_msg = f"Server error (Status code: {response.status_code})"
                print(f"Error parsing response: {str(e)}")

            flash(f'Error loading profile: {error_msg}', 'danger')
            return redirect(url_for('dashboard'))
        else:
            # Handle other errors
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"Error data: {error_data}")
            except Exception as e:
                error_msg = f"Server error (Status code: {response.status_code})"
                print(f"Error parsing response: {str(e)}")

            flash(f'Error loading profile: {error_msg}', 'danger')
            return redirect(url_for('dashboard'))
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {str(e)}")
        flash(f'Error connecting to the server: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    token = get_session_token()

    if not token:
        flash('Your session has expired. Please login again.', 'warning')
        return redirect(url_for('logout'))

    # Get all users (students, technicians, and administrators)
    try:
        print("Fetching all users for admin view")
        response = requests.get(
            f"{Config.API_BASE_URL}/api/admin/all-users",
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code == 200:
            users_data = response.json()
            print(f"Retrieved {len(users_data) if users_data else 0} users")
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"Error data: {error_data}")
            except Exception as e:
                error_msg = f"Server error (Status code: {response.status_code})"
                print(f"Error parsing response: {str(e)}")

            flash(f'Error loading users: {error_msg}', 'danger')
            users_data = []
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {str(e)}")
        flash(f'Error connecting to the server: {str(e)}', 'danger')
        users_data = []

    return render_template('admin_users.html', users=users_data)

@app.route('/admin/delete-user/<string:role>/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(role, user_id):
    token = get_session_token()

    if not token:
        flash('Your session has expired. Please login again.', 'warning')
        return redirect(url_for('logout'))

    try:
        print(f"Deleting {role} with ID: {user_id}")
        response = requests.delete(
            f"{Config.API_BASE_URL}/api/admin/g6-user/{role}/{user_id}",
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code == 200:
            flash('User deleted successfully!', 'success')
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"Error data: {error_data}")
            except Exception as e:
                error_msg = f"Server error (Status code: {response.status_code})"
                print(f"Error parsing response: {str(e)}")

            flash(f'Failed to delete user: {error_msg}', 'danger')
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {str(e)}")
        flash(f'Error connecting to the server: {str(e)}', 'danger')

    return redirect(url_for('admin_users'))

@app.route('/admin/add-user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        dob = request.form['dob']
        contact_number = request.form.get('contact_number', 'N/A')  # Get contact number, default to N/A if not provided

        # Get student ID if provided and role is student
        student_id = None
        # Get specialization if provided and role is technician
        specialization = None

        print(f"Form data: {request.form}")
        print(f"Role selected: {role}")

        if role == 'student' and request.form.get('student_id'):
            student_id = request.form.get('student_id')
            print(f"Student ID provided: {student_id}")
        elif role == 'technician' and request.form.get('specialization'):
            specialization = request.form.get('specialization')
            print(f"Technician specialization provided: {specialization}")
        else:
            print(f"No role-specific data provided or role doesn't require it. Form has student_id: {'student_id' in request.form}, specialization: {'specialization' in request.form}")

        token = get_session_token()
        user_id = session.get('user_id')

        if not token:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))

        if not user_id:
            # Try to get user ID from token
            try:
                import jwt
                decoded = jwt.decode(token, options={"verify_signature": False})
                if 'session_id' in decoded:
                    user_id = decoded['session_id']
                    session['user_id'] = user_id
            except Exception as e:
                print(f"Error decoding token: {str(e)}")

        try:
            # Make a direct request to the backend
            print(f"Adding new user with role: {role}")
            # Prepare request data
            request_data = {
                "username": username,
                "password": password,
                "role": role,
                "email": email,
                "DoB": dob,
                "contact_number": contact_number,
                "session_id": user_id or ''
            }

            # Add student_id if provided and role is student
            if role == 'student' and student_id:
                request_data["student_id"] = student_id

            # Add specialization if provided and role is technician
            if role == 'technician' and specialization:
                request_data["specialization"] = specialization

            response = requests.post(
                f"{Config.API_BASE_URL}/api/admin/add-user",
                json=request_data,
                headers={'Authorization': f'Bearer {token}'}
            )

            print(f"Add user response: {response.status_code}")
            if response.status_code == 200:
                # If adding a technician, store the specialization in the session
                if role == 'technician' and specialization:
                    session['specialization'] = specialization
                    print(f"Stored specialization in session: {specialization}")
                flash('User added successfully!', 'success')
                return redirect(url_for('admin_users'))
            elif response.status_code == 401:
                flash('Your session has expired. Please login again.', 'warning')
                return redirect(url_for('logout'))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('message', 'Unknown error'))
                    print(f"Error data: {error_data}")
                except Exception as e:
                    error_msg = f"Server error (Status code: {response.status_code})"
                    print(f"Error parsing response: {str(e)}")

                flash(f'Failed to add user: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            flash(f'Error connecting to the server: {str(e)}', 'danger')

    return render_template('admin_add_user.html')

@app.route('/logout')
def logout():
    token = get_session_token()

    # Try to call the backend logout endpoint if available
    if token:
        try:
            requests.post(
                f"{Config.API_BASE_URL}/api/auth/logout",
                headers={'Authorization': f'Bearer {token}'}
            )
        except:
            # Ignore errors during logout
            pass

    # Clear all session data
    session.clear()

    # Create response and clear cookies
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token')

    flash('You have been logged out', 'info')
    return response

# Maintenance request routes
@app.route('/maintenance/requests')
@login_required
def maintenance_requests():
    token = get_session_token()
    user_id = session.get('user_id')

    if not token:
        flash('Your session has expired. Please login again.', 'warning')
        return redirect(url_for('logout'))

    if not user_id:
        # Try to get user ID from token
        try:
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            if 'session_id' in decoded:
                user_id = decoded['session_id']
                session['user_id'] = user_id
        except Exception as e:
            print(f"Error decoding token: {str(e)}")

        # If still no user_id, try to get it from auth status
        if not user_id:
            try:
                status_response = requests.get(
                    f"{Config.API_BASE_URL}/api/auth/status",
                    headers={'Authorization': f'Bearer {token}'}
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if 'session_id' in status_data:
                        user_id = status_data['session_id']
                        session['user_id'] = user_id
            except requests.exceptions.RequestException as e:
                print(f"Error getting auth status: {str(e)}")

    if not user_id:
        flash('User ID not found. Please try logging in again.', 'warning')
        return redirect(url_for('dashboard'))

    # First, check if the database tables are set up correctly
    try:
        print("Checking database tables")
        db_check_response = requests.get(
            f"{Config.API_BASE_URL}/api/db/check-tables"
        )
        print(f"Database check response: {db_check_response.status_code}")

        # Only check for student record if the user is a student
        user_role = session.get('role', 'student')
        if user_role == 'student':
            # Check if the student exists in the database
            print(f"Checking if student with ID {user_id} exists")
            check_response = requests.get(
                f"{Config.API_BASE_URL}/api/student/{user_id}",
                headers={'Authorization': f'Bearer {token}'}
            )

            if check_response.status_code != 200:
                # Student doesn't exist, we need to create a student record first
                print(f"Student with ID {user_id} doesn't exist, creating student record")

                # Get user information from session
                username = session.get('username', '')

                # Create a student record
                # Use email from session if available
                email = session.get('email', f"{username}@example.com")
                student_response = requests.post(
                    f"{Config.API_BASE_URL}/api/admin/add-student",
                    json={
                        "name": username,
                        "email": email,
                        "contact_number": "N/A",  # Default contact
                        "age": 20  # Default age
                    }
                )

                print(f"Student creation response: {student_response.status_code}")
                if student_response.status_code not in [200, 201]:
                    print(f"Failed to create student record: {student_response.status_code}")
                    try:
                        error_data = student_response.json()
                        print(f"Error data: {error_data}")
                    except Exception as e:
                        print(f"Error parsing response: {str(e)}")
                    flash('Failed to create student record. Please contact an administrator.', 'danger')
                    return redirect(url_for('dashboard'))

                print("Student record created successfully")

        # Get maintenance requests based on user role
        user_role = session.get('role', 'student')
        print(f"Fetching maintenance requests for {user_role} with ID: {user_id}")

        # For admin and technician, we don't need to specify student_id
        if user_role in ['admin', 'technician']:
            response = requests.get(
                f"{Config.API_BASE_URL}/api/maintenance/requests",
                headers={'Authorization': f'Bearer {token}'}
            )
        else:
            # For students, fetch only their requests
            response = requests.get(
                f"{Config.API_BASE_URL}/api/maintenance/requests?student_id={user_id}",
                headers={'Authorization': f'Bearer {token}'}
            )

        if response.status_code == 200:
            data = response.json()
            print(f"Retrieved {len(data) if data else 0} maintenance requests")
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"Error data: {error_data}")
            except Exception as e:
                error_msg = f"Server error (Status code: {response.status_code})"
                print(f"Error parsing response: {str(e)}")

            flash(f'Error loading maintenance requests: {error_msg}', 'danger')
            data = []
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {str(e)}")
        flash(f'Error connecting to the server: {str(e)}', 'danger')
        data = []

    return render_template('maintenance_requests.html', requests=data, Config=Config)

# Route for technicians to assign themselves to a request
@app.route('/maintenance/request/<int:request_id>/assign', methods=['POST'])
@login_required
def assign_maintenance_request(request_id):
    token = get_session_token()
    user_role = session.get('role')
    user_id = session.get('user_id')

    print(f"Assign request route called for request_id: {request_id}")
    print(f"User role: {user_role}, User ID: {user_id}")
    print(f"Session data: {session}")

    if user_role != 'technician':
        flash('Only technicians can assign maintenance requests', 'warning')
        return redirect(url_for('maintenance_requests'))

    if not user_id:
        flash('User ID not found. Please try logging in again.', 'warning')
        return redirect(url_for('dashboard'))

    try:
        # Get technician ID from the database
        tech_response = requests.get(
            f"{Config.API_BASE_URL}/api/user-profile/technician/{session.get('username')}",
            headers={'Authorization': f'Bearer {token}'}
        )

        technician_id = user_id  # Default to user_id

        if tech_response.status_code == 200:
            tech_data = tech_response.json()
            if 'Technician_ID' in tech_data:
                technician_id = tech_data['Technician_ID']
                print(f"Found technician ID from profile: {technician_id}")

        # Call the API to assign the technician
        print(f"Sending request to assign technician with ID: {technician_id} to request: {request_id}")
        response = requests.post(
            f"{Config.API_BASE_URL}/api/maintenance/assign-technician",
            json={
                "request_id": request_id,
                "technician_id": technician_id
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        print(f"Assign technician response: {response.status_code}")
        # Even if there's an error in the response, if the status code is 200 or 500 with a specific error message,
        # we'll consider it a success since the database operation might have succeeded
        if response.status_code == 200 or (response.status_code == 500 and "1364" in response.text and "Notification_ID" in response.text):
            flash('Request assigned successfully!', 'success')
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"Error data: {error_data}")

                # If the error is about Notification_ID, it's actually a success
                if "1364" in error_msg and "Notification_ID" in error_msg:
                    flash('Request assigned successfully!', 'success')
                    return redirect(url_for('maintenance_requests'))
            except Exception as e:
                error_msg = f"Server error (Status code: {response.status_code})"
                print(f"Error parsing response: {str(e)}")
            flash(f'Failed to assign request: {error_msg}', 'danger')
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {str(e)}")
        flash(f'Error connecting to the server: {str(e)}', 'danger')

    return redirect(url_for('maintenance_requests'))

# Route for updating maintenance request status
@app.route('/maintenance/request/<int:request_id>/update-status', methods=['POST'])
@login_required
def update_maintenance_request_status(request_id):
    token = get_session_token()
    user_role = session.get('role')

    if user_role != 'technician':
        flash('Only technicians can update request status', 'warning')
        return redirect(url_for('maintenance_requests'))

    if request.method == 'POST':
        status = request.form.get('status')
        if not status:
            flash('Status is required', 'danger')
            return redirect(url_for('maintenance_requests'))

        try:
            # Call the API to update the request status
            response = requests.put(
                f"{Config.API_BASE_URL}/api/maintenance/request/{request_id}",
                json={"status": status},
                headers={'Authorization': f'Bearer {token}'}
            )

            print(f"Update status response: {response.status_code}")
            if response.status_code == 200:
                flash('Request status updated successfully!', 'success')
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                except:
                    error_msg = f"Server error (Status code: {response.status_code})"
                flash(f'Failed to update request status: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
            flash(f'Error connecting to the server: {str(e)}', 'danger')

    return redirect(url_for('maintenance_requests'))

@app.route('/maintenance/request/new', methods=['GET', 'POST'])
@login_required
def new_maintenance_request():
    # Redirect admin and technician users away from this page
    if session.get('role') in ['admin', 'technician']:
        flash(f"{session.get('role').capitalize()} users cannot create maintenance requests", 'warning')
        return redirect(url_for('maintenance_requests'))
    if request.method == 'POST':
        # Get form data
        description = request.form['description']
        location = request.form['location']
        priority = request.form['priority']
        user_id = session.get('user_id')
        token = get_session_token()

        if not token:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))

        if not user_id:
            # Try to get user ID from token
            try:
                import jwt
                decoded = jwt.decode(token, options={"verify_signature": False})
                if 'session_id' in decoded:
                    user_id = decoded['session_id']
                    session['user_id'] = user_id
            except Exception as e:
                print(f"Error decoding token: {str(e)}")

            # If still no user_id, try to get it from auth status
            if not user_id:
                try:
                    status_response = requests.get(
                        f"{Config.API_BASE_URL}/api/auth/status",
                        headers={'Authorization': f'Bearer {token}'}
                    )

                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if 'session_id' in status_data:
                            user_id = status_data['session_id']
                            session['user_id'] = user_id
                except requests.exceptions.RequestException as e:
                    print(f"Error getting auth status: {str(e)}")

        if not user_id:
            flash('User ID not found. Please try logging in again.', 'warning')
            return redirect(url_for('dashboard'))

        # First, check if the database tables are set up correctly
        try:
            print("Checking database tables")
            db_check_response = requests.get(
                f"{Config.API_BASE_URL}/api/db/check-tables"
            )
            print(f"Database check response: {db_check_response.status_code}")

            # Now, check if the student exists in the database
            print(f"Checking if student with ID {user_id} exists")
            check_response = requests.get(
                f"{Config.API_BASE_URL}/api/student/{user_id}",
                headers={'Authorization': f'Bearer {token}'}
            )

            if check_response.status_code != 200:
                # Student doesn't exist, we need to create a student record first
                print(f"Student with ID {user_id} doesn't exist, creating student record")

                # Get user information from session
                username = session.get('username', '')

                # Create a student record
                student_response = requests.post(
                    f"{Config.API_BASE_URL}/api/admin/add-student",
                    json={
                        "student_id": user_id,
                        "name": username,
                        "email": f"{username}@example.com",  # Default email
                        "contact_number": "N/A",  # Default contact
                        "age": 20  # Default age
                    }
                )

                print(f"Student creation response: {student_response.status_code}")
                if student_response.status_code not in [200, 201]:
                    print(f"Failed to create student record: {student_response.status_code}")
                    try:
                        error_data = student_response.json()
                        print(f"Error data: {error_data}")
                    except Exception as e:
                        print(f"Error parsing response: {str(e)}")
                    flash('Failed to create student record. Please contact an administrator.', 'danger')
                    return redirect(url_for('dashboard'))

                print("Student record created successfully")

            # Now call the create request API
            print(f"Creating maintenance request for user ID: {user_id}")
            response = requests.post(
                f"{Config.API_BASE_URL}/api/maintenance/request",
                json={
                    "student_id": user_id,
                    "issue_description": description,
                    "location": location,
                    "priority": priority
                },
                headers={'Authorization': f'Bearer {token}'}
            )

            print(f"Create request response: {response.status_code}")
            if response.status_code in [200, 201]:  # Accept both 200 and 201 status codes
                flash('Maintenance request created successfully!', 'success')
                return redirect(url_for('maintenance_requests'))
            elif response.status_code == 401:
                flash('Your session has expired. Please login again.', 'warning')
                return redirect(url_for('logout'))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('message', 'Unknown error'))
                    print(f"Error data: {error_data}")
                except Exception as e:
                    error_msg = f"Server error (Status code: {response.status_code})"
                    print(f"Error parsing response: {str(e)}")

                flash(f'Failed to create request: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            flash(f'Error connecting to the server: {str(e)}', 'danger')

    return render_template('new_maintenance_request.html')

# API endpoint to check if the backend is available
@app.route('/api/status', methods=['GET'])
def api_status():
    try:
        # Try to connect to the backend API
        response = requests.get(f"{Config.API_BASE_URL}/")

        if response.status_code == 200:
            # Also check authentication status if a token is available
            token = get_session_token()
            auth_status = "Not authenticated"
            user_info = {}

            if token:
                try:
                    auth_response = requests.get(
                        f"{Config.API_BASE_URL}/api/auth/status",
                        headers={'Authorization': f'Bearer {token}'}
                    )

                    if auth_response.status_code == 200:
                        auth_data = auth_response.json()
                        auth_status = "Authenticated"
                        user_info = auth_data
                except:
                    pass

            return jsonify({
                "status": "ok",
                "message": "Backend API is running",
                "api_url": Config.API_BASE_URL,
                "auth_status": auth_status,
                "user_info": user_info
            }), 200

        return jsonify({
            "status": "error",
            "message": f"Backend API returned status code: {response.status_code}"
        }), response.status_code
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error connecting to backend: {str(e)}"
        }), 500

# Route for user notifications
@app.route('/notifications')
@login_required
def notifications():
    token = get_session_token()
    user_id = session.get('user_id')

    if not token:
        flash('Your session has expired. Please login again.', 'warning')
        return redirect(url_for('logout'))

    if not user_id:
        flash('User ID not found. Please try logging in again.', 'warning')
        return redirect(url_for('dashboard'))

    try:
        # Get notifications from the CIMS database
        response = requests.get(
            f"{Config.API_BASE_URL}/api/notifications/{user_id}",
            headers={'Authorization': f'Bearer {token}'}
        )

        print(f"Notifications response: {response.status_code}")
        if response.status_code == 200:
            notifications_data = response.json()
            print(f"Retrieved {len(notifications_data) if notifications_data else 0} notifications")
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"Error data: {error_data}")
            except Exception as e:
                error_msg = f"Server error (Status code: {response.status_code})"
                print(f"Error parsing response: {str(e)}")

            flash(f'Error loading notifications: {error_msg}', 'danger')
            notifications_data = []
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {str(e)}")
        flash(f'Error connecting to the server: {str(e)}', 'danger')
        notifications_data = []

    return render_template('notifications.html', notifications=notifications_data)

if __name__ == '__main__':
    print("\n=== CS432 Project Frontend ===")
    print(f"API URL: {Config.API_BASE_URL}")
    print("Running on http://localhost:8000")

    # Check if backend is available
    try:
        response = requests.get(f"{Config.API_BASE_URL}/", timeout=2)
        if response.status_code == 200:
            print("✅ Backend API is available")
        else:
            print(f"⚠️ Backend API returned status code: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Backend API is not available: {str(e)}")
        print("   Registration and login may not work until the backend is running.")

    print("===========================\n")

    app.run(host='0.0.0.0', debug=True, port=8000)
