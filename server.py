import sys
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add streamlit directory to path to import db_manager and pipelines
sys.path.append(os.path.join(os.path.dirname(__file__), 'streamlit'))

import db_manager
from pipeline import analyze_report, score_priority, priority_tier

app = Flask(__name__)
# Enable CORS so the local index.html can call the APIs
CORS(app)

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

def parse_iso_naive(d_str):
    if not d_str:
        return None
    try:
        d_str = str(d_str).replace('Z', '+00:00')
        dt = datetime.fromisoformat(d_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        try:
            return datetime.strptime(str(d_str)[:10], "%Y-%m-%d")
        except Exception:
            return None

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        reports = db_manager.get_all_reports()
        
        category_filter = request.args.get('categories')
        severity_filter = request.args.get('severities')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        start_dt = parse_iso_naive(start_date)
        end_dt = parse_iso_naive(end_date)
        
        filtered_reports = []
        for r in reports:
            r_date_dt = parse_iso_naive(r.get('date'))
            
            if category_filter and r.get('category') not in category_filter.split(','):
                continue
            if severity_filter and r.get('severity') not in severity_filter.split(','):
                continue
            if start_dt and r_date_dt and r_date_dt < start_dt:
                continue
            if end_dt and r_date_dt and r_date_dt > end_dt:
                continue
            filtered_reports.append(r)
            
        return jsonify(filtered_reports)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        reports = db_manager.get_all_reports()
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        start_dt = parse_iso_naive(start_date)
        end_dt = parse_iso_naive(end_date)
        
        if start_dt or end_dt:
            filtered = []
            for r in reports:
                r_date_dt = parse_iso_naive(r.get('date'))
                if start_dt and r_date_dt and r_date_dt < start_dt:
                    continue
                if end_dt and r_date_dt and r_date_dt > end_dt:
                    continue
                filtered.append(r)
            reports = filtered

        total_reports = len(reports)
        categories = {}
        severities = {}
        priority_tiers = {}
        regions = {}
        daily_volume = {}
        keyword_counts = {}
        
        for r in reports:
            # Category
            cat = r['category']
            categories[cat] = categories.get(cat, 0) + 1
            
            # Severity
            sev = r['severity']
            severities[sev] = severities.get(sev, 0) + 1
            
            # Priority Tier
            tier = r['priority_tier']
            priority_tiers[tier] = priority_tiers.get(tier, 0) + 1
            
            # Region
            reg = r['region']
            regions[reg] = regions.get(reg, 0) + 1
            
            # Daily volume (extract YYYY-MM-DD)
            try:
                day_str = r['date'][:10]
                daily_volume[day_str] = daily_volume.get(day_str, 0) + 1
            except Exception:
                pass
            
            # Keywords (from prediction)
            pred = r.get('prediction', {})
            keywords = pred.get('keywords', [])
            for kw in keywords[:8]:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
                
        # Sort keywords
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_keywords = [{"keyword": k, "mentions": v} for k, v in sorted_keywords]
        
        # Sort daily volume chronologically
        sorted_volume = sorted(daily_volume.items())
        volume_trend = [{"day": k, "count": v} for k, v in sorted_volume]
        
        return jsonify({
            "total_reports": total_reports,
            "categories": categories,
            "severities": severities,
            "priority_tiers": priority_tiers,
            "regions": regions,
            "daily_volume": volume_trend,
            "top_keywords": top_keywords
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports', methods=['POST'])
def create_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        asset_criticality = data.get('asset_criticality', 'Medium')
        source = data.get('source', 'Web Form')
        affected_system = data.get('affected_system', 'Unknown')
        region = data.get('region', 'Global')
        
        if not title or not description:
            return jsonify({"error": "Title and description are required"}), 400
            
        # Run analysis pipeline
        pred = analyze_report(title, description)
        
        # Default weights for scoring
        w1, w2, w3, w4 = 0.40, 0.25, 0.20, 0.15
        
        # Calculate priority score
        score = score_priority(
            predicted_severity=pred['severity'],
            predicted_category=pred['category'],
            severity_confidence=pred['severity_confidence'],
            category_risk=pred['category_risk'],
            asset_criticality=asset_criticality,
            days_since=0,  # newly submitted report is brand new
            w1=w1, w2=w2, w3=w3, w4=w4
        )
        tier = priority_tier(score)
        
        # Generate new CTI report ID
        reports = db_manager.get_all_reports()
        next_num = 1
        if reports:
            # Find the max ID number
            nums = []
            for r in reports:
                try:
                    nums.append(int(r['report_id'].split('-')[1]))
                except Exception:
                    pass
            if nums:
                next_num = max(nums) + 1
        report_id = f"CTI-{next_num:05d}"
        
        # Save to DB
        date_str = datetime.now().isoformat()
        db_manager.insert_report(
            report_id=report_id,
            date_str=date_str,
            source=source,
            title=title,
            description=description,
            category=pred['category'],
            severity=pred['severity'],
            affected_system=affected_system,
            asset_criticality=asset_criticality,
            region=region,
            priority_score=score,
            priority_tier=tier,
            prediction_dict=pred
        )
        
        return jsonify({
            "report_id": report_id,
            "date": date_str,
            "source": source,
            "title": title,
            "description": description,
            "category": pred['category'],
            "severity": pred['severity'],
            "affected_system": affected_system,
            "asset_criticality": asset_criticality,
            "region": region,
            "priority_score": score,
            "priority_tier": tier,
            "prediction": pred
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Sensor Registry Routes ────────────────────────────────────────────────────

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    try:
        sensors = db_manager.get_all_sensors()
        return jsonify(sensors)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensors', methods=['POST'])
def create_sensor():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get('name', '').strip()
        sensor_type = data.get('sensor_type', '').strip()
        platform = data.get('platform', '').strip()
        region = data.get('region', 'Unknown').strip()
        latitude = float(data.get('latitude', 0.0))
        longitude = float(data.get('longitude', 0.0))
        notes = data.get('notes', '').strip()

        if not name or not sensor_type:
            return jsonify({"error": "Name and sensor_type are required"}), 400

        # Generate a unique sensor ID
        existing = db_manager.get_all_sensors()
        nums = []
        for s in existing:
            try:
                nums.append(int(s['sensor_id'].split('-')[1]))
            except Exception:
                pass
        next_num = (max(nums) + 1) if nums else 1
        sensor_id = f"SEN-{next_num:04d}"

        db_manager.insert_sensor(
            sensor_id=sensor_id, name=name, sensor_type=sensor_type,
            platform=platform, region=region,
            latitude=latitude, longitude=longitude, notes=notes
        )

        sensor = {"sensor_id": sensor_id, "name": name, "sensor_type": sensor_type,
                  "platform": platform, "region": region, "status": "Online",
                  "latitude": latitude, "longitude": longitude, "notes": notes,
                  "alert_count": 0}
        return jsonify(sensor), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensors/<sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    try:
        db_manager.delete_sensor(sensor_id)
        return jsonify({"deleted": sensor_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensors/<sensor_id>/status', methods=['PATCH'])
def update_sensor_status(sensor_id):
    try:
        data = request.get_json()
        status = data.get('status', 'Online')
        db_manager.update_sensor_status(sensor_id, status)
        return jsonify({"sensor_id": sensor_id, "status": status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Sensor Alert Routes ───────────────────────────────────────────────────────

@app.route('/api/sensor_alerts', methods=['GET'])
def get_sensor_alerts():
    try:
        sensor_id = request.args.get('sensor_id')
        alerts = db_manager.get_sensor_alerts(sensor_id=sensor_id, limit=100)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensor_alerts', methods=['POST'])
def create_sensor_alert():
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id', '').strip()
        alert_type = data.get('alert_type', 'Unknown').strip()
        message = data.get('message', '').strip()
        severity = data.get('severity', 'Medium').strip()
        raw_signal = data.get('raw_signal', '').strip()

        if not sensor_id or not message:
            return jsonify({"error": "sensor_id and message are required"}), 400

        # Check sensor exists
        sensors = db_manager.get_all_sensors()
        sensor_ids = [s['sensor_id'] for s in sensors]
        if sensor_id not in sensor_ids:
            return jsonify({"error": f"Sensor {sensor_id} not found"}), 404

        # Generate alert ID
        existing = db_manager.get_sensor_alerts(limit=9999)
        nums = []
        for a in existing:
            try:
                nums.append(int(a['alert_id'].split('-')[1]))
            except Exception:
                pass
        next_num = (max(nums) + 1) if nums else 1
        alert_id = f"ALT-{next_num:05d}"

        db_manager.insert_sensor_alert(
            alert_id=alert_id, sensor_id=sensor_id,
            alert_type=alert_type, message=message,
            severity=severity, raw_signal=raw_signal
        )
        return jsonify({"alert_id": alert_id, "sensor_id": sensor_id,
                        "alert_type": alert_type, "message": message,
                        "severity": severity}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensor_alerts/<alert_id>/acknowledge', methods=['PATCH'])
def acknowledge_alert(alert_id):
    try:
        db_manager.acknowledge_alert(alert_id)
        return jsonify({"acknowledged": alert_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── User Authentication Routes ────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        role = data.get('role', 'Analyst').strip()
        command_unit = data.get('command_unit', 'Northern Command').strip()

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        user = db_manager.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name or username,
            role=role,
            command_unit=command_unit
        )
        return jsonify(user), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = db_manager.get_user_by_username_or_email(username)
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401

        # Verify password
        input_hash = db_manager.hash_password(password)
        if input_hash != user['password_hash']:
            return jsonify({"error": "Invalid username or password"}), 401

        return jsonify({
            "user_id": user['user_id'],
            "username": user['username'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role'],
            "command_unit": user['command_unit']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Initialize DB (creates file and populates sample data if empty)
    db_manager.init_db()
    # Run the server on port 5001
    app.run(host='0.0.0.0', port=5001, debug=False)

