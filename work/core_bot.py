# Телеграм-бот для управления торговым роботом
# с  использованием библиотки pyTelegramBotAPI
import logging
import json
from datetime import datetime, timezone, timedelta
import pytz
from pathlib import Path
from typing import Generator

import pandas as pd               # Для датафреймов исторических свечей

from tinkoff.invest import CandleInterval
from tinkoff.invest.schemas import (
    MoneyValue, InstrumentStatus, Quotation,
    InstrumentIdType, AssetType, InstrumentType
)
from tinkoff.invest.exceptions import RequestError

# Для исторических свечей
from tinkoff.invest.services import MarketDataStreamService, MarketDataService

#from .functional import *
#from .exceptions import *
from work.functional import *
from work.exceptions import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
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
def help_message(message):
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



""" Получаем баланс счета в песочнице по id """
@bot.message_handler(commands=['portfolio'])
def get_sandbox_portfolio(message):

    words = message.text.split(' ')
    account_id = words[-1]

    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы
        accounts_info = client.users.get_accounts()  # получаем информацию о счете
        isNotAccount = True

        # Проверка наличия счета в списке
        for account in accounts_info.accounts:
            if account_id == str(account.id):     # Если нашли нужный счет, то выходим из списка
                isNotAccount = False
                break

        # Если счета нет, то выводим сообщение об ошибке и выходим из функции
        if isNotAccount:
            return None

        portfolio = client.sandbox.get_sandbox_portfolio(account_id=account_id)
        free_money =  cast_money(portfolio.total_amount_currencies)
        total_amount_shares = cast_money(portfolio.total_amount_shares)
        total_amount_bonds = cast_money(portfolio.total_amount_bonds)
        total_amount_etf = cast_money(portfolio.total_amount_etf)
        total_amount = cast_money(portfolio.total_amount_portfolio)
        profit = cast_money(portfolio.expected_yield)

        positions = portfolio.positions

        resp_message = ''
        resp_message += f'Общая стоимость портфеля: {total_amount:.2f} RUB\n'
        resp_message += f'Свободные деньги в портфеле: {free_money:.2f} RUB\n'
        resp_message += f'Стоимость акций в портфеле: {total_amount_shares:.2f} RUB\n'
        resp_message += f'Стоимость облигаций в портфеле: {total_amount_bonds:.2f} RUB\n'
        resp_message += f'Стоимость фондов в портфеле: {total_amount_etf:.2f} RUB\n'
        resp_message += f'Прибыль/убыток: {profit:.2f} %\n'

        if positions:
            resp_message += '\nПозиции:\n'
            for position in positions:
                instrument_uid = position.instrument_uid     # UID инструмента
                position_uid = position.position_uid         # Position UID инструмента
                figi = position.figi                         # FIGI
                instrument_type = position.instrument_type
                count = cast_money(position.quantity)            # Количество штук
                cur_price = cast_money(position.current_price)   # Текущая цена
                count_lots = cast_money(position.quantity_lots)  # Количество лотов
                profit = cast_money(position.expected_yield)     # Прибыль в процентах
                name = ''

                with SandboxClient(TOKEN) as client:
                    resp = client.instruments.get_instrument_by(
                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
                        id=instrument_uid
                    )
                    name = resp.instrument.name

                resp_message += f'UID: {instrument_uid}\n' + f'POSITION UID: {position_uid}\n'
                resp_message += f'FIGI: {figi}\n' + f'Name: {name}\n' + f'Type: {instrument_type}\n' + f'Count: {count}\n'
                resp_message += f'Current price = {cur_price:.2f} RUB\n' + f'Count of lots: {count_lots}\n'
                resp_message += f'Profit/Unprofit: {profit:.2f} %\n\n'

        bot.send_message(message.chat.id, resp_message)  # Отправляем состояние счета

        print("Общая стоимость портфеля: %.2f" % total_amount)
        print("Общая стоимость акций в портфеле: %.2f" % total_amount_shares)
        print("Общая стоимость облигаций в портфеле: %.2f" % total_amount_bonds)
        print("Общая стоимость ETF в портфеле: %.2f" % total_amount_etf)
        return portfolio


