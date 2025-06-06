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
import threading
import time


class EmailService:
    def __init__(self, sender_email, sender_password):
        self.sender_email = sender_email
        self.sender_password = sender_password
        print(f"EmailService initialized with sender: {sender_email}")


    def send_email(self, to_email, subject, body):
        try:
            print(f"Preparing to send email to {to_email}")
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email

            print("Connecting to SMTP server...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            print("Logging in to SMTP server...")
            server.login(self.sender_email, self.sender_password)
            
            print("Sending email...")
            server.send_message(msg)
            server.quit()
            print(f"Email sent successfully to {to_email}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP Authentication Error: {e}")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP Error: {e}")
            return False
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


        subject = 'OTP for TaskNexus Registration'
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
       
        # Start the reminder scheduler in a background thread
        self.reminder_thread = threading.Thread(target=self._reminder_scheduler, daemon=True)
        self.reminder_thread.start()
       
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
        self.app.add_url_rule('/send_reminder/<int:task_id>', 'send_reminder', self.login_required(self.send_reminder), methods=['POST'])
        self.app.add_url_rule('/set_reminder/<int:task_id>', 'set_reminder', self.login_required(self.set_reminder), methods=['POST'])
        self.app.add_url_rule('/delete_reminder/<int:task_id>', 'delete_reminder', self.login_required(self.delete_reminder), methods=['POST'])
        self.app.add_url_rule('/statistics', 'statistics', self.login_required(self.statistics))
       
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
        self.app.add_url_rule('/complete_task/<int:task_id>', 'complete_task', self.login_required(self.complete_task), methods=['POST'])
        self.app.add_url_rule('/delete_task/<int:task_id>', 'delete_task', self.login_required(self.delete_task), methods=['POST'])
        self.app.add_url_rule('/filter_tasks', 'filter_tasks', self.login_required(self.filter_tasks))
        self.app.add_url_rule('/edit_task/<int:task_id>', 'edit_task', self.edit_task, methods=['GET', 'POST'])
        self.app.add_url_rule('/search_tasks_ajax', 'search_tasks_ajax', self.search_tasks_ajax)
        self.app.add_url_rule('/view_task/<int:task_id>', 'view_task', self.view_task)
        self.app.add_url_rule('/update_task_status/<int:task_id>', 'update_task_status', self.login_required(self.update_task_status), methods=['POST'])
        self.app.add_url_rule('/toggle_auto_reminder/<int:task_id>', 'toggle_auto_reminder', self.login_required(self.toggle_auto_reminder), methods=['POST'])
       
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
            urgent_tasks = sum(1 for task in tasks if task['urgency'] <= 3)  # Count tasks with urgency <= 3 (highest urgency)
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
                # Extract and validate title
                title = request.form['title']
                if len(title) > 50:
                    flash('Task title must not exceed 50 characters', 'error')
                    return redirect(url_for('add_task'))


                # Extract form data
                deadline_datetime = request.form['deadline_datetime']
                deadline_days = self.calculate_days_left(deadline_datetime)
               
                task_data = {
                    'title': title,
                    'description': request.form['description'],
                    'category': request.form['category'],
                    'type': request.form['type'],
                    'deadline_datetime': deadline_datetime,
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
        try:
            success = self.task_db.mark_task_completed(task_id, session['user_id'])
            if success:
                return jsonify({'success': True, 'message': 'Task completed successfully'})
            return jsonify({'success': False, 'message': 'Failed to complete task'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
   
    def delete_task(self, task_id):
        try:
            success = self.task_db.delete_task(task_id, session['user_id'])
            if success:
                return jsonify({'success': True, 'message': 'Task deleted successfully'})
            return jsonify({'success': False, 'message': 'Failed to delete task'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
   
    def filter_tasks(self):
        try:
            category = request.args.get('category', '')
            sort_by = request.args.get('sort', 'priority')
            filter_type = request.args.get('filter_type', '')
            status_filter = request.args.get('status', '')
            task_id = request.args.get('task_id')
           
            # Get all tasks for the current user
            tasks = self.task_db.get_all_tasks(session['user_id'], order_by=sort_by)
           
            # If task_id is provided, return only that task
            if task_id:
                tasks = [task for task in tasks if str(task['id']) == str(task_id)]
                return jsonify(tasks)


            # Apply filters
            if filter_type == 'urgent':
                tasks = [task for task in tasks if task['urgency'] <= 3]  # Filter tasks with urgency <= 3 (highest urgency)
            elif filter_type == 'due-today':
                tasks = [task for task in tasks if task['deadline_days'] <= 1]
            elif category:  # Only apply category filter if no special filter is active
                tasks = [task for task in tasks if task['category'] == category]
           
            # Apply status filter if specified and not 'all'
            if status_filter and status_filter != 'all':
                tasks = [task for task in tasks if task.get('status', 'pending').lower() == status_filter.lower()]
           
            # Convert datetime objects to strings for JSON serialization
            for task in tasks:
                if isinstance(task['created_at'], datetime):
                    task['created_at'] = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                   
                # Ensure all required fields are present and properly formatted
                if 'priority' in task and isinstance(task['priority'], (int, float)):
                    task['priority'] = float(task['priority'])
               
                # Make sure deadline_days is an integer
                if 'deadline_days' in task:
                    task['deadline_days'] = int(task['deadline_days'])
                   
                # Add any missing fields with default values
                task.setdefault('urgency', 0)
                task.setdefault('effort', 0)
                task.setdefault('status', 'pending')
           
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


            # Convert datetime objects to strings and format data
            for task in tasks:
                if isinstance(task['created_at'], datetime):
                    task['created_at'] = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
               
                # Ensure all required fields are present and properly formatted
                if 'priority' in task and isinstance(task['priority'], (int, float)):
                    task['priority'] = float(task['priority'])
               
                # Make sure deadline_days is an integer
                if 'deadline_days' in task:
                    task['deadline_days'] = int(task['deadline_days'])
                   
                # Add any missing fields with default values
                task.setdefault('urgency', 0)
                task.setdefault('effort', 0)
                task.setdefault('status', 'pending')


            return jsonify({
                'tasks': tasks,
                'success': True
            })
        except Exception as e:
            print(f"Error in search_tasks_ajax route: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
   
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


    def view_task(self, task_id):
        if not session.get('user_id'):
            return redirect(url_for('login'))
       
        task = self.task_db.get_task(task_id, session['user_id'])
        if not task:
            flash('Task not found', 'error')
            return redirect(url_for('index'))
       
        return render_template('view_task.html',
                             task=task,
                             username=session.get('username'))


    def update_task_status(self, task_id):
        try:
            data = request.json
            if not data or 'status' not in data:
                return jsonify({'success': False, 'message': 'Status is required'}), 400
           
            new_status = data['status']
           
            # Add safeguard to prevent invalid status values
            valid_statuses = ['pending', 'in-progress', 'review', 'completed']
            if new_status not in valid_statuses:
                return jsonify({'success': False, 'message': 'Invalid status value'}), 400
           
            success = self.task_db.update_task_status(task_id, session['user_id'], new_status)
            if success:
                return jsonify({'success': True, 'message': 'Task status updated successfully'})
           
            return jsonify({'success': False, 'message': 'Failed to update task status'})
        except Exception as e:
            print(f"Error updating task status: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500


    def send_reminder(self, task_id):
        try:
            # Get the task details
            task = self.task_db.get_task(task_id, session['user_id'])
            if not task:
                return jsonify({'success': False, 'message': 'Task not found'}), 404


            # Get the user's email
            user = self.user_db.get_user_by_id(session['user_id'])
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404


            # Create the email subject and body
            subject = f'Reminder: Task - {task["title"]}'
            body = f"""
Hello {user['username']},


This is a reminder for your task:


Title: {task['title']}
Description: {task['description']}
Category: {task['category']}
Type: {task['type']}
Deadline: {task['deadline_datetime']}
Days Left: {task['deadline_days']}
Priority: {task['priority']}
Status: {task['status']}


Please make sure to complete this task before the deadline.


Best regards,
TaskNexus
"""


            # Send the email
            if self.email_service.send_email(user['email'], subject, body):
                return jsonify({'success': True, 'message': 'Reminder sent successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send reminder email'}), 500


        except Exception as e:
            print(f"Error sending reminder: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500




    def _reminder_scheduler(self):
        """Background thread that checks for and sends pending reminders"""
        print("Reminder scheduler started")
        while True:
            try:
                # Get all pending reminders
                pending_reminders = self.task_db.get_pending_reminders()
                print(f"Found {len(pending_reminders)} pending reminders")
               
                for task in pending_reminders:
                    try:
                        print(f"Processing reminder for task: {task['title']} (ID: {task['id']})")
                        # Create and send the reminder email
                        subject = f'Reminder: Task - {task["title"]}'
                        body = f"""
Hello {task['username']},

This is a reminder for your task:

Title: {task['title']}
Description: {task['description']}
Category: {task['category']}
Type: {task['type']}
Deadline: {task['deadline_datetime']}
Days Left: {task['deadline_days']}
Priority: {task['priority']}
Status: {task['status']}

Please make sure to complete this task before the deadline.

Best regards,
TaskNexus
"""
                        print(f"Sending email to {task['email']}")
                        if self.email_service.send_email(task['email'], subject, body):
                            print(f"Successfully sent reminder email for task {task['id']}")
                            # Clear the reminder after successful sending
                            self.task_db.clear_reminder(task['id'])
                            print(f"Cleared reminder for task {task['id']}")
                        else:
                            print(f"Failed to send reminder email for task {task['id']}")
                    except Exception as e:
                        print(f"Error processing reminder for task {task['id']}: {e}")
                        continue
               
            except Exception as e:
                print(f"Error in reminder scheduler: {e}")
           
            # Sleep for 1 minute before checking again
            time.sleep(60)




    def set_reminder(self, task_id):
        try:
            data = request.json
            if not data or 'reminder_datetime' not in data:
                return jsonify({'success': False, 'message': 'Reminder datetime is required'}), 400


            reminder_datetime = data['reminder_datetime']
           
            # Validate the datetime format
            try:
                datetime.strptime(reminder_datetime, '%Y-%m-%d %H:%M')
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid datetime format'}), 400


            # Set the reminder
            success = self.task_db.set_reminder(task_id, session['user_id'], reminder_datetime)
            if success:
                return jsonify({'success': True, 'message': 'Reminder set successfully'})
           
            return jsonify({'success': False, 'message': 'Failed to set reminder'})


        except Exception as e:
            print(f"Error setting reminder: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500




    def delete_reminder(self, task_id):
        try:
            # Clear the reminder
            success = self.task_db.clear_reminder(task_id)
            if success:
                return jsonify({'success': True, 'message': 'Reminder deleted successfully'})
           
            return jsonify({'success': False, 'message': 'Failed to delete reminder'})


        except Exception as e:
            print(f"Error deleting reminder: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500




    def statistics(self):
        try:
            # Get all tasks for the current user
            tasks = self.task_db.get_all_tasks(session['user_id'])
           
            # Calculate various statistics
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.get('status') == 'completed')
            pending_tasks = sum(1 for task in tasks if task.get('status') == 'pending')
            in_progress_tasks = sum(1 for task in tasks if task.get('status') == 'in-progress')
            review_tasks = sum(1 for task in tasks if task.get('status') == 'review')
           
            # Calculate task aging statistics
            current_time = datetime.now()
            fresh_tasks = 0
            stale_tasks = 0
            aging_tasks = 0
            
            for task in tasks:
                if task.get('status') == 'completed':
                    continue
                    
                created_at = task.get('created_at')
                if isinstance(created_at, str):
                    created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
                
                age_days = (current_time - created_at).days
                
                if age_days < 3:
                    fresh_tasks += 1
                elif 3 <= age_days <= 7:
                    stale_tasks += 1
                else:
                    aging_tasks += 1
           
            # Calculate urgency distribution
            high_urgency = sum(1 for task in tasks if task['urgency'] > 7)
            medium_urgency = sum(1 for task in tasks if 4 <= task['urgency'] <= 7)
            low_urgency = sum(1 for task in tasks if task['urgency'] < 4)
           
            # Calculate deadline statistics
            overdue_tasks = sum(1 for task in tasks if task['deadline_days'] == 0 and task.get('status') != 'completed')
            due_today = sum(1 for task in tasks if task['deadline_days'] == 1)
            due_this_week = sum(1 for task in tasks if 1 < task['deadline_days'] <= 7)
           
            # Calculate average effort
            if total_tasks > 0:
                avg_effort = sum(task['effort'] for task in tasks) / total_tasks
            else:
                avg_effort = 0
           
            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Calculate category statistics
            category_stats = {}
            category_completion_times = {}
            task_types_by_category = {}  # New dictionary to store task types by category

            for task in tasks:
                # Category statistics
                category = task.get('category', 'Uncategorized')
                task_type = task.get('type', 'Other')  # Default to 'Other' if type is not specified
                
                if category not in category_stats:
                    # Initialize with basic counters
                    category_stats[category] = {
                        'total': 0,
                        'completed': 0
                    }
                    task_types_by_category[category] = {}  # Initialize task types for this category
                
                category_stats[category]['total'] += 1
                if task.get('status') == 'completed':
                    category_stats[category]['completed'] += 1
                
                # Track task types for this category
                if task_type not in task_types_by_category[category]:
                    task_types_by_category[category][task_type] = 0
                task_types_by_category[category][task_type] += 1

                # Calculate completion times for completed tasks
                if task.get('status') == 'completed' and task.get('created_at') and task.get('completed_at'):
                    try:
                        created_at = datetime.strptime(task['created_at'], '%Y-%m-%d %H:%M:%S')
                        completed_at = datetime.strptime(task['completed_at'], '%Y-%m-%d %H:%M:%S')
                        completion_time = (completed_at - created_at).total_seconds() / 3600  # in hours

                        # Update category completion times
                        if category not in category_completion_times:
                            category_completion_times[category] = []
                        category_completion_times[category].append(completion_time)
                    except:
                        pass

            # Calculate average completion times
            avg_category_times = {
                category: sum(times) / len(times) if times else 0
                for category, times in category_completion_times.items()
            }

            # Find most/least active categories
            sorted_categories = sorted(
                category_stats.items(),
                key=lambda x: x[1]['total'],
                reverse=True
            )
            most_active_category = sorted_categories[0][0] if sorted_categories else None
            least_active_category = sorted_categories[-1][0] if sorted_categories else None

            # Calculate task trends over time
            task_trends = {
                'dates': [],
                'created': [],
                'completed': []
            }
            
            # Get the date range (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Initialize all dates in the range with chronological order
            date_counts = {
                'created': {},
                'completed': {}
            }
            
            # Create a list of dates for the last 30 days
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                date_counts['created'][date_str] = 0
                date_counts['completed'][date_str] = 0
                task_trends['dates'].append(current_date.strftime('%b %d'))  # Format as 'Mar 15'
                current_date += timedelta(days=1)
            
            # Count tasks created and completed for each date
            for task in tasks:
                try:
                    # Count created tasks
                    if task.get('created_at'):
                        if isinstance(task['created_at'], str):
                            created_at = datetime.strptime(task['created_at'], '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            created_at = task['created_at']
                        
                        if start_date <= created_at <= end_date:
                            created_date = created_at.strftime('%Y-%m-%d')
                            if created_date in date_counts['created']:
                                date_counts['created'][created_date] += 1
                    
                    # Count completed tasks
                    if task.get('status') == 'completed' and task.get('completed_at'):
                        if isinstance(task['completed_at'], str):
                            completed_at = datetime.strptime(task['completed_at'], '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            completed_at = task['completed_at']
                        
                        if start_date <= completed_at <= end_date:
                            completed_date = completed_at.strftime('%Y-%m-%d')
                            if completed_date in date_counts['completed']:
                                date_counts['completed'][completed_date] += 1
                except Exception as e:
                    print(f"Error processing task for trends: {e}")
                    continue

            # Convert counts to ordered lists
            task_trends['created'] = list(date_counts['created'].values())
            task_trends['completed'] = list(date_counts['completed'].values())

            return render_template('statistics.html',
                                username=session.get('username'),
                                total_tasks=total_tasks,
                                completed_tasks=completed_tasks,
                                pending_tasks=pending_tasks,
                                in_progress_tasks=in_progress_tasks,
                                review_tasks=review_tasks,
                                high_urgency=high_urgency,
                                medium_urgency=medium_urgency,
                                low_urgency=low_urgency,
                                overdue_tasks=overdue_tasks,
                                due_today=due_today,
                                due_this_week=due_this_week,
                                avg_effort=round(avg_effort, 1),
                                completion_rate=round(completion_rate, 1),
                                category_stats=category_stats,
                                avg_category_times=avg_category_times,
                                most_active_category=most_active_category,
                                least_active_category=least_active_category,
                                task_trends=task_trends,
                                task_types_by_category=task_types_by_category,
                                fresh_tasks=fresh_tasks,
                                stale_tasks=stale_tasks,
                                aging_tasks=aging_tasks)
        except Exception as e:
            print(f"Error in statistics route: {e}")
            return render_template('statistics.html', 
                                error=str(e),
                                username=session.get('username'),
                                total_tasks=0,
                                completed_tasks=0,
                                pending_tasks=0,
                                in_progress_tasks=0,
                                review_tasks=0,
                                high_urgency=0,
                                medium_urgency=0,
                                low_urgency=0,
                                overdue_tasks=0,
                                due_today=0,
                                due_this_week=0,
                                avg_effort=0,
                                completion_rate=0,
                                category_stats={},
                                avg_category_times={},
                                most_active_category=None,
                                least_active_category=None,
                                task_trends={'dates': [], 'created': [], 'completed': []},
                                task_types_by_category={},
                                fresh_tasks=0,
                                stale_tasks=0,
                                aging_tasks=0)




    def toggle_auto_reminder(self, task_id):
        try:
            data = request.json
            if not data or 'auto_reminder' not in data:
                return jsonify({'success': False, 'message': 'Auto reminder state is required'}), 400

            auto_reminder = data['auto_reminder']
            task = self.task_db.get_task(task_id, session['user_id'])
            
            if not task:
                return jsonify({'success': False, 'message': 'Task not found'}), 404

            if auto_reminder:
                # Calculate reminder time (24 hours before deadline)
                deadline = datetime.strptime(task['deadline_datetime'], '%Y-%m-%d %H:%M')
                reminder_time = deadline - timedelta(hours=24)
                
                # Only set reminder if it's in the future
                if reminder_time > datetime.now():
                    success = self.task_db.set_reminder(task_id, session['user_id'], reminder_time.strftime('%Y-%m-%d %H:%M'), auto_reminder=True)
                else:
                    return jsonify({'success': False, 'message': 'Cannot set reminder for past deadline'}), 400
            else:
                # Clear the reminder and auto_reminder flag
                success = self.task_db.clear_reminder(task_id, session['user_id'])

            if success:
                return jsonify({'success': True, 'message': 'Auto-reminder setting updated successfully'})
            return jsonify({'success': False, 'message': 'Failed to update auto-reminder setting'})

        except Exception as e:
            print(f"Error toggling auto-reminder: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500




    def run(self, debug=True):
        self.app.run(debug=debug)


# Create the application instance
task_manager = TaskManagerApp()
app = task_manager.app


if __name__ == '__main__':
    task_manager.run(debug=True)