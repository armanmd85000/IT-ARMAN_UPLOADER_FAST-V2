import os

# API Configuration
API_ID = int(os.environ.get("API_ID", ""))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

CREDIT = os.environ.get("CREDIT", "𝐈𝐓'𝐬𝐆𝐎𝐋𝐔")

# Owner Configuration
owner_id_str = os.environ.get("OWNER_ID", "")
if not owner_id_str:
    owner_id_str = os.environ.get("OWNER", "0")

try:
    OWNER_ID = int(owner_id_str)
except ValueError:
    OWNER_ID = 0

# Web Server Configuration
WEB_SERVER = os.environ.get("WEB_SERVER", "False").lower() == "true"
PORT = int(os.environ.get("PORT", 8000))
