# Загрузчик информации об свечах
import logging
from datetime import datetime, timedelta
from functools import cache
import numpy as np

from tinkoff.invest.schemas import HistoricCandle
from tinkoff.invest.exceptions import RequestError

from work import *
from work.functional import *
from work.exceptions import *
from api import crud, models
from api.database import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"


class CandlesLoader:

    def __init__(self, filename='config.txt'):
        self._file_path = filename  # Имя файла с конфигурацией
        self.uid = None              # Идентификатор инструмента
        self.timeframe = None        # Таймфрейм проверяемого инструмента
        self.weight = None           # Доля инструмента в портфеле
        self._lot = None             # Лотность инструмента
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


    @staticmethod
    def get_instrument_info(filename: str):
        res_array = np.empty((3,), dtype='<U100')
        tool_info = list([])

        # Открываем файл с информацией о бумаге, по которой торгуем
        with open(filename, 'r') as config_file:
            tool_info = config_file.readlines()

        try:
            res_array[0] = tool_info[2].rstrip('\n').split(' ')[-1]  # uid
            res_array[1] = tool_info[5].rstrip('\n').split(' ')[-1]  # timeframe
            res_array[2] = tool_info[6].rstrip('\n').split(' ')[-1]  # weight
        except IndexError as e:
            logging.error('Не хватает строк в файле config.txt')
            raise IndexError('Не хватает строк в файле config.txt')

        return res_array


    @cache
    def __get_params_candle(self, candle: HistoricCandle):
        ''' Разбираем HistoricCandle на поля '''
        open = cast_money(candle.open)
        close = cast_money(candle.close)
        low = cast_money(candle.low)
        high = cast_money(candle.high)

        utc_time = candle.time  # Получаем дату и время в UTC
        hour_msk = utc_time.hour + 3  # Переводим дату и время к Московскому часовому поясу
        moscow_time = datetime(year=utc_time.year, month=utc_time.month, day=utc_time.day,
                               hour=hour_msk, minute=utc_time.minute, second=utc_time.second)

        time = moscow_time.strftime('%Y-%m-%d_%H:%M:%S')
        volume = candle.volume

        return (open, close, low, high, time, volume)


    def _get_lot(self, db):
        # Метод для получения лотности инструмента (возможно стоит вынести в отдельный класс)
        instrument = crud.get_instrument(db, self.uid)
        self._lot = instrument.lot

    def _check_last_candles(self, db) -> int | datetime:
        """
        Проверяет время загрузки последней свечи в базу
        """
        tool_info = CandlesLoader.get_instrument_info(self._file_path) # Получаем информацию об инструменте

        db_instrument = crud.get_instrument(db, instrument_uid=tool_info[0])
        if not db_instrument:
            logging.error(f"Не найден инструмент с uid = {tool_info[0]}")
            raise ValueError(f"Не найден инструмент с uid = {tool_info[0]}")

        if not crud.check_timeframe(db, timeframe_name=tool_info[2]):
            crud.create_timeframe(db, id=None, name=tool_info[2])

        self.uid = tool_info[0]
        self.timeframe = tool_info[1]
        self.weight = tool_info[2]
        self._get_lot(db)       # Получаем лотность инструмента (сделать метод приватным)

        # Определяем id инструмента и таймфрейма
        uid_instrument = db_instrument.uid
        id_timeframe = crud.get_timeframe_id(db, timeframe_name=self.timeframe)

        # Запрашиваем 10 последних candles для инструмента
        candles =  crud.get_candles_list(db, uid_instrument, id_timeframe)
        if not candles:
            # Свеч по данному инструменту в базе вообще нет
            self._load_candles(db)
            return 1   # Возврат 1 в случае начальной подгрузки свечей
        else:
            last_candle = candles[0]
            if abs(last_candle.time_m - datetime.now()) > timedelta(hours=2):   # Исправить
                return last_candle.time_m  # Возврат времени последней свечи, если она есть и при этом разница между текущим временем значительная
        return 1   # Возврат 1 в случае, если все нормально


    def _load_candles(self, db, last_date=None):
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

        request_text = f"/get_candles {self.uid} {str_last_date} {str_cur_date} {self.timeframe}"  # Строка запроса на получение свечей

        try:
            candles = core_bot.get_candles(request_text)
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
            my_instrument = crud.get_instrument(db, instrument_uid=self.uid)
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