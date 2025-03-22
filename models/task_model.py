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
                        FOREIGN KEY (user_id) REFERENCES USERS(id)
                    )
                END
                """)
                self.conn.commit()
            except pyodbc.Error as e:
                print(f"Error creating table: {e}")
            finally:
                self.disconnect()
   
    def add_task(self, task_data, priority, user_id):
        if self.connect():
            try:
                query = """
                INSERT INTO TASKS (user_id, title, description, category, type, deadline_datetime, deadline_days,
                                urgency, effort, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
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
                    priority
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
   
    def get_all_tasks(self, user_id, order_by='priority', descending=True):
        if self.connect():
            try:
                sort_mapping = {
                    'priority': 'priority',
                    'deadline': 'deadline_datetime',
                    'effort': 'effort'
                }
                sort_column = sort_mapping.get(order_by, 'priority')
                direction = "DESC" if descending else "ASC"
               
                if order_by == 'deadline':
                    direction = "ASC" if descending else "DESC"
               
                query = f"SELECT * FROM TASKS WHERE completed = 0 AND user_id = ? ORDER BY {sort_column} {direction}"
                self.cursor.execute(query, (user_id,))
               
                columns = [column[0] for column in self.cursor.description]
                tasks = []
                for row in self.cursor.fetchall():
                    task = dict(zip(columns, row))
                    if 'deadline_datetime' in task:
                        deadline = datetime.strptime(task['deadline_datetime'], '%Y-%m-%d %H:%M')
                        current = datetime.now()
                        days_left = (deadline - current).days
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
   
    def mark_task_completed(self, task_id, user_id):
        if self.connect():
            try:
                self.cursor.execute("""
                UPDATE TASKS SET completed = 1 WHERE id = ? AND user_id = ?
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