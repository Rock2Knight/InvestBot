# Сам бот
import json
import logging
from typing import Union

from datetime import datetime, timedelta

from tinkoff.invest.schemas import InstrumentStatus, HistoricCandle
from tinkoff.invest.exceptions import RequestError

# Для исторических свечей

from work import core_bot
from work.functional import *
from work.exceptions import *
from app.StopMarketQueue import StopMarketQueue
from api import crud
from api.database import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='w')
UTC_OFFSET = "Europe/Moscow"


class InvestBot():
    """
    Класс, реализующий логику торгового робота в песочнице
    """


    def __init__(self, account_id: str):
        self.market_queue = StopMarketQueue()
        self.account_id = account_id

        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
        self.db = SessionLocal()

        self.init_db()


    def get_db(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
        create_db(self.engine)
        self.db = SessionLocal()
        try:
            yield self.db
        finally:
            self.db.close()


    def init_db(self):
        """ Заполнение базы данных"""
        if not self.db:
            raise Exception("Не указана база данных")

        instrument_list = crud.get_instrument_list(self.db)  # Достаем все записи из таблицы instrument
        if not instrument_list:                              # Если таблица instrument пуста, то выходим
            self.get_all_instruments()                # Заполняем список инструментов

    def check_get_all_instruments(self):
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
                json.dump(SharesDict, write_file)  # Dump python-dict to json

    def get_all_instruments(self):

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
                    json.dump(SharesDict, write_file)  # Dump python-dict to json

                ''' Проверка на наличие инструмента в базе данных. Если есть, переходим к следующему инструменту'''
                db_instrument = crud.get_active_by_name(self.db, active_name=instrument.name)
                if db_instrument:
                    continue

                ''' Вставка нового инструмента в таблицу '''

                '''Если в базе нет обозначения валюты инструмента, добавляем ее в базу'''
                id_cur = crud.get_curency_id(db=self.db, currency_name=instrument.currency)
                if not id_cur:
                    last_id = crud.get_last_currency_id(db=self.db)
                    last_id = last_id + 1 if last_id else 1
                    crud.create_currency(db=self.db, id=last_id, name=instrument.currency)
                    id_cur = crud.get_curency_id(db=self.db, currency_name=instrument.currency)

                '''Если в базе нет обозначения биржи инструмента, добавляем ее в базу'''
                id_exc = crud.get_exchange_id(db=self.db, exchange_name=instrument.exchange)
                if not id_exc:
                    last_id = crud.get_last_exchange_id(db=self.db)
                    last_id = last_id + 1 if last_id else 1
                    crud.create_exchange(db=self.db, id=last_id, name=instrument.exchange)
                    id_exc = crud.get_exchange_id(db=self.db, exchange_name=instrument.exchange)

                ''' Если в базе нет обозначения сектора, добавляем его в базу '''
                id_sec = crud.get_sector_id(db=self.db, sector_name=instrument.sector)
                if not id_sec:
                    last_id = crud.get_last_sector_id(db=self.db)
                    last_id = last_id + 1 if last_id else 1
                    crud.create_sector(db=self.db, id=last_id, name=instrument.sector)
                    id_sec = crud.get_sector_id(db=self.db, sector_name=instrument.sector)

                # Добавляем инструмент в таблицу
                crud.create_instrument(db=self.db, figi=instrument.figi, name=instrument.name,
                                       currency_id=id_cur, exchange_id=id_exc, sector_id=id_sec,
                                       ticker=instrument.ticker, lot=instrument.lot)


    def getDateNow(self):
        return datetime.now()

    def get_params_candle(self, candle: HistoricCandle):
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

    # Отладочный метод для проверки инструментов по бирже:
    def check_instruments(self, exchange_id: int):
        active_list = crud.get_actives_by_exchange(self.db, exchange_id=exchange_id)
        for instrument in active_list:
            print(instrument.figi, '  |   ', instrument.name)


    def check_last_candles(self):
        tool_figi = ''
        tool_timeframe = ''

        # Открываем файл с информацией о бумаге, по которой торгуем
        with open('config.txt', 'r') as config_file:
            tool_info = config_file.readlines()
            tool_figi = tool_info[0].split(' ')[-1] # Считываем FIGI бумаги
            tool_timeframe = tool_info[-1].split(' ')[-1] # Считываем таймфрейм бумаги

        # Если в имени FIGI есть символ переноса строки, то удаляем его
        if tool_figi[-1] == '\n':
            tool_figi = tool_figi[:-1]

        db_instrument = crud.get_active_by_figi(self.db, figi=tool_figi)
        if not db_instrument:
            raise ValueError(f"Не найден инструмент {tool_figi}")

        if not crud.check_timeframe(self.db, timeframe_name=tool_timeframe):
            raise ValueError(f"Не найден таймфрейм {tool_timeframe}")

        # Определяем id инструмента и таймфрейма
        id_figi = db_instrument.id
        id_timeframe = crud.get_timeframe_id(self.db, timeframe_name=tool_timeframe)

        # Запрашиваем 10 последних candles для инструмента
        candles = crud.get_candles_list(self.db, id_figi, id_timeframe)
        if not candles:
            return False
        else:
            last_candle = candles[-1]
            if last_candle.time_m - datetime.now() > timedelta(days=1):
                return False
            ''' Если нет свечей вообще, то запрашиваем 10 последних свечей за период '''
            #self.get_candles(db_instrument.figi, tool_timeframe, fill_db=True)  # Заполняем базу с нуля
        return True


    def load_candles(self, figi: str, timeframe: str, fill_db=True):
        candles = None  # Сырой массив свечей

        # Получаем границы времнного интервала для массива свечей
        cur_date = datetime.now()
        last_date = cur_date - timedelta(days=365)
        str_cur_date = cur_date.strftime("%Y-%m-%d_%H:%M:%S")
        str_last_date = last_date.strftime("%Y-%m-%d_%H:%M:%S")

        request_text = f"/get_candles {figi} {str_last_date} {str_cur_date} {timeframe}"  # Строка запроса на получение свечей

        try:
            candles = core_bot.get_candles(request_text)
        except InvestBotValueError as iverror:
            raise InvestBotValueError(iverror.msg)
        except RequestError as irerror:
            raise irerror

        ''' Обходим массив свечей и добавляем их в базу '''
        for candle in candles:
            open, close, low, high, time_obj, volume = self.get_params_candle(candle)
            str_time = datetime.strptime(time_obj, '%Y-%m-%d_%H:%M:%S')
            print(open, close, low, high, str_time, volume)

            new_id = crud.get_last_candle_id(self.db) + 1
            my_figi_id = crud.get_active_by_name(self.db, figi).id
            my_timeframe_id = crud.get_active_by_name(self.db, timeframe).id

            try:
                crud.create_candle(id=new_id, time_m=time_obj, volume=volume,
                                   open=open, close=close, low=low, high=high,
                                   id_figi=my_figi_id, id_timeframe=my_timeframe_id)
            except ValueError as vr:
                print(vr.msg)

        print("Data have been written")

    def check_have_candles(self, timeframe: str):
        """ Отладочный метод для проверки наличи данных по инструментам, которые есть в базе """
        if crud.get_last_active_id(self.db) == 0:
            print("В базе нет данных об инструментах")
            return None

        # Получаем границы времнного интервала для массива свечей
        cur_date = datetime.now()
        last_date = cur_date - timedelta(days=365*3)
        str_cur_date = cur_date.strftime("%Y-%m-%d_%H:%M:%S")
        str_last_date = last_date.strftime("%Y-%m-%d_%H:%M:%S")

        instruments = crud.get_filter_by_exchange_actives(self.db, exchange_id=list([1]))
        if not instruments:
            raise AttributeError("В базе нет данных об инструментах с переданным списком exchange_id")

        for instrument in instruments:
            db_model = crud.get_rezerve_active_by_figi(self.db, figi=instrument.figi)
            if db_model:
                continue

            print(instrument)
            request_text = f"/get_candles {instrument.figi} {str_last_date} {str_cur_date} {timeframe}"  # Строка запроса на получение свечей

            try:
                candles_figi = core_bot.get_candles(request_text)
            except Exception as irerror:
                print(irerror.args[0])
                continue

            have_data = False
            if len(candles_figi) > 10:
                have_data = True

            crud.create_instrument_rezerve(self.db, orig_instrument=instrument, is_data=have_data)


    def run(self):
        """ Главный цикл торгового робота """
        if not self.check_last_candles():
            self.load_candles(figi='TCS30A0DKVS5', timeframe='DAY')

        while True:
            print("Bot is working\n")