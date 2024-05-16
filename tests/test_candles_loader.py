import unittest
import numpy as np

from app.candles_loader import *
from api import *

class TestCandlesLoader(unittest.TestCase):
    def setUp(self):
        self.candlesLoader = CandlesLoader()

    def test_get_lot(self):
        db = SessionLocal()
        vtb_lot = 10000
        self.candlesLoader._get_lot(db)
        test_vtb_lot = self.candlesLoader._lot
        self.assertEqual(test_vtb_lot, vtb_lot, "Лотность вычислена правильно")

    def test_get_instrument_info(self):
        test_array = np.empty((6,), dtype='<U100')
        test_array[0] = "e6123145-9665-43e0-8413-cd61b8aa9b13"
        test_array[1] = "41eb2102-5333-4713-bf15-72b204c4bf7b"
        test_array[2] = "BBG004730N88"
        test_array[3] = "TQBR"
        test_array[4] = "SBER"
        test_array[5] = "1_MIN"

        self.assertEqual(list(CandlesLoader.get_instrument_info("C:\\Users\\User\\PycharmProjects\\teleBotTest\\app\\config.txt")), list(test_array), "Массивы содержат одинаковую информацию")


if __name__ == "__main__":
    unittest.main()