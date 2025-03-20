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
        """
        Predict the priority of a task based on its features
        
        Args:
            task_data: Dictionary with keys:
                - category: Task category
                - type: Task type
                - deadline_days: Days left for deadline
                - urgency: Urgency on scale 1-10
                - effort: Estimated effort in hours
        
        Returns:
            float: Priority score (1-10)
        """
        if not self.is_model_loaded:
            # Fallback formula if model isn't loaded
            urgency = task_data['urgency']
            deadline = max(1, task_data['deadline_days'])  # Avoid division by zero
            effort = task_data['effort']
            
            # Simple prioritization formula
            priority = (urgency * 0.5) + (10/deadline * 0.3) + (min(effort, 10)/10 * 0.2)
            return min(10, max(1, priority))
        
        try:
            # Encode categorical features
            category_encoded = self.category_encoder.transform([task_data['category']])[0]
            task_type_encoded = self.type_encoder.transform([task_data['type']])[0]
            
            # Scale numerical features
            numerical_features = np.array([
                task_data['urgency'],
                task_data['effort'],
                task_data['deadline_days']
            ]).reshape(1, -1)
            
            scaled_numerical = self.scaler.transform(numerical_features)[0]
            
            # Create feature vector
            X = np.array([
                category_encoded,
                task_type_encoded,
                scaled_numerical[0],  # Urgency
                scaled_numerical[1],  # Effort
                scaled_numerical[2]   # Deadline
            ]).reshape(1, -1)
            
            # Predict priority
            priority = self.model.predict(X)[0]
            
            # Ensure priority is within range
            return min(10, max(1, priority))
            
        except Exception as e:
            print(f"Error predicting priority: {e}")
            # Fallback method
            return (task_data['urgency'] * 0.6) + ((10 / max(1, task_data['deadline_days'])) * 0.4)