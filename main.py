from flask import Flask, request, jsonify, make_response
import mysql.connector
import bcrypt
import jwt
import datetime
import logging
import hashlib
import psycopg2
import AddUser
import Login
import requests
import UpdateImage
import hashlib
from functools import wraps

def hash_password_md5(password):
    # Encode the password to bytes, then create MD5 hash
    md5_hash = hashlib.md5(password.encode())
    return md5_hash.hexdigest()



app = Flask(__name__)
app.config['SECRET_KEY']  = 'CS'  # Change this in production

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

#  Corrected Database Configuration
db_config_proj = {
    "host": "10.0.116.125",  # Only the IP or hostname, no http or phpmyadmin
    "user": "cs432g6",
    "password": "pZ3nLbKX",  # Use your real password here
    "database": "cs432g6"
}

db_config_cism = {
    "host": "10.0.116.125",
    "user": "cs432g6",
    "password": "pZ3nLbKX",  # Use your real password here
    "database": "cs432cims"
}

def get_db_connection(cims = True):
    """Establish a database connection."""
    if cims:
        return mysql.connector.connect(**db_config_cism)
    else:
        return mysql.connector.connect(**db_config_proj)

# Role-based access control decorator
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get('session_token')
            
            # Check if Authorization header exists as fallback
            if not token and 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Check for token in request parameters as another fallback
            if not token and 'token' in request.args:
                token = request.args.get('token')
                
            if not token:
                return jsonify({"error": "Authentication required"}), 401
                
            try:
                # Decode the JWT token
                decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                
                # Check if user's role is in allowed roles
                if decoded["role"] not in allowed_roles:
                    logging.warning(f"Access denied: User {decoded['user']} with role {decoded['role']} attempted to access {request.path}")
                    return jsonify({"error": "Insufficient permissions"}), 403
                    
                # Add user info to request for potential use in the route handler
                request.user = decoded
                
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Session expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/addUser', methods=['POST'])
@role_required(['admin'])
def add_user():
    session_id = request.json['session_id']
    # isAuthorised = requests.get("http://10.0.116.125:5000/isAuth",params={"session_id":session_id})
    # if isAuthorised.status_code != 200:
    #     return jsonify({"error": "Unauthorized"}), 401
    out = AddUser.AddUser(request, logging, get_db_connection())
    return out.response()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username, password = data.get('user'), data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Get MemberID from members table using the username
        cursor.execute("SELECT ID FROM members WHERE UserName = %s", (username,))
        member = cursor.fetchone()
        
        if not member:
            return jsonify({"error": "User not found"}), 404

        member_id = member['ID']
        
        # Now, retrieve password and role from the Login table using MemberID
        cursor.execute("SELECT Password, Role FROM Login WHERE MemberID = %s", (member_id,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    # Use MD5 comparison instead of bcrypt
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    if not user or hashed_password != user['Password']:
        return jsonify({"error": "Invalid credentials"}), 401

    # Include the role in the token payload
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
    
    # Update session in database
    login = Login.Login(request, get_db_connection(), logging, app.config['SECRET_KEY'])
    login.get_session()

    # Return the response with token
    if login.response:
        return login.response
    return response

# Add a new admin-only route for database management
@app.route('/adminDatabaseAccess', methods=['GET'])
@role_required(['admin'])  # Only allow admin role
def admin_database_access():
    # This route gives admins access to database information
    action = request.args.get('action')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if action == 'list_members':
            cursor.execute("SELECT * FROM members")
            members = cursor.fetchall()
            return jsonify(members), 200
        elif action == 'list_logins':
            cursor.execute("SELECT * FROM Login")
            logins = cursor.fetchall()
            return jsonify(logins), 200
        else:
            return jsonify({"error": "Invalid action"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Add a route to delete members (admin only)
@app.route('/deleteMember/<int:member_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_member(member_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE ID = %s", (member_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Member not found"}), 404
            
        # Delete from Login table first
        cursor.execute("DELETE FROM Login WHERE MemberID = %s", (str(member_id),))
        
        # Then delete from members table
        cursor.execute("DELETE FROM members WHERE ID = %s", (member_id,))
        
        conn.commit()
        return jsonify({"message": f"Member {member_id} deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/isAuth', methods=['GET'])
def is_auth():
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

@app.route('/dbcon', methods=['GET'])
def dbcon():
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

@app.route('/updateImage', methods=['POST'])
def updateImage():
    UpdateImage.UpdateImage(request, get_db_connection(), logging).update_image()

@app.route('/', methods=['GET'])
def hello():
    return jsonify({"message": "Hello, you are welcome"}), 200

if __name__ == '__main__':
    # Optional: test DB connection on startup
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

