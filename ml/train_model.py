# Imports
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os


# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))


# Load dataset
file_path = os.path.join(current_dir, "task-management-dataset.csv")
df = pd.read_csv(file_path)


# Trim spaces from column names
df.columns = df.columns.str.strip()


# Check for missing values
print("Missing values:")
print(df.isnull().sum())


# Drop rows with missing values
df = df.dropna()


# Label encode 'Task Category' and 'Task Type'
label_enc_category = LabelEncoder()
df["Task Category"] = label_enc_category.fit_transform(df["Task Category"])


label_enc_type = LabelEncoder()
df["Task Type"] = label_enc_type.fit_transform(df["Task Type"])


# Save the encoders
joblib.dump(label_enc_category, os.path.join(current_dir, "label_enc_category.pkl"))
joblib.dump(label_enc_type, os.path.join(current_dir, "label_enc_type.pkl"))


# MinMax Scaler
scaler = MinMaxScaler()


# Normalize 'Urgency (1-10)', 'Estimated Effort (hours)', 'Deadline (Days Left)'
df[["Urgency (1-10)", "Estimated Effort (hours)", "Deadline (Days Left)"]] = scaler.fit_transform(
    df[["Urgency (1-10)", "Estimated Effort (hours)", "Deadline (Days Left)"]]
)


# Save the scaler
joblib.dump(scaler, os.path.join(current_dir, "scaler.pkl"))
print("Scaler saved successfully!")


# Define input features (X) and target (y)
X = df.drop(columns=["Priority (Target: 1-10)", "Task Title", "Task Description"])  # Drop text columns
y = df["Priority (Target: 1-10)"]


# Train-test split (80-20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


print("Training data shape:", X_train.shape)
print("Testing data shape:", X_test.shape)


# Define parameter grid
param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 20, None],
    "min_samples_split": [2, 5, 10]
}


# Perform Grid Search
rf = RandomForestRegressor(random_state=42)
grid_search = GridSearchCV(rf, param_grid, cv=5, scoring="r2", n_jobs=-1)
grid_search.fit(X_train, y_train)


# Get best model
best_rf = grid_search.best_estimator_
print("Best Parameters:", grid_search.best_params_)


# Train best model
best_rf.fit(X_train, y_train)


# Predict on test data
y_pred_rf = best_rf.predict(X_test)


# Evaluate model
mae_rf = mean_absolute_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)


print(f"Random Forest MAE: {mae_rf}")
print(f"Random Forest R² Score: {r2_rf}")


# Save model for later use
joblib.dump(best_rf, os.path.join(current_dir, "random_forest_task_priority.pkl"))
print("Random Forest Model Saved!")


def predict_priority(task_details):


    # Load the trained model and encoders
    best_rf = joblib.load(os.path.join(current_dir, "random_forest_task_priority.pkl"))
    label_enc_category = joblib.load(os.path.join(current_dir, "label_enc_category.pkl"))
    label_enc_type = joblib.load(os.path.join(current_dir, "label_enc_type.pkl"))
    scaler = joblib.load(os.path.join(current_dir, "scaler.pkl"))
   
    # Check if the category exists in the encoder
    if task_details["Task Category"] in label_enc_category.classes_:
        task_details["Task Category"] = label_enc_category.transform([task_details["Task Category"]])[0]
    else:
        task_details["Task Category"] = -1


    # Check if the task type exists in the encoder
    if task_details["Task Type"] in label_enc_type.classes_:
        task_details["Task Type"] = label_enc_type.transform([task_details["Task Type"]])[0]
    else:
        task_details["Task Type"] = -1
   
    # Scale numerical values using MinMaxScaler with correct feature names
    task_input_scaled = pd.DataFrame(
        [[task_details["Urgency (1-10)"], task_details["Estimated Effort (hours)"], task_details["Deadline (Days Left)"]]],
        columns=["Urgency (1-10)", "Estimated Effort (hours)", "Deadline (Days Left)"]
    )


    scaled_values = scaler.transform(task_input_scaled)
   
    task_details["Urgency (1-10)"], task_details["Estimated Effort (hours)"], task_details["Deadline (Days Left)"] = scaled_values[0]


    # Convert to array
    task_input = np.array([list(task_details.values())])


    # Convert task_input into a DataFrame with proper feature names
    task_input_df = pd.DataFrame(task_input, columns=X_train.columns)
   
    # Predict priority
    predicted_priority = best_rf.predict(task_input_df)
    return predicted_priority[0]


if __name__ == "__main__":
    # Example usage
    example_task = {
        "Task Category": "Work or Professional",
        "Task Type": "Project Deadlines",
        "Deadline (Days Left)": 15,
        "Urgency (1-10)": 5,
        "Estimated Effort (hours)": 3
    }
   
    predicted_priority = predict_priority(example_task)
    print(f"Predicted Task Priority: {predicted_priority}")