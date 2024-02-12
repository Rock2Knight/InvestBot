# Мой первый телеграм-бот
# с  использованием библиотки pyTelegramBotAPI
import logging
import json
from datetime import datetime, timezone, timedelta
import pytz
from pathlib import Path
import pandas as pd               # Для датафреймов исторических свечей

from tinkoff.invest import CandleInterval
from tinkoff.invest.schemas import MoneyValue, InstrumentStatus, Quotation

# Для исторических свечей
from tinkoff.invest.services import MarketDataCache, MarketDataStreamService
from tinkoff.invest.caching.market_data_cache.cache_settings import (
    MarketDataCacheSettings,
)

from functional import *
from exceptions import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='w')
UTC_OFFSET = "Europe/Moscow"

# Handle '/start' and '/help'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am TraderBot.
I can help you to deal with shares, bonds and other. To get info about account, send \"info\"\
""")

# Handle '/start' and '/help'
@bot.message_handler(commands=['help'])
def helpMessage(message):
    message_text = "Краткая справка по командам в InvestBot: \n"
    message_text += "\"/start\" - Приветственное сообщение\n"
    message_text += "\"/help\" - Получить справку\n"
    message_text += "\"/portfolio account_id\" - Информация о портфеле счета с ID account_id\n"
    message_text += "\"/accounts\" - Получение всех аккаунтов в песочнице\n"
    message_text += "\"/open\" - Открытие счета в песочнице\n"
    message_text += "\"/info\" - Получение информации об активном счете в Тинькофф-песочнице\n"
    message_text += "\"/PayIn amount\" - Внесение на активный счет Тинькофф-песочницы суммы amount руб\n"
    message_text += "\"/get_instruments\" - Получение всех доступных для торговли инструментов и\n" \
                    "запись их в json-файл\n"
    message_text += "\"/get_candles\" - Получение часового свечного графика по указанному\n" \
                    "инструменту за последнюю неделю\n"
    bot.send_message(message.chat.id, message_text)      # Отправляем состояние счета



# Получаем баланс счета в песочнице по id
@bot.message_handler(commands=['portfolio'])
def getSandboxPortfolio(message):
    words = message.text.split(' ')

    if len(words) == 1:
        raise InvestBotValueError('Incorrect id')

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
        # portfolio = client.sandbox.get_sandbox_portfolio(account_id=in_account_id)
        portfolio = client.operations.get_portfolio(account_id=in_account_id)
        total_amount = portfolio.total_amount_portfolio
        message_text += "Currency: " + total_amount.currency + "\n"
        message_text += "Units: " + str(total_amount.units) + "\n"
        message_text += "Nano: " + str(total_amount.nano)

        bot.send_message(message.chat.id, message_text)   # Отправляем состояние счета


""" Get all actions and write them to json """
@bot.message_handler(commands=['get_instruments'])
def getAllInstruments(message):

    SharesDict = dict()
    target_figi, target_name = '', ''      # FIGI и наименование искомого инструмента

    words = message.text.split(' ')
    if len(words) != 1:
        target_figi = words[1]

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

            if target_figi == instrument.figi:
                target_name = instrument.name

        bot.send_message(message.chat.id, target_name+' '+target_figi)
        with open("../shares.json", "w") as write_file:
            json.dump(SharesDict, write_file)          # Dump python-dict to json


