from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
from models.task_model import TaskDatabase
from models.user_model import UserDatabase
from models.ml_model import TaskPrioritizer
from datetime import datetime, timedelta
from functools import wraps




class TaskManagerApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)  # Required for session management
       
        DRIVER_NAME = 'SQL SERVER'
        SERVER_NAME = r'ANURADHA\SQLEXPRESS01'
        DATABASE_NAME = 'TaskManager'
        self.connection_string = f"""
        DRIVER={{SQL Server}};
        SERVER={SERVER_NAME};
        DATABASE={DATABASE_NAME};
        Trusted_Connection=yes;
        """
        self.task_db = TaskDatabase(self.connection_string)
        self.user_db = UserDatabase(self.connection_string)
        self.task_prioritizer = TaskPrioritizer()
       
        # Register routes
        self._register_routes()
   
    def login_required(self, f):
        """Decorator to require login for routes."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
   
    def _register_routes(self):
        """Register all application routes."""
        # Auth routes
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/signup', 'signup', self.signup, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.logout)
       
        # Landing page route (default route)
        @self.app.route('/')
        def landing():
            return render_template('landing.html')
       
        # Dashboard route (protected)
        self.app.add_url_rule('/dashboard', 'index', self.login_required(self.index))
        self.app.add_url_rule('/add', 'add_task', self.login_required(self.add_task), methods=['GET', 'POST'])
        self.app.add_url_rule('/get_types/<category>', 'get_types', self.login_required(self.get_types))
        self.app.add_url_rule('/complete_task/<int:task_id>', 'complete_task', self.login_required(self.complete_task))
        self.app.add_url_rule('/delete_task/<int:task_id>', 'delete_task', self.login_required(self.delete_task))
        self.app.add_url_rule('/filter_tasks', 'filter_tasks', self.login_required(self.filter_tasks))
       
        # Dark mode toggle route
        @self.app.route('/toggle_theme', methods=['POST'])
        def toggle_theme():
            current_theme = session.get('theme', 'light')
            new_theme = 'dark' if current_theme == 'light' else 'light'
            session['theme'] = new_theme
            return jsonify({'theme': new_theme})
       
        # Contact form submission route
        @self.app.route('/contact', methods=['POST'])
        def contact():
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
           
            # Here you would typically handle the contact form submission
            # For now, we'll just return a success message
            return jsonify({'status': 'success', 'message': 'Thank you for your message!'})
   
    def login(self):
        """Handle user login."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
           
            success, user_id = self.user_db.verify_user(username, password)
            if success:
                session['user_id'] = user_id
                session['username'] = username
                return redirect(url_for('index'))  # This will now redirect to /dashboard
            else:
                return render_template('login.html', error='Invalid username or password')
       
        return render_template('login.html')
   
    def signup(self):
        """Handle user registration."""
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
           
            if password != confirm_password:
                return render_template('signup.html', error='Passwords do not match')
           
            success, message = self.user_db.create_user(username, email, password)
            if success:
                return redirect(url_for('login'))
            else:
                return render_template('signup.html', error=message)
       
        return render_template('signup.html')
   
    def logout(self):
        """Handle user logout."""
        session.clear()
        return redirect(url_for('login'))
   
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
                                due_today=due_today,
                                username=session.get('username'))
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