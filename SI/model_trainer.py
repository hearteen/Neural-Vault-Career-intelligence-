import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np

# --- SECTION 1: PERFORMANCE PREDICTION MODEL ---
# Updated Logic: Pass Mark is 30.
# Features Map: [Attendance%, Marks(GPA*10), Practical_Skills, Behavior_Score]
performance_data = {
    # High Performers, Average (Pass > 30), and At-Risk (Fail < 30)
    'attendance': [90, 85, 95, 88, 92, 75, 65, 40, 30, 20, 55],
    'marks':      [85, 90, 88, 82, 95, 70, 45, 25, 28, 15, 35], # 30 is the threshold
    'skills':     [80, 95, 85, 75, 90, 60, 50, 20, 15, 10, 40],
    'behavior':   [9, 10, 9, 8, 10, 7, 6, 3, 2, 1, 5],
    # Result: 1 (Good/Pass), 0 (At Risk/Fail)
    'result':     [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1] 
}

df_perf = pd.DataFrame(performance_data)
X_perf = df_perf.drop('result', axis=1)
y_perf = df_perf['result']

# Random Forest Classifier with 100 Trees
perf_model = RandomForestClassifier(n_estimators=100, random_state=42)
perf_model.fit(X_perf, y_perf)

# Save Performance Model
joblib.dump(perf_model, 'student_model.pkl')
print("✅ Success: Performance Model (Pass Mark 30) saved as student_model.pkl")


# --- SECTION 2: CAREER RECOMMENDATION MODEL ---
# Features: [GPA, Coding_Score, Comm_Score, Attendance]
# Roles: 0: Data Scientist, 1: Project Manager, 2: Web Developer
career_data = {
    'gpa':        [9.0, 7.5, 8.5, 6.0, 9.5, 5.5, 8.0, 7.0, 9.2, 6.5, 8.8],
    'coding':     [95, 60, 85, 40, 90, 30, 80, 50, 98, 45, 92],
    'comm':       [70, 90, 80, 85, 60, 95, 75, 88, 65, 92, 72],
    'attendance': [95, 80, 90, 75, 98, 70, 92, 85, 96, 78, 94],
    'role':       [0, 1, 0, 1, 2, 1, 2, 1, 0, 2, 0] 
}

df_career = pd.DataFrame(career_data)
X_career = df_career.drop('role', axis=1)
y_career = df_career['role']

career_model = RandomForestClassifier(n_estimators=100, random_state=42)
career_model.fit(X_career, y_career)

# Save Career Model
joblib.dump(career_model, 'career_model.pkl')
print("✅ Success: Career Model saved as career_model.pkl")