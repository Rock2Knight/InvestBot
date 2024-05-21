""" CRUD-операции. Пока без схем FastAPI """
import logging
from typing import Optional
from functools import cache

import sqlalchemy.exc
from sqlalchemy.orm import Session, exc
from sqlalchemy.orm.exc import UnmappedInstanceError
from . import models
from .database import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

""" Получение списка валют """
def get_currency_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Currency]]:
    return db.query(models.Currency).offset(skip).limit(limit).all()

""" Получение списка бирж """
def get_exchange_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Exchange]]:
    return db.query(models.Exchange).offset(skip).limit(limit).all()

""" Получение списка секторов """
def get_sectors_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Sector]]:
    return db.query(models.Sector).offset(skip).limit(limit).all()

""" Получение списка активов """
def get_assets_list(db: Session, skip: int = 0, limit: int = 100) -> Optional[list[models.Asset]]:
    return db.query(models.Asset).offset(skip).limit(limit).all()

""" Получение названия валюты по id """
def get_currency(db: Session, currency_id: int) -> Optional[models.Currency]:
    return db.query(models.Currency).filter(models.Currency.id == currency_id).first()

""" Получение id валюты по названию """
def get_currency_id(db: Session, currency_name: str) -> Optional[int]:
    db_currency = db.query(models.Currency).filter(models.Currency.name == currency_name).first()
    return db_currency.id if db_currency else None

def get_currency_by_uid(db: Session, currency_uid: str) -> Optional[models.Currency]:
    return db.query(models.Currency).filter(models.Currency.uid == currency_uid).first()

""" Получение id последней записи """
def get_last_currency_id(db: Session) -> Optional[int]:
    db_currency = db.query(models.Currency).order_by(models.Currency.id.desc()).first()
    return db_currency.id if db_currency else None

""" Получение названия биржы по id """
def get_exchange(db: Session, exchange_id: int) -> Optional[models.Exchange]:
    return db.query(models.Exchange).filter(models.Exchange.id == exchange_id).first()

""" Получение id биржы по названию """
def get_exchange_id(db: Session, exchange_name: str) -> Optional[int]:
    db_exchange = db.query(models.Exchange).filter(models.Exchange.name == exchange_name).first()
    return db_exchange.id if db_exchange else None

""" Получение id последней записи в таблице "Exchange" """
def get_last_exchange_id(db: Session) -> Optional[int]:
    db_exchange = db.query(models.Exchange).order_by(models.Exchange.id.desc()).first()
    return db_exchange.id if db_exchange else None

""" Получение названия сектора по id """
def get_sector(db: Session, sector_id: int) -> Optional[models.Sector]:
    return db.query(models.Sector).filter(models.Sector.id == sector_id).first()

""" Получение id сектора по названию """
def get_sector_id(db: Session, sector_name: str) -> Optional[int]:
    db_sector = db.query(models.Sector).filter(models.Sector.name == sector_name).first()
    return db_sector.id if db_sector else None

""" Получение id последней записи в таблице "Sector" """
def get_last_sector_id(db: Session) -> Optional[int]:
    db_sector = db.query(models.Sector).order_by(models.Sector.id.desc()).first()
    return db_sector.id if db_sector else None


""" GET-запросы для типов активов """
''' Получение типа актива по id '''
def get_asset_type(db: Session, asset_type_id: int) -> Optional[models.AssetType]:
    db_asset_type = db.query(models.AssetType).filter(models.AssetType.id == asset_type_id).first()
    return db_asset_type if db_asset_type else None

""" Получение типа актива по имени """
def get_asset_type_name(db: Session, asset_type_name: str) -> Optional[models.AssetType]:
    db_asset_type = db.query(models.AssetType).filter(models.AssetType.name == asset_type_name).first()
    return db_asset_type if db_asset_type else None

''' Получение id последенго типа актива в таблице '''
def get_last_asset_type_id(db: Session) -> Optional[int]:
    db_asset_type = db.query(models.AssetType).order_by(models.AssetType.id.desc()).first()
    return db_asset_type.id if db_asset_type else None


""" GET-запросы для типов инструментов """
''' Получение типа инструмента по id '''
def get_instrument_type(db: Session, instrument_type_id: int) -> Optional[models.InstrumentType]:
    db_instrument_type = db.query(models.InstrumentType).filter(models.InstrumentType.id == instrument_type_id).first()
    return db_instrument_type if db_instrument_type else None

