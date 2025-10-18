# train_model.py
import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Load dataset
data = pd.read_csv('dataset/study_data.csv')

# Encode categorical features
le_course = LabelEncoder()
le_diff = LabelEncoder()

data['Course_enc'] = le_course.fit_transform(data['Course'])
data['Diff_enc'] = le_diff.fit_transform(data['Difficulty_Level'])

# Features and target
X = data[['Course_enc', 'Diff_enc']]
y = data['Hours_of_Study']

# Train model (simple regressor)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model and encoders
pickle.dump(model, open('model_hours.pkl', 'wb'))
pickle.dump(le_course, open('le_course.pkl', 'wb'))
pickle.dump(le_diff, open('le_diff.pkl', 'wb'))

# Also prepare a mapping Course+Difficulty -> representative Recommended_Schedule
# We'll store the first matching recommended schedule as a quick lookup.
schedule_map = {}
for _, row in data.iterrows():
    key = f"{row['Course']}||{row['Difficulty_Level']}"
    if key not in schedule_map:
        schedule_map[key] = row['Recommended_Schedule']

pickle.dump(schedule_map, open('schedule_map.pkl', 'wb'))

print("✅ Training complete. Saved: model_hours.pkl, le_course.pkl, le_diff.pkl, schedule_map.pkl")
