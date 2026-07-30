import sqlite3
import random
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_manager import insert_report
from pipeline import score_priority, priority_tier, analyze_report

categories = [
    ("Zero-Day Exploit", "Critical"),
    ("Ransomware", "High"),
    ("Nation-State Attack", "Critical"),
    ("Network Intrusion", "High"),
    ("Data Breach", "Medium"),
    ("DDoS", "Medium"),
    ("Phishing", "Low"),
    ("Insider Threat", "High")
]

actors = ["APT29", "Lazarus Group", "LockBit", "Fancy Bear", "Anonymous", "Sandworm", "Unknown State Actor", "FIN7", "DarkSide"]
systems = ["Domain Controller", "Exchange Server", "SCADA Network", "AWS S3 Bucket", "VPN Gateway", "Employee Workstation", "SolarWinds Orion", "Kaseya VSA"]
regions = ["APAC", "EMEA", "North America", "South America", "Global"]

def generate_historical_incidents(n=400):
    start_date = datetime(2017, 1, 1)
    end_date = datetime(2021, 12, 31)
    total_days = (end_date - start_date).days
    
    count = 0
    for i in range(n):
        cat_sev = random.choice(categories)
        category = cat_sev[0]
        severity = cat_sev[1]
        
        actor = random.choice(actors)
        system = random.choice(systems)
        region = random.choice(regions)
        
        title = f"{actor} targeted {system} via {category}"
        description = f"Historical Intel: Detected a sophisticated {category.lower()} campaign operated by {actor}. The primary target was the {system} located in the {region} sector."
        
        random_days = random.randint(0, total_days)
        dt = start_date + timedelta(days=random_days)
        date_str = dt.isoformat()
        
        report_id = f"CTI-HIST-{random.randint(100000, 999999)}"
        source = "Historical DB"
        
        asset_criticality = random.choice(["Low", "Medium", "High", "Critical"])
        
        pred = analyze_report(title, description)
        
        # Calculate days since dt for score
        days_since = (datetime.now() - dt).days
        
        score = score_priority(
            predicted_severity=severity,
            predicted_category=category,
            severity_confidence=0.9,
            category_risk=0.85,
            asset_criticality=asset_criticality,
            days_since=days_since,
            w1=0.40, w2=0.25, w3=0.20, w4=0.15
        )
        tier = priority_tier(score)
        
        try:
            insert_report(report_id, date_str, source, title, description, category, severity, system, asset_criticality, region, score, tier, pred)
            count += 1
        except sqlite3.IntegrityError:
            pass
            
    print(f"Successfully generated and ingested {count} historical incidents from 2017 to 2021.")

if __name__ == "__main__":
    print("Generating 400 historical incidents (2017-2021)...")
    generate_historical_incidents(400)