""" Получение типа инструмента по имени """
def get_instrument_type_name(db: Session, instrument_type_name: str) -> Optional[models.InstrumentType]:
    db_instrument_type = db.query(models.InstrumentType).filter(models.InstrumentType.name == instrument_type_name).first()
    return db_instrument_type if db_instrument_type else None

''' Получение id последенго типа инструмента в таблице '''
def get_last_instrument_type_id(db: Session) -> Optional[int]:
    db_instrument_type = db.query(models.InstrumentType).order_by(models.InstrumentType.id.desc()).first()
    return db_instrument_type.id if db_instrument_type else None


""" GET-запросы для активов"""
''' Получение списка активов '''
def get_asset_list(db: Session, skip: int = 0, limit: int = 100) -> Optional[list[models.Asset]]:
    return db.query(models.Asset).offset(skip).limit(limit).all()

''' Получение актива по uid '''
def get_asset(db: Session, asset_uid: str) -> Optional[models.Asset]:
    db_asset = db.query(models.Asset).filter(models.Asset.uid == asset_uid).first()
    return db_asset if db_asset else None

''' Получение актива по uid '''
def get_asset_uid(db: Session, asset_uid: str) -> Optional[models.Asset]:
    db_asset = db.query(models.Asset).filter(models.Asset.uid == asset_uid).first()
    return db_asset if db_asset else None

''' Получение актива по имени'''
def get_asset_name(db: Session, asset_name: str) -> Optional[models.Asset]:
    db_asset = db.query(models.Asset).filter(models.Asset.name == asset_name).first()
    return db_asset if db_asset else None

''' Получение id последнего актива в таблице '''
def get_last_asset_uid(db: Session) -> Optional[int]:
    db_asset = db.query(models.Asset).order_by(models.Asset.uid.desc()).first()
    return db_asset.uid if db_asset else None


""" GET-запросы для инструментов """
""" Получение списка бумаг """
def get_instrument_list(db: Session, skip: int = 0, limit: int = 100) -> Optional[list[models.Instrument]]:
    return db.query(models.Instrument).offset(skip).limit(limit).all()

""" Получение бумаги по id (теперь аналогично get_instrument_uid) """
def get_instrument(db: Session, instrument_uid: str) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.uid == instrument_uid).first()

""" Получение последнего id инструмента"""
def get_last_instrument_uid(db: Session) -> int:
    model_instrument = db.query(models.Instrument).order_by(models.Instrument.uid.desc()).first()

    if not model_instrument:
        return 0
    else:
        return model_instrument.uid

""" Получение инструмента  по FIGI """
def get_instrument_by_figi(db: Session, figi: str, exchange_id: int = 1) -> Optional[models.Instrument]:
    db_figi = db.query(models.Instrument).filter(models.Instrument.figi == figi).first()
    return db_figi

""" Получение инструмента по тикеру """
def get_instrument_by_ticker(db: Session, ticker: str) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.ticker == ticker).first()

""" Получение инструмента по uid """
def get_instrument_uid(db: Session, instrument_uid: str) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.uid == instrument_uid).first()

""" Получение инструмента по position_uid """
def get_instrument_by_position_uid(db: Session, position_uid: str) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.position_uid == position_uid).first()

""" Получение инструментов определенной биржи """
def get_instruments_by_exchange(db: Session, exchange_id: int) -> Optional[list[models.Instrument]]:
    return db.query(models.Instrument).filter(models.Instrument.id_exchange == exchange_id).order_by(models.Instrument.name).all()

""" Получение бумаги по название """
def get_instrument_by_name(db: Session, instrument_name: str) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.name == instrument_name).first()

''' Получение списка инструментов определенных бирж '''
def get_filter_by_exchange_instruments(db: Session, exchange_id: list[int]) -> Optional[list[models.Instrument]]:
    return db.query(models.Instrument).filter(models.Instrument.id_exchange.in_(exchange_id)).order_by(models.Instrument.name).all()



""" GET-запросы для таймфреймов """
""" Получение таймфрейма по id """
@cache
def get_timeframe(db: Session, timeframe_id: int) -> Optional[models.Timeframe]:
    return db.query(models.Timeframe).filter(models.Timeframe.id == timeframe_id).first()

""" Получение id последней записи в таблице "Timeframe" """
@cache
def get_last_timeframe_id(db: Session) -> Optional[int]:
    db_timeframe = db.query(models.Timeframe).order_by(models.Timeframe.id.desc()).first()
    return db_timeframe.id if db_timeframe else None

