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
            
    def initialize_db(self):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if self.connect():
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
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
                INSERT INTO tasks (title, description, category, type, deadline_days, 
                                   urgency, effort, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_data['title'],
                    task_data['description'],
                    task_data['category'],
                    task_data['type'],
                    task_data['deadline_days'],
                    task_data['urgency'],
                    task_data['effort'],
                    priority
                ))
                self.conn.commit()
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
                query = f"SELECT * FROM tasks WHERE completed = 0 ORDER BY {order_by} {direction}"
                self.cursor.execute(query)
                tasks = [dict(row) for row in self.cursor.fetchall()]
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
                UPDATE tasks SET completed = 1 WHERE id = ?
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
                DELETE FROM tasks WHERE id = ?
                ''', (task_id,))
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error deleting task: {e}")
                return False
            finally:
                self.disconnect()
        return False