import unittest
from datetime import datetime

import pandas as pd

from work.MA_indicator import SMA_indicator

class TestMA_indicator(unittest.TestCase):
    def setUp(self):
        testCandles = pd.read_csv("../share_history.csv")
        self.sma_indicator = SMA_indicator(MA_interval=5, CandlesDF=testCandles)

    def test_getTime(self):
        test_sma_value = 1422.2400000000002
        sma_value = self.sma_indicator.get_SMA(-1)

        self.assertEqual(sma_value, test_sma_value)