import hashlib
from flask import jsonify
import mysql.connector
import psycopg2
import time


class AddUser:
    def __init__(self, request, logging, conn):
        self.request = request
        self.logging = logging
        self.conn = conn
        self.data = request.json
        self.success = True
        self.message = ''
        self.member_id = None
        self.status = 200
        self.check_keys()
        self.add_user()
        self.add_group_mapping()
        self.create_login()

    def response(self):
        return jsonify(self.message),self.status    

    def check_keys(self):
        keys = ['username','password','role', 'email', 'session_id', 'DoB']
        for key in keys:
            if key not in self.data.keys():
                self.success = False
                self.message = {'error', f'Bad request: {key} not found'}, 400
                return

    def add_user(self):
        if not self.success:
            return
        self.username = self.data['username']
        self.email = self.data['email']
        self.DoB = self.data['DoB']

        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM members where UserName = (%s);", (self.username,))
            name = cursor.fetchall()
            if name:
                self.member_id = name[0][1]  # Assuming the first column is the ID
                return
            else:
                cursor.execute("INSERT INTO members (UserName, emailID, DoB) VALUES (%s, %s, %s);", 
                            (self.username, self.email, self.DoB))
                self.conn.commit()
                # Get the ID of the newly inserted member
                cursor.execute("SELECT ID FROM members WHERE UserName = %s", (self.username,))
                result = cursor.fetchone()
                if result:
                    self.member_id = result[0]
                    self.logging.info(f"User {self.username} added with ID {self.member_id}")
                else:
                    self.success = False
                    self.message = "Failed to retrieve member ID after insertion"
                    self.status = 500
        except mysql.connector.Error as e:
            self.success = False
            self.logging.error(f"MySQL Error: {e}")
            self.message = {'error': str(e)}
            self.status = 500
        finally:
            cursor.close()

    def add_group_mapping(self):
        pass

    def get_group_id(self, session_id):
        if not self.success:
            return
        pass

    def create_login(self):
        if not self.success or not self.member_id:
            return
            
        cursor = self.conn.cursor()
        try:
            # Check if login entry already exists
            cursor.execute("SELECT MemberID FROM Login WHERE MemberID = %s", (str(self.member_id),))
            login_exists = cursor.fetchone()
            
            if login_exists:
                # Update existing login entry
                cursor.execute(
                    'UPDATE Login SET Password = %s, Role = %s WHERE MemberID = %s', 
                    (hashlib.md5(self.data.get('password', self.username).encode()).hexdigest(), 
                     self.data['role'], 
                     str(self.member_id))
                )
            else:
                # Create new login entry
                cursor.execute(
                    'INSERT INTO Login (MemberID, Password, Role) VALUES (%s, %s, %s)', 
                    (str(self.member_id), 
                     hashlib.md5(self.data.get('password', '').encode()).hexdigest(), 
                     self.data['role'])
                )
            
            self.conn.commit()
            self.logging.info(f"User {self.username} added to login table with ID {self.member_id}")
            self.message = {'message': 'User added successfully with default login credentials'}
            self.status = 200
        except Exception as e:
            self.message = {'error': f'Failed to add user to login table: {str(e)}'}
            self.status = 500
            self.logging.error(f"Error adding user to login table: {e}")
        finally:
            cursor.close()

    def __del__(self):
        try:
            self.conn.close()
        except:
            pass