from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from models.task_model import TaskDatabase
from models.ml_model import TaskPrioritizer


class TaskManagerApp:
    """Class responsible for the Flask application and routes."""
    
    def __init__(self):
        """Initialize the Flask application and its components."""
        self.app = Flask(__name__)
        
        # Initialize database and ML model
        self.db_path = os.path.join('data', 'task_data.db')
        self.task_db = TaskDatabase(self.db_path)
        self.task_prioritizer = TaskPrioritizer()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all application routes."""
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/add', 'add_task', self.add_task, methods=['GET', 'POST'])
        self.app.add_url_rule('/get_types/<category>', 'get_types', self.get_types)
        self.app.add_url_rule('/complete_task/<int:task_id>', 'complete_task', self.complete_task)
        self.app.add_url_rule('/delete_task/<int:task_id>', 'delete_task', self.delete_task)
    
    def index(self):
        """Home page with task listing."""
        tasks = self.task_db.get_all_tasks()
        return render_template('index.html', tasks=tasks)
    
    def add_task(self):
        """Add a new task."""
        if request.method == 'POST':
            # Extract form data
            task_data = {
                'title': request.form['title'],
                'description': request.form['description'],
                'category': request.form['category'],
                'type': request.form['type'],
                'deadline_days': int(request.form['deadline_days']),
                'urgency': int(request.form['urgency']),
                'effort': float(request.form['effort'])
            }
            
            # Predict priority
            priority = self.task_prioritizer.predict_priority(task_data)
            
            # Save task to database
            self.task_db.add_task(task_data, priority)
            
            return redirect(url_for('index'))
        
        # GET request - show the form
        categories = self.task_prioritizer.get_all_categories()
        return render_template('add_task.html', categories=categories)
    
    def get_types(self, category):
        """API to get task types for a given category."""
        types = self.task_prioritizer.get_types_for_category(category)
        return jsonify(types)
    
    def complete_task(self, task_id):
        """Mark a task as completed."""
        self.task_db.mark_task_completed(task_id)
        return redirect(url_for('index'))
    
    def delete_task(self, task_id):
        """Delete a task."""
        self.task_db.delete_task(task_id)
        return redirect(url_for('index'))
    
    def run(self, debug=True):
        """Run the Flask application."""
        # Ensure directories exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('ml', exist_ok=True)
        
        self.app.run(debug=debug)


# Create the application instance
task_manager = TaskManagerApp()
app = task_manager.app


if __name__ == '__main__':
    task_manager.run(debug=True)