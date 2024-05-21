# Загрузчик информации об свечах
import sys
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from functools import cache
import numpy as np
import asyncio

from tinkoff.invest.schemas import HistoricCandle
from tinkoff.invest.exceptions import RequestError

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)
sys.path.append('.')

from work.exceptions import *
from api import crud, models
from api.database import *
from config import *
from utils_funcs import utils_funcs

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"


class CandlesLoader:

    def __init__(self, filename='../settings.ini'):
        self._file_path = filename  # Имя файла с конфигурацией
        config = program_config.ProgramConfiguration(filename)
        self.strategies = config.strategies
        self.uid = None              # Идентификатор инструмента
        self.timeframe = config.timeframe        # Таймфрейм проверяемого инструмента
        self.weight = None           # Доля инструмента в портфеле
        self._delay = 0              # Задержка между сделками


    def _init_delay(self):
        """ 
        Определяем задержку между сделками в секундах
        """
        match self.timeframe:
            case '1_MIN':
                self._delay = 60
            case '5_MIN':
                self._delay = 60 * 5
            case '15_MIN':
                self._delay = 60 * 15
            case 'HOUR':
                self._delay = 60 * 60
            case 'DAY':
                self._delay = 60 * 60 * 24
            case '2_MIN':
                self._delay = 60 * 2
            case '3_MIN':
                self._delay = 60 * 3
            case '10_MIN':
                self._delay = 60 * 10
            case '30_MIN':
                self._delay = 60 * 30
            case '2_HOUR':
                self._delay = 60 * 60 * 2
            case '4_HOUR':
                self._delay = 60 * 60 * 4
            case 'WEEK':
                self._delay = 60 * 60 * 24 * 7
            case 'MONTH':
                self._delay = 60 * 60 * 24 * 31


    @cache
    def __get_params_candle(self, candle: HistoricCandle):
        ''' Разбираем HistoricCandle на поля '''
        open = utils_funcs.cast_money(candle.open)
        close = utils_funcs.cast_money(candle.close)
        low = utils_funcs.cast_money(candle.low)
        high = utils_funcs.cast_money(candle.high)

        utc_time = candle.time  # Получаем дату и время в UTC
        hour_msk = utc_time.hour + 3  # Переводим дату и время к Московскому часовому поясу
        moscow_time = datetime(year=utc_time.year, month=utc_time.month, day=utc_time.day,
                               hour=hour_msk, minute=utc_time.minute, second=utc_time.second)

        time = moscow_time.strftime('%Y-%m-%d_%H:%M:%S')
        volume = candle.volume

        return (open, close, low, high, time, volume)


    @cache
    def get_lot(self, db, uid: str) -> int:
        # Метод для получения лотности инструмента (возможно стоит вынести в отдельный класс)
        instrument = crud.get_instrument(db, uid)
        return instrument.lot

    def _check_last_candles(self, db) -> dict:
        """
        Проверяет время загрузки последней свечи в базу
        """
        loaded_candles = dict()

        for ticker in self.strategies.keys():
            db_instrument = crud.get_instrument(db, instrument_uid=self.strategies[ticker]['uid'])
            if not db_instrument:
                logging.error(f"Не найден инструмент с uid = {self.strategies[ticker]['uid']}")
                raise ValueError(f"Не найден инструмент с uid = {self.strategies[ticker]['uid']}")

            if not crud.check_timeframe(db, timeframe_name=self.timeframe):
                crud.create_timeframe(db, id=None, name=self.timeframe)

            self.get_lot(db, self.strategies[ticker]['uid'])       # Получаем лотность инструмента (сделать метод приватным)

            # Определяем id инструмента и таймфрейма
            uid_instrument = db_instrument.uid
            id_timeframe = crud.get_timeframe_id(db, timeframe_name=self.timeframe)

            # Запрашиваем 10 последних candles для инструмента
            candles =  crud.get_candles_list(db, uid_instrument, id_timeframe)
            if not candles:
                # Свеч по данному инструменту в базе вообще нет
                #self._load_candles(db, uid_instrument)
                loaded_candles[uid_instrument] = None
            else:
                last_candle = candles[0]
                if abs(last_candle.time_m - datetime.now()) > timedelta(hours=2):   # Исправить
                    loaded_candles[uid_instrument] = last_candle.time_m # Возврат времени последней свечи, если она есть и при этом разница между текущим временем значительная
        return loaded_candles   # Возврат словаря с идентификаторами инструментов, для которых надо подгрузить данные


    async def _load_candles(self, db, uid, last_date=None):
        """
        Метод для загрузки свечей по инструменту

        :param last_date: начальное время для запроса
        """

        candles = None  # Сырой массив свечей

        # Получаем границы времнного интервала для массива свечей
        cur_date = datetime.now()
        if not last_date:
            last_date = cur_date - timedelta(minutes=60*24)

        str_cur_date = cur_date.strftime("%Y-%m-%d_%H:%M:%S")
        str_last_date = last_date.strftime("%Y-%m-%d_%H:%M:%S")

        request_text = f"/get_candles {uid} {str_last_date} {str_cur_date} {self.timeframe}"  # Строка запроса на получение свечей

        try:
            candles = utils_funcs.get_candles(request_text)
        except InvestBotValueError as iverror:
            logging.error(f"Ошибка в методе CandlesLoader.load_candles во время обработки котировок: {iverror.args}")
            raise InvestBotValueError(iverror.msg)
        except RequestError as irerror:
            logging.error("Ошибка в методе CandlesLoader.load_candles во время выгрузки котировок на стороне сервера")
            raise irerror

        ''' Обходим массив свечей и добавляем их в базу '''
        for candle in candles:
            open, close, low, high, time_obj, volume = self.__get_params_candle(candle)
            str_time = datetime.strptime(time_obj, '%Y-%m-%d_%H:%M:%S')

            new_id = crud.get_last_candle_id(db) + 1
            my_instrument = crud.get_instrument(db, instrument_uid=uid)
            my_timeframe_id = crud.get_timeframe_id(db, self.timeframe)
            if not my_timeframe_id:
                crud.create_timeframe(db, name=self.timeframe)
                my_timeframe_id =  crud.get_timeframe_id(db, self.timeframe)
                my_timeframe_id = my_timeframe_id.id

            try:
                 crud.create_candle(db, id=new_id, time_m=time_obj, volume=volume,
                                   open=open, close=close, low=low, high=high,
                                   uid_instrument=my_instrument.uid, id_timeframe=my_timeframe_id)
            except ValueError as vr:
                logging.error(f"В методе InvestBot.load_candles() в метод await crud.create_candles() передан неверный аргумент передан")
                print(vr.args)