# Преобразует даты и время (начала и конца периода)
# к типу datetime
def CandlesParamsSettings(paramList: list[str]):

    moment1_raw = None
    moment1 = None
    new_datetime = 0
    try:
        moment1_raw = datetime.strptime(paramList[2], '%Y-%m-%d_%H:%M:%S')
    except ValueError:
        raise InvestBotValueError("Invalid format of start datetime object")
    finally:
        hour_value = 0
        if UTC_OFFSET == "Europe/Moscow":
            hour_value = moment1_raw.hour - 3
        moment1 = datetime(year=moment1_raw.year, month=moment1_raw.month, day=moment1_raw.day,
                       hour=hour_value, minute=moment1_raw.minute, second=moment1_raw.second,
                       tzinfo=timezone.utc)

    moment2_raw = None
    moment2 = None
    try:
        moment2_raw = datetime.strptime(paramList[3], '%Y-%m-%d_%H:%M:%S').replace(tzinfo=pytz.timezone('Europe/Moscow'))
    except ValueError:
        raise InvestBotValueError("Invalid format of end datetime object")
    finally:
        hour_value = 0
        if UTC_OFFSET == "Europe/Moscow":
            hour_value = moment2_raw.hour - 3
        moment2 = datetime(year=moment2_raw.year, month=moment2_raw.month, day=moment2_raw.day,
                        hour=hour_value, minute=moment2_raw.minute, second = moment2_raw.second,
                        tzinfo = timezone.utc)

    CI_str = paramList[4]

    # Определение интервала свечи
    if CI_str == '1_MIN':
        candle_interval = CandleInterval.CANDLE_INTERVAL_1_MIN
    elif CI_str == '2_MIN':
        candle_interval = CandleInterval.CANDLE_INTERVAL_2_MIN
    elif CI_str == '3_MIN':
        candle_interval = CandleInterval.CANDLE_INTERVAL_3_MIN
    elif CI_str == '5_MIN':
        candle_interval = CandleInterval.CANDLE_INTERVAL_5_MIN
    elif CI_str == '10_MIN':
        candle_interval = CandleInterval.CANDLE_INTERVAL_10_MIN
    elif CI_str == '15_MIN':
        candle_interval = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif CI_str == '30_MIN':
        candle_interval = CandleInterval.CANDLE_INTERVAL_30_MIN
    elif CI_str == 'HOUR':
        candle_interval = CandleInterval.CANDLE_INTERVAL_HOUR
    elif CI_str == '2_HOUR':
        candle_interval = CandleInterval.CANDLE_INTERVAL_2_HOUR
    elif CI_str == '4_HOUR':
        candle_interval = CandleInterval.CANDLE_INTERVAL_4_HOUR
    elif CI_str == 'DAY':
        candle_interval = CandleInterval.CANDLE_INTERVAL_DAY
    elif CI_str == 'WEEK':
        candle_interval = CandleInterval.CANDLE_INTERVAL_WEEK
    elif CI_str == 'MONTH':
        candle_interval = CandleInterval.CANDLE_INTERVAL_MONTH
    else:
        raise InvestBotValueError("Invalid value of CandleInterval")

    getCandlesParams = (paramList[1], moment1, moment2, candle_interval)
    return getCandlesParams


def getCandles(param_list: str):

    param_list = param_list.split(' ')  # Список параметров
    candlesParams = None                  # Список параметров для getCandles

    try:
        candlesParams = CandlesParamsSettings(param_list)
    except InvestBotValueError as iverror:
        raise InvestBotValueError(iverror.msg)


    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы
        # Set MarketDataCache
        settings = MarketDataCacheSettings(base_cache_dir=Path("../market_data_cache"))
        market_data_cache = MarketDataCache(settings=settings, services=client)

        candles = list([])
        candles_raw = market_data_cache.get_all_candles(        # Test candle
                figi=candlesParams[0],
                from_=candlesParams[1],
                to=candlesParams[2],
                interval=candlesParams[3],
        )

        for candle in candles_raw:
            candles.append(candle)

    return candles


@bot.message_handler(commands=['get_candles'])
def save_candles(message):

    try:
        candles = getCandles(message.text)
    except InvestBotValueError as iverror:
        raise InvestBotValueError(iverror.msg)

    size = len(candles)

    # Форматированные исторические свечи
    updated_candles = {'open': list([]), 'close': list([]),
                       'low': list([]), 'high': list([]),
                       'time': list([]), 'volume': list([])}

    # Создаем сырой датафрейм форматированных свечей
    for i in range(size):
        open = str(cast_money(candles[i].open))
        close = str(cast_money(candles[i].close))
        low = str(cast_money(candles[i].low))
        high = str(cast_money(candles[i].high))

        utc_time = candles[i].time
        hour_msk = utc_time.hour + 3
        moscow_time = datetime(year=utc_time.year, month=utc_time.month, day=utc_time.day,
                               hour=hour_msk, minute=utc_time.minute, second=utc_time.second)

        time = moscow_time.strftime('%Y-%m-%d_%H:%M:%S')
        volume = str(candles[i].volume)

        # Добавляем строку в сырой датафрейм
        updated_candles['open'].append(open)
        updated_candles['close'].append(close)
        updated_candles['low'].append(low)
        updated_candles['high'].append(high)
        updated_candles['time'].append(time)
        updated_candles['volume'].append(volume)

    df_candles = pd.DataFrame(updated_candles)   # Создаем датафрейм с форматированными свечами
    df_candles.to_csv("../share_history.csv", sep=',')

    print("Data have been written")

if __name__ == '__main__':
    bot.infinity_polling()