""" Получение id таймфрейма по названию """
@cache
def get_timeframe_id(db: Session, timeframe_name: str) -> Optional[int]:
    db_timeframe = db.query(models.Timeframe).filter(models.Timeframe.name == timeframe_name).first()
    return db_timeframe.id if db_timeframe else None

""" Проверка на наличие таймфрейма в базе """
@cache
def check_timeframe(db: Session, timeframe_name: str) -> bool:
    db_timeframe = db.query(models.Timeframe).filter(models.Timeframe.name == timeframe_name).first()
    return True if db_timeframe else False

""" Получение списка бирж """
@cache
def get_exchange_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Exchange]]:
    return db.query(models.Exchange).offset(skip).limit(limit).all()

""" Получение списка секторов """
@cache
def get_sectors_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Sector]]:
    return db.query(models.Sector).offset(skip).limit(limit).all()


"""GET-запросы для свеч """
""" Получение списка 10 свеч по инструменту за определенный таймфрейм"""
def get_candles_list(db: Session, instrument_uid: str, frame_id: int) -> list[Optional[models.Candle]]:
    # Выбираем 10 последних свечей по инструменту за заданный таймфрейм
    return db.query(models.Candle).filter(models.Candle.uid_instrument == instrument_uid,
                                          models.Candle.id_timeframe == frame_id).order_by(
        models.Candle.time_m.desc()).limit(10).all()

""" Получение свечи по id """
@cache
def get_candle(db: Session, candle_id: int) -> Optional[models.Candle]:
    return db.query(models.Candle).filter(models.Candle.id == candle_id).first()

""" Поулчаем последнюю свечу """
def get_last_candle(db: Session, instrument_uid: str, frame_id: int) -> Optional[models.Candle]:
    res = db.query(models.Candle).filter(models.Candle.uid_instrument == instrument_uid,
                                          models.Candle.id_timeframe == frame_id).order_by(
        models.Candle.time_m.desc()).limit(1)
    res = db.execute(res).all()
    print(res)
    return res

@cache
def check_candle_by_time(db: Session, time_obj) -> bool:
    db_candle = db.query(models.Candle).filter(models.Candle.time_m == time_obj).first()
    return True if db_candle else False


""" Получаем id последней свечи по figi иснтрумента"""
def get_last_candle_id(db: Session) -> Optional[int]:
    db_candle = db.query(models.Candle).order_by(models.Candle.id.desc()).first()
    if not db_candle:
        return 0
    else:
        return db_candle.id


""" Поулчаем две последние свечи """
@cache
def get_last_candles(db: Session, uid_instrument: str, frame_id: int) -> tuple[Optional[models.Candle]]:
    last_candles = db.query(models.Candle).filter(models.Candle.uid_instrument == uid_instrument,
                                                  models.Candle.id_timeframe == frame_id).order_by(models.Candle.time_m.desc()).limit(2)
    if len(last_candles) != 2:
        raise Exception("Недостаточно элементов в списке")
    return last_candles[1], last_candles[0]


""" (1) Отладочный метод 
def get_last_active_rezerve_id(db: Session) -> int:
    db_instrument_rezerve = db.query(models.InstrumentRezerve).order_by(models.InstrumentRezerve.id.desc()).first()
    if not db_instrument_rezerve:
        return 0
    return db_instrument_rezerve.id

 (3) Отладочный метод
def get_rezerve_active_by_figi(db: Session, figi: str) -> Optional[models.InstrumentRezerve]:
    return db.query(models.InstrumentRezerve).filter(models.InstrumentRezerve.figi == figi).first()
"""




""" CREATE-операции """
""" Создание новой валюты"""
def create_currency(db: Session, id: Optional[int], name: str) -> models.Currency:
    new_id = None
    if id:
        new_id = id
    else:
        new_id =  get_last_currency_id(db)
        new_id = 1 if not new_id else new_id + 1

    db_currency = models.Currency(id=new_id, name=name)
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency

""" Создание новой биржи """
def create_exchange(db: Session, id: Optional[int], name: str) -> models.Exchange:
    new_id = None
    if id:
        new_id = id
    else:
        new_id =  get_last_exchange_id(db)
        new_id = 1 if not new_id else new_id + 1

    db_exchange = models.Exchange(id=new_id, name=name)
    db.add(db_exchange)
    db.commit()
    db.refresh(db_exchange)
    return db_exchange

