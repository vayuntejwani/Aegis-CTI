import sqlite3
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pipeline import analyze_report

def recompute_keywords():
    db_path = os.path.join(os.path.dirname(__file__), "..", "cti_database.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT report_id, title, description, prediction_json FROM reports")
    reports = cursor.fetchall()
    
    for row in reports:
        report_id, title, desc, pred_json = row
        
        # Analyze the report again to generate new keywords using the updated stopword list
        new_pred = analyze_report(title, desc)
        
        # Keep original category and severity from database if needed, but analyze_report returns the stub ones anyway.
        # It's safest just to update the entire prediction json
        pred_str = json.dumps(new_pred)
        
        cursor.execute("UPDATE reports SET prediction_json = ? WHERE report_id = ?", (pred_str, report_id))
        
    conn.commit()
    conn.close()
    print(f"Recomputed keywords for {len(reports)} incidents.")

if __name__ == "__main__":
    recompute_keywords()
