""" Пример работы со стримом """
import sys
import os
import time
import logging
import asyncio
from functools import cache
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

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

from sqlalchemy.exc import ProgrammingError

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)

from work.exceptions import *
from api import crud, models
from api.database import *
from config.program_config import ProgramConfiguration
from utils_funcs import utils_funcs

TOKEN = os.getenv("TINKOFF_TOKEN")

instrument_uid = list([])
timeframe_str = ''
timeframe = 0


def get_params_candle(candle: Candle):
    ''' Разбираем HistoricCandle на поля '''
    open = utils_funcs.cast_money(candle.open)
    close = utils_funcs.cast_money(candle.close)
    low = utils_funcs.cast_money(candle.low)
    high = utils_funcs.cast_money(candle.high)
    volume = candle.volume
    time = candle.time

    return (open, close, low, high, time, volume)


@utils_funcs.invest_api_retry()
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
    except ProgrammingError as e:
        logging.error(
            f"В функции get_candles_in_stream() в методе crud.create_candles() произошел сбой при параметрах:"+
            f"\ninstrument_uid={instrument_uid}, \nid_timeframe={my_timeframe_id}")
        logging.error(e.args)
    print("end of handle")

async def get_candles_in_stream(db, uid: str):
    global timeframe_str
    global timeframe

    def request_iterator(uid, timeframe):
        yield MarketDataRequest(
            subscribe_candles_request=SubscribeCandlesRequest(
                waiting_close=True,
                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                instruments=[
                    CandleInstrument(
                        instrument_id=uid,
                        interval=timeframe,
                    )
                ],
            )
        )
        while True:
            time.sleep(0.5)

    with SandboxClient(TOKEN) as client:
        for marketdata in client.market_data_stream.market_data_stream(
            request_iterator(uid, timeframe)
        ):
            if marketdata.candle:
                print(marketdata.candle)
                await handle_candle(db, marketdata.candle)
            print(marketdata)

def init_stream_data(config: ProgramConfiguration):
    global instrument_uid
    global timeframe_str

    try:
        tools_info = config.strategies
        for tool_info in tools_info.values():
            instrument_uid.append(tool_info['uid'])
        timeframe_str = config.timeframe
    except IndexError as e:
        logging.error('Не хватает строк в файле config.txt')
        raise IndexError('Не хватает строк в файле config.txt')


def analyze_interval():
    global timeframe
    global timeframe_str
    """ Сопоставление IndicatorInterval с строчным описанием интервала """
    timeframe = utils_funcs.get_sub_timeframe_by_name(timeframe_str)


async def init_stream():
    """
    Запуск стрима
    """
    global instrument_uid
    db = SessionLocal()

    tasks = list([])
    for uid in instrument_uid:
        task = asyncio.create_task(get_candles_in_stream(db, uid))
        tasks.append(task)
    await asyncio.gather(*tasks)

def setup_stream(config: ProgramConfiguration):
    """
    Инициализация и запуск стрима
    """
    init_stream_data(config)       # Получаем uid инструмента и таймфрейм торговли
    analyze_interval()       # Конвертируем таймфрейм из строки в SubscriptionInterval
    asyncio.run(init_stream()) # Запускаем получение данных в стриме
