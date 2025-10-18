# app.py
from flask import Flask, render_template, request
from ai_logic.scheduler import generate_schedule
import os

app = Flask(__name__)

# Homepage
@app.route('/')
def home():
    return render_template('index.html')

# Generate route
@app.route('/generate', methods=['POST'])
def generate():
    # collect up to 6 subjects from the form
    subjects = []
    for i in range(1,7):
        course = request.form.get(f'subject{i}','').strip()
        diff = request.form.get(f'difficulty{i}','').strip()
        if course:
            # if difficulty not provided, default to Medium
            if diff == '':
                diff = 'Medium'
            subjects.append((course, diff))
    if not subjects:
        return render_template('index.html', error="Please select at least one subject.")

    # user available hours per day
    try:
        hours_per_day = int(request.form.get('hours_per_day','4'))
    except:
        hours_per_day = 4

    # start date and days left
    start_date = request.form.get('start_date','')
    try:
        days_left = int(request.form.get('days_left','7'))
    except:
        days_left = 7

    plan = generate_schedule(subjects, hours_per_day, start_date, days_left)
    return render_template('schedule.html', plan=plan, hours_per_day=hours_per_day)

if __name__ == '__main__':
    # ensure templates auto-reload during development
    app.run(debug=True)
