""" Модели таблиц SQLAlchemy """
from sqlalchemy import MetaData, Table, Integer, String, Column, ForeignKey, Numeric, TIMESTAMP, Boolean, TEXT
from sqlalchemy.orm import relationship
from .database import Base

metadata = MetaData()

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
    uid = Column(String, nullable=True)
    position_uid = Column(String, nullable=True)
    figi = Column(String, nullable=True)
    ticker = Column(String, nullable=True)
    class_code = Column(String(20), nullable=True)

    or_cur_ref = relationship("Instrument", backref="instr1_back", cascade="all, delete-orphan")

""" Таблица Exchange """
class Exchange(Base):
    __tablename__ = 'exchange'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

    or_exc_ref = relationship("Instrument", backref="instr2_back", cascade="all, delete-orphan")
    #or_exc_ref1 = relationship("InstrumentRezerve", backref="instr3_back", cascade="all, delete-orphan")

""" Таблица Timeframe """
class Timeframe(Base):
    __tablename__ = 'timeframe'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

    or_frm_ref = relationship("Candle", backref="cnd_back", cascade="all, delete-orphan")

""" Таблица AssetType """
class AssetType(Base):
    __tablename__ = 'asset_type'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

    as_ref = relationship("Asset", backref="as_back", cascade="all, delete-orphan")

""" Таблица InstrumentType """
class InstrumentType(Base):
    __tablename__ = 'instrument_type'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)

    ins_type_ref = relationship("Instrument", backref="ins_type_back", cascade="all, delete-orphan")


""" Таблица Asset """
class Asset(Base):
    __tablename__ = 'asset'

    uid = Column(String(100), primary_key=True, nullable=False)
    type_id = Column(Integer, ForeignKey("asset_type.id"), nullable=False)
    name = Column(TEXT, nullable=False)

    type_as_ref = relationship("AssetType", backref="type_as_back")

""" Таблица  Instrument """
class Instrument(Base):
    __tablename__ = 'instrument'

    uid = Column(String(100), primary_key=True, nullable=False)
    sector_id = Column(Integer, ForeignKey("sector.id"), nullable=False)
    currency_id = Column(Integer, ForeignKey("currency.id"), nullable=False)
    exchange_id = Column(Integer, ForeignKey("exchange.id"), nullable=False)
    asset_uid = Column(String(100), ForeignKey("asset.uid"), nullable=False)
    type_id = Column(Integer, ForeignKey("instrument_type.id"), nullable=False)

    position_uid = Column(String(100), nullable=False)
    figi = Column(String(15), nullable=False)
    name = Column(String(100), nullable=True)
    lot = Column(Integer, nullable=False)
    ticker = Column(String(100), nullable=True)
    class_code = Column(String(20), nullable=False)

    sector_ref = relationship("Sector", backref="sector_back")
    currency_ref = relationship("Currency", backref="currency_back")
    exchange_ref = relationship("Exchange", backref="exchange_back")
    instrument_type_ref = relationship("InstrumentType", backref="ins_type_back1")
    asset_ref = relationship("Asset", backref="as_back_instr1")
    candle_ref = relationship("Candle", backref="candle_back", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Instrument(id={self.id}, uid={self.uid}, position_uid={self.position_uid}, figi={self.figi}, name={self.name}, class_code={self.class_code}, ticker={self.ticker}, id_exchange={self.id_exchange})>"


""" Таблица для проверки наличия данных по инструменту """
'''
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
'''

""" Таблица Candle """
class Candle(Base):
    __tablename__ = 'candle'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uid_instrument = Column(String(100), ForeignKey("instrument.uid"), nullable=False)
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

    instr_ref = relationship("Instrument", backref="cnd_intsr_back")
    timeframe_ref = relationship("Timeframe", backref="fr_instr_back")

candleTable = Table('candle', metadata,
    Column('id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column('uid_instrument', String(100), ForeignKey("instrument.uid"), nullable=False),
    Column('id_timeframe', Integer, ForeignKey("timeframe.id"), nullable=False),
    Column('time_m', TIMESTAMP, nullable=False),
    Column('open', Numeric(precision=6), nullable=False),
    Column('close', Numeric(precision=6), nullable=False),
    Column('low', Numeric(precision=6), nullable=False),
    Column('high', Numeric(precision=6), nullable=False),
    Column('volume', Integer, nullable=False),
    Column('fast_sma', Numeric(precision=3), nullable=True),
    Column('slow_sma', Numeric(precision=3), nullable=True),
    Column('rsi', Numeric(precision=3), nullable=True)
)