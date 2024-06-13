""" Database engine """
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
db_name = os.getenv('DB_NAME')
user_name = os.getenv('DB_USER')
passw = os.getenv('DB_PASS')
port = os.getenv('DB_PORT')

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{user_name}:{passw}@localhost:{port}/{db_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

Base = declarative_base()

# Создание БД с нуля
def create_db(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)