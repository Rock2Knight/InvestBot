# Мой первый телеграм-бот
# с  использованием библиотки pyTelegramBotAPI
from datetime import datetime
#import os
import telebot
import json

from tinkoff.invest import CandleInterval
from tinkoff.invest.schemas import MoneyValue, InstrumentStatus, Quotation

# Для исторических свечей
from tinkoff.invest.services import MarketDataCache
from tinkoff.invest.caching.market_data_cache.cache_settings import (
    MarketDataCacheSettings,
)
from tinkoff.invest.utils import now

from datetime import timedelta
from pathlib import Path
from functional import *

#API_TOKEN = os.environ['TELE_TOKEN']     # Токен бота
#TOKEN = os.environ['TINKOFF_TOKEN']      # Токен тинькофф-инвестиций

#bot = telebot.TeleBot(API_TOKEN)         # сам бот

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am TraderBot.
I can help you to deal with shares, bonds and other. To get info about account, send \"info\"\
""")


# Получаем баланс счета в песочнице по id
@bot.message_handler(commands=['portfolio'])
def getSandboxPortfolio(message):
    words = message.text.split(' ')
    in_account_id = words[-1]         # Введенный id

    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы
        accounts_info = client.users.get_accounts()  # получаем информацию о счете
        isNotAccount = True

        # Проверка наличия счета в списке
        for account in accounts_info.accounts:
            if in_account_id == str(account.id):     # Если нашли нужный счет, то выходим из списка
                isNotAccount = False
                break

        # Если счета нет, то выводим сообщение об ошибке и выходим из функции
        if isNotAccount:
            bot.send_message(message.chat.id, "Неверно указан id счета")
            return

        # Формулировка сообщения
        message_text = f"Баланс счета {in_account_id}: \n"
        portfolio = client.sandbox.get_sandbox_portfolio(account_id=in_account_id)
        total_amount = portfolio.total_amount_portfolio
        message_text += "Currency: " + total_amount.currency + "\n"
        message_text += "Units: " + str(total_amount.units) + "\n"
        message_text += "Nano: " + str(total_amount.nano)

        bot.send_message(message.chat.id, message_text)   # Отправляем состояние счета


""" Get all actions and write them to json """
@bot.message_handler(commands=['get_instruments'])
def getAllInstruments(message):

    SharesDict = dict()

    with SandboxClient(TOKEN) as client:  # Запускаем клиент тинькофф-песочницы
        # Получаем информацию обо всех акциях
        shares = client.instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_ALL)
        for instrument in shares.instruments:
            SharesDict[instrument.name] = {"figi": instrument.figi,
                                           "currency": instrument.currency,
                                           "ticker": instrument.ticker,
                                           "sector": instrument.sector,
                                           "isin": instrument.isin,
                                           "lot": instrument.lot,
                                           "exchange": instrument.exchange,
                                           "nominal": cast_money(instrument.nominal)}

        with open("../shares.json", "w") as write_file:
            json.dump(SharesDict, write_file)          # Dump python-dict to json


@bot.message_handler(commands=['get_candles'])
def getCandles(message):
    figi = message.text

    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы
        # Set MarketDataCache
        settings = MarketDataCacheSettings(base_cache_dir=Path("../market_data_cache"))
        market_data_cache = MarketDataCache(settings=settings, services=client)

        candles = list([])
        candles_raw = market_data_cache.get_all_candles(        # Test candle
                figi="BBG004730N88",
                from_=now() - timedelta(days=7),
                interval=CandleInterval.CANDLE_INTERVAL_HOUR,
        )

        for candle in candles_raw:
            candles.append(candle)
        print(f"Amount of candles: {len(candles)}\n")

        for i in range(5):
            print(f"Open: {cast_money(candles[i].open)}\n",     # Open cast
                  f"Close: {cast_money(candles[i].close)}\n",   # Close cast
                  f"Low: {cast_money(candles[i].low)}\n",       # Min cast
                  f"High: {cast_money(candles[i].high)}\n",     # Max cast
                  f"Time: {candles[i].time}\n",                 # Time of candle
                  f"Volume: {candles[i].volume}\n\n", sep='')   # Volume


if __name__ == '__main__':
    bot.infinity_polling()