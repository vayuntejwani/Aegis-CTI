import sqlite3
import random
import os

def divide_india_regions():
    db_path = os.path.join(os.path.dirname(__file__), "..", "cti_database.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    india_regions = [
        "North India", 
        "South India", 
        "East India", 
        "West India", 
        "Central India", 
        "Northeast India"
    ]
    
    cursor.execute("SELECT report_id FROM reports")
    reports = cursor.fetchall()
    
    for (report_id,) in reports:
        new_region = random.choice(india_regions)
        cursor.execute("UPDATE reports SET region = ? WHERE report_id = ?", (new_region, report_id))
        
    conn.commit()
    conn.close()
    
    print(f"Successfully divided {len(reports)} incidents across major regions of India.")

if __name__ == "__main__":
    divide_india_regions()
