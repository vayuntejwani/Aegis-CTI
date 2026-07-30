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

actors = ["APT29", "Lazarus Group", "LockBit", "Fancy Bear", "Anonymous", "Sandworm", "Unknown State Actor"]
systems = ["Domain Controller", "Exchange Server", "SCADA Network", "AWS S3 Bucket", "VPN Gateway", "Employee Workstation"]
regions = ["APAC", "EMEA", "North America", "South America", "Global"]

def generate_incidents(n=100):
    for i in range(n):
        cat_sev = random.choice(categories)
        category = cat_sev[0]
        severity = cat_sev[1]
        
        actor = random.choice(actors)
        system = random.choice(systems)
        region = random.choice(regions)
        
        title = f"{actor} targeted {system} via {category}"
        description = f"We detected a sophisticated {category.lower()} campaign operated by {actor}. The primary target was the {system} located in the {region} sector. Immediate mitigation is advised."
        
        # Random date in the last 180 days
        days_ago = random.randint(0, 180)
        dt = datetime.now() - timedelta(days=days_ago)
        date_str = dt.isoformat()
        
        report_id = f"CTI-SYN-{random.randint(1000, 999999)}"
        source = "Synthetic AI Intel"
        
        asset_criticality = random.choice(["Low", "Medium", "High", "Critical"])
        
        pred = analyze_report(title, description)
        
        score = score_priority(
            predicted_severity=severity,
            predicted_category=category,
            severity_confidence=0.9,
            category_risk=0.85,
            asset_criticality=asset_criticality,
            days_since=days_ago,
            w1=0.40, w2=0.25, w3=0.20, w4=0.15
        )
        tier = priority_tier(score)
        
        try:
            insert_report(report_id, date_str, source, title, description, category, severity, system, asset_criticality, region, score, tier, pred)
        except sqlite3.IntegrityError:
            pass

if __name__ == "__main__":
    print("Generating 150 synthetic CTI incidents...")
    generate_incidents(150)
    print("Synthetic data generated and ingested successfully.")
