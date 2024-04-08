# Сам бот
import json
import logging

from datetime import datetime, timedelta, timezone
from functools import cache
import numpy as np

from tinkoff.invest.schemas import (
    InstrumentStatus,
    HistoricCandle,
    AssetType,
    InstrumentType,
    InstrumentIdType,
    CandleInterval,
    AssetRequest
)
from tinkoff.invest.exceptions import RequestError

# Для исторических свечей

from work import *
from work.functional import *
from work.exceptions import *
from app.StopMarketQueue import StopMarketQueue
from api import crud, models
from api.database import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"


class InvestBot():
    """
    Класс, реализующий логику торгового робота в песочнице
    """


    def __init__(self, account_id: str, autofill=True):
        self.market_queue = StopMarketQueue()
        self.account_id = account_id
        self.uid = None
        self.timeframe = None

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

        instrument_list = crud.get_instrument_list(self.db)  # Достаем все записи из таблицы instrument
        if not instrument_list or fill:                              # Если таблица instrument пуста, то выходим
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
                db_asset = crud.get_asset_uid(self.db, asset_uid=asset.uid)
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
                        db_instrument = crud.get_instrument_by_name(self.db, instrument_name=instrument_name)
                        if db_instrument:
                            continue

                        ''' Вставка нового инструмента в таблицу '''

                        '''Если в базе нет обозначения валюты инструмента, добавляем ее в базу'''
                        id_cur = crud.get_curency_id(db=self.db, currency_name=currency_name)
                        if not id_cur:
                            last_id = crud.get_last_currency_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_currency(db=self.db, id=last_id, name=currency_name)
                            id_cur = crud.get_curency_id(db=self.db, currency_name=currency_name)

                        '''Если в базе нет обозначения биржи инструмента, добавляем ее в базу'''
                        id_exc = crud.get_exchange_id(db=self.db, exchange_name=exchange_name)
                        if not id_exc:
                            last_id = crud.get_last_exchange_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_exchange(db=self.db, id=last_id, name=exchange_name)
                            id_exc = crud.get_exchange_id(db=self.db, exchange_name=exchange_name)

                        ''' Если в базе нет обозначения сектора, добавляем его в базу '''
                        id_sec = crud.get_sector_id(db=self.db, sector_name=sector_name)
                        if not id_sec:
                            last_id = crud.get_last_sector_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_sector(db=self.db, id=last_id, name=sector_name)
                            id_sec = crud.get_sector_id(db=self.db, sector_name=sector_name)

                        ''' Если в базе нет обозначения типа инструмента, добавляем его в базу '''
                        str_instr_type = self.get_str_type(instrument.instrument_kind, False)
                        id_instr_type = crud.get_instrument_type_name(db=self.db, instrument_type_name=str_instr_type)
                        if not id_instr_type:
                            last_id = crud.get_last_instrument_type_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_instrument_type(db=self.db, id=last_id, name=str_instr_type)
                            id_instr_type = crud.get_instrument_type_name(db=self.db,
                                                                          instrument_type_name=str_instr_type).id
                        elif isinstance(id_instr_type, models.InstrumentType):
                            id_instr_type = id_instr_type.id

                        """ Если в базе нет обозначения актива инструмента, добавляем его в базу """
                        id_asset = crud.get_asset_uid(db=self.db, asset_uid=asset.uid)
                        if not id_asset:
                            last_id = crud.get_last_asset_id(db=self.db)
                            last_id = last_id + 1 if last_id else 1
                            crud.create_asset(db=self.db, id=last_id, uid=asset.uid, name=asset.name)
                            id_asset = crud.get_asset_uid(db=self.db, asset_uid=asset.uid).id
                        elif isinstance(id_asset, models.Asset):
                            id_asset = id_asset.id

                        # Добавляем инструмент в таблицу
                        crud.create_instrument(db=self.db, figi=instrument.figi, name=instrument_name,
                                               uid=instrument.uid, position_uid=instrument.position_uid,
                                               currency_id=id_cur, exchange_id=id_exc, sector_id=id_sec,
                                               type_id=id_instr_type, asset_id=id_asset,
                                               ticker=instrument.ticker, lot=lot,
                                               class_code=instrument.class_code)
                    continue

                """ Проверка на наличие типа актива в БД """
                str_asset_type = self.get_str_type(asset.type, True)
                db_asset_type_id = crud.get_asset_type_name(self.db, asset_type_name=str_asset_type)
                if not db_asset_type_id:
                    last_id = crud.get_last_asset_type_id(self.db)
                    last_id = last_id + 1 if last_id else 1
                    db_asset_type_id = crud.create_asset_type(self.db, id=last_id, name=str_asset_type).id
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
                    db_instrument = crud.get_instrument_by_name(self.db, instrument_name=instrument_name)
                    if db_instrument:
                        continue

                    ''' Вставка нового инструмента в таблицу '''


                    '''Если в базе нет обозначения валюты инструмента, добавляем ее в базу'''
                    id_cur = crud.get_curency_id(db=self.db, currency_name=currency_name)
                    if not id_cur:
                        last_id = crud.get_last_currency_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_currency(db=self.db, id=last_id, name=currency_name)
                        id_cur = crud.get_curency_id(db=self.db, currency_name=currency_name)

                    '''Если в базе нет обозначения биржи инструмента, добавляем ее в базу'''
                    id_exc = crud.get_exchange_id(db=self.db, exchange_name=exchange_name)
                    if not id_exc:
                        last_id = crud.get_last_exchange_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_exchange(db=self.db, id=last_id, name=exchange_name)
                        id_exc = crud.get_exchange_id(db=self.db, exchange_name=exchange_name)

                    ''' Если в базе нет обозначения сектора, добавляем его в базу '''
                    id_sec = crud.get_sector_id(db=self.db, sector_name=sector_name)
                    if not id_sec:
                        last_id = crud.get_last_sector_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_sector(db=self.db, id=last_id, name=sector_name)
                        id_sec = crud.get_sector_id(db=self.db, sector_name=sector_name)

                    ''' Если в базе нет обозначения типа инструмента, добавляем его в базу '''
                    str_instr_type = self.get_str_type(instrument.instrument_kind, False)
                    id_instr_type = crud.get_instrument_type_name(db=self.db, instrument_type_name=str_instr_type)
                    if not id_instr_type:
                        last_id = crud.get_last_instrument_type_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_instrument_type(db=self.db, id=last_id, name=str_instr_type)
                        id_instr_type = crud.get_instrument_type_name(db=self.db, instrument_type_name=str_instr_type).id
                    elif isinstance(id_instr_type, models.InstrumentType):
                        id_instr_type = id_instr_type.id

                    """ Если в базе нет обозначения актива инструмента, добавляем его в базу """
                    id_asset = crud.get_asset_uid(db=self.db, asset_uid=asset.uid)
                    if not id_asset:
                        last_id = crud.get_last_asset_id(db=self.db)
                        last_id = last_id + 1 if last_id else 1
                        crud.create_asset(db=self.db, id=last_id, uid=asset.uid, name=asset.name)
                        id_asset = crud.get_asset_uid(db=self.db, asset_uid=asset.uid).id
                    elif isinstance(id_asset, models.Asset):
                        id_asset = id_asset.id


                    # Добавляем инструмент в таблицу
                    crud.create_instrument(db=self.db, figi=instrument.figi, name=instrument_name,
                                           uid=instrument.uid, position_uid=instrument.position_uid,
                                           currency_id=id_cur, exchange_id=id_exc, sector_id=id_sec,
                                           type_id=id_instr_type, asset_id=id_asset,
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
        active_list = crud.get_actives_by_exchange(self.db, exchange_id=exchange_id)
        for instrument in active_list:
            print(instrument.figi, '  |   ', instrument.name)

    """ Метод для получения информации об отслеживаемом инструменте """
    @staticmethod
    def get_instrument_info(filename: str):
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

        return res_array


    def check_last_candles(self):
        tool_figi = ''
        tool_timeframe = ''

        tool_info = InvestBot.get_instrument_info("config.txt") # Получаем информацию об инструменте

        db_instrument = crud.get_instrument_uid(self.db, instrument_uid=tool_info[0])
        if not db_instrument:
            logging.error(f"Не найден инструмент с uid = {tool_info[0]}")
            raise ValueError(f"Не найден инструмент с uid = {tool_info[0]}")

        if not crud.check_timeframe(self.db, timeframe_name=tool_info[5]):
            crud.create_timeframe(self.db, name=tool_info[5])

        self.uid = tool_info[0]
        self.timeframe = tool_info[-1]

        # Определяем id инструмента и таймфрейма
        id_instrument = db_instrument.id
        id_timeframe = crud.get_timeframe_id(self.db, timeframe_name=tool_timeframe)
        db_timeframe = crud.get_timeframe(self.db, id_timeframe)
        interval = self.get_timeframe_by_name(db_timeframe.name)

        # Запрашиваем 10 последних candles для инструмента
        candles = crud.get_candles_list(self.db, id_instrument, id_timeframe)
        if not candles:
            # Свеч по данному инструменту в базе вообще нет
            self.load_candles()
            return 1
        else:
            last_candle = candles[-1]
            if last_candle.time_m - datetime.now() > timedelta(hours=2):
                return last_candle.time_m
            ''' Если нет свечей вообще, то запрашиваем 10 последних свечей за период '''
            #self.get_candles(db_instrument.figi, tool_timeframe, fill_db=True)  # Заполняем базу с нуля
        return 1

    ''' Отладочный метод (1) на загрузку некоторых свечей в базу '''
    def load_some_candles(self):

        tool_info = InvestBot.get_instrument_info("config.txt")  # Получаем информацию об инструменте
        uid = tool_info[0]
        frame = tool_info[-1]
        db_instrument = crud.get_instrument_uid(self.db, instrument_uid=uid)

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

            is_candle = crud.check_candle_by_time(self.db, str_time)
            if is_candle:
                continue

            new_id = crud.get_last_candle_id(self.db) + 1
            my_instrument = crud.get_instrument_uid(self.db, instrument_uid=uid)
            my_timeframe_id = crud.get_timeframe_id(self.db, frame)

            if not my_timeframe_id:
                crud.create_timeframe(self.db, id=None, name=frame)
                my_timeframe_id = crud.get_timeframe_id(self.db, frame)
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
        candles = None  # Сырой массив свечей
        mode = 1

        # Получаем границы времнного интервала для массива свечей
        cur_date = datetime.now()
        if not last_date:
            last_date = cur_date - timedelta(hours=365*24)

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
            my_instrument = crud.get_instrument_uid(self.db, instrument_uid=self.uid)
            my_timeframe_id = crud.get_timeframe_id(self.db, self.timeframe)
            if not my_timeframe_id:
                crud.create_timeframe(self.db, name=self.timeframe)
                my_timeframe_id = crud.get_timeframe_id(self.db, self.timeframe)
                my_timeframe_id = my_timeframe_id.id

            try:
                crud.create_candle(id=new_id, time_m=time_obj, volume=volume,
                                   open=open, close=close, low=low, high=high,
                                   id_instrument=my_instrument.id, id_timeframe=my_timeframe_id)
            except ValueError as vr:
                logging.error(f"В методе InvestBot.load_candles() в метод crud.create_candles() передан неверный аргумент передан")
                print(vr.args)

        print(f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}: Candles have been written")


    '''
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

            #crud.create_instrument_rezerve(self.db, orig_instrument=instrument, is_data=have_data)
    '''


    def run(self):
        """ Главный цикл торгового робота """
        last_time = self.check_last_candles()
        if isinstance(last_time, datetime):
            self.load_candles(last_time)

        while True:
            print("Bot is working\n")