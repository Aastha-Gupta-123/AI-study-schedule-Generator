# app.py
from flask import Flask, render_template, request
from ai_logic.scheduler import generate_schedule
import os
import re

app = Flask(__name__)

# Homepage
@app.route('/')
def home():
    return render_template('index.html')

# Generator page
@app.route('/generator')
def generator():
    return render_template('generator.html')

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
        return render_template('generator.html', error="Please select at least one subject.")

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

# Sentiment Analysis page
@app.route('/sentiment')
def sentiment():
    return render_template('sentiment.html')

# Sentiment Prediction route
@app.route('/predict', methods=['POST'])
def predict_sentiment():
    review = request.form.get('review', '').strip()
    
    if not review:
        return render_template('sentiment.html', error="Please enter some text to analyze.")
    
    # Simple sentiment analysis using keyword matching
    # Positive words
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
                     'love', 'enjoy', 'happy', 'pleased', 'satisfied', 'easy', 'clear', 
                     'understand', 'helpful', 'useful', 'perfect', 'best', 'awesome', 
                     'brilliant', 'outstanding', 'superb', 'delighted', 'glad', 'pleased',
                     'success', 'improve', 'better', 'progress', 'learn', 'mastered']
    
    # Negative words
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'difficult',
                     'hard', 'confusing', 'frustrated', 'annoyed', 'disappointed', 'worst',
                     'poor', 'fail', 'struggle', 'problem', 'issue', 'error', 'mistake',
                     'stuck', 'confused', 'overwhelmed', 'stress', 'worried', 'anxious']
    
    # Convert to lowercase for matching
    review_lower = review.lower()
    
    # Count positive and negative words
    positive_count = sum(1 for word in positive_words if word in review_lower)
    negative_count = sum(1 for word in negative_words if word in review_lower)
    
    # Determine sentiment
    if positive_count > negative_count:
        prediction = 'Positive'
    elif negative_count > positive_count:
        prediction = 'Negative'
    else:
        prediction = 'Neutral'
    
    return render_template('sentiment.html', prediction=prediction)

# About page
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    # ensure templates auto-reload during development
    app.run(debug=True)
