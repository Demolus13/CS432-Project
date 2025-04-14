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

    if not user_id:
        # Try to get user ID from auth status
        try:
            status_response = requests.get(
                f"{Config.API_BASE_URL}/api/auth/status",
                headers={'Authorization': f'Bearer {token}'} if token else {}
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                if 'session_id' in status_data:
                    user_id = status_data['session_id']
                    session['user_id'] = user_id
        except requests.exceptions.RequestException:
            pass

    if not user_id:
        flash('User profile not found', 'warning')
        return redirect(url_for('dashboard'))

    # Get user profile data
    try:
        response = requests.get(
            f"{Config.API_BASE_URL}/api/student/{user_id}",
            headers={'Authorization': f'Bearer {token}'} if token else {}
        )

        if response.status_code == 200:
            profile_data = response.json()
            return render_template('profile.html', profile=profile_data)
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
            except:
                error_msg = f"Server error (Status code: {response.status_code})"

            flash(f'Error loading profile: {error_msg}', 'danger')
            return redirect(url_for('dashboard'))
    except requests.exceptions.RequestException as e:
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

    # Get all students
    try:
        response = requests.get(
            f"{Config.API_BASE_URL}/api/admin/students",
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code == 200:
            students_data = response.json()
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
            except:
                error_msg = f"Server error (Status code: {response.status_code})"

            flash(f'Error loading students: {error_msg}', 'danger')
            students_data = []
    except requests.exceptions.RequestException as e:
        flash(f'Error connecting to the server: {str(e)}', 'danger')
        students_data = []

    return render_template('admin_users.html', students=students_data)

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

        token = get_session_token()

        if not token:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))

        try:
            # Make a direct request to the backend
            response = requests.post(
                f"{Config.API_BASE_URL}/api/admin/add-user",
                json={
                    "username": username,
                    "password": password,
                    "role": role,
                    "email": email,
                    "DoB": dob,
                    "session_id": session.get('user_id', '')
                },
                headers={'Authorization': f'Bearer {token}'}
            )

            if response.status_code == 200:
                flash('User added successfully!', 'success')
                return redirect(url_for('admin_users'))
            elif response.status_code == 401:
                flash('Your session has expired. Please login again.', 'warning')
                return redirect(url_for('logout'))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('message', 'Unknown error'))
                except:
                    error_msg = f"Server error (Status code: {response.status_code})"

                flash(f'Failed to add user: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
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
        # Try to get user ID from auth status
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
        except:
            pass

    if not user_id:
        flash('User ID not found', 'warning')
        return redirect(url_for('dashboard'))

    # Get maintenance requests for the user
    try:
        response = requests.get(
            f"{Config.API_BASE_URL}/api/maintenance/requests?student_id={user_id}",
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code == 200:
            data = response.json()
        elif response.status_code == 401:
            flash('Your session has expired. Please login again.', 'warning')
            return redirect(url_for('logout'))
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
            except:
                error_msg = f"Server error (Status code: {response.status_code})"

            flash(f'Error loading maintenance requests: {error_msg}', 'danger')
            data = []
    except requests.exceptions.RequestException as e:
        flash(f'Error connecting to the server: {str(e)}', 'danger')
        data = []

    return render_template('maintenance_requests.html', requests=data)

@app.route('/maintenance/request/new', methods=['GET', 'POST'])
@login_required
def new_maintenance_request():
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
            # Try to get user ID from auth status
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
            except:
                pass

        if not user_id:
            flash('User ID not found', 'warning')
            return redirect(url_for('dashboard'))

        # Call the create request API
        try:
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

            if response.status_code == 200:
                flash('Maintenance request created successfully!', 'success')
                return redirect(url_for('maintenance_requests'))
            elif response.status_code == 401:
                flash('Your session has expired. Please login again.', 'warning')
                return redirect(url_for('logout'))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('message', 'Unknown error'))
                except:
                    error_msg = f"Server error (Status code: {response.status_code})"

                flash(f'Failed to create request: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
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

    app.run(debug=True, port=8000)
