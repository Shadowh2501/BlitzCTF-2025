from flask import Flask, render_template, request, session, redirect, url_for, jsonify , send_file
import json, io, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
flag_value = os.getenv("PRICE")
flag_string = os.getenv("FLAG")


@app.route('/')
def base():
    if 'clicks' not in session:
        session['clicks'] = 0
    return render_template("main.html", clicks=session['clicks'])

@app.route('/buy')
def buy():
    if 'clicks' not in session:
        session['clicks'] = 0
    return render_template("buy.html",clicks=session['clicks'])


@app.route('/save', methods=['POST'])
def save():
    if 'clicks' not in session:
        return jsonify({"error": "Submission to override non-existing data, exiting..."}), 400

    data = request.get_json()
    try:
        original_clicks = int(session.get('clicks', 0))
        updated_clicks = int(data.get('clicks', 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input data."}), 400

    if abs(updated_clicks - original_clicks) > 6:
        return jsonify({"error": "Bot behavior detected. Save limit exceeded (50 clicks max per save)."}), 403

    session['clicks'] = updated_clicks
    return jsonify({"message": "Clicks updated successfully.", "clicks": session['clicks']})


@app.route('/buy_item', methods=['POST'])
def buy_item():
    if 'clicks' not in session:
        return jsonify({"success": False, "message": "Missing clicks in session."}), 400

    current_clicks = int(session['clicks'])

    try:
        required_clicks = int(flag_value)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid server configuration for item price."}), 500

    if current_clicks >= required_clicks:
        session['clicks'] = current_clicks - required_clicks
        return jsonify({
            "success": True,
            "message": f"Transaction Completed. Flag: {flag_string}",
            "new_clicks": session['clicks']
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "Insufficient Funds"
        }), 400


@app.route('/create_backup')
def create_backup():
    if 'clicks' not in session:
        return jsonify({"error": "No data to back up."}), 400

    clicks = session['clicks']
    nonce = os.urandom(16).hex()  # A more realistic nonce (longer)

    backup_data = {
        "profile": {
            "user": {
                "id": "user_78291",
                "username": "PlayerOne",
                "email": "playerone@example.com",
                "join_date": "2021-03-12T14:55:02Z",
                "last_login": "2025-04-22T09:15:33Z"
            },
            "settings": {
                "theme": "dark",
                "language": "en",
                "notifications_enabled": True,
                "privacy_level": "high"
            }
        },
        "game": {
            "title": "ChronoTapper",
            "version": "v1.9.2-beta",
            "developer": "Shadowh",
            "build_hash": "b9248f67a21eaa6e82647e441af7204f9b40a9ad",
            "content_hash": "a31d7c8ff60da6873fca63764ad432cfed0f8a7c",
            "session_id": nonce  # This is the nonce you mentioned (realistic value)
        },
        "stats": {
            "level": 15,
            "progress": 78,
            "quests_completed": 3,
            "achievements": ["fast_clicker", "precision_tapper"],
            "items_purchased": ["premium_pack", "double_points_boost"]
        },
        "session_data": {
            "timestamp": datetime.utcnow().isoformat(),
            "clicks_data": {
                "clickStore": clicks,
                "currency": "tokens",
                "daily_limit_reached": False
            },
            "last_session_duration": "30m 25s",
            "current_session_duration": "5m 17s",
            "active_boosts": ["speed_boost", "click_multiplier"],
            "server_id": "srv_2098b",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "client_version": "v1.9.2-beta"
        },
        "security": {
            "session_token": nonce,  # Ensuring uniqueness
            "csrf_token": os.urandom(32).hex(),  # Random CSRF token to add noise
            "integrity_check": os.urandom(64).hex(),  # Fake integrity check hash
            "previous_backup_hash": "3b9e69a6beae74069f74d3b2f94668d4a0249d1f"  # Random example hash
        },
        "metadata": {
            "device_id": "d3d6f12b-545f-40b6-a920-76734667b758",
            "region": "US-EAST-2",
            "os": "Windows 10",
            "browser": "Chrome 92.0.4515.159",
            "network": "fiber"
        }
    }

    json_data = json.dumps(backup_data, indent=2)
    file_obj = io.BytesIO(json_data.encode('utf-8'))
    file_obj.seek(0)

    return send_file(
        file_obj,
        mimetype='application/json',
        as_attachment=True,
        download_name='backup.json'
    )


@app.route('/restore_backup', methods=['POST'])
def restore_backup():
    try:
        # Get the backup data from the request
        backup_data = request.get_json()

        # Check if the required fields are present
        if 'session_data' not in backup_data or 'clicks_data' not in backup_data['session_data']:
            return jsonify({"error": "Invalid backup data."}), 400

        # Extract the click store from the backup data
        click_store = backup_data['session_data']['clicks_data']['clickStore']

        if click_store is None or not isinstance(click_store, (int, float)) or click_store < 0 or click_store > 99999:
            click_store = 0
            session['clicks'] = click_store
            return jsonify({"error": "Invalid clicks data , or exceeding maximum 99999 clicks limit , resetting to 0..."}), 400



        # Store the click store in the session
        session['clicks'] = click_store

        return jsonify({"success": "Backup restored successfully!"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
	app.run(debug=True)
