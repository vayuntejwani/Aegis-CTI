import pandas as pd
import json
import sqlite3
import random
from datetime import datetime
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
import sys

# Ensure we can import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_manager import insert_report, insert_sensor_alert
from pipeline import score_priority, priority_tier

# 1. Load GTD Dataset
print("Loading GTD...")
df = pd.read_csv(r'C:\Users\Lenovo\Downloads\globalterrorismdb_0718dist.csv\globalterrorismdb_0718dist.csv', encoding='ISO-8859-1', low_memory=False)

# Filter for rows with summary
df = df.dropna(subset=['summary'])

# Sample to speed things up
df = df.sample(n=10000, random_state=42)

def get_severity(row):
    kill = pd.to_numeric(row['nkill'], errors='coerce')
    wound = pd.to_numeric(row['nwound'], errors='coerce')
    casualties = (0 if pd.isna(kill) else kill) + (0 if pd.isna(wound) else wound)
    if casualties > 10:
        return 'Critical'
    if casualties > 0:
        return 'High'
    return 'Low'

df['severity'] = df.apply(get_severity, axis=1)

# Train simple model for severity
print("Training Severity Model...")
X = df['summary']
y = df['severity']

model = make_pipeline(TfidfVectorizer(max_features=5000, stop_words='english'), LogisticRegression(max_iter=1000))
model.fit(X, y)

# Save model
os.makedirs(r'C:\Users\Lenovo\Desktop\cti-website\streamlit\models', exist_ok=True)
joblib.dump(model, r'C:\Users\Lenovo\Desktop\cti-website\streamlit\models\severity_model.joblib')

print("Trained severity model and saved to models/severity_model.joblib")

# 2. Ingest 50 random incidents into cti_database.db
print("Ingesting GTD reports...")
sample_to_ingest = df.sample(n=50, random_state=42)
for idx, row in sample_to_ingest.iterrows():
    report_id = f"CTI-GTD-{idx}"
    try:
        dt = datetime(int(row['iyear']), int(row['imonth']), int(row['iday']))
    except:
        dt = datetime.now()
    
    date_str = dt.isoformat()
    source = "GTD Integration"
    title = f"{row['attacktype1_txt']} in {row['city']}"
    description = row['summary']
    category = "Terrorism"
    severity = row['severity']
    affected_system = str(row['targtype1_txt'])
    asset_criticality = "High" if severity in ["Critical", "High"] else "Medium"
    region = str(row['country_txt'])
    
    score = score_priority(
        predicted_severity=severity,
        predicted_category=category,
        severity_confidence=0.85,
        category_risk=0.8,
        asset_criticality=asset_criticality,
        days_since=0,
        w1=0.40, w2=0.25, w3=0.20, w4=0.15
    )
    tier = priority_tier(score)
    
    pred_dict = {
        "severity": severity,
        "category": category,
        "severity_confidence": 0.85,
        "category_risk": 0.8,
        "keywords": [],
        "iocs": [],
        "summary": description[:100]
    }
    
    try:
        insert_report(report_id, date_str, source, title, description, category, severity, affected_system, asset_criticality, region, score, tier, pred_dict)
    except sqlite3.IntegrityError:
        pass

# 3. Ingest labels_with_split.csv into sensor_alerts
print("Ingesting sensor alerts...")
labels_df = pd.read_csv(r'C:\Users\Lenovo\Downloads\labels_with_split.csv')
sample_labels = labels_df.sample(n=20, random_state=42)

for idx, row in sample_labels.iterrows():
    alert_id = f"ALT-IMG-{idx}"
    sensor_id = "SEN-0001" # Assuming first sensor
    alert_type = "Aircraft Detection (AI Vision)"
    message = f"Detected {row['class']} at bounding box ({row['xmin']},{row['ymin']},{row['xmax']},{row['ymax']})"
    severity = "High" if row['class'] in ['Mi28', 'F16', 'H6'] else "Medium"
    raw_signal = f"Image Source ID: {row['filename']}"
    
    try:
        insert_sensor_alert(alert_id, sensor_id, alert_type, message, severity, raw_signal)
    except sqlite3.IntegrityError:
        pass

print("Done!")
