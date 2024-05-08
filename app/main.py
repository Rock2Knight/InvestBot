import logging
import multiprocessing as mp
import sys
sys.path.append('C:\\Users\\User\\PycharmProjects\\teleBotTest\\app')

import bot
import stream_client

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

# Раздел констант
ACCOUNT_ID = "2ba038af-dbd8-46e4-9838-a49c30583a49"
MAX_MIN_INTERVAL = 14                                  # Интервал поиска максимумов и минимумов
COMMISION = 0.003                                      # коммисия брокера

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ACCOUNT_ID = sys.argv[1]
    investBot = bot.InvestBot(account_id=ACCOUNT_ID, correct_sum=False, autofill=False)
    investBot.run()