import pyodbc
import os
import json
from datetime import datetime


class TaskDatabase:
    def __init__(self, connection_string=None):
        # Default connection string - update with your SQL Server details
        self.connection_string = connection_string or (
            "DRIVER={SQL Server};"
            "SERVER=YOUR_SERVER_NAME;"  # Replace with your server name
            "DATABASE=TaskManager;"     # Replace with your database name
            "Trusted_Connection=yes;"   # For Windows authentication
        )
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
                # Check if the table exists
                self.cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TASKS')
                BEGIN
                    CREATE TABLE TASKS (
                        id INT IDENTITY(1,1) PRIMARY KEY,
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
                        completed BIT DEFAULT 0
                    )
                END
                """)
                self.conn.commit()
            except pyodbc.Error as e:
                print(f"Error creating table: {e}")
            finally:
                self.disconnect()
   
    def add_task(self, task_data, priority):
        if self.connect():
            try:
                query = """
                INSERT INTO TASKS (title, description, category, type, deadline_datetime, deadline_days,
                                urgency, effort, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    priority
                ))
                self.conn.commit()
                
                # Get the last insert ID (different from SQLite)
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
   
    def get_all_tasks(self, order_by='priority', descending=True):
        if self.connect():
            try:
                direction = "DESC" if descending else "ASC"
                query = f"SELECT * FROM TASKS WHERE completed = 0 ORDER BY {order_by} {direction}"
                self.cursor.execute(query)
                
                # Convert rows to dictionaries
                columns = [column[0] for column in self.cursor.description]
                tasks = []
                for row in self.cursor.fetchall():
                    task = dict(zip(columns, row))
                    
                    # Update days left for each task
                    if 'deadline_datetime' in task:
                        deadline = datetime.strptime(task['deadline_datetime'], '%Y-%m-%d %H:%M')
                        current = datetime.now()
                        days_left = (deadline - current).days
                       
                        # Add 1 if there are still hours left in the current day
                        if (deadline - current).seconds > 0 and days_left >= 0:
                            days_left += 1
                       
                        task['deadline_days'] = max(0, days_left)
                    
                    tasks.append(task)
               
                print(f"Retrieved {len(tasks)} tasks from database with query: {query}")
                return tasks
            except pyodbc.Error as e:
                print(f"Error retrieving tasks: {e}")
                return []
            finally:
                self.disconnect()
        return []
   
    def mark_task_completed(self, task_id):
        if self.connect():
            try:
                self.cursor.execute("""
                UPDATE TASKS SET completed = 1 WHERE id = ?
                """, (task_id,))
                self.conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"Error completing task: {e}")
                return False
            finally:
                self.disconnect()
        return False
   
    def delete_task(self, task_id):
        if self.connect():
            try:
                self.cursor.execute("""
                DELETE FROM TASKS WHERE id = ?
                """, (task_id,))
                self.conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"Error deleting task: {e}")
                return False
            finally:
                self.disconnect()
        return False