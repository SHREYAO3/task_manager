import os
import sys
import subprocess

class ApplicationSetup:
    def __init__(self):
        """Initialize the application setup."""
        self.required_packages = ['flask', 'pandas', 'numpy', 'scikit-learn', 'joblib', 'pyodbc']
        self.directories = ['templates', 'static/css', 'static/js', 'data', 'ml', 'models']
        self.model_path = os.path.join('ml', 'random_forest_task_priority.pkl')
   
    def check_requirements(self):
        for package in self.required_packages:
            try:
                __import__(package)
                print(f"✓ {package} is installed")
            except ImportError:
                print(f"✗ {package} is not installed. Installing...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} has been installed")
        return True
   
    def setup_directories(self):
        for directory in self.directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")
        return True
   
    def prepare_ml_models(self):
        if not os.path.exists(self.model_path):
            print("Preparing ML models...")
            try:
                from transfer_ml_model import main
                main()
                print("ML models created successfully")
            except Exception as e:
                print(f"Error creating ML models: {e}")
                print("Running the app without ML models (will use fallback prioritization)")
        return True
   
    def check_sql_connection(self):
        try:
            import pyodbc
            print("Testing SQL Server connection...")
            # Define your SQL Server connection string
            DRIVER_NAME = 'SQL SERVER'
            SERVER_NAME = r'ANURADHA\SQLEXPRESS01'
            DATABASE_NAME = 'TaskManager'
            connection_string = f"""
            DRIVER={DRIVER_NAME};
            SERVER={SERVER_NAME};
            DATABASE={DATABASE_NAME};
            Trusted_Connection=yes;
            """
           
            # Try to connect
            connection = pyodbc.connect(connection_string)
            cursor = connection.cursor()
            cursor.execute("SELECT @@VERSION")
            sql_version = cursor.fetchone()[0]
            print(f"✓ SQL Server connection successful. Version: {sql_version.split()[0]}")
            connection.close()
            return True
        except Exception as e:
            print(f"✗ SQL Server connection failed: {e}")
            print("Please check your SQL Server configuration and try again.")
            return False

class ApplicationRunner:
    def __init__(self):
        self.app = None
   
    def run(self):
        try:
            from app import app
            self.app = app
            print("\n=== ML Task Manager ===")
            print("Starting the application...")
            print("Open your browser and go to: http://127.0.0.1:5000/")
            self.app.run(debug=True)
        except Exception as e:
            print(f"Error running the application: {e}")

def main():
    print("Setting up ML Task Manager...")
   
    # Setup application
    setup = ApplicationSetup()
    setup.check_requirements()
    setup.setup_directories()
    setup.prepare_ml_models()
   
    # Test SQL Server connection
    if not setup.check_sql_connection():
        print("Application setup cannot continue due to database connection issues.")
        return
   
    # Run application
    runner = ApplicationRunner()
    runner.run()

if __name__ == "__main__":
    main()