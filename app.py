from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import os
from models.task_model import TaskDatabase
from models.user_model import UserDatabase
from models.ml_model import TaskPrioritizer
from datetime import datetime, timedelta
from functools import wraps
import smtplib
from email.mime.text import MIMEText
import random

class EmailService:
    def __init__(self, sender_email, sender_password):
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_email(self, to_email, subject, body):
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False

class OTPManager:
    def __init__(self):
        self.storage = {}
        self.expiry_minutes = 5

    def generate_otp(self):
        return str(random.randint(100000, 999999))

    def store_otp(self, email, otp):
        self.storage[email] = {
            'otp': otp,
            'expires': datetime.now() + timedelta(minutes=self.expiry_minutes)
        }

    def verify_otp(self, email, otp):
        stored_data = self.storage.get(email)
        if not stored_data or stored_data['expires'] < datetime.now():
            return False, "OTP expired. Please resend."
        
        if otp != stored_data['otp']:
            return False, "Invalid OTP"
        
        del self.storage[email]
        return True, "OTP verified successfully"

class AuthManager:
    def __init__(self, user_db, email_service, otp_manager):
        self.user_db = user_db
        self.email_service = email_service
        self.otp_manager = otp_manager

    def handle_login(self, username, password):
        success, user_id = self.user_db.verify_user(username, password)
        if success:
            session['user_id'] = user_id
            session['username'] = username
            return True, None
        return False, "Invalid username or password"

    def handle_signup(self, username, email, password, confirm_password):
        if password != confirm_password:
            return False, "Passwords do not match"

        if email != session.get('verified_email'):
            return False, "Please verify your email first"

        success, message = self.user_db.create_user(username, email, password)
        if success:
            session.pop('verified_email', None)
            return True, None
        return False, message

    def handle_send_otp(self, email):
        if not email:
            return False, "Email is required"

        otp = self.otp_manager.generate_otp()
        self.otp_manager.store_otp(email, otp)

        subject = 'OTP for ML Task Manager Registration'
        body = f'Your OTP is: {otp}. It will expire in {self.otp_manager.expiry_minutes} minutes.'

        if self.email_service.send_email(email, subject, body):
            return True, "OTP sent successfully"
        return False, "Failed to send OTP"

    def handle_verify_otp(self, email, otp):
        if not email or not otp:
            return False, "Email and OTP are required"

        success, message = self.otp_manager.verify_otp(email, otp)
        if success:
            session['verified_email'] = email
        return success, message

class TaskManagerApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
       
        # Database configuration
        DRIVER_NAME = 'SQL SERVER'
        SERVER_NAME = r'ANURADHA\SQLEXPRESS01'
        DATABASE_NAME = 'TaskManager'
        self.connection_string = f"""
        DRIVER={{SQL Server}};
        SERVER={SERVER_NAME};
        DATABASE={DATABASE_NAME};
        Trusted_Connection=yes;
        """
        
        # Initialize services
        self.task_db = TaskDatabase(self.connection_string)
        self.user_db = UserDatabase(self.connection_string)
        self.task_prioritizer = TaskPrioritizer()
        self.email_service = EmailService('a.saha.study@gmail.com', 'ekcq kefw clqi kyxl')
        self.otp_manager = OTPManager()
        self.auth_manager = AuthManager(self.user_db, self.email_service, self.otp_manager)
       
        # Register routes
        self._register_routes()
   
    def login_required(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
   
    def _register_routes(self):
        # Auth routes
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/signup', 'signup', self.signup, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.logout)
        self.app.add_url_rule('/send_otp', 'send_otp', self.send_otp, methods=['POST'])
        self.app.add_url_rule('/verify_otp', 'verify_otp', self.verify_otp, methods=['POST'])
       
        # Landing page route
        @self.app.route('/')
        @self.app.route('/landing')
        def landing():
            if 'user_id' in session:
                # Get user data
                user = self.user_db.get_user_by_id(session['user_id'])
                if user:
                    return render_template('landing.html',
                                        logged_in=True,
                                        username=user['username'],
                                        email=user['email'])
            return render_template('landing.html', logged_in=False)
       
        # Protected routes
        self.app.add_url_rule('/dashboard', 'index', self.login_required(self.index))
        self.app.add_url_rule('/add', 'add_task', self.login_required(self.add_task), methods=['GET', 'POST'])
        self.app.add_url_rule('/get_types/<category>', 'get_types', self.login_required(self.get_types))
        self.app.add_url_rule('/complete_task/<int:task_id>', 'complete_task', self.login_required(self.complete_task))
        self.app.add_url_rule('/delete_task/<int:task_id>', 'delete_task', self.login_required(self.delete_task))
        self.app.add_url_rule('/filter_tasks', 'filter_tasks', self.login_required(self.filter_tasks))
        self.app.add_url_rule('/edit_task/<int:task_id>', 'edit_task', self.edit_task, methods=['GET', 'POST'])
        self.app.add_url_rule('/search_tasks_ajax', 'search_tasks_ajax', self.search_tasks_ajax)
       
        @self.app.route('/toggle_theme', methods=['POST'])
        def toggle_theme():
            current_theme = session.get('theme', 'light')
            new_theme = 'dark' if current_theme == 'light' else 'light'
            session['theme'] = new_theme
            return jsonify({'theme': new_theme})
   
    def login(self):
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
           
            success, error = self.auth_manager.handle_login(username, password)
            if success:
                return redirect(url_for('index'))
            return render_template('signin.html', error=error)
       
        return render_template('signin.html')
   
    def signup(self):
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
           
            success, error = self.auth_manager.handle_signup(username, email, password, confirm_password)
            if success:
                return redirect(url_for('login'))
            return render_template('signin.html', error=error)
       
        return render_template('signin.html')
   
    def logout(self):
        session.clear()
        return redirect(url_for('landing'))
   
    def send_otp(self):
        email = request.form.get('email')
        success, message = self.auth_manager.handle_send_otp(email)
        return jsonify({"success": success, "message": message}), 200 if success else 400

    def verify_otp(self):
        email = request.form.get('email')
        otp = request.form.get('otp')
        success, message = self.auth_manager.handle_verify_otp(email, otp)
        return jsonify({"success": success, "message": message}), 200 if success else 400
   
    def index(self):
        try:
            # Get search query from request args
            search_query = request.args.get('search', '').strip()
            
            # Get tasks based on search query
            if search_query:
                tasks = self.task_db.search_tasks(session['user_id'], search_query)
            else:
                tasks = self.task_db.get_all_tasks(session['user_id'])
            
            categories = self.task_prioritizer.get_all_categories()
           
            # Calculate stats
            urgent_tasks = sum(1 for task in tasks if task['urgency'] > 6)  # Count tasks with urgency > 6
            due_today = sum(1 for task in tasks if task['deadline_days'] <= 1)
           
            return render_template('index.html',
                                tasks=tasks,
                                categories=categories,
                                urgent_tasks=urgent_tasks,
                                due_today=due_today,
                                username=session.get('username'),
                                search_query=search_query)
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
                success = self.task_db.add_task(task_data, priority, session['user_id'])
               
                if not success:
                    print("Failed to add task to database")
                    return render_template('add_task.html',
                                          categories=self.task_prioritizer.get_all_categories(),
                                          username=session.get('username'),
                                          error="Failed to add task to database")
               
                # Redirect to index page
                return redirect(url_for('index'))
            except Exception as e:
                print(f"Error in add_task route: {e}")
                return render_template('add_task.html',
                                      categories=self.task_prioritizer.get_all_categories(),
                                      username=session.get('username'),
                                      error=str(e))
       
        # GET request - show the form
        categories = self.task_prioritizer.get_all_categories()
        return render_template('add_task.html',
                             categories=categories,
                             username=session.get('username'))
   
    def get_types(self, category):
        types = self.task_prioritizer.get_types_for_category(category)
        return jsonify(types)
   
    def complete_task(self, task_id):
        self.task_db.mark_task_completed(task_id, session['user_id'])
        return redirect(url_for('index'))
   
    def delete_task(self, task_id):
        self.task_db.delete_task(task_id, session['user_id'])
        return redirect(url_for('index'))
   
    def filter_tasks(self):
        try:
            category = request.args.get('category', '')
            sort_by = request.args.get('sort', 'priority')
            filter_type = request.args.get('filter_type', '')
           
            # Get all tasks for the current user
            tasks = self.task_db.get_all_tasks(session['user_id'], order_by=sort_by)
           
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

    def search_tasks_ajax(self):
        try:
            search_query = request.args.get('search', '').strip()
            if search_query:
                tasks = self.task_db.search_tasks(session['user_id'], search_query)
            else:
                tasks = self.task_db.get_all_tasks(session['user_id'])

            # Convert datetime objects to strings for JSON serialization
            for task in tasks:
                if isinstance(task['created_at'], datetime):
                    task['created_at'] = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            return jsonify({
                'tasks': tasks,
                'html': render_template('task_list_partial.html', 
                                     tasks=tasks,
                                     search_query=search_query)
            })
        except Exception as e:
            print(f"Error in search_tasks_ajax route: {e}")
            return jsonify({'error': str(e)}), 500
   
    def edit_task(self, task_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'GET':
            # Get the task details
            task = self.task_db.get_task(task_id, session['user_id'])
            if not task:
                flash('Task not found or you do not have permission to edit it.', 'error')
                return redirect(url_for('index'))
            
            return render_template('edit_task.html',
                                 task=task,
                                 categories=self.task_prioritizer.get_all_categories(),
                                 username=session['username'])
        
        elif request.method == 'POST':
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            category = request.form.get('category')
            type = request.form.get('type')
            deadline = request.form.get('deadline_datetime')
            urgency = int(request.form.get('urgency'))
            effort = float(request.form.get('effort'))
            
            # Calculate days left
            deadline_days = self.calculate_days_left(deadline)
            
            # Update the task
            task_data = {
                'title': title,
                'description': description,
                'category': category,
                'type': type,
                'deadline_datetime': deadline,
                'deadline_days': deadline_days,
                'urgency': urgency,
                'effort': effort
            }
            
            # Predict new priority
            priority = self.task_prioritizer.predict_priority(task_data)
            
            # Update the task
            self.task_db.update_task(task_id, session['user_id'], task_data, priority)
            
            flash('Task updated successfully!', 'success')
            return redirect(url_for('index'))
   
    def run(self, debug=True):
        self.app.run(debug=debug)

# Create the application instance
task_manager = TaskManagerApp()
app = task_manager.app

if __name__ == '__main__':
    task_manager.run(debug=True)