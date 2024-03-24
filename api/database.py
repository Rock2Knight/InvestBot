""" Database engine """
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:asakura2150@localhost:5432/InvestBotDatabase"

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Создание БД с нуля
def create_db(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)