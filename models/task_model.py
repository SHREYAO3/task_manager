import pyodbc
import os
import json
from datetime import datetime


class TaskDatabase:
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
                # Create tasks table if it doesn't exist
                self.cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TASKS')
                BEGIN
                    CREATE TABLE TASKS (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user_id INT NOT NULL,
                        title NVARCHAR(255) NOT NULL,
                        description NVARCHAR(MAX),
                        category NVARCHAR(100) NOT NULL,
                        type NVARCHAR(100) NOT NULL,
                        deadline_datetime NVARCHAR(50) NOT NULL,
                        deadline_days INT NOT NULL,
                        urgency INT NOT NULL,
                        effort FLOAT NOT NULL,
                        priority FLOAT NOT NULL,
                        created_at DATETIME DEFAULT GETDATE(),
                        completed BIT DEFAULT 0,
                        status NVARCHAR(20) DEFAULT 'pending',
                        reminder_datetime NVARCHAR(50),
                        FOREIGN KEY (user_id) REFERENCES USERS(id)
                    )
                END
                """)
                self.conn.commit()
               
                # Check if reminder_datetime column exists
                has_reminder_column = True
                try:
                    self.cursor.execute("SELECT reminder_datetime FROM TASKS WHERE 1=0")
                except pyodbc.Error:
                    has_reminder_column = False
               
                # Add reminder_datetime column if it doesn't exist
                if not has_reminder_column:
                    try:
                        self.cursor.execute("ALTER TABLE TASKS ADD reminder_datetime NVARCHAR(50)")
                        self.conn.commit()
                        print("Added reminder_datetime column to TASKS table")
                    except pyodbc.Error as e:
                        print(f"Error adding reminder_datetime column: {e}")
               
                # Check if status column exists
                has_status_column = True
                try:
                    self.cursor.execute("SELECT status FROM TASKS WHERE 1=0")
                except pyodbc.Error:
                    has_status_column = False
               
                # Add status column if it doesn't exist
                if not has_status_column:
                    try:
                        self.cursor.execute("ALTER TABLE TASKS ADD status NVARCHAR(20) DEFAULT 'pending'")
                        self.conn.commit()
                        print("Added status column to TASKS table")
                    except pyodbc.Error as e:
                        print(f"Error adding status column: {e}")
               
            except pyodbc.Error as e:
                print(f"Error creating table: {e}")
            finally:
                self.disconnect()
   
    def add_task(self, task_data, priority, user_id):
        if self.connect():
            try:
                query = """
                INSERT INTO TASKS (user_id, title, description, category, type, deadline_datetime, deadline_days,
                                urgency, effort, priority, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                status = task_data.get('status', 'pending')
                self.cursor.execute(query, (
                    user_id,
                    task_data['title'],
                    task_data['description'],
                    task_data['category'],
                    task_data['type'],
                    task_data['deadline_datetime'],
                    task_data['deadline_days'],
                    task_data['urgency'],
                    task_data['effort'],
                    priority,
                    status
                ))
                self.conn.commit()
                self.cursor.execute("SELECT @@IDENTITY AS ID")
                last_id = self.cursor.fetchone()[0]
                print(f"Task inserted with ID: {last_id}")
                return True
            except pyodbc.Error as e:
                print(f"Error adding task: {e}")
                return False
            finally:
                self.disconnect()
        return False
   
    def get_all_tasks(self, user_id, order_by='priority', descending=False):
        if self.connect():
            try:
                sort_mapping = {
                    'priority': 'priority',
                    'deadline': 'deadline_datetime',
                    'effort': 'effort'
                }
                sort_column = sort_mapping.get(order_by, 'priority')
                direction = "DESC" if descending else "ASC"
               
                query = f"SELECT * FROM TASKS WHERE user_id = ? ORDER BY {sort_column} {direction}"
                self.cursor.execute(query, (user_id,))
               
                columns = [column[0] for column in self.cursor.description]
                tasks = []
               
                # Fetch all rows before closing the connection
                rows = self.cursor.fetchall()
               
                # Process the rows after fetching all data
                for row in rows:
                    task = dict(zip(columns, row))
                    if 'deadline_datetime' in task:
                        deadline = datetime.strptime(task['deadline_datetime'], '%Y-%m-%d %H:%M')
                        current = datetime.now()
                        days_left = (deadline - current).days
                        if (deadline - current).seconds > 0 and days_left >= 0:
                            days_left += 1
                       
                        task['deadline_days'] = max(0, days_left)
                   
                    # Set default status if not present
                    if 'status' not in task or task['status'] is None:
                        task['status'] = 'pending'
                       
                    # Ensure status is consistent with completed flag
                    if task.get('completed'):
                        task['status'] = 'completed'
                   
                    tasks.append(task)
               
                print(f"Retrieved {len(tasks)} tasks from database with query: {query}")
                return tasks
            except pyodbc.Error as e:
                print(f"Error retrieving tasks: {e}")
                return []
            finally:
                self.disconnect()
        return []
   
    def mark_task_completed(self, task_id, user_id):
        if self.connect():
            try:
                self.cursor.execute("""
                UPDATE TASKS SET completed = 1, status = 'completed' WHERE id = ? AND user_id = ?
                """, (task_id, user_id))
                self.conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"Error completing task: {e}")
                return False
            finally:
                self.disconnect()
        return False
   
    def delete_task(self, task_id, user_id):
        if self.connect():
            try:
                self.cursor.execute("""
                DELETE FROM TASKS WHERE id = ? AND user_id = ?
                """, (task_id, user_id))
                self.conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"Error deleting task: {e}")
                return False
            finally:
                self.disconnect()
        return False




    def update_task_status(self, task_id, user_id, status):
        if self.connect():
            try:
                # Check if status column exists
                has_status_column = True
                try:
                    self.cursor.execute("SELECT status FROM TASKS WHERE id = ?", (task_id,))
                    self.cursor.fetchone()  # Just to check if it works
                except pyodbc.Error:
                    has_status_column = False
               
                # Create status column if it doesn't exist
                if not has_status_column:
                    self.cursor.execute("ALTER TABLE TASKS ADD status NVARCHAR(20) DEFAULT 'pending'")
                    self.conn.commit()
               
                # Update the task status
                self.cursor.execute("""
                UPDATE TASKS SET status = ? WHERE id = ? AND user_id = ?
                """, (status, task_id, user_id))
                self.conn.commit()
               
                # If status is 'completed', also update the completed flag
                if status == 'completed':
                    self.cursor.execute("""
                    UPDATE TASKS SET completed = 1 WHERE id = ? AND user_id = ?
                    """, (task_id, user_id))
                    self.conn.commit()
                elif status != 'completed':
                    # If status is not 'completed', ensure completed flag is set to 0
                    self.cursor.execute("""
                    UPDATE TASKS SET completed = 0 WHERE id = ? AND user_id = ?
                    """, (task_id, user_id))
                    self.conn.commit()
               
                return True
            except pyodbc.Error as e:
                print(f"Error updating task status: {e}")
                return False
            finally:
                self.disconnect()
        return False




    def get_task(self, task_id, user_id):
        if self.connect():
            try:
                query = "SELECT * FROM TASKS WHERE id = ? AND user_id = ?"
                self.cursor.execute(query, (task_id, user_id))
               
                # Get column names
                columns = [column[0] for column in self.cursor.description]
               
                # Fetch the row before closing the connection
                row = self.cursor.fetchone()
               
                if row:
                    task = dict(zip(columns, row))
                    if 'deadline_datetime' in task:
                        deadline = datetime.strptime(task['deadline_datetime'], '%Y-%m-%d %H:%M')
                        current = datetime.now()
                        days_left = (deadline - current).days
                        if (deadline - current).seconds > 0 and days_left >= 0:
                            days_left += 1
                        task['deadline_days'] = max(0, days_left)
                   
                    # Set default status if not present
                    if 'status' not in task or task['status'] is None:
                        task['status'] = 'pending'
                       
                    # Ensure status is consistent with completed flag
                    if task.get('completed'):
                        task['status'] = 'completed'
                       
                    return task
                return None
            except pyodbc.Error as e:
                print(f"Error retrieving task: {e}")
                return None
            finally:
                self.disconnect()
        return None




    def update_task(self, task_id, user_id, task_data, priority):
        if self.connect():
            try:
                # First, get the existing task to preserve the status if not explicitly changed
                current_status = 'pending'
                try:
                    self.cursor.execute("SELECT status FROM TASKS WHERE id = ? AND user_id = ?", (task_id, user_id))
                    row = self.cursor.fetchone()
                    if row and row[0]:
                        current_status = row[0]
                except pyodbc.Error:
                    # If there's an error, use default 'pending' status
                    pass
               
                # Use the provided status or keep the current one
                status = task_data.get('status', current_status)
               
                # Execute the update query in one go
                query = """
                UPDATE TASKS
                SET title = ?, description = ?, category = ?, type = ?,
                    deadline_datetime = ?, deadline_days = ?, urgency = ?,
                    effort = ?, priority = ?, status = ?
                WHERE id = ? AND user_id = ?
                """
                self.cursor.execute(query, (
                    task_data['title'],
                    task_data['description'],
                    task_data['category'],
                    task_data['type'],
                    task_data['deadline_datetime'],
                    task_data['deadline_days'],
                    task_data['urgency'],
                    task_data['effort'],
                    priority,
                    status,
                    task_id,
                    user_id
                ))
                self.conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"Error updating task: {e}")
                return False
            finally:
                self.disconnect()
        return False








    def search_tasks(self, user_id, search_query):
        if self.connect():
            try:
                query = """
                SELECT * FROM TASKS
                WHERE user_id = ?
                AND (
                    LOWER(title) LIKE LOWER(?)
                    OR LOWER(description) LIKE LOWER(?)
                )
                ORDER BY priority DESC
                """
                search_pattern = f"%{search_query}%"
                self.cursor.execute(query, (user_id, search_pattern, search_pattern))
               
                columns = [column[0] for column in self.cursor.description]
                tasks = []
               
                # Fetch all rows before closing the connection
                rows = self.cursor.fetchall()
               
                # Process the rows after fetching all data
                for row in rows:
                    task = dict(zip(columns, row))
                    if 'deadline_datetime' in task:
                        deadline = datetime.strptime(task['deadline_datetime'], '%Y-%m-%d %H:%M')
                        current = datetime.now()
                        days_left = (deadline - current).days
                        if (deadline - current).seconds > 0 and days_left >= 0:
                            days_left += 1
                        task['deadline_days'] = max(0, days_left)
                   
                    # Set default status if not present
                    if 'status' not in task or task['status'] is None:
                        task['status'] = 'pending'
                       
                    # Ensure status is consistent with completed flag
                    if task.get('completed'):
                        task['status'] = 'completed'
                       
                    tasks.append(task)
               
                return tasks
            except pyodbc.Error as e:
                print(f"Error searching tasks: {e}")
                return []
            finally:
                self.disconnect()
        return []


    def set_reminder(self, task_id, user_id, reminder_datetime):
        if self.connect():
            try:
                self.cursor.execute("""
                UPDATE TASKS SET reminder_datetime = ? WHERE id = ? AND user_id = ?
                """, (reminder_datetime, task_id, user_id))
                self.conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"Error setting reminder: {e}")
                return False
            finally:
                self.disconnect()
        return False


    def get_pending_reminders(self):
        """Get all tasks with reminders that need to be sent"""
        if self.connect():
            try:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                self.cursor.execute("""
                SELECT t.*, u.email, u.username
                FROM TASKS t
                JOIN USERS u ON t.user_id = u.id
                WHERE t.reminder_datetime <= ?
                AND t.reminder_datetime IS NOT NULL
                AND t.status != 'completed'
                """, (current_time,))
               
                columns = [column[0] for column in self.cursor.description]
                tasks = []
               
                rows = self.cursor.fetchall()
                for row in rows:
                    task = dict(zip(columns, row))
                    tasks.append(task)
               
                return tasks
            except pyodbc.Error as e:
                print(f"Error getting pending reminders: {e}")
                return []
            finally:
                self.disconnect()
        return []


    def clear_reminder(self, task_id):
        """Clear the reminder after it has been sent"""
        if self.connect():
            try:
                self.cursor.execute("""
                UPDATE TASKS SET reminder_datetime = NULL WHERE id = ?
                """, (task_id,))
                self.conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"Error clearing reminder: {e}")
                return False
            finally:
                self.disconnect()
        return False