import bot

# Раздел констант
ACCOUNT_ID = "0a475568-a650-449d-b5a8-ebab32e6b5ce"
MAX_MIN_INTERVAL = 14                                  # Интервал поиска максимумов и минимумов
COMMISION = 0.003                                      # коммисия брокера

if __name__ == '__main__':
    invest_bot = bot.InvestBot(account_id=ACCOUNT_ID)
    invest_bot.check_get_all_instruments()
    #invest_bot.check_instruments(1)
    #invest_bot.run()