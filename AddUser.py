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
            # print('name', name)
            if name:
                self.member_id = name[0][1]  # Assuming the first column is the ID
                # print('if', name)
                return
            else:
                cursor.execute("INSERT INTO members (UserName, emailID, DoB) VALUES (%s, %s, %s);", 
                            (self.username, self.email, self.DoB))
                self.conn.commit()
        except mysql.connector.Error as e:
            self.success = False
            self.logging.error(f"MySQL Error: {e}")
            self.success = False
            self.message = f"'error': {str(e)}"
            self.status = 400
        finally:
            cursor.close()

    def add_group_mapping(self):
        pass

    def get_group_id(self, session_id):
        if not self.success:
            return
        pass

    def create_login(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ID FROM members WHERE UserName = (%s);", (self.username,))
            name = cursor.fetchall()
            # print('name',name)
            self.member_id = name[0][0]
            # print('login', self.member_id)
            # if user already exists then just update the password and role
            cursor.execute('INSERT INTO Login (MemberID, Password, Role) VALUES (%s, %s, %s)', (self.member_id, hashlib.md5(self.data.get('password', '').encode()).hexdigest(), self.data['role']))
            self.conn.commit()
            self.logging.info(f"User {self.username} added to login table")
            self.message = {'message': 'User added successfully'}
            self.status = 200
        except Exception as e:
            self.message = self.message + ' -- Failed to add user to login table'
            self.status = 500
            # print(e)
            self.logging.error(f"Error adding user to login table: {e}")
        finally:
            cursor.close()

    def __del__(self):
        try:
            self.conn.close()
        finally:
            pass