import pyodbc
import os
import hashlib
import secrets


class UserDatabase:
    def __init__(self, connection_string=None):
        DRIVER_NAME = 'SQL SERVER'
        SERVER_NAME = r'ANURADHA\SQLEXPRESS01'
        DATABASE_NAME = 'TaskManager'
        self.connection_string = f"""
        DRIVER={DRIVER_NAME};
        SERVER={SERVER_NAME};
        DATABASE={DATABASE_NAME};
        Trusted_Connection=yes;
        """
        self.conn = None
        self.cursor = None
        self.initialize_db()
   
    def connect(self):
        try:
            self.conn = pyodbc.connect(self.connection_string)
            self.cursor = self.conn.cursor()
            return True
        except pyodbc.Error as e:
            print(f"Database connection error: {e}")
            return False
   
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
   
    def initialize_db(self):
        if self.connect():
            try:
                # Create users table
                self.cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'USERS')
                BEGIN
                    CREATE TABLE USERS (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username NVARCHAR(50) UNIQUE NOT NULL,
                        email NVARCHAR(100) UNIQUE NOT NULL,
                        password_hash NVARCHAR(64) NOT NULL,
                        salt NVARCHAR(32) NOT NULL,
                        created_at DATETIME DEFAULT GETDATE()
                    )
                END
                """)
                self.conn.commit()
            except pyodbc.Error as e:
                print(f"Error creating users table: {e}")
            finally:
                self.disconnect()
   
    def _hash_password(self, password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode('utf-8'))
        return hash_obj.hexdigest(), salt
   
    def create_user(self, username, email, password):
        if self.connect():
            try:
                # Check if username or email already exists
                self.cursor.execute("""
                SELECT COUNT(*) FROM USERS
                WHERE username = ? OR email = ?
                """, (username, email))
                if self.cursor.fetchone()[0] > 0:
                    return False, "Username or email already exists"
               
                # Hash password and create user
                password_hash, salt = self._hash_password(password)
                self.cursor.execute("""
                INSERT INTO USERS (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
                """, (username, email, password_hash, salt))
                self.conn.commit()
                return True, "User created successfully"
            except pyodbc.Error as e:
                print(f"Error creating user: {e}")
                return False, "Error creating user"
            finally:
                self.disconnect()
        return False, "Database connection error"
   
    def verify_user(self, username, password):
        if self.connect():
            try:
                # Get user's salt and password hash
                self.cursor.execute("""
                SELECT id, password_hash, salt FROM USERS
                WHERE username = ?
                """, (username,))
                result = self.cursor.fetchone()
               
                if not result:
                    return False, None
               
                user_id, stored_hash, salt = result
               
                # Verify password
                password_hash, _ = self._hash_password(password, salt)
                if password_hash == stored_hash:
                    return True, user_id
                return False, None
            except pyodbc.Error as e:
                print(f"Error verifying user: {e}")
                return False, None
            finally:
                self.disconnect()
        return False, None
   
    def get_user_by_id(self, user_id):
        if self.connect():
            try:
                self.cursor.execute("""
                SELECT id, username, email, created_at
                FROM USERS WHERE id = ?
                """, (user_id,))
                result = self.cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'username': result[1],
                        'email': result[2],
                        'created_at': result[3]
                    }
                return None
            except pyodbc.Error as e:
                print(f"Error getting user: {e}")
                return None
            finally:
                self.disconnect()
        return None