""" Get all actions and write them to json """
@bot.message_handler(commands=['get_instruments'])
def get_all_instruments(message):

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

        #bot.send_message(message.chat.id, target_name+' '+target_figi)
        with open("../shares.json", "w") as write_file:
            json.dump(SharesDict, write_file)          # Dump python-dict to json


""" Получение информации об активах """
@bot.message_handler(commands=['get_assets'])
def get_all_assets(message):
    func_time1 = datetime.now(timezone.utc)

    # Создаем словарь для хранения информации о активах
    #activeDict = {'asset_uid': [], 'type': [], 'asset_name': [], 'instruments': []}
    activeDict = dict()

    with SandboxClient(TOKEN) as client:   # Запускаем клиент тинькофф-песочницы
        moment1 = datetime.now(timezone.utc)
        response = client.instruments.get_assets() # Получаем список всех активов
        moment2 = datetime.now(timezone.utc)
        delta = moment2 - moment1

        print(f"Время выполнения метода GetAssets: {delta} секунд\n")

        for asset in response.assets:
            # Если актив не относится к ценным бумагам, пропускаем, его
            if asset.type != AssetType.ASSET_TYPE_SECURITY:
                continue

            activeDict[asset.name] = {'asset_uid': asset.uid, 'instruments': None}

            '''
            Создаем словарь для списка инструментов по активу
            instrument_uid - уникальный идентификатор инструмента
            position_uid - id позиции
            figi - FIGI инструмента
            instrument_type - тип инструмента
            ticker - тикер инструмента
            class_code - класс-код (секция торгов)
            links - массив связанных инструментов
            instrument_kind - тип инструмента
            '''
            instrumentDict = dict()

            # Собираем в словарь все инструменты, входящие в актив
            for instrument in asset.instruments:
                # Если инструмент не является акцией, пропускаем его
                if instrument.instrument_kind != InstrumentType.INSTRUMENT_TYPE_SHARE:
                    continue

                instrumentDict[instrument.uid] = {'instrument_uid': instrument.uid, 'figi': instrument.figi,
                                                    'instrument_type': instrument.instrument_type,
                                                    'ticker': instrument.ticker,
                                                    'class_code': instrument.class_code,
                                                    'position_uid': instrument.position_uid,
                                                    'instrument_kind': 'Акция'}
                '''
                Словарь связанных инструментов
                
                type - тип связи
                instrument_uid - уникальный идентификатор инструмента
                '''
                linkDict = {'type': [], 'instrument_uid': []}

                for link in instrument.links:
                    linkDict['type'].append(link.type)
                    linkDict['instrument_uid'].append(link.instrument_uid)

                instrumentDict[instrument.uid]['link'] = linkDict # Добавляем массив связанных инструментов в словарь

            activeDict[asset.name]['instruments'] = instrumentDict  # Добавляем массив инструментов актива в словарь

    with open("../assets.json", 'w') as assets_json:
        json.dump(activeDict, assets_json)  # Конвертируем датафрейм с активами в json-файл

    func_time2 = datetime.now(timezone.utc)
    func_delta = func_time2 - func_time1
    print('Assets are seccessfully loaded!')
    print(f'Время выполнения функции: {func_delta} секунд')


