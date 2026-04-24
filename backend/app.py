from flask import Flask, request, jsonify
from flask_cors import CORS
from panel_registry import PanelRegistry
from discovery_service import PanelDiscoveryService
import os
from dotenv import load_dotenv

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
        with open('static/index.html', 'r') as f:
            print(f"✅ [SERVE] Serving index.html", flush=True)
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ [SERVE] static/index.html not found", flush=True)
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GHOST COMMANDER</title>
            <style>
                body { 
                    font-family: monospace; 
                    background: #0f0f1e; 
                    color: #ecf0f1; 
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; 
                    margin: 0; 
                }
                .container { text-align: center; }
                h1 { color: #0f3460; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>👻 GHOST COMMANDER</h1>
                <p>Loading dashboard...</p>
                <p><small>Connecting to backend...</small></p>
            </div>
            <script>
                const API_BASE = '/api';
                const AUTH_KEY = 'GHOST_SECRET_2026';
                
                async function loadStatus() {
                    try {
                        const resp = await fetch(API_BASE + '/status', {
                            headers: { 'X-Auth-Key': AUTH_KEY }
                        });
                        if (resp.ok) {
                            const data = await resp.json();
                            document.body.innerHTML = `
                                <div style="text-align: center;">
                                    <h1>✅ Dashboard Connected!</h1>
                                    <pre style="background: #16213e; padding: 20px; border-radius: 8px;">
                                    Online: ${data.online}
                                    Busy: ${data.busy}
                                    Idle: ${data.idle}
                                    Total Panels: ${data.total_panels}
                                    </pre>
                                </div>
                            `;
                        } else {
                            throw new Error('HTTP ' + resp.status);
                        }
                    } catch (e) {
                        document.body.innerHTML = '<h1>❌ Error: ' + e.message + '</h1>';
                    }
                }
                
                loadStatus();
            </script>
        </body>
        </html>
        """

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    print(f"📊 [HEALTH] Health check", flush=True)
    return jsonify({"status": "healthy"}), 200

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
    """Get dashboard status summary"""
    try:
        summary = registry.get_status_summary()
        print(f"📊 [STATUS] Online: {summary['online']}, Busy: {summary['busy']}, Idle: {summary['idle']}", flush=True)
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

if __name__ == '__main__':
    print("🚀 [DASHBOARD] Starting GHOST COMMANDER on port 5000", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
