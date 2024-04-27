""" Пример работы со стримом """
import os
import time
import logging
import asyncio
from functools import cache
from datetime import datetime, timezone, timedelta

import numpy as np

from tinkoff.invest import (
    CandleInstrument,
    Client,
    MarketDataRequest,
    SubscribeCandlesRequest,
    SubscriptionAction,
    SubscriptionInterval,
    Candle
)
from tinkoff.invest.schemas import IndicatorInterval
from tinkoff.invest.sandbox.client import SandboxClient

from work import *
from work.functional import *
from work.exceptions import *
from api import crud, models
from api.database import *

TOKEN = os.getenv("TINKOFF_TOKEN")

instrument_uid = ''
timeframe_str = ''
timeframe = 0


def get_params_candle(candle: Candle):
    ''' Разбираем HistoricCandle на поля '''
    open = cast_money(candle.open)
    close = cast_money(candle.close)
    low = cast_money(candle.low)
    high = cast_money(candle.high)
    volume = candle.volume
    time = candle.time

    return (open, close, low, high, time, volume)


async def handle_candle(db, data_candle):
    print("begin of handle")
    open, close, low, high, time, volume = get_params_candle(data_candle)
    my_timeframe_id = crud.get_timeframe_id(db, timeframe_str)
    if not my_timeframe_id:
        crud.create_timeframe(db, name=timeframe_str)
        my_timeframe_id = crud.get_timeframe_id(db, timeframe_str)
        my_timeframe_id = my_timeframe_id.id

    try:
        crud.create_candle(db, time_m=time, volume=volume,
                           open=open, close=close, low=low, high=high,
                           uid_instrument=instrument_uid, id_timeframe=my_timeframe_id)
        print(data_candle)
    except ValueError as vr:
        logging.error(
            f"В функции get_candles_in_stream() в методе crud.create_candles() передан неверный аргумент передан")
        print(vr.args)
    print("end of handle")

async def get_candles_in_stream():
    global instrument_uid
    global timeframe_str
    global timeframe
    db = SessionLocal()

    def request_iterator(instrument_uid, timeframe):
        yield MarketDataRequest(
            subscribe_candles_request=SubscribeCandlesRequest(
                waiting_close=True,
                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                instruments=[
                    CandleInstrument(
                        instrument_id=instrument_uid,
                        interval=timeframe,
                    )
                ],
            )
        )
        while True:
            time.sleep(0.5)

    with SandboxClient(TOKEN) as client:
        for marketdata in client.market_data_stream.market_data_stream(
            request_iterator(instrument_uid, timeframe)
        ):
            if marketdata.candle:
                print(marketdata.candle)
                await handle_candle(db, marketdata.candle)

def init_stream_data():
    global instrument_uid
    global timeframe_str

    res_array = np.empty((6,), dtype='<U100')
    tool_info = list([])
    # Открываем файл с информацией о бумаге, по которой торгуем
    with open('config.txt', 'r') as config_file:
        tool_info = config_file.readlines()

    try:
        res_array[0] = tool_info[0].split(' ')[-1]  # uid
        if res_array[0][-1] == '\n':
            res_array[0] = res_array[0][:-1]
        res_array[1] = tool_info[1].split(' ')[-1]  # position_uid
        if res_array[1][-1] == '\n':
            res_array[1] = res_array[1][:-1]
        res_array[2] = tool_info[2].split(' ')[-1]  # figi
        if res_array[2][-1] == '\n':
            res_array[2] = res_array[2][:-1]
        res_array[3] = tool_info[3].split(' ')[-1]  # class_code
        if res_array[3][-1] == '\n':
            res_array[3] = res_array[3][:-1]
        res_array[4] = tool_info[4].split(' ')[-1]  # ticker
        if res_array[4][-1] == '\n':
            res_array[4] = res_array[4][:-1]
        res_array[5] = tool_info[5].split(' ')[-1]  # timeframe
        if res_array[5][-1] == '\n':
            res_array[5] = res_array[5][:-1]
    except IndexError as e:
        logging.error('Не хватает строк в файле config.txt')
        raise IndexError('Не хватает строк в файле config.txt')

    instrument_uid = res_array[0]
    timeframe_str = res_array[5]


def analyze_interval():
    global timeframe
    global timeframe_str
    """ Сопоставление IndicatorInterval с строчным описанием интервала """
    match timeframe_str:
        case '1_MIN':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
        case '2_MIN':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_2_MIN
        case '5_MIN':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIVE_MINUTES
        case '10_MIN':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_10_MIN
        case '15_MIN':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIFTEEN_MINUTES
        case '30_MIN':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_30_MIN
        case 'HOUR':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_HOUR
        case '2_HOUR':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_2_HOUR
        case '4_HOUR':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_4_HOUR
        case 'DAY':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_DAY
        case 'WEEK':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_WEEK
        case 'MONTH':
            timeframe = SubscriptionInterval.SUBSCRIPTION_INTERVAL_MONTH


def setup_stream():
    init_stream_data()       # Получаем uid инструмента и таймфрейм торговли
    analyze_interval()       # Конвертируем таймфрейм из строки в SubscriptionInterval
    asyncio.run(get_candles_in_stream()) # Запускаем получение данных в стриме