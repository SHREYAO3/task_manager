import sqlite3
import os
import json
from datetime import datetime

class TaskDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_db()
       
    def connect(self):
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # This enables column access by name
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return False
           
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
           
    def initialize_db(self):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
       
        if self.connect():
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS TASKS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                deadline_datetime TEXT NOT NULL,
                deadline_days INTEGER NOT NULL,
                urgency INTEGER NOT NULL,
                effort REAL NOT NULL,
                priority REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT 0
            )
            ''')
            self.conn.commit()
            self.disconnect()
   
    def add_task(self, task_data, priority):
        if self.connect():
            try:
                self.cursor.execute('''
                INSERT INTO TASKS (title, description, category, type, deadline_datetime, deadline_days,
                                   urgency, effort, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
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
                print(f"Task inserted with ID: {self.cursor.lastrowid}")
                return True
            except sqlite3.Error as e:
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
                tasks = [dict(row) for row in self.cursor.fetchall()]
                
                # Debug task retrieval
                print(f"Retrieved {len(tasks)} tasks from database with query: {query}")
                
                # Update days left for each task
                for task in tasks:
                    if 'deadline_datetime' in task:
                        deadline = datetime.strptime(task['deadline_datetime'], '%Y-%m-%d %H:%M')
                        current = datetime.now()
                        days_left = (deadline - current).days
                       
                        # Add 1 if there are still hours left in the current day
                        if (deadline - current).seconds > 0 and days_left >= 0:
                            days_left += 1
                       
                        task['deadline_days'] = max(0, days_left)
               
                return tasks
            except sqlite3.Error as e:
                print(f"Error retrieving tasks: {e}")
                return []
            finally:
                self.disconnect()
        return []
   
    def mark_task_completed(self, task_id):
        if self.connect():
            try:
                self.cursor.execute('''
                UPDATE TASKS SET completed = 1 WHERE id = ?
                ''', (task_id,))
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error completing task: {e}")
                return False
            finally:
                self.disconnect()
        return False
   
    def delete_task(self, task_id):
        if self.connect():
            try:
                self.cursor.execute('''
                DELETE FROM TASKS WHERE id = ?
                ''', (task_id,))
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error deleting task: {e}")
                return False
            finally:
                self.disconnect()
        return False