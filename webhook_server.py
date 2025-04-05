from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from database import WatchDatabase
from notifications import NotificationManager

app = Flask(__name__)
load_dotenv()

VERIFICATION_TOKEN = "9cKxL4Rm8HtWaX3sZ7qDpJNU2FveyAgKTB6uYVpFMCGh"  # Use the token shown in your screenshot

@app.route('/')
def home():
    """Health check endpoint"""
    return "eBay webhook server is running!"

@app.route('/ebay-deletion', methods=['GET'])
def verify_endpoint():
    """Handle eBay's endpoint verification"""
    challenge_code = request.args.get('challenge_code')
    if challenge_code:
        return jsonify({"challengeResponse": challenge_code})
    return jsonify({"error": "No challenge code provided"}), 400

@app.route('/ebay-deletion', methods=['POST'])
def handle_notification():
    """Handle eBay's notifications"""
    # Verify the request
    if request.headers.get('X-Ebay-Signature') != VERIFICATION_TOKEN:
        return jsonify({"error": "Invalid token"}), 401
    
    # Process the notification
    data = request.json
    print("Received notification:", data)
    return jsonify({"status": "success"}), 200

def run_webhook_server():
    """Run the webhook server"""
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 10000))
    # Run the app on 0.0.0.0 (all network interfaces)
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_webhook_server() 