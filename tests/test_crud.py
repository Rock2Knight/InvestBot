import unittest
from datetime import datetime, timedelta

from api import models, crud
from api.database import *

class CrudTest(unittest.TestCase):

    '''
    def test_create_candle(self):
        params = {
            'id': 10977,
            'uid_instrument': 'cc68221f-cc21-42a4-a52f-d819bfe4d4c0',
            'id_timeframe': 2,
            'open': 1400.56, 'close': 1401.61, 'high': 1402.12, 'low': 1398.53,
            'volume': 535425,
            'time_m': datetime.now()
        }

        db = SessionLocal()
        t1 = datetime.now()
        self.assertIsInstance(crud.create_candle(db, **params), models.Candle, "Метод вставки свечи в базу работает корректно")
        t2 = datetime.now()
        diff = t2 - t1
        print(f"Duratoin = {str(diff)}")
    '''

    def test_get_sector(self):
        db = SessionLocal()
        db_sector = crud.get_sector_by_name(db, 'energy')
        self.assertIsNotNone(db_sector, "Ответ для запроса <energy> не None!")
        if db_sector:
            print("Ответ для запроса <energy> не None!")
        db_sector = crud.get_sector_by_name(db, "lsdfdsf")
        self.assertIsNone(db_sector, "Ответ для запроса: None!")
        if not db_sector:
            print("Ответ для запроса: None!")

if __name__ == '__main__':
    unittest.main()