""" CRUD-операции. Пока без схем FastAPI """
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import UnmappedInstanceError
from . import models

""" Получение списка валют """
def get_currency_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Currency]]:
    return db.query(models.Currency).offset(skip).limit(limit).all()

""" Получение списка бирж """
def get_exchange_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Exchange]]:
    return db.query(models.Exchange).offset(skip).limit(limit).all()

""" Получение списка секторов """
def get_sectors_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Sector]]:
    return db.query(models.Sector).offset(skip).limit(limit).all()

""" Получение списка бумаг """
def get_instrument_list(db: Session, skip: int = 0, limit: int = 100) -> Optional[list[models.Instrument]]:
    return db.query(models.Instrument).offset(skip).limit(limit).all()

""" Получение названия валюты по id """
def get_currency(db: Session, currency_id: int) -> Optional[models.Currency]:
    return db.query(models.Currency).filter(models.Currency.id == currency_id).first()

""" Получение id валюты по названию """
def get_curency_id(db: Session, currency_name: str) -> Optional[int]:
    db_currency = db.query(models.Currency).filter(models.Currency.name == currency_name).first()
    return db_currency.id if db_currency else None

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

""" Получение бумаги по id """
def get_active(db: Session, active_id: int) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.id == active_id).first()

""" Получение последнего id инструмента"""
def get_last_active_id(db: Session) -> int:
    model_instrument = db.query(models.Instrument).order_by(models.Instrument.id.desc()).first()

    if not model_instrument:
        return 0
    else:
        return model_instrument.id

""" Получение таймфрейма по id """
def get_timeframe(db: Session, timeframe_id: int) -> Optional[models.Timeframe]:
    return db.query(models.Timeframe).filter(models.Timeframe.id == timeframe_id).first()

""" Получение id последней записи в таблице "Timeframe" """
def get_last_timeframe_id(db: Session) -> Optional[int]:
    db_timeframe = db.query(models.Timeframe).order_by(models.Timeframe.id.desc()).first()
    return db_timeframe.id if db_timeframe else None

""" Получение id таймфрейма по названию """
def get_timeframe_id(db: Session, timeframe_name: str) -> Optional[int]:
    db_timeframe = db.query(models.Timeframe).filter(models.Timeframe.name == timeframe_name).first()
    return db_timeframe.id if db_timeframe else None

""" Проверка на наличие таймфрейма в базе """
def check_timeframe(db: Session, timeframe_name: str) -> bool:
    db_timeframe = db.query(models.Timeframe).filter(models.Timeframe.name == timeframe_name).first()
    return True if db_timeframe else False

""" Получение бумаги по название """
def get_active_by_name(db: Session, active_name: str) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.name == active_name).first()

""" Получение бумаги по FIGI """
def get_active_by_figi(db: Session, figi: str, exchange_id: int = 1) -> Optional[models.Instrument]:
    db_figi = db.query(models.Instrument).filter(models.Instrument.figi == figi).first()
    return db_figi

""" Получение бумаги по тикеру """
def get_active_by_ticker(db: Session, ticker: str) -> Optional[models.Instrument]:
    return db.query(models.Instrument).filter(models.Instrument.ticker == ticker).first()

""" Получение инструментов определенной биржи """
def get_actives_by_exchange(db: Session, exchange_id: int) -> Optional[list[models.Instrument]]:
    return db.query(models.Instrument).filter(models.Instrument.id_exchange == exchange_id).order_by(models.Instrument.name).all()

def get_filter_by_exchange_actives(db: Session, exchange_id: list[int]) -> Optional[list[models.Instrument]]:
    return db.query(models.Instrument).filter(models.Instrument.id_exchange.in_(exchange_id)).order_by(models.Instrument.name).all()

""" Получение списка бирж """
def get_exchange_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Exchange]]:
    return db.query(models.Exchange).offset(skip).limit(limit).all()

""" Получение списка секторов """
def get_sectors_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Sector]]:
    return db.query(models.Sector).offset(skip).limit(limit).all()

""" Получение списка бумаг """
def get_instrument_list(db: Session, skip: int = 0, limit: int = 100) -> list[Optional[models.Instrument]]:
    return db.query(models.Instrument).offset(skip).limit(limit).all()

""" Получение списка 10 свеч по инструменту за определенный таймфрейм"""
def get_candles_list(db: Session, figi_id: int, frame_id: int) -> list[Optional[models.Candle]]:
    # Выбираем 10 последних свечей по инструменту за заданный таймфрейм
    return db.query(models.Candle).filter(models.Candle.id_instrument == figi_id,
                                          models.Candle.id_timeframe == frame_id).order_by(
        models.Candle.time_m.desc()).limit(10).all()

""" Получение свечи по id """
def get_candle(db: Session, candle_id: int) -> Optional[models.Candle]:
    return db.query(models.Candle).filter(models.Candle.id == candle_id).first()

""" Поулчаем последнюю свечу """
def get_last_candle(db: Session, figi_id: int, frame_id: int) -> Optional[models.Candle]:
    return db.query(models.Candle).filter(models.Candle.id_instrument == figi_id,
                                          models.Candle.id_timeframe == frame_id).order_by(
        models.Candle.time_m.desc()).limit(1)

