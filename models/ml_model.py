import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

class TaskPrioritizer:
    def __init__(self, model_dir='ml'):
        self.model_path = os.path.join(model_dir, 'random_forest_task_priority.pkl')
        self.category_encoder_path = os.path.join(model_dir, 'label_enc_category.pkl')
        self.type_encoder_path = os.path.join(model_dir, 'label_enc_type.pkl')
        self.scaler_path = os.path.join(model_dir, 'scaler.pkl')
       
        # Load model and preprocessors
        try:
            self.model = joblib.load(self.model_path)
            self.category_encoder = joblib.load(self.category_encoder_path)
            self.type_encoder = joblib.load(self.type_encoder_path)
            self.scaler = joblib.load(self.scaler_path)
            self.is_model_loaded = True
        except (FileNotFoundError, joblib.exc.JoblibException) as e:
            print(f"Error loading ML model components: {e}")
            self.is_model_loaded = False
       
        # Define category-type mapping
        self.category_type_mapping = {
            "Work or Professional": [
                "Meetings", "Project deadlines", "Reports and documentation",
                "Client follow-ups", "Team collaboration"
            ],
            "Personal": [
                "Household chores", "Fitness and health", "Personal finance",
                "Leisure and hobbies", "Family and social events"
            ],
            "Educational": [
                "Study sessions", "Assignments and homework", "Exam preparation",
                "Research projects", "Online courses"
            ],
            "Health & Wellness": [
                "Medical appointments", "Medication reminders", "Workout plans",
                "Mental health check-ins"
            ],
            "Financial": [
                "Bill payments", "Budgeting and expense tracking", "Investment planning",
                "Tax filing"
            ],
            "Social or Community": [
                "Social gatherings", "Volunteering events", "Networking events",
                "Club or group activities"
            ],
            "Errands": [
                "Grocery shopping", "Car maintenance", "Post office visits",
                "Banking tasks"
            ],
            "Travel & Leisure": [
                "Vacation planning", "Packing lists", "Travel bookings",
                "Sightseeing plans"
            ],
            "Creative": [
                "Writing", "Design projects", "Art and music", "Content creation"
            ],
            "Miscellaneous": [
                "Random ideas", "To-do lists", "Future plans", "General reminders"
            ]
        }
   
    def get_types_for_category(self, category):
        """Return task types for a given category"""
        return self.category_type_mapping.get(category, [])
   
    def get_all_categories(self):
        """Return all task categories"""
        return list(self.category_type_mapping.keys())
   
    def predict_priority(self, task_data):
        if not self.is_model_loaded:
            raise Exception("ML model components not loaded. Please ensure model files exist in the ml directory.")
       
        try:
            # Prepare input data with correct feature names
            task_input = {
                "Task Category": task_data['category'],
                "Task Type": task_data['type'],
                "Deadline (Days Left)": task_data['deadline_days'],
                "Urgency (1-10)": task_data['urgency'],
                "Estimated Effort (hours)": task_data['effort']
            }
           
            # Encode categorical features
            if task_input["Task Category"] in self.category_encoder.classes_:
                task_input["Task Category"] = self.category_encoder.transform([task_input["Task Category"]])[0]
            else:
                raise ValueError(f"Unknown task category: {task_input['Task Category']}")


            if task_input["Task Type"] in self.type_encoder.classes_:
                task_input["Task Type"] = self.type_encoder.transform([task_input["Task Type"]])[0]
            else:
                raise ValueError(f"Unknown task type: {task_input['Task Type']}")
           
            # Scale numerical features
            numerical_features = pd.DataFrame({
                "Urgency (1-10)": [task_input["Urgency (1-10)"]],
                "Estimated Effort (hours)": [task_input["Estimated Effort (hours)"]],
                "Deadline (Days Left)": [task_input["Deadline (Days Left)"]]
            })
           
            scaled_numerical = self.scaler.transform(numerical_features)[0]
            task_input["Urgency (1-10)"], task_input["Estimated Effort (hours)"], task_input["Deadline (Days Left)"] = scaled_numerical
           
            # Create feature vector with proper feature names
            X = pd.DataFrame([task_input])
           
            # Predict priority and round to 1 decimal place
            # priority = round(self.model.predict(X)[0], 1)
            priority = self.model.predict(X)[0]
           
            # Ensure priority is within range
            # return min(10, max(1, priority))
            return priority
           
        except Exception as e:
            print(f"Error predicting priority: {e}")
            raise Exception(f"Failed to predict priority: {str(e)}")