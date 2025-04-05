"""
Configuration settings for the watch deal finder.
"""

# Target brands to search for
BRANDS = [
    "Seiko",
    "Omega",
    "Rolex",
    "Tudor",
    "Grand Seiko"
]

# Price thresholds
MAX_PRICE = 5000  # Maximum price to consider
MIN_PRICE = 50   # Minimum price to consider

# Time remaining filter (in hours)
MAX_TIME_REMAINING = 24

# Search keywords to include
KEYWORDS = [
    "vintage",
    "diver",
    "limited edition",
    "automatic",
    "mechanical",
    "chronograph",
    "GMT",
    "perpetual calendar"
]

# eBay API settings
EBAY_API_VERSION = "967"
EBAY_SITE_ID = "0"  # US site

# Database settings
DB_PATH = "watches.db"

# Deal detection settings
MIN_PRICE_DROP_PERCENT = 10  # Minimum price drop to flag as potential deal
MIN_MARGIN_PERCENT = 20      # Minimum potential profit margin

# Output settings
SAVE_TO_CSV = True
CSV_FILENAME = "watch_deals.csv"

# Notification settings
ENABLE_NOTIFICATIONS = True
NOTIFICATION_EMAIL = None  # Set to your email for notifications

# Discord webhook for notifications (optional)
DISCORD_WEBHOOK_URL = None  # Set to your Discord webhook URL

# Telegram settings (optional)
TELEGRAM_BOT_TOKEN = None
TELEGRAM_CHAT_ID = None 