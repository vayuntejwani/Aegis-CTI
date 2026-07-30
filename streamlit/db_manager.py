import os
import sqlite3
import json
from datetime import datetime

# Resolve DB path in the root folder (one level above this script)
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "cti_database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        date TEXT,
        source TEXT,
        title TEXT,
        description TEXT,
        category TEXT,
        severity TEXT,
        affected_system TEXT,
        asset_criticality TEXT,
        region TEXT,
        priority_score REAL,
        priority_tier TEXT,
        prediction_json TEXT
    )
    """)

    # Create the sensors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensors (
        sensor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        sensor_type TEXT NOT NULL,
        platform TEXT,
        region TEXT,
        status TEXT DEFAULT 'Online',
        last_seen TEXT,
        alert_count INTEGER DEFAULT 0,
        latitude REAL,
        longitude REAL,
        notes TEXT,
        registered_at TEXT
    )
    """)

    # Create the sensor_alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_alerts (
        alert_id TEXT PRIMARY KEY,
        sensor_id TEXT,
        timestamp TEXT,
        alert_type TEXT,
        message TEXT,
        severity TEXT,
        raw_signal TEXT,
        acknowledged INTEGER DEFAULT 0
    )
    """)

    # Create the users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'Analyst',
        command_unit TEXT DEFAULT 'Northern Command',
        created_at TEXT
    )
    """)
    conn.commit()

    # Pre-populate default commander user if empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        import hashlib
        def_pass = hashlib.sha256("CTI_SALT_2026_Password123".encode('utf-8')).hexdigest()
        now_str = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO users (user_id, username, email, password_hash, full_name, role, command_unit, created_at)
        VALUES ('USR-0001', 'commander', 'commander@defence.gov.in', ?, 'Cmdr. Vikram Singh', 'Commander', 'Defence Cyber Agency (DCyA)', ?)
        """, (def_pass, now_str))
        conn.commit()
    
    # Check if empty, and pre-populate if needed
    cursor.execute("SELECT COUNT(*) as count FROM reports")
    row = cursor.fetchone()
    if row["count"] == 0:
        print("Pre-populating SQLite database with sample data...")
        from sample_data import load_sample_reports
        from pipeline import analyze_report, score_priority, priority_tier
        
        corpus = load_sample_reports()
        for r in corpus:
            pred = analyze_report(r["title"], r["description"])
            # Calculate priority score using default weights
            score = score_priority(
                predicted_severity=r["severity"],
                predicted_category=r["category"],
                severity_confidence=pred["severity_confidence"],
                category_risk=pred["category_risk"],
                asset_criticality=r["asset_criticality"],
                days_since=(datetime.now() - r["date"]).days,
                w1=0.40, w2=0.25, w3=0.20, w4=0.15
            )
            tier = priority_tier(score)
            
            cursor.execute("""
            INSERT INTO reports (
                report_id, date, source, title, description, category, 
                severity, affected_system, asset_criticality, region, 
                priority_score, priority_tier, prediction_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["report_id"],
                r["date"].isoformat() if isinstance(r["date"], datetime) else r["date"],
                r["source"],
                r["title"],
                r["description"],
                r["category"],
                r["severity"],
                r["affected_system"],
                r["asset_criticality"],
                r["region"],
                score,
                tier,
                json.dumps(pred)
            ))
        conn.commit()
    conn.close()

def get_all_reports():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY priority_score DESC")
    rows = cursor.fetchall()
    
    reports = []
    for r in rows:
        report = dict(r)
        report["prediction"] = json.loads(report["prediction_json"])
        # convert date back to datetime object/string where needed
        reports.append(report)
    conn.close()
    return reports

def insert_report(report_id, date_str, source, title, description, category, 
                  severity, affected_system, asset_criticality, region, 
                  priority_score, priority_tier, prediction_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO reports (
        report_id, date, source, title, description, category, 
        severity, affected_system, asset_criticality, region, 
        priority_score, priority_tier, prediction_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id, date_str, source, title, description, category, 
        severity, affected_system, asset_criticality, region, 
        priority_score, priority_tier, json.dumps(prediction_dict)
    ))
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()

# ── Sensor Registry CRUD ─────────────────────────────────────────────────────

def get_all_sensors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensors ORDER BY registered_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_sensor(sensor_id, name, sensor_type, platform, region, latitude, longitude, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO sensors
        (sensor_id, name, sensor_type, platform, region, status, last_seen,
         alert_count, latitude, longitude, notes, registered_at)
    VALUES (?, ?, ?, ?, ?, 'Online', ?, 0, ?, ?, ?, ?)
    """, (sensor_id, name, sensor_type, platform, region, now, latitude, longitude, notes, now))
    conn.commit()
    conn.close()


def update_sensor_status(sensor_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sensors SET status=?, last_seen=? WHERE sensor_id=?",
        (status, datetime.now().isoformat(), sensor_id)
    )
    conn.commit()
    conn.close()


def delete_sensor(sensor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensors WHERE sensor_id=?", (sensor_id,))
    cursor.execute("DELETE FROM sensor_alerts WHERE sensor_id=?", (sensor_id,))
    conn.commit()
    conn.close()


# ── Sensor Alerts CRUD ───────────────────────────────────────────────────────

def get_sensor_alerts(sensor_id=None, limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    if sensor_id:
        cursor.execute(
            "SELECT * FROM sensor_alerts WHERE sensor_id=? ORDER BY timestamp DESC LIMIT ?",
            (sensor_id, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM sensor_alerts ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_sensor_alert(alert_id, sensor_id, alert_type, message, severity, raw_signal=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO sensor_alerts
        (alert_id, sensor_id, timestamp, alert_type, message, severity, raw_signal, acknowledged)
    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (alert_id, sensor_id, now, alert_type, message, severity, raw_signal))
    # Bump alert counter on sensor
    cursor.execute(
        "UPDATE sensors SET alert_count = alert_count + 1, last_seen=? WHERE sensor_id=?",
        (now, sensor_id)
    )
    conn.commit()
    conn.close()


def acknowledge_alert(alert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sensor_alerts SET acknowledged=1 WHERE alert_id=?", (alert_id,))
    conn.commit()
    conn.close()


# ── User Authentication CRUD ──────────────────────────────────────────────────

import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(f"CTI_SALT_2026_{password}".encode('utf-8')).hexdigest()


def get_user_by_username_or_email(identifier: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? OR email=?", (identifier, identifier)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username, email, password, full_name, role, command_unit):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if username or email exists
    cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username, email))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Username or email already registered")

    # Generate user_id
    cursor.execute("SELECT COUNT(*) as count FROM users")
    count = cursor.fetchone()["count"]
    user_id = f"USR-{count+1:04d}"
    
    pw_hash = hash_password(password)
    now_str = datetime.now().isoformat()
    
    cursor.execute("""
    INSERT INTO users (user_id, username, email, password_hash, full_name, role, command_unit, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, email, pw_hash, full_name, role, command_unit, now_str))
    
    conn.commit()
    conn.close()
    
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "full_name": full_name,
        "role": role,
        "command_unit": command_unit
    }


def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, email, full_name, role, command_unit, created_at FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


