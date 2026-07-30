import sqlite3
import pandas as pd
import random
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_manager import insert_report
from pipeline import score_priority, priority_tier, analyze_report

def ingest_kev():
    csv_path = r"C:\Users\Lenovo\Downloads\kev.csv"
    if not os.path.exists(csv_path):
        print("KEV csv not found.")
        return
        
    df = pd.read_csv(csv_path)
    
    # We want to fill the gap, so let's just take everything or a random sample of 500
    if len(df) > 500:
        df = df.sample(n=500, random_state=42)
        
    count = 0
    for idx, row in df.iterrows():
        try:
            cve_id = str(row['cveID'])
            title = f"{cve_id}: {row['vulnerabilityName']}"
            desc = str(row['shortDescription'])
            date_added = str(row['dateAdded'])
            
            # Format date to iso format
            dt = datetime.strptime(date_added, "%Y-%m-%d")
            
            category = "Zero-Day Exploit" if "zero" in desc.lower() else "Vulnerability"
            severity = "Critical"
            
            asset_crit = random.choice(["Medium", "High", "Critical"])
            system = str(row['product'])
            region = "Global"
            
            pred = analyze_report(title, desc)
            days_since = (datetime.now() - dt).days
            
            score = score_priority(
                predicted_severity=severity,
                predicted_category=category,
                severity_confidence=0.9,
                category_risk=0.8,
                asset_criticality=asset_crit,
                days_since=days_since,
                w1=0.40, w2=0.25, w3=0.20, w4=0.15
            )
            tier = priority_tier(score)
            
            insert_report(cve_id, dt.isoformat(), "CISA KEV", title, desc, category, severity, system, asset_crit, region, score, tier, pred)
            count += 1
        except Exception as e:
            continue
            
    print(f"Successfully ingested {count} KEV incidents to fill the historical gap!")

if __name__ == "__main__":
    ingest_kev()
