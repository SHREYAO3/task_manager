from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from models.task_model import TaskDatabase
from models.ml_model import TaskPrioritizer
from datetime import datetime, timedelta

class TaskManagerApp:
    def __init__(self):
        self.app = Flask(__name__)
       
        DRIVER_NAME = 'SQL SERVER'
        SERVER_NAME = r'ANURADHA\SQLEXPRESS01'
        DATABASE_NAME = 'TaskManager'
        self.connection_string = f"""
        DRIVER={DRIVER_NAME};
        SERVER={SERVER_NAME};
        DATABASE={DATABASE_NAME};
        Trusted_Connection=yes;
        """
        self.task_db = TaskDatabase(self.connection_string)
        self.task_prioritizer = TaskPrioritizer()
       
        # Register routes
        self._register_routes()
   
    def _register_routes(self):
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/add', 'add_task', self.add_task, methods=['GET', 'POST'])
        self.app.add_url_rule('/get_types/<category>', 'get_types', self.get_types)
        self.app.add_url_rule('/complete_task/<int:task_id>', 'complete_task', self.complete_task)
        self.app.add_url_rule('/delete_task/<int:task_id>', 'delete_task', self.delete_task)
        self.app.add_url_rule('/filter_tasks', 'filter_tasks', self.filter_tasks)
   
    def index(self):
        try:
            tasks = self.task_db.get_all_tasks()
            categories = self.task_prioritizer.get_all_categories()
           
            # Calculate stats
            urgent_tasks = sum(1 for task in tasks if task['urgency'] > 6)  # Count tasks with urgency > 6
            due_today = sum(1 for task in tasks if task['deadline_days'] <= 1)
           
            return render_template('index.html',
                                tasks=tasks,
                                categories=categories,
                                urgent_tasks=urgent_tasks,
                                due_today=due_today)
        except Exception as e:
            print(f"Error in index route: {e}")
            return render_template('index.html', tasks=[], error=str(e))
   
    def calculate_days_left(self, deadline_datetime_str):
        deadline_datetime = datetime.strptime(deadline_datetime_str, '%Y-%m-%d %H:%M')
        current_datetime = datetime.now()
       
        # Calculate the difference in days
        days_left = (deadline_datetime - current_datetime).days
       
        # Add 1 if there are still hours left in the current day
        if (deadline_datetime - current_datetime).seconds > 0 and days_left >= 0:
            days_left += 1
           
        return max(0, days_left)  # Ensure we don't have negative days
   
    def add_task(self):
        if request.method == 'POST':
            try:
                # Extract form data
                deadline_datetime = request.form['deadline_datetime']
                deadline_days = self.calculate_days_left(deadline_datetime)
               
                task_data = {
                    'title': request.form['title'],
                    'description': request.form['description'],
                    'category': request.form['category'],
                    'type': request.form['type'],
                    'deadline_datetime': deadline_datetime,  # Store the actual deadline datetime
                    'deadline_days': deadline_days,
                    'urgency': int(request.form['urgency']),
                    'effort': float(request.form['effort'])
                }
               
                # Debug the task data
                print(f"Adding task: {task_data}")
               
                # Predict priority
                priority = self.task_prioritizer.predict_priority(task_data)
                print(f"Calculated priority: {priority}")
               
                # Save task to database
                success = self.task_db.add_task(task_data, priority)
               
                if not success:
                    print("Failed to add task to database")
                    return render_template('add_task.html',
                                          categories=self.task_prioritizer.get_all_categories(),
                                          error="Failed to add task to database")
               
                # Redirect to index page
                return redirect(url_for('index'))
            except Exception as e:
                print(f"Error in add_task route: {e}")
                return render_template('add_task.html',
                                      categories=self.task_prioritizer.get_all_categories(),
                                      error=str(e))
       
        # GET request - show the form
        categories = self.task_prioritizer.get_all_categories()
        return render_template('add_task.html', categories=categories)
   
    def get_types(self, category):
        types = self.task_prioritizer.get_types_for_category(category)
        return jsonify(types)
   
    def complete_task(self, task_id):
        self.task_db.mark_task_completed(task_id)
        return redirect(url_for('index'))
   
    def delete_task(self, task_id):
        self.task_db.delete_task(task_id)
        return redirect(url_for('index'))
   
    def filter_tasks(self):
        try:
            category = request.args.get('category', '')
            sort_by = request.args.get('sort', 'priority')
            filter_type = request.args.get('filter_type', '')
           
            # Get all tasks
            tasks = self.task_db.get_all_tasks(order_by=sort_by)
           
            # Apply filters
            if filter_type == 'urgent':
                tasks = [task for task in tasks if task['urgency'] > 6]
            elif filter_type == 'due-today':
                tasks = [task for task in tasks if task['deadline_days'] <= 1]
            elif category:  # Only apply category filter if no special filter is active
                tasks = [task for task in tasks if task['category'] == category]
           
            # Convert datetime objects to strings for JSON serialization
            for task in tasks:
                if isinstance(task['created_at'], datetime):
                    task['created_at'] = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
           
            return jsonify(tasks)
        except Exception as e:
            print(f"Error in filter_tasks route: {e}")
            return jsonify({'error': str(e)}), 500
   
    def run(self, debug=True):
        self.app.run(debug=debug)

# Create the application instance
task_manager = TaskManagerApp()
app = task_manager.app

if __name__ == '__main__':
    task_manager.run(debug=True)