""" Получаем id последней свечи по figi иснтрумента"""
def get_last_candle_id(db: Session) -> Optional[int]:
    return db.query(models.Candle).order_by(models.Candle.id.desc()).first().id


""" Поулчаем две последние свечи """
def get_last_candles(db: Session, figi_id: int, frame_id: int) -> tuple[Optional[models.Candle]]:
    last_candles = db.query(models.Candle).filter(models.Candle.id_instrument == figi_id,
                                                  models.Candle.id_timeframe == frame_id).order_by(models.Candle.time_m.desc()).limit(2)
    if len(last_candles) != 2:
        raise Exception("Недостаточно элементов в списке")
    return last_candles[1], last_candles[0]


""" (1) Отладочный метод """
def get_last_active_rezerve_id(db: Session) -> int:
    db_instrument_rezerve = db.query(models.InstrumentRezerve).order_by(models.InstrumentRezerve.id.desc()).first()
    if not db_instrument_rezerve:
        return 0
    return db_instrument_rezerve.id

""" (3) Отладочный метод"""
def get_rezerve_active_by_figi(db: Session, figi: str) -> Optional[models.InstrumentRezerve]:
    return db.query(models.InstrumentRezerve).filter(models.InstrumentRezerve.figi == figi).first()


""" CREATE-операции """
""" Создание новой валюты"""
def create_currency(db: Session, id: Optional[int], name: str) -> models.Currency:
    new_id = None
    if id:
        new_id = id
    else:
        new_id = get_last_currency_id(db)
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
        new_id = get_last_exchange_id(db)
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
        new_id = get_last_sector_id(db)
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


""" Добавление нового инструмена в базу данных """
def create_instrument(db: Session, **kwargs):

    db_currency = get_currency(db, kwargs['currency_id'])
    if not db_currency:
        raise ValueError("Валюта не найдена")

    db_exchange = get_exchange(db, kwargs['exchange_id'])
    if not db_exchange:
        raise ValueError("Биржа не найдена")

    db_sector = get_sector(db, kwargs['sector_id'])
    if not db_sector:
        raise ValueError("Сектор не найден")

    last_active_id = get_last_active_id(db)
    new_id = None

    if last_active_id == 0:
        new_id = 1
    else:
        new_id = last_active_id + 1

    instrument = models.Instrument(id=new_id, figi=kwargs['figi'], name=kwargs['name'],
                                   ticker=kwargs['ticker'], lot=kwargs['lot'], id_currency=kwargs['currency_id'],
                                   id_exchange=kwargs['exchange_id'], id_sector=kwargs['sector_id'])
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument

""" (2) Отладочный метод """
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


""" Добавление новой свечи в базу данных """
def create_candle(db: Session, **kwargs):

    db_instrument = get_active(db, kwargs['id_figi'])
    if not db_instrument:
        raise ValueError("Инструмент не найден")

    db_timeframe = get_timeframe(db, kwargs['id_timeframe'])
    if not db_timeframe:
        raise ValueError("Таймфрейм не найден")

    candle = models.Candle(id=kwargs['id'], time_m=kwargs['time_m'], open=kwargs['open'],
                           high=kwargs['high'], low=kwargs['low'], close=kwargs['close'],
                           volume=kwargs['volume'], id_figi=kwargs['id_figi'], id_timeframe=kwargs['id_timeframe'])

    try:
        db.add(candle)
    except UnmappedInstanceError as UIerror:
        print(UIerror.with_traceback())

    db.commit()
    db.refresh(candle)
    return candle

"""DELETE-операции"""

""" Удаление сектора """
def delete_sector(db: Session, id: int):
    db_sector = get_sector(db, id)
    if not db_sector:
        raise ValueError("Сектор не найден")
    db.delete(db_sector)
    db.commit()
    return db_sector

"""Удаление валюты"""
def delete_currency(db: Session, id: int):
    db_currency = get_currency(db, id)
    if not db_currency:
        raise ValueError("Валюта не найдена")
    db.delete(db_currency)
    db.commit()


""" Удаление биржи  """
def delete_exchange(db: Session, id: int):
    db_exchange = get_exchange(db, id)
    if not db_exchange:
        raise ValueError("Биржа не найдена")
    db.delete(db_exchange)
    db.commit()

""" Удаление таймфрейма """
def delete_timeframe(db: Session, id: int):
    db_timeframe = get_timeframe(db, id)
    if not db_timeframe:
        raise ValueError("Таймфрейм не найден")
    db.delete(db_timeframe)
    db.commit()

""" Удаление иснтрумента """
def delete_instrument(db: Session, id: int):
    db_instrument = get_active(db, id)
    if not db_instrument:
        raise ValueError("Инструмент не найден")
    db.delete(db_instrument)
    db.commit()

""" Удаление свечи """
def delete_candle(db: Session, id: int):
    db_candle = get_candle(db, id)
    if not db_candle:
        raise ValueError("Свеча не найдена")
    db.delete(db_candle)
    db.commit()