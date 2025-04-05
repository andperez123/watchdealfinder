"""
Notification handlers for the watch deal finder.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Dict, List
import config

class NotificationManager:
    @staticmethod
    def format_deal_message(deal: Dict) -> str:
        """Format a deal into a readable message."""
        return f"""
🔥 Potential Watch Deal Found!

Watch: {deal['title']}
Brand: {deal['brand']}
Current Price: ${deal['current_price']}
Price Drop: {deal['price_drop_percent']}%
URL: {deal['url']}
        """.strip()

    def send_email(self, subject: str, body: str):
        """Send email notification."""
        if not config.NOTIFICATION_EMAIL:
            return
            
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SMTP_FROM_EMAIL')
        msg['To'] = config.NOTIFICATION_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(os.getenv('SMTP_SERVER'), 587) as server:
                server.starttls()
                server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

    def send_discord(self, message: str):
        """Send Discord notification."""
        if not config.DISCORD_WEBHOOK_URL:
            return
            
        try:
            requests.post(
                config.DISCORD_WEBHOOK_URL,
                json={"content": message}
            )
        except Exception as e:
            print(f"Failed to send Discord notification: {str(e)}")

    def send_telegram(self, message: str):
        """Send Telegram notification."""
        if not all([config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID]):
            return
            
        try:
            requests.post(
                f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": config.TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
        except Exception as e:
            print(f"Failed to send Telegram notification: {str(e)}")

    def notify_deal(self, deal: Dict):
        """Send notifications about a potential deal through all configured channels."""
        message = self.format_deal_message(deal)
        
        if config.ENABLE_NOTIFICATIONS:
            self.send_email("Watch Deal Alert! 🔥", message)
            self.send_discord(message)
            self.send_telegram(message) 