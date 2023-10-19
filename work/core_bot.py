# Мой первый телеграм-бот
# с  использованием библиотки pyTelegramBotAPI
import json
from datetime import timedelta, datetime, timezone
from pathlib import Path

from tinkoff.invest import CandleInterval
from tinkoff.invest.schemas import MoneyValue, InstrumentStatus, Quotation

# Для исторических свечей
from tinkoff.invest.services import MarketDataCache
from tinkoff.invest.caching.market_data_cache.cache_settings import (
    MarketDataCacheSettings,
)

from functional import *


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


def cast_money(sum: Quotation) -> float:
    return sum.units + sum.nano / 1e9


def string_data(dt: datetime) -> str:
    dt_tuple = dt.timetuple()
    dt_string = str(dt_tuple[0])+'-'+str(dt_tuple[1])+'-'+str(dt_tuple[2])+'-'+str(dt_tuple[3])+'-'+str(dt_tuple[4])+'-'+str(dt_tuple[5])
    return dt_string


# Преобразует даты и время (начала и конца периода)
# к типу datetime
def CandlesParamsSettings(paramList: list[str]):

    getCandlesParams = None
    candle_interval = None    # Интервал свечи

    year_ = int(paramList[2][:4])
    month_ = int(paramList[2][5:7])
    day_ = int(paramList[2][8:10])
    hour_ = int(paramList[2][11:13])
    minute_ = int(paramList[2][14:16])
    second_ = int(paramList[2][17:19])

    moment1 = datetime(year=year_, month=month_, day=day_,
                       hour=hour_, minute=minute_, second=second_,
                       tzinfo=timezone.utc)

    year_ = int(paramList[3][:4])
    month_ = int(paramList[3][5:7])
    day_ = int(paramList[3][8:10])
    hour_ = int(paramList[3][11:13])
    minute_ = int(paramList[3][14:16])
    second_ = int(paramList[3][17:19])

    moment2 = datetime(year=year_, month=month_, day=day_,
                       hour=hour_, minute=minute_, second=second_,
                       tzinfo=timezone.utc)

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
        raise ValueError

    getCandlesParams = (paramList[1], moment1, moment2, candle_interval)
    return getCandlesParams


@bot.message_handler(commands=['get_candles'])
def getCandles(message):

    param_list = message.text.split(' ')  # Список параметров
    candlesParams = None                  # Список параметров для getCandles

    try:
        candlesParams = CandlesParamsSettings(param_list)
    except ValueError:
        print('Incorrect value of CandleInterval')


    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы
        # Set MarketDataCache
        settings = MarketDataCacheSettings(base_cache_dir=Path("../market_data_cache"))
        market_data_cache = MarketDataCache(settings=settings, services=client)

        candles = list([])
        up_candles = list([])
        candles_raw = market_data_cache.get_all_candles(        # Test candle
                figi=candlesParams[0],
                from_=candlesParams[1],
                to=candlesParams[2],
                interval=candlesParams[3],
        )

        for candle in candles_raw:
            candles.append(candle)
        print(f"Amount of candles: {len(candles)}\n")
        size = len(candles)

        for i in range(5):
            print(f"Open: {cast_money(candles[i].open)}\n",     # Open cast
                  f"Close: {cast_money(candles[i].close)}\n",   # Close cast
                  f"Low: {cast_money(candles[i].low)}\n",       # Min cast
                  f"High: {cast_money(candles[i].high)}\n",     # Max cast
                  f"Time: {candles[i].time}\n",                 # Time of candle
                  f"Volume: {candles[i].volume}\n\n", sep='')   # Volume


        with open("../share_history_other.txt", "w") as write_file:
            write_file.write('Time open close low high volume\n')
            for i in range(size):
                up_candle = dict()
                up_candle['open'] = str(cast_money(candles[i].open))
                up_candle['close'] = str(cast_money(candles[i].close))
                up_candle['low'] = str(cast_money(candles[i].low))
                up_candle['high'] = str(cast_money(candles[i].high))
                up_candle['time'] = string_data(candles[i].time)
                up_candle['volume'] = str(candles[i].volume)

                write_file.write(up_candle['time']+' '+up_candle['open']+' '+up_candle['close']+' '+
                                 up_candle['low']+' '+up_candle['high']+' '+up_candle['volume']+'\n')

if __name__ == '__main__':
    bot.infinity_polling()