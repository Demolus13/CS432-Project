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
    "user": "insta",
    "password": "tempPass",  # Use your real password here
    "database": "insta"
}

db_config_cism = {
    "host": "10.0.116.125",
    "user": "insta",
    "password": "tempPass",  # Use your real password here
    "database": "cs432cims"
}

def get_db_connection(cims = True):
    """Establish a database connection."""
    if cims:
        return mysql.connector.connect(**db_config_cism)
    else:
        return mysql.connector.connect(**db_config_proj)



@app.route('/addUser', methods=['POST'])
def add_user():
    session_id = request.json['session_id']
    isAuthorised = requests.get("http://10.0.116.125:5000/isAuth",params={"session_id":session_id})
    if isAuthorised.status_code != 200:
        return jsonify({"error": "Unauthorized"}), 401
    out = AddUser.AddUser(request, logging, get_db_connection())
    return out.response()

@app.route('/login', methods=['POST'])
def login():
    # data = request.json
    # username, password = data.get('user'), data.get('password')

    # if not username or not password:
    #     return jsonify({"error": "Missing parameters"}), 400

    # try:
    #     conn = get_db_connection()
    #     cursor = conn.cursor(dictionary=True)
    #     cursor.execute("SELECT Password, Role FROM Login WHERE User = %s", (username,))
    #     user = cursor.fetchone()
    # finally:
    #     cursor.close()
    #     conn.close()

    # if not user or not bcrypt.checkpw(password.encode(), user['Password'].encode()):
    #     return jsonify({"error": "Invalid credentials"}), 401

    # token = jwt.encode({
    #     "user": username,
    #     "role": user['Role'],
    #     "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    # }, app.config['SECRET_KEY'], algorithm="HS256")

    # response = make_response(jsonify({"message": "Login successful"}))
    # response.set_cookie('session_token', token, max_age=3600, httponly=True)
    login = Login.Login(request, get_db_connection(), logging, app.config['SECRET_KEY'])
    login.get_session()

    # return jsonify({'message': 'Login successful'}), 200
    return login.response

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

