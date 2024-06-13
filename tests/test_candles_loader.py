import unittest
import asyncio

from app.candles_loader import *
from api import *

class TestCandlesLoader(unittest.TestCase):
    def setUp(self):
        self.candlesLoader = CandlesLoader()

    def test_get_lot(self):
        db = SessionLocal()
        sber_lot = 10
        uid = "e6123145-9665-43e0-8413-cd61b8aa9b13"
        self.assertEqual(self.candlesLoader.get_lot(db, uid), sber_lot, "Лотность вычислена правильно")

    def test_load_candles(self):
        db = SessionLocal()
        last_time_dict = self.candlesLoader._check_last_candles(db)
        uid = list(last_time_dict.keys())
        size = len(uid)
        if size > 0:
            uid = uid[0]
            last_date = last_time_dict[uid]
            asyncio.run(self.candlesLoader._load_candles(db, uid, last_date))
            candles = crud.get_candles_list(db, uid, 2)
            last_time = candles[0].time_m
            cur_time = datetime.now()
            delta = cur_time.timestamp() - last_time.timestamp()
            self.assertLess(delta, 370)

if __name__ == "__main__":
    unittest.main()