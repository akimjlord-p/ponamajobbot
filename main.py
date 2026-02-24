import logging
from bot import main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(filename='app.log', level=logging.DEBUG)


main()