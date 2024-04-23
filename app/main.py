import logging
import bot

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

# Раздел констант
ACCOUNT_ID = "0a475568-a650-449d-b5a8-ebab32e6b5ce"
MAX_MIN_INTERVAL = 14                                  # Интервал поиска максимумов и минимумов
COMMISION = 0.003                                      # коммисия брокера

if __name__ == '__main__':
    investBot = bot.InvestBot(account_id=ACCOUNT_ID, autofill=False)
    investBot.run()