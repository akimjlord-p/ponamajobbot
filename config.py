import os
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY=os.getenv("OPENAPI_API_KEY")
PROXY_URL=os.getenv("PROXY_URL")
RUN_LLM_TEST=os.getenv("RUN_LLM_TEST") == 'True'
TG_PROXY_URL=os.getenv("TG_PROXY_URL")