""" На основе запроса пользователя формирует кортеж аргументов для вызова функции get_all_candles сервиса котировок """
def candles_formatter(paramList: list[str]):

    moment1_raw = None
    moment1 = None
    new_datetime = 0
    try:
        moment1_raw = datetime.strptime(paramList[2], '%Y-%m-%d_%H:%M:%S')
    except ValueError:
        logging.error("Invalid format of start datetime object\n")
        raise InvestBotValueError("Invalid format of start datetime object")
    finally:
        hour_value = 0
        if UTC_OFFSET == "Europe/Moscow":
            hour_value = moment1_raw.hour - 3
            if hour_value < 0:
                hour_value = 0
        moment1 = datetime(year=moment1_raw.year, month=moment1_raw.month, day=moment1_raw.day,
                       hour=hour_value, minute=moment1_raw.minute, second=moment1_raw.second,
                       tzinfo=timezone.utc)

    moment2_raw = None
    moment2 = None
    try:
        moment2_raw = datetime.strptime(paramList[3], '%Y-%m-%d_%H:%M:%S').replace(tzinfo=pytz.timezone('Europe/Moscow'))
    except ValueError:
        logging.error("Invalid format of end datetime object\n")
        raise InvestBotValueError("Invalid format of end datetime object")
    finally:
        hour_value = 0
        if UTC_OFFSET == "Europe/Moscow":
            hour_value = moment2_raw.hour - 3
            if hour_value < 0:
                hour_value = 0
        moment2 = datetime(year=moment2_raw.year, month=moment2_raw.month, day=moment2_raw.day,
                        hour=hour_value, minute=moment2_raw.minute, second = moment2_raw.second,
                        tzinfo = timezone.utc)

    CI_str = paramList[4]
    with open("../candle_interval.txt", 'w', encoding='utf-8') as file:
        file.write(CI_str)

    candle_interval = None   # Длина таймфрейма

    # Определение интервала свечи
    match CI_str:
        case '1_MIN':
            candle_interval = CandleInterval.CANDLE_INTERVAL_1_MIN
        case '2_MIN':
            candle_interval = CandleInterval.CANDLE_INTERVAL_2_MIN
        case '3_MIN':
            candle_interval = CandleInterval.CANDLE_INTERVAL_3_MIN
        case '5_MIN':
            candle_interval = CandleInterval.CANDLE_INTERVAL_5_MIN
        case '10_MIN':
            candle_interval = CandleInterval.CANDLE_INTERVAL_10_MIN
        case '15_MIN':
            candle_interval = CandleInterval.CANDLE_INTERVAL_15_MIN
        case '30_MIN':
            candle_interval = CandleInterval.CANDLE_INTERVAL_30_MIN
        case 'HOUR':
            candle_interval = CandleInterval.CANDLE_INTERVAL_HOUR
        case '2_HOUR':
            candle_interval = CandleInterval.CANDLE_INTERVAL_2_HOUR
        case '4_HOUR':
            candle_interval = CandleInterval.CANDLE_INTERVAL_4_HOUR
        case 'DAY':
            candle_interval = CandleInterval.CANDLE_INTERVAL_DAY
        case 'WEEK':
            candle_interval = CandleInterval.CANDLE_INTERVAL_WEEK
        case 'MONTH':
            candle_interval = CandleInterval.CANDLE_INTERVAL_MONTH
        case _:
            logging.error("Invalid value of CandleInterval\n")
            raise InvestBotValueError("Invalid value of CandleInterval")

    return paramList[1], moment1, moment2, candle_interval


def get_candles(param_list: str):

    param_list = param_list.split(' ')  # Список параметров
    candlesParams = None                  # Список параметров для get_candles

    #mode_uid = int(param_list[-1])

    try:
        candlesParams = candles_formatter(param_list)
    except InvestBotValueError as iverror:
        logging.error(f"Ошибка во время выполнения метода core_bot.get_candles: {iverror.msg}\n")
        raise InvestBotValueError(iverror.msg)


    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы

        candles = list([])
        candles_raw = None
        try:
            candles_raw = client.market_data.get_candles(
                instrument_id=candlesParams[0],
                from_=candlesParams[1],
                to=candlesParams[2],
                interval=candlesParams[3]
            )
        except Exception as irerror:
            print('\n\n', irerror.args, '\n')
            raise irerror
        finally:
            #if mode_uid == 0:
            #    for candle in candles_raw:
            #        candles.append(candle)
            #else:
            for candle in candles_raw.candles:
                candles.append(candle)

    return candles


