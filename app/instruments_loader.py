# Загрузчик информации об инструментах
import logging
from typing import Any

from tinkoff.invest.schemas import (
    InstrumentIdType, Asset,
    AssetInstrument, InstrumentType,
)
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.exceptions import RequestError

from work.functional import *
from api import crud, models
from api.database import *

from . import app_utils

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"


class InstrumentsLoader:

    def __init__(self, autofill: bool = True):
        self._db = SessionLocal()
        if autofill:
            self._init_db()


    def _init_db(self):
        """ 
        Заполнение базы данных
        """
        if not self._db:
            logging.error("Не указана база данных")
            raise Exception("Не указана база данных")

        instrument_list =  crud.get_instrument_list(self._db)  # Достаем все записи из таблицы instrument
        if not instrument_list:                              # Если таблица instrument пуста, то выходим
            self._load_instruments()


    def __check_instrument_kind(self, sb_client: SandboxClient, instr: AssetInstrument) -> tuple[str | Any] | bool:
        """
        Проверка типа торгового инструмента
        """
        currency_name = None
        sector_name = None
        exchange_name = None
        instrument_name = None
        lot = 1

        match instr.instrument_kind:
            case InstrumentType.INSTRUMENT_TYPE_SHARE:
                shareResp = None
                try:
                    shareResp = sb_client.instruments.share_by(
                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                        id=instr.ticker,
                        class_code=instr.class_code)
                except Exception as e:
                    if isinstance(e, RequestError):
                        logging.error("Ошбика во время запроса данных об акции на стороне сервера\n")
                        return False
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
                    bondResp = sb_client.instruments.bond_by(
                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                        id=instr.ticker,
                        class_code=instr.class_code)
                except Exception as e:
                    if isinstance(e, RequestError):
                        logging.error(
                            "Ошбика во время запроса данных об облигации на стороне сервера\n")
                        return False
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
                    etfResp = sb_client.instruments.etf_by(
                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                        id=instr.ticker,
                        class_code=instr.class_code)
                except Exception as e:
                    if isinstance(e, RequestError):
                        logging.error("Ошбика во время запроса данных об ETF на стороне сервера\n")
                        return False
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

        return currency_name, sector_name, exchange_name, instrument_name, lot


    def __create_instrument(self, sb_client: SandboxClient, instrument: AssetInstrument, asset: Asset) -> bool:
        """
        Метод для добавления торгвого инструмента в базу

        :param instrument - торговый инструмент
        :return bool - признак досрочного продолжения цикла (досрочного завершения итерации)
        """

        resp = self.__check_instrument_kind(sb_client, instrument)
        if isinstance(resp, bool):
            if not resp:
                return True
        currency_name = resp[0]
        sector_name = resp[1]
        exchange_name = resp[2]
        instrument_name = resp[3]
        lot = resp[4]

        # Проверка на наличие инструмента в базе данных. Если есть, переходим к следующему инструменту
        db_instrument =  crud.get_instrument_by_name(self._db, instrument_name=instrument_name)
        if db_instrument:
            return True     # Возвращаем признак continue

        # Если в базе нет обозначения валюты инструмента, добавляем ее в базу
        id_cur = crud.get_currency_id(db=self._db, currency_name=currency_name)
        if not id_cur:
            last_id =  crud.get_last_currency_id(db=self._db)
            last_id = last_id + 1 if last_id else 1
            crud.create_currency(db=self._db, id=last_id, name=currency_name)
            id_cur =  crud.get_currency_id(db=self._db, currency_name=currency_name)

        # Если в базе нет обозначения биржи инструмента, добавляем ее в базу
        id_exc =  crud.get_exchange_id(db=self._db, exchange_name=exchange_name)
        if not id_exc:
            last_id =  crud.get_last_exchange_id(db=self._db)
            last_id = last_id + 1 if last_id else 1
            crud.create_exchange(db=self._db, id=last_id, name=exchange_name)
            id_exc =  crud.get_exchange_id(db=self._db, exchange_name=exchange_name)

        # Если в базе нет обозначения сектора, добавляем его в базу 
        id_sec =  crud.get_sector_id(db=self._db, sector_name=sector_name)
        if not id_sec:
            last_id =  crud.get_last_sector_id(db=self._db)
            last_id = last_id + 1 if last_id else 1
            crud.create_sector(db=self._db, id=last_id, name=sector_name)
            id_sec =  crud.get_sector_id(db=self._db, sector_name=sector_name)

        # Если в базе нет обозначения типа инструмента, добавляем его в базу 
        str_instr_type = app_utils.get_str_type(instrument.instrument_kind, False)
        id_instr_type =  crud.get_instrument_type_name(db=self._db, instrument_type_name=str_instr_type)
        if not id_instr_type:
            last_id =  crud.get_last_instrument_type_id(db=self._db)
            last_id = last_id + 1 if last_id else 1
            crud.create_instrument_type(db=self._db, id=last_id, name=str_instr_type)
            id_instr_type =  crud.get_instrument_type_name(db=self._db,
                                                            instrument_type_name=str_instr_type)
            id_instr_type = id_instr_type.id
        elif isinstance(id_instr_type, models.InstrumentType):
            id_instr_type = id_instr_type.id

        # Если в базе нет обозначения актива инструмента, добавляем его в базу
        uid_asset =  crud.get_asset_uid(db=self._db, asset_uid=asset.uid)
        if not uid_asset:
            crud.create_asset(db=self._db, uid=asset.uid, name=asset.name)
            uid_asset = crud.get_asset_uid(db=self._db, asset_uid=asset.uid)
            uid_asset = uid_asset.uid
        elif isinstance(uid_asset, models.Asset):
            uid_asset = uid_asset.uid

        # Добавляем инструмент в таблицу
        crud.create_instrument(db=self._db, figi=instrument.figi, name=instrument_name,
            uid=instrument.uid, position_uid=instrument.position_uid,
            currency_id=id_cur, exchange_id=id_exc, sector_id=id_sec,
            type_id=id_instr_type, asset_uid=uid_asset,
            ticker=instrument.ticker, lot=lot,
            class_code=instrument.class_code)
        return False
    

    def __create_asset(self, asset: Asset):
        """
        Добавляем актив в базу
        :param asset - объект типа Asset (актив)
        :return
        """

        str_asset_type = app_utils.get_str_type(asset.type, True)
        db_asset_type_id = crud.get_asset_type_name(self._db, asset_type_name=str_asset_type)
        if not db_asset_type_id:
            last_id =  crud.get_last_asset_type_id(self._db)
            last_id = last_id + 1 if last_id else 1
            db_asset_type_id =  crud.create_asset_type(self._db, id=last_id, name=str_asset_type)
            db_asset_type_id = db_asset_type_id
        else:
            db_asset_type_id = db_asset_type_id.id

        # Добавляем актив в БД
        crud.create_asset(self._db, uid=asset.uid,
                            name=asset.name,
                            type_id=db_asset_type_id)


    def _load_instruments(self):
        """
        Метод для загрузки в базу информации о всех возможных инструментах с Tinkoff Invest API
        """
        resp = None
        my_sb_client = None
        
        with SandboxClient(TOKEN) as sb_client:
            my_sb_client = sb_client
            resp = sb_client.instruments.get_assets()  # Получаем список всех активов

        for asset in resp.assets:
            db_asset = crud.get_asset(self._db, asset_uid=asset.uid)
            if db_asset:
                for instrument in asset.instruments:
                    is_cont = self.__create_instrument(my_sb_client, instrument, asset) # Добавляем торговый инструмент в базу
                    if is_cont:
                        continue

                self.__create_asset(asset)

            for instrument in asset.instruments:
                is_cont = self.__create_instrument(my_sb_client, instrument, asset) # Добавляем торговый инструмент в базу
                if is_cont:
                    continue