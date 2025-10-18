# ai_logic/scheduler.py
import pickle
import pandas as pd
from datetime import datetime, timedelta
import os

# load artifacts
MODEL_PATH = os.path.join(os.getcwd(), 'model_hours.pkl')
LE_COURSE = os.path.join(os.getcwd(), 'le_course.pkl')
LE_DIFF = os.path.join(os.getcwd(), 'le_diff.pkl')
SCHEDULE_MAP = os.path.join(os.getcwd(), 'schedule_map.pkl')
DATASET_CSV = os.path.join(os.getcwd(), 'dataset', 'study_data.csv')

model = pickle.load(open(MODEL_PATH, 'rb'))
le_course = pickle.load(open(LE_COURSE, 'rb'))
le_diff = pickle.load(open(LE_DIFF, 'rb'))
schedule_map = pickle.load(open(SCHEDULE_MAP, 'rb'))

# helper to predict hours for a (course, difficulty) pair
def predict_hours(course, difficulty):
    try:
        course_enc = le_course.transform([course])[0]
        diff_enc = le_diff.transform([difficulty])[0]
    except Exception:
        # if unknown, fallback to mean hours for difficulty
        df = pd.read_csv(DATASET_CSV)
        if difficulty in df['Difficulty_Level'].values:
            return int(round(df[df['Difficulty_Level']==difficulty]['Hours_of_Study'].mean()))
        return 1
    pred = model.predict([[course_enc, diff_enc]])[0]
    return max(1, round(pred))  # at least 1 hour

# create schedule: subjects_with_difficulty = list of (course, difficulty)
def generate_schedule(subjects_with_difficulty, hours_per_day, start_date_str, days_left):
    """
    subjects_with_difficulty: list of tuples [('Python','Hard'), ('DBMS','Medium'), ...]
    hours_per_day: integer (available hours per day)
    start_date_str: 'YYYY-MM-DD' or '' for today
    days_left: total number of days to plan
    returns: list of dicts: [{'date':..., 'day':..., 'slots':[{'time':'Morning','subject':'Python','hours':1,'note':...}, ...]}, ...]
    """
    # parse start date
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    else:
        start_date = datetime.today()

    # Predict recommended hours for each subject
    predicted = []
    for course, diff in subjects_with_difficulty:
        hrs = predict_hours(course, diff)
        # get textual guidance if available
        note = schedule_map.get(f"{course}||{diff}", "")
        predicted.append({'course': course, 'difficulty': diff, 'rec_hours': hrs, 'note': note})

    # Sum of recommended hours
    total_rec = sum(p['rec_hours'] for p in predicted)
    if total_rec == 0:
        total_rec = len(predicted)

    # We'll scale predicted hours so that daily total equals hours_per_day distributed across subjects and days_left
    # per-day assignment per subject: scaled = (rec_hours / total_rec) * hours_per_day
    # But we also want integer hours; so we create fractional assignment and round smartly across slots.

    # prepare plan days
    plan = []
    # daily time slots (you can change slots or add more)
    slots = ['Morning', 'Afternoon', 'Evening']
    for day_idx in range(days_left):
        date = start_date + timedelta(days=day_idx)
        slots_list = []
        # compute per subject fractional hrs for this day
        frac_hours = []
        for p in predicted:
            frac = (p['rec_hours'] / total_rec) * hours_per_day
            frac_hours.append(frac)
        # now allocate integer hours per subject for the day using largest remainder
        int_hours = [int(h) for h in frac_hours]
        remainder = [h - int(h) for h in frac_hours]
        remaining_hours = hours_per_day - sum(int_hours)
        # distribute remaining hours based on largest remainder
        while remaining_hours > 0:
            idx = max(range(len(remainder)), key=lambda i: remainder[i])
            int_hours[idx] += 1
            remainder[idx] = 0  # avoid picking again
            remaining_hours -= 1
        # Now for each subject, split its int_hours into slots (Morning/Afternoon/Evening)
        for subj_idx, p in enumerate(predicted):
            h = int_hours[subj_idx]
            if h == 0:
                continue
            # break h into slot pieces, prefer 1-2 hours per slot
            assigned = []
            for s in range(min(h, len(slots))):
                assigned.append(1)
            remaining = h - sum(assigned)
            si = 0
            while remaining > 0:
                assigned[si % len(assigned)] += 1
                si += 1
                remaining -= 1
            # map assigned to actual slots (rotate slots to balance across subjects)
            for i, hr_chunk in enumerate(assigned):
                slot_name = slots[(subj_idx + i) % len(slots)]
                slots_list.append({
                    'time': slot_name,
                    'subject': p['course'],
                    'hours': hr_chunk,
                    'difficulty': p['difficulty'],
                    'note': p['note']
                })
        # sort slots to Morning->Afternoon->Evening order
        order = {'Morning':0,'Afternoon':1,'Evening':2}
        slots_list.sort(key=lambda x: order.get(x['time'], 0))
        plan.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%A'),
            'slots': slots_list
        })

    return plan
