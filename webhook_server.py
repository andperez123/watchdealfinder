from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from database import WatchDatabase
from notifications import NotificationManager

app = Flask(__name__)
load_dotenv()

@app.route('/webhook/deals', methods=['POST'])
def deals_webhook():
    """Endpoint to receive deal notifications"""
    data = request.json
    notifier = NotificationManager()
    notifier.notify_deal(data)
    return jsonify({"status": "success"}), 200

def run_webhook_server():
    """Run the webhook server"""
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')

if __name__ == "__main__":
    run_webhook_server() 