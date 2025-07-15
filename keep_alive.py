from flask import Flask, render_template_string
import threading
import logging

# Configure logging for Flask
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)

@app.route('/')
def home():
    """Home page showing bot status."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Maggod Fight Bot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #2f3136;
                color: #ffffff;
            }
            .container {
                text-align: center;
            }
            .status {
                background: #40444b;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .online {
                color: #43b581;
            }
            .logo {
                font-size: 3em;
                margin-bottom: 10px;
            }
            .features {
                text-align: left;
                max-width: 600px;
                margin: 0 auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">⚔️</div>
            <h1>Maggod Fight Discord Bot</h1>
            <div class="status">
                <h2 class="online">🟢 Bot is Online</h2>
                <p>The Maggod Fight bot is running and ready to host epic battles!</p>
            </div>
            <div class="status">
                <h3>🎮 Game Features</h3>
                <div class="features">
                    <ul>
                        <li>⚔️ Turn-based combat with 20 unique Greek gods</li>
                        <li>🏟️ Automatic lobby creation and management</li>
                        <li>👥 Strategic team building with god selection</li>
                        <li>🎯 Complex abilities and effects system</li>
                        <li>📊 Real-time battle tracking with Discord embeds</li>
                        <li>🔄 Multiple concurrent matches support</li>
                        <li>⚡ Interactive UI with Discord buttons</li>
                    </ul>
                </div>
            </div>
            <div class="status">
                <h3>🔧 Available Commands</h3>
                <div class="features">
                    <ul>
                        <li><code>/create_maggod_lobbies</code> - Create battle lobbies</li>
                        <li><code>/join</code> - Join a Maggod Fight lobby</li>
                        <li><code>/leave</code> - Leave current match</li>
                        <li><code>/start</code> - Start team building phase</li>
                        <li><code>/choose</code> - Choose gods for your team</li>
                        <li><code>/do_turn</code> - Make your turn in battle</li>
                        <li><code>/ping</code> - Check bot latency</li>
                        <li><code>/status</code> - Bot status information</li>
                        <li><code>/help</code> - Get detailed help</li>
                    </ul>
                </div>
            </div>
            <div class="status">
                <h3>🏛️ Greek Gods Available</h3>
                <p>Choose from 20 legendary Greek gods, each with unique abilities:</p>
                <div class="features">
                    <ul>
                        <li><strong>Olympians:</strong> Zeus, Poseidon, Hera, Athena, Apollo, Artemis, Ares, Aphrodite, Hephaestus, Hermes</li>
                        <li><strong>Underworld:</strong> Hades (Overworld), Hades (Underworld), Persephone, Charon, Thanatos, Cerberus</li>
                        <li><strong>Furies:</strong> Tisiphone, Alecto, Megaera</li>
                        <li><strong>Magic:</strong> Hecate</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'maggod-fight-bot'}

def run():
    """Run the Flask app."""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def keep_alive():
    """Start the keep alive server in a separate thread."""
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
