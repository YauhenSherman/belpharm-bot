import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "")

USER_MAP = {
    310118050: "Женя Ш.",
    545300714: "Алексей C.",
    6010461781: "Денис П.",
    748571095: "Алёна Ш.",
    120690170: "Юля",
    695687106: "Женя Ч.",
    7441197929: "Сергей П.",
    5977196297: "Александра Д.",
}