""" Создание нового сектора """
def create_sector(db: Session, id: Optional[int], name: str) -> models.Sector:
    new_id = None
    if id:
        new_id = id
    else:
        new_id =  get_last_sector_id(db)
        new_id = 1 if not new_id else new_id + 1

    db_sector = models.Sector(id=new_id, name=name)
    db.add(db_sector)
    db.commit()
    db.refresh(db_sector)
    return db_sector

"""Создание нового таймфрейма"""
def create_timeframe(db: Session, id: Optional[int], name: str) -> models.Timeframe:
    new_id = None
    if id:
        new_id = id
    else:
        new_id = get_last_timeframe_id(db)
        new_id = 1 if not new_id else new_id + 1

    db_timeframe = models.Timeframe(id=new_id, name=name)
    db.add(db_timeframe)
    db.commit()
    db.refresh(db_timeframe)
    return db_timeframe

""" Создание типа актива """
def create_asset_type(db: Session, id: Optional[int], name: str) -> models.AssetType:
    new_id = None
    if id:
        new_id = id
    else:
        new_id =  get_last_asset_type_id()
        new_id = 1 if not new_id else new_id + 1

    db_asset_type = models.AssetType(id=new_id, name=name)
    db.add(db_asset_type)
    db.commit()
    db.refresh(db_asset_type)
    return db_asset_type


""" Создание типа инструмента """
def create_instrument_type(db: Session, id: Optional[int], name: str) -> models.InstrumentType:
    new_id = None
    if id:
        new_id = id
    else:
        new_id =  get_last_instrument_type_id(db)
        new_id = 1 if not new_id else new_id + 1

    db_instrument_type = models.InstrumentType(id=new_id, name=name)
    db.add(db_instrument_type)
    db.commit()
    db.refresh(db_instrument_type)


""" Добаление нового актива в базу данных """
def create_asset(db: Session, **kwargs) -> models.Asset:

    db_asset_type =  get_asset_type(db, kwargs['type_id'])
    if not db_asset_type:
        logging.error("Тип актива не найден")
        raise ValueError("Тип актива не найден")

    asset = models.Asset(uid=kwargs['uid'], name=kwargs['name'], type_id=kwargs['type_id'])

    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

""" Добавление нового инструмена в базу данных """
def create_instrument(db: Session, **kwargs):

    db_instrument_type =  get_instrument_type(db, kwargs['type_id'])
    if not db_instrument_type:
        logging.error("Ошибка в методе crud.create_instrument: тип инструмента не найден")
        raise ValueError("Тип инструмента не найден")

    db_asset =  get_asset(db, kwargs['asset_uid'])
    if not db_asset:
        logging.error("Ошибка в методе crud.create_instrument: актив не найден")
        raise ValueError("Актив не найден")

    db_currency =  get_currency(db, kwargs['currency_id'])
    if not db_currency:
        logging.error("Ошибка в методе crud.create_instrument: валюта не найдена")
        raise ValueError("Валюта не найдена")

    db_exchange =  get_exchange(db, kwargs['exchange_id'])
    if not db_exchange:
        logging.error("Ошибка в методе crud.create_instrument: биржа не найдена")
        raise ValueError("Биржа не найдена")

    db_sector =  get_sector(db, kwargs['sector_id'])
    if not db_sector:
        logging.error("Ошибка в методе crud.create_instrument: сектор не найден")
        raise ValueError("Сектор не найден")

    instrument = models.Instrument(uid=kwargs['uid'], position_uid=kwargs['position_uid'],
                                   figi=kwargs['figi'], name=kwargs['name'], class_code=kwargs['class_code'],
                                   ticker=kwargs['ticker'], lot=kwargs['lot'],
                                   currency_id=kwargs['currency_id'], exchange_id=kwargs['exchange_id'],
                                   sector_id=kwargs['sector_id'], type_id=kwargs['type_id'],
                                   asset_uid=kwargs['asset_uid'])
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument

""" (2) Отладочный метод 
def create_instrument_rezerve(db: Session, orig_instrument: models.Instrument, is_data: bool):

    last_active_id = get_last_active_rezerve_id(db)
    new_id = None

    if last_active_id == 0:
        new_id = 1
    else:
        new_id = last_active_id + 1

    instrument_rez = models.InstrumentRezerve(id=new_id, figi=orig_instrument.figi, name=orig_instrument.name,
                                   ticker=orig_instrument.ticker, lot=orig_instrument.lot,
                                   id_exchange=orig_instrument.id_exchange, is_data=is_data)
    db.add(instrument_rez)
    db.commit()
    db.refresh(instrument_rez)
    return instrument_rez
"""


