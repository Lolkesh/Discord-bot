import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://{your-repl-url}.repl.co/callback").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000

# Validation
def validate_config():
    if not all([DISCORD_BOT_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        print("ERROR: Missing required environment variables!")
        print("Please set DISCORD_BOT_TOKEN, CLIENT_ID, and CLIENT_SECRET")
        exit(1)