async def async_get_candles(param_list: str):

    param_list = param_list.split(' ')  # Список параметров
    candlesParams = None                  # Список параметров для get_candles
    # Форматированные исторические свечи
    updated_candles = {'open': list([]), 'close': list([]),
                       'low': list([]), 'high': list([]),
                       'time': list([]), 'volume': list([])}

    #mode_uid = int(param_list[-1])

    try:
        candlesParams = candles_formatter(param_list)
    except InvestBotValueError as iverror:
        logging.error(f"Ошибка во время выполнения метода core_bot.async_get_candles: {iverror.msg}\n")
        raise InvestBotValueError(iverror.msg)


    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы

        candles = list([])
        candles_raw = None
        try:
            candles_raw = client.market_data.get_candles(
                instrument_id=candlesParams[0],
                from_=candlesParams[1],
                to=candlesParams[2],
                interval=candlesParams[3]
            )
        except Exception as irerror:
            print('\n\n', irerror.args, '\n')
            logging.error("Ошибка во время запроса котировок в методе core_bot.async_get_candles")
            raise irerror
        finally:
            #if mode_uid == 0:
            #    for candle in candles_raw:
            #        candles.append(candle)
            #else:
            if candles_raw:
                for candle in candles_raw.candles:
                    open = str(cast_money(candle.open))
                    close = str(cast_money(candle.close))
                    low = str(cast_money(candle.low))
                    high = str(cast_money(candle.high))

                    utc_time = candle.time  # Получаем дату и время в UTC
                    hour_msk = utc_time.hour + 3  # Переводим дату и время к Московскому часовому поясу
                    moscow_time = datetime(year=utc_time.year, month=utc_time.month, day=utc_time.day,
                                       hour=hour_msk, minute=utc_time.minute, second=utc_time.second)

                    time = moscow_time.strftime('%Y-%m-%d_%H:%M:%S')
                    volume = str(candle.volume)

                    # Добавляем строку в сырой датафрейм
                    updated_candles['open'].append(open)
                    updated_candles['close'].append(close)
                    updated_candles['low'].append(low)
                    updated_candles['high'].append(high)
                    updated_candles['time'].append(time)
                    updated_candles['volume'].append(volume)
                    candles.append(candle)

    return updated_candles


@bot.message_handler(commands=['get_candles'])
def save_candles(message):

    try:
        candles = get_candles(message.text)
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

        utc_time = candles[i].time        # Получаем дату и время в UTC
        hour_msk = utc_time.hour + 3      # Переводим дату и время к Московскому часовому поясу
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


@bot.message_handler(commands=['find_instrument'])
def find_instrument(message):
    words = message.text.split(' ')
    if not words or len(words) < 2:
        bot.send_message(message.chat.id, 'Неправильный формат команды')

    figi_name = words[-1]

    with SandboxClient(TOKEN) as client:
        #instrument_info = client.instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi_name)
        instruments_info = client.instruments.find_instrument(query=figi_name)

        for instrument in instruments_info.instruments:
            print(f"Info about instrument with name = {instrument.name}")
            print(f"FIGI = {instrument.figi}")
            print(f"ticker = {instrument.ticker}")
            print(f"isin = {instrument.isin}")
            print(f"postion_uid = {instrument.position_uid}")
            print(f"uid = {instrument.uid}")
            print(f"class_code = {instrument.class_code}")
            print("\n\n")

@bot.message_handler(commands=['currency'])
def get_currency(message):
    words = message.text.split(' ')
    if not words or len(words) < 2:
        raise ValueError('Неправильный формат команды')

    uid = words[-1]
    with SandboxClient(TOKEN) as client:
        currency = client.instruments.currency_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
                                                  id=uid)
        if currency:
            bot.send_message(message.chat.id, f"Валюта инструмента = {currency.name}")
        else:
            bot.send_message(message.chat.id, f"Валюта инструмента не найдена")

if __name__ == '__main__':
    #bot.infinity_polling()
    bot.polling(non_stop=True)