""" Добавление новой свечи в базу данных """
def create_candle(db: Session, **kwargs):

    db_instrument =  get_instrument(db, instrument_uid=kwargs['uid_instrument'])
    if not db_instrument:
        logging.error("Ошибка в методе crud.create_candle: инструмент не найден")
        raise ValueError("Инструмент не найден")

    db_timeframe =  get_timeframe(db, kwargs['id_timeframe'])
    if not db_timeframe:
        logging.error("Ошибка в методе crud.create_candle: таймфрейм не найден")
        raise ValueError("Таймфрейм не найден")

    last_id = get_last_candle_id(db)
    if not last_id:
        last_id = 1
    else:
        last_id += 1

    new_id = None
    if 'id' in kwargs.keys():
        new_id = kwargs['id']
    else:
        new_id = last_id

    candle = models.Candle(id=new_id, time_m=kwargs['time_m'], open=kwargs['open'],
                           high=kwargs['high'], low=kwargs['low'], close=kwargs['close'],
                           volume=kwargs['volume'], uid_instrument=kwargs['uid_instrument'],
                           id_timeframe=kwargs['id_timeframe'])

    models.metadata.create_all(engine)
    ins = models.candleTable.insert().values(
        id=new_id, time_m=kwargs['time_m'], open=kwargs['open'],
        high=kwargs['high'], low=kwargs['low'], close=kwargs['close'],
        volume=kwargs['volume'], uid_instrument=kwargs['uid_instrument'],
        id_timeframe=kwargs['id_timeframe']
    )

    try:
        #db.add(candle)
        conn = engine.connect()
        r = conn.execute(ins)
        conn.commit()
    except UnmappedInstanceError as UIerror:
        logging.error("Ошибка в методе crud.create_candle: ошибка при попытке добавить свечу в базу")
        print(UIerror.with_traceback())
    except sqlalchemy.exc.InternalError as e:
        logging.error(e.args, e.detail)
    except sqlalchemy.exc.ProgrammingError as e:
        logging.error(e.args, e.detail)

    return candle



"""DELETE-операции"""

""" Удаление типа актива """
def delete_asset_type(db: Session, id: int):
    db_asset_type =  get_asset_type(db, id)
    if not db_asset_type:
        logging.error("Ошибка в методе crud.delete_asset_type: тип актива не найден")
        raise ValueError("Тип актива не найден")
    db.delete(db_asset_type)
    db.commit()
    return db_asset_type

""" Удаление типа инструмента """
def delete_instrument_type(db: Session, id: int):
    db_instrument_type =  get_instrument_type(db, id)
    if not db_instrument_type:
        logging.error("Ошибка в методе crud.delete_instrument_type: тип инструмента не найден")
        raise ValueError("Тип инструмента не найден")
    db.delete(db_instrument_type)
    db.commit()
    return db_instrument_type


""" Удаление сектора """
def delete_sector(db: Session, id: int):
    db_sector =  get_sector(db, id)
    if not db_sector:
        raise ValueError("Сектор не найден")
    db.delete(db_sector)
    db.commit()
    return db_sector

"""Удаление валюты"""
def delete_currency(db: Session, id: int):
    db_currency =  get_currency(db, id)
    if not db_currency:
        raise ValueError("Валюта не найдена")
    db.delete(db_currency)
    db.commit()


""" Удаление биржи  """
def delete_exchange(db: Session, id: int):
    db_exchange =  get_exchange(db, id)
    if not db_exchange:
        raise ValueError("Биржа не найдена")
    db.delete(db_exchange)
    db.commit()

""" Удаление таймфрейма """
def delete_timeframe(db: Session, id: int):
    db_timeframe =  get_timeframe(db, id)
    if not db_timeframe:
        raise ValueError("Таймфрейм не найден")
    db.delete(db_timeframe)
    db.commit()

"""" Удаление актива """
def delete_asset(db: Session, uid: str):
    db_asset =  get_asset(db, uid)
    if not db_asset:
        raise ValueError("Актив не найден")
    db.delete(db_asset)
    db.commit()

""" Удаление иснтрумента """
def delete_instrument(db: Session, uid: str):
    db_instrument =  get_instrument(db, uid)
    if not db_instrument:
        raise ValueError("Инструмент не найден")
    db.delete(db_instrument)
    db.commit()

""" Удаление свечи """
def delete_candle(db: Session, id: int):
    db_candle =  get_candle(db, id)
    if not db_candle:
        raise ValueError("Свеча не найдена")
    db.delete(db_candle)
    db.commit()