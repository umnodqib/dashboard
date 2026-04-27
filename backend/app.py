from flask import Flask, request, jsonify
from flask_cors import CORS
from panel_registry import PanelRegistry
from discovery_service import PanelDiscoveryService
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

registry = PanelRegistry()
discovery_service = PanelDiscoveryService(registry)

@app.before_request
def startup():
    if not discovery_service.running:
        discovery_service.start()

AUTH_KEY = os.getenv("DASHBOARD_AUTH_KEY", "GHOST_SECRET_2026")

@app.before_request
def check_auth():
    """Skip auth untuk static files, health, dan root"""
    # ✅ FIX: Check function names, not string names
    if request.path == '/' or request.path.startswith('/static/') or request.path == '/health':
        return
    if request.path.startswith('/favicon'):
        return
    
    # Require auth untuk /api/*
    if request.path.startswith('/api/'):
        if request.headers.get("X-Auth-Key") != AUTH_KEY:
            print(f"❌ [AUTH] Unauthorized: {request.method} {request.path}", flush=True)
            return jsonify({"error": "Unauthorized"}), 401

# ============================================
# SERVE STATIC FILES
# ============================================
@app.route('/')
def serve_index():
    """Serve dashboard index.html"""
    try:
        with open('frontend/index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({"error": "index.html not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    print(f"📊 [HEALTH] Health check", flush=True)
    return jsonify({"status": "healthy"}), 200

# ============================================
# API: COMMANDS (Baru)
# ============================================
if not hasattr(app, 'commands'):
    app.commands = {}
@app.route('/api/command/create', methods=['POST'])
def create_command():
    """Create command dengan payload (email, password, urls)"""
    try:
        data = request.json or {}
        
        slot = data.get('slot')
        action = data.get('action')
        payload = data.get('payload', {})
        
        print(f"➕ [COMMAND] Creating: slot={slot}, action={action}, payload={payload}", flush=True)
        
        if not slot or not action:
            return jsonify({"error": "Missing slot or action"}), 400
        
        # Generate command ID
        cmd_id = str(uuid.uuid4())
        
        # Store command
        app.commands[cmd_id] = {
            "id": cmd_id,
            "slot": slot,
            "action": action,
            "payload": payload,
            "status": "PENDING",
            "created_at": datetime.now().isoformat()
        }
        
        print(f"✅ [COMMAND] Created: {cmd_id}", flush=True)
        return jsonify({
            "id": cmd_id,
            "status": "PENDING"
        }), 201
        
    except Exception as e:
        print(f"❌ [COMMAND] Error: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/command/get/<int:slot>', methods=['GET'])
def get_commands(slot):
    """Panel pull commands untuk slot tertentu"""
    try:
        # Filter commands untuk slot ini yang PENDING
        pending_cmds = [
            cmd for cmd in app.commands.values() 
            if cmd.get('slot') == slot and cmd.get('status') == 'PENDING'
        ]
        
        print(f"📥 [COMMAND] Slot {slot} pulling {len(pending_cmds)} commands", flush=True)
        
        # Update status to SENT
        for cmd in pending_cmds:
            cmd['status'] = 'SENT'
        
        return jsonify(pending_cmds), 200
        
    except Exception as e:
        print(f"❌ [COMMAND] Error: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/command/update/<cmd_id>', methods=['POST'])
def update_command(cmd_id):
    """Panel report command status"""
    try:
        data = request.json or {}
        
        if cmd_id not in app.commands:
            return jsonify({"error": "Command not found"}), 404
        
        # Update status
        app.commands[cmd_id]['status'] = data.get('status', 'UNKNOWN')
        app.commands[cmd_id]['result'] = data.get('result')
        
        print(f"🔄 [COMMAND] Updated {cmd_id}: {data.get('status')}", flush=True)
        
        return jsonify({"status": "updated"}), 200
        
    except Exception as e:
        print(f"❌ [COMMAND] Error: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/command/list', methods=['GET'])
def list_commands():
    """Get all commands"""
    try:
        commands = list(app.commands.values())
        return jsonify(commands), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ============================================
# API: PANEL REGISTRATION
# ============================================
@app.route('/api/register', methods=['POST'])
def register_panel():
    """Register new panel to dashboard"""
    try:
        data = request.json or {}
        
        # Get panel data
        slot = data.get('slot')
        ip = data.get('ip')
        url = data.get('url')
        port = data.get('port', 7860)
        
        print(f"📡 [REGISTER] Incoming: slot={slot}, ip={ip}, url={url}, port={port}", flush=True)
        
        # Validate
        if not all([slot, ip, url]):
            print(f"❌ [REGISTER] Missing fields: slot={slot}, ip={ip}, url={url}", flush=True)
            return jsonify({
                "error": "Missing fields",
                "received": {"slot": slot, "ip": ip, "url": url}
            }), 400
        
        # Register
        registry.register_panel(slot, ip, url, port)
        print(f"✅ [REGISTER] Panel registered successfully: Slot {slot}", flush=True)
        
        return jsonify({
            "status": "registered",
            "slot": slot,
            "message": f"Panel slot {slot} registered successfully"
        }), 200
        
    except Exception as e:
        print(f"❌ [REGISTER] Exception: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# ============================================
# API: HEARTBEAT
# ============================================
@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    """Update panel heartbeat status"""
    try:
        data = request.json or {}
        
        slot = data.get('slot')
        state = data.get('state')
        panel_data = data.get('data', {})
        
        print(f"💓 [HEARTBEAT] Slot {slot}: {state} | Emails: {panel_data.get('emails', 0)}, Links: {panel_data.get('links', 0)}", flush=True)
        
        if not slot or not state:
            print(f"⚠️ [HEARTBEAT] Missing slot or state", flush=True)
            return jsonify({"error": "Missing slot or state"}), 400
        
        registry.update_heartbeat(slot, state, panel_data)
        return jsonify({"status": "updated"}), 200
        
    except Exception as e:
        print(f"❌ [HEARTBEAT] Exception: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# ============================================
# API: STATUS
# ============================================
@app.route('/api/status', methods=['GET'])
def status():
    try:
        from datetime import datetime
        current_time = datetime.now()
        
        for panel_id, panel_data in registry.panels.items():
            try:
                last_hb_str = panel_data.get('last_heartbeat', '')
                if not last_hb_str:
                    panel_data['status'] = 'OFFLINE'
                    continue
                    
                last_hb = datetime.fromisoformat(last_hb_str)
                elapsed = (current_time - last_hb).total_seconds()
                
                # ✅ FIX: 300 detik = 5 menit (heartbeat tiap 30s, kasih buffer 10x)
                panel_data['status'] = 'ONLINE' if elapsed <= 300 else 'OFFLINE'
                
            except Exception as e:
                print(f"⚠️ [STATUS] Error parsing panel {panel_id}: {e}", flush=True)
                panel_data['status'] = 'OFFLINE'
        
        summary = registry.get_status_summary()
        print(f"📊 [STATUS] Online: {summary['online']}, Busy: {summary['busy']}", flush=True)
        return jsonify(summary), 200
        
    except Exception as e:
        print(f"❌ [STATUS] Exception: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# ============================================
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500

# ============================================
# API: GET PANEL LOG
# ============================================
# Edit dashboardfix/backend/app.py line ~780
# Ubah ke gunakan localhost jika panel di host yang sama

@app.route('/api/panel/<int:slot>/logs', methods=['GET'])
def get_panel_logs(slot):
    try:
        panel_id = f"panel_{slot}"
        if panel_id not in registry.panels:
            return jsonify({"error": "Panel not found"}), 404
        
        panel_data = registry.panels[panel_id]
        panel_url = panel_data.get('url')
        
        if not panel_url:
            return jsonify({"error": "Panel URL not found"}), 400
        
        # ✅ FIX: Gunakan internal IP daripada public URL
        # panel_url mungkin https://domain.io, ubah ke http://local-ip:7860
        panel_ip = panel_data.get('ip')
        if panel_ip and panel_ip != 'Unknown IP':
            internal_url = f"http://{panel_ip}:7860"
        else:
            internal_url = panel_url
        
        print(f"📋 [LOGS] Fetching from {internal_url}/logs", flush=True)
        
        resp = requests.get(
            f"{internal_url}/logs",
            headers={"X-Auth-Key": AUTH_KEY},
            timeout=5,
            verify=False
        )
        
        if resp.status_code == 200:
            return jsonify(resp.json()), 200
        else:
            return jsonify({"error": f"Panel error: {resp.status_code}"}), 500
            
    except Exception as e:
        print(f"❌ [LOGS] Error: {e}", flush=True)
        return jsonify({"error": str(e), "trace": str(e)}), 500
        
if __name__ == '__main__':
    print("🚀 [DASHBOARD] Starting GHOST COMMANDER on port 5000", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
