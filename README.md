# TaskNexus - Advanced Task Management System

TaskNexus is a sophisticated task management application built using Flask, following the MVC (Model-View-Controller) architecture pattern. It provides a comprehensive solution for task management with features like task prioritization, email notifications, and statistical analysis.

## Project Structure

```
task_manager/
├── app.py             # Main application file containing core logic
├── run.py             # Application entry point
├── models/            # Database models and ML components
│   ├── task_model.py  # Task database operations
│   ├── user_model.py  # User database operations
│   └── ml_model.py    # Machine learning for task prioritization
├── static/            # Static assets (CSS, JS, images)
├── templates/         # HTML templates
└── ml/                # Machine learning related files
```

## Features

### 1. MVC Architecture
- **Models**: Database models for tasks and users
- **Views**: HTML templates for user interface
- **Controllers**: Route handlers in app.py

### 2. Database Design
- SQL Server database with tables for:
  - Users
  - Tasks
  - Reminders
  - Task Categories
  - Task Types

### 3. File Handling
- Secure file uploads for task attachments
- Static file serving for assets
- Template rendering system

### 4. UI Design
- Responsive web interface
- Dark/Light theme support
- Interactive task management dashboard
- Real-time task updates
- Progress tracking visualization

### 5. Validation
- User input validation
- Email verification system
- OTP-based authentication
- Password strength requirements
- Form validation on both client and server side

### 6. Task Management Features
- Task creation and editing
- Priority-based task organization
- Deadline management
- Task categorization
- Status tracking
- Search and filter capabilities
- Task reminders and notifications

### 7. Result Analysis
- Task completion statistics
- Performance metrics
- Time-based analytics
- Category-wise task distribution
- Progress tracking
- Custom report generation

### 8. Security Features
- User authentication
- Session management
- Password hashing
- Email verification
- OTP-based security
- Protected routes

### 9. Additional Features
- Email notifications
- Task reminders
- Auto-prioritization using ML
- Task sharing capabilities
- Export functionality
- Theme customization

## Technical Stack

- **Backend**: Python/Flask
- **Database**: SQL Server
- **Frontend**: HTML, CSS, JavaScript
- **ML Components**: Python-based task prioritization
- **Email Service**: SMTP (Gmail)

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure database connection in app.py
5. Set up email service credentials
6. Run the application:
   ```bash
   python run.py
   ```

## Configuration

The application requires the following configurations:
- Database connection string
- Email service credentials
- Secret key for session management
- SMTP server settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
