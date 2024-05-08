# Сам бот
import os
import logging
import asyncio
import math
from enum import Enum
import multiprocessing as mp
import csv

import time
from datetime import datetime, timedelta, timezone
from functools import cache
import numpy as np
import psutil

from tinkoff.invest.schemas import (
    InstrumentStatus,
    HistoricCandle,
    AssetType,
    InstrumentType,
    InstrumentIdType,
    CandleInterval,
    AssetRequest,
    OrderDirection,
    OrderType,
    PriceType,
    PostOrderResponse,
    TechAnalysisItem
)
from tinkoff.invest.exceptions import RequestError

import app.technical_indicators
# Для исторических свечей

import stream_client
from work import *
from work.functional import *
from work.exceptions import *
from work.functional import reverse_money, reverse_money_mv
from app.StopMarketQueue import StopMarketQueue
from api import crud, models
from api.database import *
from technical_indicators import *
from app import PROCESS_SWITCH

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"
MAXInter = 5

class DirectTrade(Enum):
    UNSPECIFIED = 0,
    BUY = 1,
    SELL = 2


class InvestBot():
    """
    Класс, реализующий логику торгового робота в песочнице
    """


    def __init__(self, account_id: str, correct_sum=False, cor_sum_value=0, filename='config.txt', autofill=True):
        self.market_queue = StopMarketQueue()
        self.account_id = account_id
        self.uid = None
        self.timeframe = None
        self.direct_trade = DirectTrade.UNSPECIFIED    # Направление сделки (купить/продать)
        self.lot = 0
        self.profit = 0                                # Прибыль портфеля в процентах
        self.delay = 0                                 # Задержка для совершения сделок
        self.trades_list = dict()                      # Журнал сделок
        self.buy_cast_list = list([])                  # Список пар "цена покупки"-"количество лотов"
        self.__cor_sum = correct_sum
        self.__cor_sum_val = cor_sum_value             # Сумма для пополнения
        self.__last_prices = list([])                  # Список последних цен покупки
        #self.event_loop = asyncio.new_event_loop()
        self.file_path = filename
        tool_info = InvestBot.get_instrument_info(self.file_path)  # Получаем информацию об инструменте
        self.timeframe = tool_info[5]
        self.__stream_process = mp.Process(target=stream_client.setup_stream, args=[self.file_path])  # Процесс загрузки данных через Stream
        self.__init_delay()

        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
        self.db = SessionLocal()

        if autofill:
            self.init_db()


    def get_db(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
        create_db(self.engine)
        self.db = SessionLocal()
        try:
            yield self.db
        finally:
            self.db.close()


    def init_db(self, fill=True):
        """ Заполнение базы данных"""
        if not self.db:
            logging.error("Не указана база данных")
            raise Exception("Не указана база данных")

        instrument_list =  crud.get_instrument_list(self.db)  # Достаем все записи из таблицы instrument
        if not instrument_list or fill:                              # Если таблица instrument пуста, то выходим
             self.get_all_instruments()                # Заполняем список инструментов


    def __init_delay(self):
        """ Определяем задержку между сделками в секундах """
        match self.timeframe:
            case '1_MIN':
                self.delay = 60
            case '5_MIN':
                self.delay = 60 * 5
            case '15_MIN':
                self.delay = 60 * 15
            case 'HOUR':
                self.delay = 60 * 60
            case 'DAY':
                self.delay = 60 * 60 * 24
            case '2_MIN':
                self.delay = 60 * 2
            case '3_MIN':
                self.delay = 60 * 3
            case '10_MIN':
                self.delay = 60 * 10
            case '30_MIN':
                self.delay = 60 * 30
            case '2_HOUR':
                self.delay = 60 * 60 * 2
            case '4_HOUR':
                self.delay = 60 * 60 * 4
            case 'WEEK':
                self.delay = 60 * 60 * 24 * 7
            case 'MONTH':
                self.delay = 60 * 60 * 24 * 31


    @cache
    def get_str_type(self, value, is_asset=True):
        if is_asset:
            match value:
                case AssetType.ASSET_TYPE_UNSPECIFIED:
                    return "UNSPECIFIED"
                case AssetType.ASSET_TYPE_COMMODITY:
                    return "COMMODITY"
                case AssetType.ASSET_TYPE_CURRENCY:
                    return "CURRENCY"
                case AssetType.ASSET_TYPE_INDEX:
                    return "INDEX"
                case AssetType.ASSET_TYPE_SECURITY:
                    return "SECURITY"
        else:
            match value:
                case InstrumentType.INSTRUMENT_TYPE_SHARE:
                    return "SHARE"
                case InstrumentType.INSTRUMENT_TYPE_BOND:
                    return "BOND"
                case InstrumentType.INSTRUMENT_TYPE_ETF:
                    return "ETF"
                case InstrumentType.INSTRUMENT_TYPE_SP:
                    return "SP"


    @cache
    def get_timeframe_by_name(self, value):
        match value:
            case 'UNSPECIFIED':
                return CandleInterval.CANDLE_INTERVAL_UNSPECIFIED
            case '1_MIN':
                return CandleInterval.CANDLE_INTERVAL_1_MIN
            case '5_MIN':
                return CandleInterval.CANDLE_INTERVAL_5_MIN
            case '15_MIN':
                return CandleInterval.CANDLE_INTERVAL_15_MIN
            case 'HOUR':
                return CandleInterval.CANDLE_INTERVAL_HOUR
            case 'DAY':
                return CandleInterval.CANDLE_INTERVAL_DAY
            case '2_MIN':
                return CandleInterval.CANDLE_INTERVAL_2_MIN
            case '3_MIN':
                return CandleInterval.CANDLE_INTERVAL_3_MIN
            case '10_MIN':
                return CandleInterval.CANDLE_INTERVAL_10_MIN
            case '30_MIN':
                return CandleInterval.CANDLE_INTERVAL_30_MIN
            case '2_HOUR':
                return CandleInterval.CANDLE_INTERVAL_2_HOUR
            case '4_HOUR':
                return CandleInterval.CANDLE_INTERVAL_4_HOUR
            case 'WEEK':
                return CandleInterval.CANDLE_INTERVAL_WEEK
            case 'MONTH':
                return CandleInterval.CANDLE_INTERVAL_MONTH

    @cache
    def get_name_by_timeframe(self, frame):
        match frame:
            case CandleInterval.CANDLE_INTERVAL_UNSPECIFIED:
                return 'UNSPECIFIED'
            case CandleInterval.CANDLE_INTERVAL_1_MIN:
                return '1_MIN'
            case CandleInterval.CANDLE_INTERVAL_5_MIN:
                return '5_MIN'
            case CandleInterval.CANDLE_INTERVAL_15_MIN:
                return '15_MIN'
            case CandleInterval.CANDLE_INTERVAL_HOUR:
                return 'HOUR'
            case CandleInterval.CANDLE_INTERVAL_DAY:
                return 'DAY'
            case CandleInterval.CANDLE_INTERVAL_2_MIN:
                return '2_MIN'
            case CandleInterval.CANDLE_INTERVAL_3_MIN:
                return "3_MIN"
            case CandleInterval.CANDLE_INTERVAL_10_MIN:
                return '10_MIN'
            case CandleInterval.CANDLE_INTERVAL_30_MIN:
                return '30_MIN'
            case CandleInterval.CANDLE_INTERVAL_2_HOUR:
                return '2_HOUR'
            case CandleInterval.CANDLE_INTERVAL_4_HOUR:
                return '4_HOUR'
            case CandleInterval.CANDLE_INTERVAL_WEEK:
                return 'WEEK'
            case CandleInterval.CANDLE_INTERVAL_MONTH:
                return 'MONTH'


    def get_all_instruments(self):

        with SandboxClient(TOKEN) as client:  # Запускаем клиент тинькофф-песочницы
            response = client.instruments.get_assets()  # Получаем список всех активов

            for asset in response.assets:

                """ Проверка на наличие актива в базе данных. Если есть, переходим к следующему активу """
                db_asset = crud.get_asset(self.db, asset_uid=asset.uid)
                if db_asset:
                    for instrument in asset.instruments:
                        currency_name = None
                        sector_name = None
                        exchange_name = None
                        instrument_name = None
                        lot = 1

                        # Находим подробную информацию об инструменте, по типу инструмента
                        match instrument.instrument_kind:
                            case InstrumentType.INSTRUMENT_TYPE_SHARE:
                                shareResp = None
                                try:
                                    shareResp = client.instruments.share_by(
                                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                        id=instrument.ticker,
                                        class_code=instrument.class_code)
                                except Exception as e:
                                    if isinstance(e, RequestError):
                                        logging.error("Ошбика во время запроса данных об акции на стороне сервера\n")
                                        continue
                                    else:
                                        logging.error("Неправильно указаны параметры запроса\n")
                                        raise e

                                if shareResp:
                                    currency_name = shareResp.instrument.currency
                                    sector_name = shareResp.instrument.sector
                                    exchange_name = shareResp.instrument.exchange
                                    lot = shareResp.instrument.lot
                                    instrument_name = shareResp.instrument.name
                                else:
                                    # Иначе ставим неопределенное значения
                                    currency_name = "undefined"
                                    sector_name = "undefined"
                                    exchange_name = "undefined"
                            case InstrumentType.INSTRUMENT_TYPE_BOND:
                                bondResp = None
                                try:
                                    bondResp = client.instruments.bond_by(
                                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                        id=instrument.ticker,
                                        class_code=instrument.class_code)
                                except Exception as e:
                                    if isinstance(e, RequestError):
                                        logging.error(
                                            "Ошбика во время запроса данных об облигации на стороне сервера\n")
                                        continue
                                    else:
                                        logging.error("Неправильно указаны параметры запроса\n")
                                        raise e

                                if bondResp:
                                    currency_name = bondResp.instrument.currency
                                    sector_name = bondResp.instrument.sector
                                    exchange_name = bondResp.instrument.exchange
                                    lot = bondResp.instrument.lot
                                    instrument_name = bondResp.instrument.name
                                else:
                                    # Иначе ставим неопределенное значения
                                    currency_name = "undefined"
                                    sector_name = "undefined"
                                    exchange_name = "undefined"
                            case InstrumentType.INSTRUMENT_TYPE_ETF:
                                etfResp = None
                                try:
                                    etfResp = client.instruments.etf_by(
                                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                        id=instrument.ticker,
                                        class_code=instrument.class_code)
                                except Exception as e:
                                    if isinstance(e, RequestError):
                                        logging.error("Ошбика во время запроса данных об ETF на стороне сервера\n")
                                        continue
                                    else:
                                        logging.error("Неправильно указаны параметры запроса\n")
                                        raise e

                                if etfResp:
                                    currency_name = etfResp.instrument.currency
                                    sector_name = etfResp.instrument.sector
                                    exchange_name = etfResp.instrument.exchange
                                    lot = etfResp.instrument.lot
                                    instrument_name = etfResp.instrument.name
                                else:
                                    # Иначе ставим неопределенное значения
                                    currency_name = "undefined"
                                    sector_name = "undefined"
                                    exchange_name = "undefined"
                            case _:
                                # Иначе ставим неопределенное значения
                                logging.warning("Неопределенное значение типа торгового инструмента")
                                currency_name = "undefined"
                                sector_name = "undefined"
                                exchange_name = "undefined"

                        ''' Проверка на наличие инструмента в базе данных. Если есть, переходим к следующему инструменту'''
                        db_instrument =  crud.get_instrument_by_name(self.db, instrument_name=instrument_name)
                        if db_instrument:
                            continue

                        ''' Вставка нового инструмента в таблицу '''

                        '''Если в базе нет обозначения валюты инструмента, добавляем ее в базу'''
                        id_cur =  crud.get_currency_id(db=self.db, currency_name=currency_name)
                        if not id_cur:
                            last_id =  crud.get_last_currency_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_currency(db=self.db, id=last_id, name=currency_name)
                            id_cur =  crud.get_currency_id(db=self.db, currency_name=currency_name)

                        '''Если в базе нет обозначения биржи инструмента, добавляем ее в базу'''
                        id_exc =  crud.get_exchange_id(db=self.db, exchange_name=exchange_name)
                        if not id_exc:
                            last_id =  crud.get_last_exchange_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_exchange(db=self.db, id=last_id, name=exchange_name)
                            id_exc =  crud.get_exchange_id(db=self.db, exchange_name=exchange_name)

                        ''' Если в базе нет обозначения сектора, добавляем его в базу '''
                        id_sec =  crud.get_sector_id(db=self.db, sector_name=sector_name)
                        if not id_sec:
                            last_id =  crud.get_last_sector_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_sector(db=self.db, id=last_id, name=sector_name)
                            id_sec =  crud.get_sector_id(db=self.db, sector_name=sector_name)

                        ''' Если в базе нет обозначения типа инструмента, добавляем его в базу '''
                        str_instr_type = self.get_str_type(instrument.instrument_kind, False)
                        id_instr_type =  crud.get_instrument_type_name(db=self.db, instrument_type_name=str_instr_type)
                        if not id_instr_type:
                            last_id =  crud.get_last_instrument_type_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_instrument_type(db=self.db, id=last_id, name=str_instr_type)
                            id_instr_type =  crud.get_instrument_type_name(db=self.db,
                                                                          instrument_type_name=str_instr_type)
                            id_instr_type = id_instr_type.id
                        elif isinstance(id_instr_type, models.InstrumentType):
                            id_instr_type = id_instr_type.id

                        """ Если в базе нет обозначения актива инструмента, добавляем его в базу """
                        uid_asset =  crud.get_asset_uid(db=self.db, asset_uid=asset.uid)
                        if not uid_asset:
                            crud.create_asset(db=self.db, uid=asset.uid, name=asset.name)
                            uid_asset =  crud.get_asset_uid(db=self.db, asset_uid=asset.uid)
                            uid_asset = uid_asset.uid
                        elif isinstance(uid_asset, models.Asset):
                            uid_asset = uid_asset.uid

                        # (1) Отладочная часть для проверки наличия нужных инструментов
                        if asset.uid == "bfc8184d-9562-4ea2-87dd-be6e76dc1279":
                            with open("info_file.txt", 'w', encoding='utf-8') as w_file:
                                text = "\n\nЭто активы Газпрома\n"
                                w_file.write(text)
                                if len(asset.instruments) == 0:
                                    w_file.write(f"Нет инструментов, принадлежащих {asset.name}")
                                for instrument in asset.instruments:
                                    w_file.write("lol\n")
                                    w_file.write(instrument.uid + '\n')
                                db_asset = crud.get_asset(self.db, asset_uid=asset.uid)
                                if db_asset:
                                    w_file.write(f'\n{db_asset.uid}')
                                    w_file.write(f'\n{db_asset.name}')

                        # Добавляем инструмент в таблицу
                        crud.create_instrument(db=self.db, figi=instrument.figi, name=instrument_name,
                                               uid=instrument.uid, position_uid=instrument.position_uid,
                                               currency_id=id_cur, exchange_id=id_exc, sector_id=id_sec,
                                               type_id=id_instr_type, asset_uid=uid_asset,
                                               ticker=instrument.ticker, lot=lot,
                                               class_code=instrument.class_code)
                    continue

                """ Проверка на наличие типа актива в БД """
                str_asset_type = self.get_str_type(asset.type, True)
                db_asset_type_id =  crud.get_asset_type_name(self.db, asset_type_name=str_asset_type)
                if not db_asset_type_id:
                    last_id =  crud.get_last_asset_type_id(self.db)
                    last_id = last_id + 1 if last_id else 1
                    db_asset_type_id =  crud.create_asset_type(self.db, id=last_id, name=str_asset_type)
                    db_asset_type_id = db_asset_type_id
                else:
                    db_asset_type_id = db_asset_type_id.id

                # Добавляем актив в БД
                crud.create_asset(self.db, uid=asset.uid,
                                  name=asset.name,
                                  type_id=db_asset_type_id)

                # Собираем в словарь все инструменты, входящие в актив
                for instrument in asset.instruments:

                    currency_name = None
                    sector_name = None
                    exchange_name = None
                    instrument_name = None
                    lot = 1

                    # Находим подробную информацию об инструменте, по типу инструмента
                    match instrument.instrument_kind:
                        case InstrumentType.INSTRUMENT_TYPE_SHARE:
                            shareResp = None
                            try:
                                shareResp = client.instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                                    id=instrument.ticker,
                                                                    class_code=instrument.class_code)
                            except Exception as e:
                                if isinstance(e, RequestError):
                                    logging.error("Ошбика во время запроса данных об акции на стороне сервера\n")
                                    continue
                                else:
                                    logging.error("Неправильно указаны параметры запроса\n")
                                    raise e

                            if shareResp:
                                currency_name = shareResp.instrument.currency
                                sector_name = shareResp.instrument.sector
                                exchange_name = shareResp.instrument.exchange
                                lot = shareResp.instrument.lot
                                instrument_name = shareResp.instrument.name
                            else:
                                # Иначе ставим неопределенное значения
                                currency_name = "undefined"
                                sector_name = "undefined"
                                exchange_name = "undefined"
                        case InstrumentType.INSTRUMENT_TYPE_BOND:
                            bondResp = None
                            try:
                                bondResp = client.instruments.bond_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                                  id=instrument.ticker,
                                                                  class_code=instrument.class_code)
                            except Exception as e:
                                if isinstance(e, RequestError):
                                    logging.error("Ошбика во время запроса данных об облигации на стороне сервера\n")
                                    continue
                                else:
                                    logging.error("Неправильно указаны параметры запроса\n")
                                    raise e

                            if bondResp:
                                currency_name = bondResp.instrument.currency
                                sector_name = bondResp.instrument.sector
                                exchange_name = bondResp.instrument.exchange
                                lot = bondResp.instrument.lot
                                instrument_name = bondResp.instrument.name
                            else:
                                # Иначе ставим неопределенное значения
                                currency_name = "undefined"
                                sector_name = "undefined"
                                exchange_name = "undefined"
                        case InstrumentType.INSTRUMENT_TYPE_ETF:
                            etfResp = None
                            try:
                                etfResp = client.instruments.etf_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                                id=instrument.ticker,
                                                                class_code=instrument.class_code)
                            except Exception as e:
                                if isinstance(e, RequestError):
                                    logging.error("Ошбика во время запроса данных об ETF на стороне сервера\n")
                                    continue
                                else:
                                    logging.error("Неправильно указаны параметры запроса\n")
                                    raise e

                            if etfResp:
                                currency_name = etfResp.instrument.currency
                                sector_name = etfResp.instrument.sector
                                exchange_name = etfResp.instrument.exchange
                                lot = etfResp.instrument.lot
                                instrument_name = etfResp.instrument.name
                            else:
                                # Иначе ставим неопределенное значения
                                currency_name = "undefined"
                                sector_name = "undefined"
                                exchange_name = "undefined"
                        case _:
                            # Иначе ставим неопределенное значения
                            logging.warning("Неопределенное значение типа торгового инструмента")
                            currency_name = "undefined"
                            sector_name = "undefined"
                            exchange_name = "undefined"

                    ''' Проверка на наличие инструмента в базе данных. Если есть, переходим к следующему инструменту'''
                    db_instrument =  crud.get_instrument_by_name(self.db, instrument_name=instrument_name)
                    if db_instrument:
                        continue

                    ''' Вставка нового инструмента в таблицу '''


                    '''Если в базе нет обозначения валюты инструмента, добавляем ее в базу'''
                    id_cur =  crud.get_currency_id(db=self.db, currency_name=currency_name)
                    if not id_cur:
                        last_id =  crud.get_last_currency_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_currency(db=self.db, id=last_id, name=currency_name)
                        id_cur =  crud.get_currency_id(db=self.db, currency_name=currency_name)

                    '''Если в базе нет обозначения биржи инструмента, добавляем ее в базу'''
                    id_exc =  crud.get_exchange_id(db=self.db, exchange_name=exchange_name)
                    if not id_exc:
                        last_id =  crud.get_last_exchange_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_exchange(db=self.db, id=last_id, name=exchange_name)
                        id_exc =  crud.get_exchange_id(db=self.db, exchange_name=exchange_name)

                    ''' Если в базе нет обозначения сектора, добавляем его в базу '''
                    id_sec =  crud.get_sector_id(db=self.db, sector_name=sector_name)
                    if not id_sec:
                        last_id =  crud.get_last_sector_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_sector(db=self.db, id=last_id, name=sector_name)
                        id_sec =  crud.get_sector_id(db=self.db, sector_name=sector_name)

                    ''' Если в базе нет обозначения типа инструмента, добавляем его в базу '''
                    str_instr_type = self.get_str_type(instrument.instrument_kind, False)
                    id_instr_type =  crud.get_instrument_type_name(db=self.db, instrument_type_name=str_instr_type)
                    if not id_instr_type:
                        last_id =  crud.get_last_instrument_type_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_instrument_type(db=self.db, id=last_id, name=str_instr_type)
                        id_instr_type =  crud.get_instrument_type_name(db=self.db, instrument_type_name=str_instr_type)
                        id_instr_type = id_instr_type.id
                    elif isinstance(id_instr_type, models.InstrumentType):
                        id_instr_type = id_instr_type.id

                    """ Если в базе нет обозначения актива инструмента, добавляем его в базу """
                    uid_asset =  crud.get_asset_uid(db=self.db, asset_uid=asset.uid)
                    if not uid_asset:
                        crud.create_asset(db=self.db, uid=asset.uid, name=asset.name)
                        uid_asset =  crud.get_asset_uid(db=self.db, asset_uid=asset.uid)
                        uid_asset = uid_asset.uid
                    elif isinstance(uid_asset, models.Asset):
                        uid_asset = uid_asset.uid

                    # (1) Отладочная часть для проверки наличия нужных инструментов
                    if asset.uid == "bfc8184d-9562-4ea2-87dd-be6e76dc1279":
                        with open("info_file.txt", 'w', encoding='utf-8') as w_file:
                            text = "\n\nЭто активы Газпрома\n"
                            w_file.write(text)
                            if len(asset.instruments) == 0:
                                w_file.write(f"Нет инструментов, принадлежащих {asset.name}")
                            for instrument in asset.instruments:
                                w_file.write("lol\n")
                                w_file.write(instrument.uid + '\n')
                            db_asset = crud.get_asset(self.db, asset_uid=asset.uid)
                            if db_asset:
                                w_file.write(f'\n{db_asset.uid}')
                                w_file.write(f'\n{db_asset.name}')

                    # Добавляем инструмент в таблицу
                    crud.create_instrument(db=self.db, figi=instrument.figi, name=instrument_name,
                                           uid=instrument.uid, position_uid=instrument.position_uid,
                                           currency_id=id_cur, exchange_id=id_exc, sector_id=id_sec,
                                           type_id=id_instr_type, asset_uid=uid_asset,
                                           ticker=instrument.ticker, lot=lot,
                                           class_code=instrument.class_code)

        print('\nAssets and instruments are successfully loaded!\n\n')


    def getDateNow(self):
        return datetime.now()

    @cache
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
        active_list =  crud.get_actives_by_exchange(self.db, exchange_id=exchange_id)
        for instrument in active_list:
            print(instrument.figi, '  |   ', instrument.name)

    """ Метод для получения информации об отслеживаемом инструменте """
    @staticmethod
    def get_instrument_info(filename: str):
        res_array = np.empty((6,), dtype='<U100')
        tool_info = list([])
        # Открываем файл с информацией о бумаге, по которой торгуем
        with open(filename, 'r') as config_file:
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

        return res_array


    def check_last_candles(self):
        tool_info = InvestBot.get_instrument_info(self.file_path) # Получаем информацию об инструменте

        db_instrument = crud.get_instrument(self.db, instrument_uid=tool_info[0])
        if not db_instrument:
            logging.error(f"Не найден инструмент с uid = {tool_info[0]}")
            raise ValueError(f"Не найден инструмент с uid = {tool_info[0]}")

        if not crud.check_timeframe(self.db, timeframe_name=tool_info[5]):
            crud.create_timeframe(self.db, id=None, name=tool_info[5])

        self.uid = tool_info[0]
        self.timeframe = tool_info[-1]
        self.get_lot()

        # Определяем id инструмента и таймфрейма
        uid_instrument = db_instrument.uid
        id_timeframe = crud.get_timeframe_id(self.db, timeframe_name=self.timeframe)
        #db_timeframe = crud.get_timeframe(self.db, id_timeframe)
        #interval = self.get_timeframe_by_name(db_timeframe.name)

        # Запрашиваем 10 последних candles для инструмента
        candles =  crud.get_candles_list(self.db, uid_instrument, id_timeframe)
        if not candles:
            # Свеч по данному инструменту в базе вообще нет
            self.load_candles()
            return 1   # Возврат 1 в случае начальной подгрузки свечей
        else:
            last_candle = candles[0]
            if last_candle.time_m - datetime.now() > timedelta(hours=2):
                return last_candle.time_m  # Возврат времени последней свечи, если она есть и при этом разница между текущим временем значительная
            ''' Если нет свечей вообще, то запрашиваем 10 последних свечей за период '''
            #self.get_candles(db_instrument.figi, tool_timeframe, fill_db=True)  # Заполняем базу с нуля
        return 1   # Возврат 1 в случае, если все нормально

    ''' Отладочный метод (1) на загрузку некоторых свечей в базу '''
    def load_some_candles(self):

        tool_info = InvestBot.get_instrument_info("config.txt")  # Получаем информацию об инструменте
        uid = tool_info[0]
        frame = tool_info[-1]
        db_instrument =  crud.get_instrument_uid(self.db, instrument_uid=uid)

        # Получаем границы времнного интервала для массива свечей
        cur_date = datetime.now()
        last_date = cur_date - timedelta(hours=6 * 24)

        str_cur_date = cur_date.strftime("%Y-%m-%d_%H:%M:%S")
        str_last_date = last_date.strftime("%Y-%m-%d_%H:%M:%S")

        request_text = f"/get_candles {uid} {str_last_date} {str_cur_date} {frame}"  # Строка запроса на получение свечей\
        try:
            candles = core_bot.get_candles(request_text)
        except InvestBotValueError as iverror:
            logging.error(f"InvestBotValueError: {iverror.msg}")
            raise InvestBotValueError(iverror.msg)
        except RequestError as irerror:
            logging.error("Ошибка во время запроса котировок на стороне сервера")
            raise irerror

        ''' Обходим массив свечей и добавляем их в базу '''
        for candle in candles:
            open, close, low, high, time_obj, volume = self.get_params_candle(candle)
            str_time = datetime.strptime(time_obj, '%Y-%m-%d_%H:%M:%S')
            print(open, close, low, high, str_time, volume)

            is_candle =  crud.check_candle_by_time(self.db, str_time)
            if is_candle:
                continue

            new_id =  crud.get_last_candle_id(self.db) + 1
            my_instrument =  crud.get_instrument_uid(self.db, instrument_uid=uid)
            my_timeframe_id =  crud.get_timeframe_id(self.db, frame)

            if not my_timeframe_id:
                crud.create_timeframe(self.db, id=None, name=frame)
                my_timeframe_id =  crud.get_timeframe_id(self.db, frame)
                my_timeframe_id = my_timeframe_id.id

            try:
                 crud.create_candle(self.db, id=new_id, time_m=time_obj, volume=volume,
                                   open=open, close=close, low=low, high=high,
                                   id_instrument=my_instrument.id, id_timeframe=my_timeframe_id)
            except ValueError as vr:
                logging.error(f"Ошибка во время создания записи в таблице \'Candle\'. Аргументы: {vr.args}")
                print(vr.args)

        print('Data have been written')


    def load_candles(self, last_date=None):
        """
        Метод для загрузки свечей по инструменту

        :param last_date: начальное время для запроса
        """
        candles = None  # Сырой массив свечей
        mode = 1

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
            logging.error(f"Ошибка в методе InvestBot.load_candles во время обработки котировок: {iverror.args}")
            raise InvestBotValueError(iverror.msg)
        except RequestError as irerror:
            logging.error("Ошибка в методе InvestBot.load_candles во время выгрузки котировок на стороне сервера")
            raise irerror

        ''' Обходим массив свечей и добавляем их в базу '''
        for candle in candles:
            open, close, low, high, time_obj, volume = self.get_params_candle(candle)
            str_time = datetime.strptime(time_obj, '%Y-%m-%d_%H:%M:%S')
            print(open, close, low, high, str_time, volume)

            new_id = crud.get_last_candle_id(self.db) + 1
            my_instrument = crud.get_instrument(self.db, instrument_uid=self.uid)
            my_timeframe_id = crud.get_timeframe_id(self.db, self.timeframe)
            if not my_timeframe_id:
                crud.create_timeframe(self.db, name=self.timeframe)
                my_timeframe_id =  crud.get_timeframe_id(self.db, self.timeframe)
                my_timeframe_id = my_timeframe_id.id

            try:
                 crud.create_candle(self.db, id=new_id, time_m=time_obj, volume=volume,
                                   open=open, close=close, low=low, high=high,
                                   uid_instrument=my_instrument.uid, id_timeframe=my_timeframe_id)
            except ValueError as vr:
                logging.error(f"В методе InvestBot.load_candles() в метод await crud.create_candles() передан неверный аргумент передан")
                print(vr.args)

        print(f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}: Candles have been written\n")

    def get_lot(self):
        instrument = crud.get_instrument(self.db, self.uid)
        self.lot = instrument.lot

    def __correct_sum(self):
        balance = None
        with SandboxClient(TOKEN) as client:
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            free_money = cast_money(balance.total_amount_currencies)
            while free_money < 20000:
                self.pay_in(5000)
                balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
                free_money = cast_money(balance.total_amount_currencies)


    def pay_in(self, sum_rub: float):
        """ Пополнение счета в песочнице """
        with SandboxClient(TOKEN) as client:
            sum_trade = reverse_money_mv(sum_rub)
            client.sandbox.sandbox_pay_in(account_id=self.account_id, amount=sum_trade)  # Пополнение счета на сумму pay_sum
            print(f"\nПортфель пополнен на {sum_rub:.2f} RUB\n\n")


    def __print_candle(self, candle: models.Candle):
        """
         Метод для вывода свечи в консоль
        """
        time_m = candle.time_m.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\nOpen: {candle.open:.2f}, Close: {candle.close:.2f}, Low: {candle.low:.2f}, High: {candle.high:.2f}, Time: {time_m}\n")


    def __print_sma(self, sma_prev: TechAnalysisItem, sma_cur: TechAnalysisItem):
        time_prev = sma_prev.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        time_cur = sma_cur.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        sma_prev_value = cast_money(sma_prev.signal)
        sma_cur_value = cast_money(sma_cur.signal)

        print(f'\nSMA prev time = {time_prev},  SMA prev value = {sma_prev_value:.2f}')
        print(f'SMA cur time = {time_cur},  SMA cur value = {sma_cur_value:.2f}\n')


    def check_signal(self):
        """
        Метод, проверяющий наличие торговых сигналов
        """
        tf_id = crud.get_timeframe_id(self.db, self.timeframe)
        last_candles = crud.get_candles_list(self.db, self.uid, tf_id)

        t2 = last_candles[0].time_m
        t1 = None
        tf = self.get_timeframe_by_name(self.timeframe)
        #self.make_trade()
        match tf:
            case CandleInterval.CANDLE_INTERVAL_1_MIN:
                t1 = t2 - timedelta(minutes=60)
            case CandleInterval.CANDLE_INTERVAL_2_MIN:
                t1 = t2 - timedelta(minutes=120)
            case CandleInterval.CANDLE_INTERVAL_5_MIN:
                t1 = t2 - timedelta(hours=3)
            case CandleInterval.CANDLE_INTERVAL_10_MIN:
                t1 = t2 - timedelta(hours=3)
            case CandleInterval.CANDLE_INTERVAL_15_MIN:
                t1 = t2 - timedelta(hours=5)
            case CandleInterval.CANDLE_INTERVAL_30_MIN:
                t1 = t2 - timedelta(hours=12)
            case CandleInterval.CANDLE_INTERVAL_30_MIN:
                t1 = t2 - timedelta(hours=24)
            case CandleInterval.CANDLE_INTERVAL_HOUR:
                t1 = t2 - timedelta(hours=36)
            case CandleInterval.CANDLE_INTERVAL_2_HOUR:
                t1 = t2 - timedelta(days=7)
            case CandleInterval.CANDLE_INTERVAL_4_HOUR:
                t1 = t2 - timedelta(days=14)
            case CandleInterval.CANDLE_INTERVAL_DAY:
                t1 = t2 - timedelta(days=31)
            case CandleInterval.CANDLE_INTERVAL_WEEK:
                t1 = t2 - timedelta(days=31*4)
            case CandleInterval.CANDLE_INTERVAL_MONTH:
                t1 = t2 - timedelta(days=365*2)

        valuesEMA = getEMA(self.uid, t1, t2, tf, interval=SMA_INTERVAL)
        valuesRSI = getRSI(self.uid, t1, t2, tf, interval=RSI_INTERVAL)

        # Выводим значения последних свечей и SMA в консоль для отладки
        self.__print_candle(last_candles[2])
        self.__print_candle(last_candles[1])
        self.__print_sma(valuesEMA[-2], valuesEMA[-1])

        #sma_prev_time, sma_cur_time = valuesSMA[-2].timestamp, valuesSMA[-1].timestamp 
        sma_prev, sma_cur = cast_money(valuesEMA[-2].signal), cast_money(valuesEMA[-1].signal)
        rsiVal = cast_money(valuesRSI[-1].signal)

        if last_candles[2].close < sma_prev and last_candles[1].close > sma_cur:
            self.direct_trade = DirectTrade.BUY
        elif last_candles[2].close > sma_prev and last_candles[1].close < sma_cur:
            self.direct_trade = DirectTrade.SELL
        else:
            self.direct_trade = DirectTrade.UNSPECIFIED
            return False

        print('\nSIGNAL 1 TAKEN\n')
        valuesSMA = valuesEMA[-10:]
        size = len(valuesSMA)
        last_candles = last_candles[:-1]
        last_candles.reverse()
        if len(last_candles) > size:
            last_candles = last_candles[-size:]
        cntInter = 0
        valuesSMA[0] = cast_money(valuesSMA[0].signal)
        for i in range(1, size):
            print(f"ITERATION = {i}")
            try:
                valuesSMA[i] = cast_money(valuesSMA[i].signal)
                if last_candles[i-1].close < valuesSMA[i-1] and last_candles[i].close > valuesSMA[i]:
                    cntInter += 1
                elif last_candles[i-1].close > valuesSMA[i-1] and last_candles[i].close < valuesSMA[i]:
                    cntInter += 1
            except IndexError:
                break

        if cntInter > MAXInter:
            return False

        print('\nSIGNAL 2 TAKEN\n')

        if self.direct_trade == DirectTrade.BUY and rsiVal > 70:
            return False
        elif self.direct_trade == DirectTrade.SELL and rsiVal < 30:
            return False

        print('\nSIGNAL 3 TAKEN\n')

        return True

    def make_trade(self):
        balance = None
        with SandboxClient(TOKEN) as client:
            print("BEGIN OF TRADE\n")
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            free_money = cast_money(balance.total_amount_currencies)
            positionSize = free_money * STOP_ACCOUNT / STOP_LOSS  # Расчитываем размер позиции (сделки)

            my_timeframe_id = crud.get_timeframe_id(self.db, self.timeframe)
            last_price = crud.get_candles_list(self.db, self.uid, my_timeframe_id)
            last_price = last_price[0].close

            if last_price != 0:
                print(f"Last price = {last_price}")
            else:
                print("No last price!\n")
                exit(1)
            print(f"\nLAST PRICE = {last_price} rub/item\n")
            if last_price == 0:
                exit(1)
            print(f"\nLOT = {self.lot}\n")
            last_price = float(last_price)
            trade_price = reverse_money(last_price)
            lot_cast = last_price * self.lot
            print(f"\nLOT CAST = {lot_cast:.3f} rub/lot\n")
            lot_count = int(positionSize / lot_cast)
            direct = None

            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            total_amount_shares = cast_money(balance.total_amount_shares)
            total_amount_bonds = cast_money(balance.total_amount_bonds)
            total_amount_etf = cast_money(balance.total_amount_etf)
            free_money = cast_money(balance.total_amount_currencies)
            total_amount_portfolio = cast_money(balance.total_amount_portfolio)
            self.profit = cast_money(balance.expected_yield)

            if self.direct_trade == DirectTrade.BUY:
                direct = OrderDirection.ORDER_DIRECTION_BUY
                if free_money < positionSize:
                    while lot_count != 0 or free_money < positionSize:
                        lot_count -= 1
                        positionSize = lot_cast * lot_count
                    if free_money < positionSize:
                        print('\n-----------------------------\nNOT ENOUGH MONEY FOR BUY\n\n')
                        return
            else:
                direct = OrderDirection.ORDER_DIRECTION_SELL
                if lot_cast * lot_count > total_amount_shares:
                    print('\n-----------------------------\nNOT ENOUGH MONEY FOR SELL\n\n')
                    return
                #lot_count = self.__check_buy(self.uid, lot_count, last_price) # Корректируем количество лотов на продажу, чтобы была прибыль, а не убыток
                #if lot_count <= 0: # Если по итогам корректировки количество лотов на продажу = 0, отменяем сделку
                #    return

            if lot_count < 0:
                lot_count = -lot_count
            if lot_count == 0:
                lot_count = 1
            POResponse = client.sandbox.post_sandbox_order(instrument_id=self.uid, price=trade_price, direction=direct,
                                              account_id=self.account_id, order_type=OrderType.ORDER_TYPE_MARKET,
                                              price_type=PriceType.PRICE_TYPE_CURRENCY, quantity=lot_count)
            print("END OF TRADE\n")

            self.printPostOrderResponse(POResponse)
            self.__save_trade(POResponse)

    def check_loss(self):
        if math.fabs(self.profit / 100) > STOP_ACCOUNT and self.profit < 0:
            print("CRITCAL LOSS. EXIT")
            return True
        return False


    def __save_trade(self, POResponse):
        """
        Сохранаяем данные о сделке в журнал сделок
        :param POResponse:  PostOrderResponse - ответ о статусе сделки и информацией о ней
        :return:
        """
        if POResponse.instrument_uid not in self.trades_list.keys():
            self.trades_list[POResponse.instrument_uid] = list([])

        self.trades_list[POResponse.instrument_uid].append(dict())
        self.trades_list[POResponse.instrument_uid][-1]['time'] = POResponse.response_metadata.server_time
        self.trades_list[POResponse.instrument_uid][-1]['direct'] = POResponse.direction
        self.trades_list[POResponse.instrument_uid][-1]['cast_order'] = cast_money(POResponse.executed_order_price)
        self.trades_list[POResponse.instrument_uid][-1]['count'] = POResponse.lots_executed
        self.trades_list[POResponse.instrument_uid][-1]['commision'] = cast_money(POResponse.executed_commission)


    def __check_buy(self, uid, lot_count, last_price):
        """
        Метод, проверяющий потенциальную прибыль/риск от сделки
        :param uid: UID инструмента
        :param lot_count: Запрашиваемое количество лотов на продажу
        :param last_price: Цена по рынку
        """

        portfolio = None
        pos = None
        with SandboxClient(TOKEN) as client:
            portfolio = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
        for position in portfolio.positions:
            if position.instrument_uid == uid:
                pos = position
        lot_pos = int(cast_money(pos.quantity) / self.lot)   # Количество лотов актива X
        if lot_pos < lot_count:
            lot_count = lot_pos
        if lot_count == 0:
            return lot_count

        # 5. Проверяем сделки от текущей k до 0 по этой акции. Заводим счетчик cntShares = K
        cntShares = lot_count             # Количество лотов на момент проверки сделки
        cur_trade = len(self.trades_list[uid]) - 1 # Стартуем с N-1 сделки
        while cntShares > 0 and cur_trade >= 0:
            if self.trades_list[uid][cur_trade]['direct'] == OrderDirection.ORDER_DIRECTION_BUY:
                cntShares -= self.trades_list[uid][cur_trade]['count']
                buy_pair = list([self.trades_list[uid][cur_trade]['cast_order'], self.trades_list[uid][cur_trade]['count']])
                buy_pair.append(self.trades_list[uid][cur_trade]['commision'])
                self.buy_cast_list.append(buy_pair)
            elif self.trades_list[uid][cur_trade]['direct'] == OrderDirection.ORDER_DIRECTION_SELL:
                cntShares += self.trades_list[uid][cur_trade]['count']


        request_lots, request_sum = 0, 0
        buy_com = 0
        if not self.buy_cast_list or not self.buy_cast_list[-1][2]:
            buy_com = 0
        else:
            buy_com = self.buy_cast_list[-1][2]
        size = len(self.buy_cast_list)
        for i in range(size-1, -1, -1):
            if i < 0:
                break
            lots = self.buy_cast_list[i][1]
            while lots != 0 and request_lots != lot_count:
                lots -= 1
                request_lots += 1
                request_sum += self.buy_cast_list[i][0] * self.lot
                self.__last_prices.append(self.buy_cast_list[i][0])
        
        # Рассчитываем потенциальную прибыль с учетом комиссии
        k = lot_count
        if lot_count > request_lots and request_lots != 0:
            k = request_lots
        profit = (k * last_price - request_sum) - (buy_com + 0.0005 * k * last_price)
        while profit <= 0 and k > 0:
            # Пока со сделки наблюдается убыток, уменьшаем возможное количество лотов
            k -= 1
            profit = (k * last_price - request_sum) - (buy_com + 0.0005 * k * last_price)

        return k    # Возвращаем итоговое количество лотов на продажу 
        

    def printPostOrderResponse(self, POResponse: PostOrderResponse):
        print('\nINFO ABOUT TRADE\n-----------------------------------------------------\n')
        direct_str = ''
        order_type = ''
        match POResponse.direction:
            case OrderDirection.ORDER_DIRECTION_BUY:
                print("Direct of trade = BUY")
                direct_str = 'BUY'
            case OrderDirection.ORDER_DIRECTION_SELL:
                print("Direct of trade = SELL")
                direct_str = 'SELL'
        print(f"Executed order price = {POResponse.executed_order_price}")
        print(f"Executed commission = {POResponse.executed_commission}")
        print(f"UID instrument = {POResponse.instrument_uid}")
        print(f"Requested lots = {POResponse.lots_requested}")
        print(f"Executed lots = {POResponse.lots_executed}")
        match POResponse.order_type:
            case OrderType.ORDER_TYPE_MARKET:
                print(f"Order type = MARKET")
                order_type = 'MARKET'
            case OrderType.ORDER_TYPE_LIMIT:
                print(f"Order type = LIMIT")
                order_type = 'LIMIT'
            case OrderType.ORDER_TYPE_BESTPRICE:
                print(f"Order type = BESTPRICE")
                order_type = 'BESTPRICE'
        print(f"Total order amount = {POResponse.total_order_amount}\n\n")
        print(f"Tracking id = {POResponse.response_metadata.tracking_id}")
        server_time = POResponse.response_metadata.server_time.strftime('%Y-%m-%d_%H:%M:%S')
        print(f"Time of trade = {server_time}")
        data_csv = list([POResponse.instrument_uid, str(cast_money(POResponse.executed_order_price)),
                         str(cast_money(POResponse.executed_commission)),
                         str(POResponse.instrument_uid), str(POResponse.lots_requested),
                         str(POResponse.lots_executed), order_type, direct_str,
                         str(cast_money(POResponse.total_order_amount)),
                         POResponse.response_metadata.tracking_id, server_time])

        instrument_uid = str(POResponse.instrument_uid)
        ticker = 'lol'
        instrument = crud.get_instrument(self.db, instrument_uid)
        ticker = instrument.ticker

        file_trades = "C:\\Users\\User\\PycharmProjects\\teleBotTest\\app\\trades_stat"
        filename = self.get_full_filename(file_trades, ticker)
        if os.path.exists(filename):
            with open(filename, 'a') as csv_file:
                writer = csv.writer(csv_file, delimiter=';')
                writer.writerow(data_csv)
        else:
            with open(filename, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=';')
                writer.writerow(data_csv)


    def printPortfolio(self):
        print("MY PORTFOLIO\n-----------------------------------\n")
        with SandboxClient(TOKEN) as client:
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            total_amount_shares = cast_money(balance.total_amount_shares)
            total_amount_bonds = cast_money(balance.total_amount_bonds)
            total_amount_etf = cast_money(balance.total_amount_etf)
            free_money = cast_money(balance.total_amount_currencies)
            total_amount_portfolio = cast_money(balance.total_amount_portfolio)
            self.profit = cast_money(balance.expected_yield)
            server_time = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M:%S')
            data_csv = list([str(total_amount_portfolio), str(free_money),
                             str(self.profit), str(total_amount_shares),
                             str(total_amount_bonds), str(total_amount_etf), server_time])

            print(f"Free money = {free_money} RUB")
            print(f"Total amount shares = {total_amount_shares} RUB")
            print(f"Total amount portfolio = {total_amount_portfolio} RUB")
            print(f"Profit/Unprofit = {self.profit} %\n")
            print(f"Time = {server_time}")
            print("Positions\n-----------------------------------")
            
            for position in balance.positions:
                instrument_uid = position.instrument_uid
                position_uid = position.position_uid
                figi = position.figi
                instrument_type = position.instrument_type
                ticker = ''
                count = cast_money(position.quantity)
                cur_price = cast_money(position.current_price)
                count_lots = cast_money(position.quantity_lots)
                profit = cast_money(position.expected_yield)

                instrument = crud.get_instrument(self.db, instrument_uid)
                name = None
                if instrument:
                    name = instrument.name
                    ticker = instrument.ticker
                else:
                    currency = crud.get_currency_by_uid(self.db, instrument_uid)
                    if currency:
                        name = currency.name
                        ticker = currency.ticker

                print(f"Instrument UID = {instrument_uid}")
                print(f"Position UID = {position_uid}")
                print(f"FIGI = {figi}")
                if ticker:
                    print(f"TICKER = {ticker}")
                if name:
                    print(f"Name = {name}")
                print(f"Instrument type = {instrument_type}")
                print(f"Quantity = {count}")
                print(f"Current price = {cur_price:.2f}")
                print(f"Count of lots = {count_lots}")
                print(f"Profit/Unprofit = {profit} %\n")
            print('\n---------------------------------------------------\n---------------------------------------------\n')

            filename = "C:\\Users\\User\\PycharmProjects\\teleBotTest\\app\\porfolio_stat"
            filename = self.get_full_filename(filename, ticker)
            if os.path.exists(filename):
                with open(filename, 'a') as csv_file:
                    writer = csv.writer(csv_file, delimiter=';')
                    writer.writerow(data_csv)
            else:
                with open(filename, 'w') as csv_file:
                    writer = csv.writer(csv_file, delimiter=';')
                    writer.writerow(data_csv)


    def get_full_filename(self, filename: str, ticker: str):
        filename = filename + '_' + ticker + '_' + self.timeframe + '.csv'
        return filename

    def buy_shares(self):
        ''' Отладочный метод для восполнения недостающих акций '''
        my_timeframe_id = crud.get_timeframe_id(self.db, self.timeframe)
        last_price = crud.get_candles_list(self.db, self.uid, my_timeframe_id)
        last_price = last_price[0].close
        last_price = float(last_price)
        trade_price = reverse_money(last_price)

        with SandboxClient(TOKEN) as client:
            POResponse = client.sandbox.post_sandbox_order(instrument_id=self.uid, price=trade_price, direction=OrderDirection.ORDER_DIRECTION_BUY,
                                                           account_id=self.account_id,
                                                           order_type=OrderType.ORDER_TYPE_MARKET,
                                                           price_type=PriceType.PRICE_TYPE_CURRENCY, quantity=5)
            self.printPostOrderResponse(POResponse)

    def run(self):
        print('lol_1')
        """ Главный цикл торгового робота """
        last_time = self.check_last_candles()
        if isinstance(last_time, datetime):
            # Если check_last_candles() вернул datetime-объект, значит у нас значительный разрыв по времени, требуется
            # еще подгрузка
            self.load_candles(last_time)

        if not self.__cor_sum:      # Если не стоит флаг коррекции суммы
            self.__correct_sum()
        else:
            self.pay_in(self.__cor_sum_val)
        #self.buy_shares()

        self.__stream_process.start()   # Запускаем процесс загрузки данных через Stream

        while True:
            self.printPortfolio()
            if self.check_loss():                   # Если у нас потери превысили риск
                self.__stream_process.terminate()     # Завершаем процесс стрима
                print('\nStream process terminated')
                print('Session was exited')
                return                                # Выходим из функции
            if self.check_signal():
                self.make_trade()
            time.sleep(self.delay)