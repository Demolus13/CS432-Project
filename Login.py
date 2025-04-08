import hashlib
import mysql.connector
from flask import jsonify, make_response
import jwt
import datetime

class Login:
    def __init__(self, request, conn, logging, secret_key):
        self.data = request.json
        self.username = self.data.get('username')
        self.password = self.data.get('password')
        self.group = self.data.get('group')
        self.password = hashlib.md5(self.password.encode()).hexdigest()
        self.conn = conn
        self.logging = logging
        self.success = True
        self.message = ''
        self.status = 200
        self.secret_key = secret_key
        self.get_member_id()
        self.response = None

    def get_member_id(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT ID FROM members WHERE UserName = (%s);", (self.username,))
            name = cursor.fetchall()
            if name:
                self.member_id = name[0][0]  # Assuming the first column is the ID
                return
            else:
                self.success = False
                self.message = f"Member {self.username} does not exist"
                self.logging.info(f"Member {self.username} does not exist")
                return
        except mysql.connector.Error as e:
            self.success = False
            self.logging.error(f"MySQL Error: {e}")

    def get_session(self):
        if not self.success:
            return
        self.cursor = self.conn.cursor()
        try:
            # check if member with member id exisits in group mapping with group id or not.

            try:
                cursor = self.conn.cursor(dictionary=True)
                cursor.execute("SELECT Password, Role FROM Login WHERE MemberID = %s", (self.member_id,))
                user = cursor.fetchone()
            except Exception as e:
                print(e)
            finally:
                cursor.close()

            if not user or self.password != user['Password']:
                self.response = jsonify({"error": "Invalid credentials"}), 401
                return
            expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            expiry = expiry.timestamp()
            token = jwt.encode({
                "user": self.username,
                "role": user['Role'],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                "group": self.group,
                "session_id": self.member_id
            }, self.secret_key, algorithm="HS256")
            cursor = self.conn.cursor()
            print(token)
            cursor.execute('UPDATE Login SET Session = %s, Expiry = %s WHERE MemberID = %s', 
                           (token, expiry, self.member_id))
            self.conn.commit()
            print('update', token, expiry, self.member_id)
            return
            self.response = jsonify({"message": "Login successful", 'session_token': token,
                                              'max_age':3600, 'username': self.username, 'group': self.group,
                                              'role': self.role})
            print('******************************',self.response)
            cursor.close()
            self.conn.comiit()
        except mysql.connector.Error as e:
            self.success = False
            self.logging.error(f"MySQL Error: {e}")
        return self