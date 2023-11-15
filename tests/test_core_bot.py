import unittest
from datetime import datetime, timezone

from tinkoff.invest import CandleInterval

from work.core_bot import CandlesParamsSettings, getCandles

class CoreBotTest(unittest.TestCase):
    def test_CandlesParamsSettings(self):
        test_param_list = list(['/get_candles', 'BBG004730N88', '2022-07-16_00:00:00', '2022-10-16_00:00:00', 'HOUR'])
        moment1 = datetime(year=2022, month=7, day=16, hour=0, minute=0, second=0, tzinfo=timezone.utc)
        moment2 = datetime(year=2022, month=10, day=16, hour=0, minute=0, second=0, tzinfo=timezone.utc)
        candleInterval = CandleInterval.CANDLE_INTERVAL_HOUR

        resParamTuple = (test_param_list[1], moment1, moment2, candleInterval)
        self.assertEqual(CandlesParamsSettings(test_param_list), resParamTuple)