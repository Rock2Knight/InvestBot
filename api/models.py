""" Модели таблиц SQLAlchemy """
from sqlalchemy import Integer, String, Column, ForeignKey, Numeric, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship
from .database import Base

""" Таблица Sector """
class Sector(Base):
    __tablename__ = 'sector'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

""" Таблица Currency """
class Currency(Base):
    __tablename__ = 'currency'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

    or_cur_ref = relationship("Instrument", backref="instr1_back", cascade="all, delete-orphan")

""" Таблица Exchange """
class Exchange(Base):
    __tablename__ = 'exchange'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

    or_exc_ref = relationship("Instrument", backref="instr2_back", cascade="all, delete-orphan")
    or_exc_ref1 = relationship("InstrumentRezerve", backref="instr3_back", cascade="all, delete-orphan")

""" Таблица Timeframe """
class Timeframe(Base):
    __tablename__ = 'timeframe'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

    or_frm_ref = relationship("Candle", backref="cnd_back", cascade="all, delete-orphan")

""" Таблица  Instrument """
class Instrument(Base):
    __tablename__ = 'instrument'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    figi = Column(String(15), nullable=False)
    name = Column(String, nullable=True)
    lot = Column(Integer, nullable=False)
    ticker = Column(String, nullable=False)
    id_sector = Column(Integer, ForeignKey("sector.id"),nullable=False)
    id_currency = Column(Integer, ForeignKey("currency.id"), nullable=False)
    id_exchange = Column(Integer, ForeignKey("exchange.id"), nullable=False)

    sector_ref = relationship("Sector", backref="sector_back")
    currency_ref = relationship("Currency", backref="currency_back")
    exchange_ref = relationship("Exchange", backref="exchange_back")
    candle_ref = relationship("Candle", backref="candle_back", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Instrument(id={self.id}, figi={self.figi}, name={self.name}, lot={self.lot}, ticker={self.ticker}, id_sector={self.id_sector}, id_currency={self.id_currency}, id_exchange={self.id_exchange})>"


""" Таблица для проверки наличия данных по инструменту """
class InstrumentRezerve(Base):
    __tablename__ = 'instrument_rezerve'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    figi = Column(String(15), nullable=False)
    name = Column(String, nullable=True)
    lot = Column(Integer, nullable=False)
    ticker = Column(String, nullable=False)
    id_exchange = Column(Integer, ForeignKey("exchange.id"), nullable=False)
    is_data = Column(Boolean, nullable=True)

    exchange_ref1 = relationship("Exchange", backref="exchange1_back")

""" Таблица Candle """
class Candle(Base):
    __tablename__ = 'candle'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    id_instrument = Column(Integer, ForeignKey("instrument.id"), nullable=False)
    id_timeframe = Column(Integer, ForeignKey("timeframe.id"), nullable=False)
    time_m = Column(TIMESTAMP, nullable=False)
    open = Column(Numeric(precision=6), nullable=False)
    low = Column(Numeric(precision=6), nullable=False)
    high = Column(Numeric(precision=6), nullable=False)
    close = Column(Numeric(precision=6), nullable=False)
    volume = Column(Integer, nullable=False)
    fast_sma = Column(Numeric(precision=3), nullable=True)
    slow_sma = Column(Numeric(precision=3), nullable=True)
    rsi = Column(Numeric(precision=3), nullable=True)

    figi_ref = relationship("Instrument", backref="cnd_intsr_back")
    timeframe_ref = relationship("Timeframe", backref="fr_instr_back")