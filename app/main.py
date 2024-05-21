import sys
import os
from dotenv import load_dotenv
import logging
import multiprocessing as mp
import asyncio

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)

import bot
import stream_client

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

# Раздел констант
ACCOUNT_ID = "2ba038af-dbd8-46e4-9838-a49c30583a49"
CONFIG_FILE = "../settings.ini"
MAX_MIN_INTERVAL = 14                                  # Интервал поиска максимумов и минимумов
COMMISION = 0.003                                      # коммисия брокера

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ACCOUNT_ID = sys.argv[1]
        CONFIG_FILE = sys.argv[2]
    investBot = bot.InvestBot(account_id=ACCOUNT_ID, correct_sum=False, filename=CONFIG_FILE, autofill=False)
    asyncio.run(investBot.run())