import logging
from bot import main
import asyncio
from db import create_db_and_tables

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
create_db_and_tables()

asyncio.run(main())