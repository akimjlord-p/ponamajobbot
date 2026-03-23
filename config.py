import os
from dotenv import load_dotenv


load_dotenv()

MAIN_ID=os.environ.get("MAIN_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS=os.getenv("ADMINS").split(',')
OPENAI_API_KEY=os.getenv("OPENAPI_API_KEY")
PROXY_URL=os.getenv("PROXY_URL")
RUN_LLM_TEST=os.getenv("RUN_LLM_TEST") == 'True'