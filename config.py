import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

USER_MAP = {
    310118050: "Женя Ш.",
    # 987654321: "Алена Ш.",
    # 555555555: "Денис П.",
}