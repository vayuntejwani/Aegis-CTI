import sqlite3
import os

def convert_to_india():
    db_path = os.path.join(os.path.dirname(__file__), "..", "cti_database.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update region column
    cursor.execute("UPDATE reports SET region = 'India'")
    
    # Update descriptions to reflect India
    regions_to_replace = ["North America", "South America", "APAC", "EMEA", "Global"]
    for r in regions_to_replace:
        cursor.execute(f"UPDATE reports SET description = replace(description, '{r}', 'India')")
        cursor.execute(f"UPDATE reports SET title = replace(title, '{r}', 'India')")
        
    conn.commit()
    conn.close()
    
    print("Database successfully updated. All data is now exclusively for India.")

if __name__ == "__main__":
    convert_to_india()
