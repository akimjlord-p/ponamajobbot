import os
from dotenv import load_dotenv

load_dotenv()

MAIN_ID=os.environ.get("MAIN_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS=os.getenv("ADMINS").split(',')