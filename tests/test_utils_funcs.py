import unittest
from time import perf_counter

from utils_funcs import utils_funcs

from tinkoff.invest.schemas import (
    AssetType,
    InstrumentType,
    CandleInterval,
    SubscriptionInterval,
    IndicatorInterval,
    Quotation, MoneyValue
)

class UtilsFuncsTest(unittest.TestCase):
    def test_get_str_type(self):
        res_list = ['UNSPECIFIED', 'COMMODITY', 'CURRENCY', 'INDEX', 'SECURITY',
                    'SHARE', 'BOND', 'ETF', 'SP']

        self.assertEqual(res_list[0], utils_funcs.get_str_type(AssetType.ASSET_TYPE_UNSPECIFIED))
        self.assertEqual(res_list[1], utils_funcs.get_str_type(AssetType.ASSET_TYPE_COMMODITY))
        self.assertEqual(res_list[2], utils_funcs.get_str_type(AssetType.ASSET_TYPE_CURRENCY))
        self.assertEqual(res_list[3], utils_funcs.get_str_type(AssetType.ASSET_TYPE_INDEX))
        self.assertEqual(res_list[4], utils_funcs.get_str_type(AssetType.ASSET_TYPE_SECURITY))
        self.assertEqual(res_list[5], utils_funcs.get_str_type(InstrumentType.INSTRUMENT_TYPE_SHARE, False))
        self.assertEqual(res_list[6], utils_funcs.get_str_type(InstrumentType.INSTRUMENT_TYPE_BOND, False))
        self.assertEqual(res_list[7], utils_funcs.get_str_type(InstrumentType.INSTRUMENT_TYPE_ETF, False))
        self.assertEqual(res_list[8], utils_funcs.get_str_type(InstrumentType.INSTRUMENT_TYPE_SP, False))
        self.assertNotEqual(res_list[0], utils_funcs.get_str_type(InstrumentType.INSTRUMENT_TYPE_SHARE, False))

    def test_get_timeframe_by_name(self):
        # Проверка для значения 'UNSPECIFIED'
        self.assertEqual(utils_funcs.get_timeframe_by_name('UNSPECIFIED'), CandleInterval.CANDLE_INTERVAL_UNSPECIFIED)

        # Проверка для значения '1_MIN'
        self.assertEqual(utils_funcs.get_timeframe_by_name('1_MIN'), CandleInterval.CANDLE_INTERVAL_1_MIN)

        # Проверка для значения '5_MIN'
        self.assertEqual(utils_funcs.get_timeframe_by_name('5_MIN'), CandleInterval.CANDLE_INTERVAL_5_MIN)

        # Проверка для значения '15_MIN'
        self.assertEqual(utils_funcs.get_timeframe_by_name('15_MIN'), CandleInterval.CANDLE_INTERVAL_15_MIN)

        # Проверка для значения 'HOUR'
        self.assertEqual(utils_funcs.get_timeframe_by_name('HOUR'), CandleInterval.CANDLE_INTERVAL_HOUR)

        # Проверка для значения 'DAY'
        self.assertEqual(utils_funcs.get_timeframe_by_name('DAY'), CandleInterval.CANDLE_INTERVAL_DAY)

        # Проверка для значения '2_MIN'
        self.assertEqual(utils_funcs.get_timeframe_by_name('2_MIN'), CandleInterval.CANDLE_INTERVAL_2_MIN)

        # Проверка для значения '3_MIN'
        self.assertEqual(utils_funcs.get_timeframe_by_name('3_MIN'), CandleInterval.CANDLE_INTERVAL_3_MIN)

        # Проверка для значения '10_MIN'
        self.assertEqual(utils_funcs.get_timeframe_by_name('10_MIN'), CandleInterval.CANDLE_INTERVAL_10_MIN)

        # Проверка для значения '30_MIN'
        self.assertEqual(utils_funcs.get_timeframe_by_name('30_MIN'), CandleInterval.CANDLE_INTERVAL_30_MIN)

        # Проверка для значения '2_HOUR'
        self.assertEqual(utils_funcs.get_timeframe_by_name('2_HOUR'), CandleInterval.CANDLE_INTERVAL_2_HOUR)

        # Проверка для значения '4_HOUR'
        self.assertEqual(utils_funcs.get_timeframe_by_name('4_HOUR'), CandleInterval.CANDLE_INTERVAL_4_HOUR)

        # Проверка для значения 'WEEK'
        self.assertEqual(utils_funcs.get_timeframe_by_name('WEEK'), CandleInterval.CANDLE_INTERVAL_WEEK)

        # Проверка для значения 'MONTH'
        self.assertEqual(utils_funcs.get_timeframe_by_name('MONTH'), CandleInterval.CANDLE_INTERVAL_MONTH)

    def test_get_name_by_timeframe(self):
        # Проверка для значения CandleInterval.CANDLE_INTERVAL_UNSPECIFIED
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_UNSPECIFIED), 'UNSPECIFIED')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_1_MIN
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_1_MIN), '1_MIN')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_5_MIN
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_5_MIN), '5_MIN')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_15_MIN
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_15_MIN), '15_MIN')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_HOUR
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_HOUR), 'HOUR')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_DAY
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_DAY), 'DAY')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_2_MIN
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_2_MIN), '2_MIN')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_3_MIN
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_3_MIN), '3_MIN')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_10_MIN
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_10_MIN), '10_MIN')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_30_MIN
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_30_MIN), '30_MIN')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_2_HOUR
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_2_HOUR), '2_HOUR')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_4_HOUR
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_4_HOUR), '4_HOUR')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_WEEK
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_WEEK), 'WEEK')

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_MONTH
        self.assertEqual(utils_funcs.get_name_by_timeframe(CandleInterval.CANDLE_INTERVAL_MONTH), 'MONTH')

    def test_get_sub_timeframe_by_name(self):
        # Проверка для значения '1_MIN'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('1_MIN'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE)

        # Проверка для значения '2_MIN'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('2_MIN'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_2_MIN)

        # Проверка для значения '5_MIN'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('5_MIN'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIVE_MINUTES)

        # Проверка для значения '10_MIN'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('10_MIN'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_10_MIN)

        # Проверка для значения '15_MIN'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('15_MIN'),
                         SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIFTEEN_MINUTES)

        # Проверка для значения '30_MIN'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('30_MIN'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_30_MIN)

        # Проверка для значения 'HOUR'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('HOUR'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_HOUR)

        # Проверка для значения '2_HOUR'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('2_HOUR'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_2_HOUR)

        # Проверка для значения '4_HOUR'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('4_HOUR'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_4_HOUR)

        # Проверка для значения 'DAY'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('DAY'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_DAY)

        # Проверка для значения 'WEEK'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('WEEK'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_WEEK)

        # Проверка для значения 'MONTH'
        self.assertEqual(utils_funcs.get_sub_timeframe_by_name('MONTH'), SubscriptionInterval.SUBSCRIPTION_INTERVAL_MONTH)


    def test_candle_to_indicator(self):
        # Проверка для значения CandleInterval.CANDLE_INTERVAL_1_MIN
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_1_MIN),
                         IndicatorInterval.INDICATOR_INTERVAL_ONE_MINUTE)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_2_MIN
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_2_MIN),
                         IndicatorInterval.INDICATOR_INTERVAL_2_MIN)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_5_MIN
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_5_MIN),
                         IndicatorInterval.INDICATOR_INTERVAL_FIVE_MINUTES)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_10_MIN
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_10_MIN),
                         IndicatorInterval.INDICATOR_INTERVAL_10_MIN)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_15_MIN
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_15_MIN),
                         IndicatorInterval.INDICATOR_INTERVAL_FIFTEEN_MINUTES)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_30_MIN
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_30_MIN),
                         IndicatorInterval.INDICATOR_INTERVAL_30_MIN)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_HOUR
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_HOUR),
                         IndicatorInterval.INDICATOR_INTERVAL_ONE_HOUR)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_2_HOUR
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_2_HOUR),
                         IndicatorInterval.INDICATOR_INTERVAL_2_HOUR)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_4_HOUR
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_4_HOUR),
                         IndicatorInterval.INDICATOR_INTERVAL_4_HOUR)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_DAY
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_DAY),
                         IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_WEEK
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_WEEK),
                         IndicatorInterval.INDICATOR_INTERVAL_WEEK)

        # Проверка для значения CandleInterval.CANDLE_INTERVAL_MONTH
        self.assertEqual(utils_funcs.candle_to_indicator(CandleInterval.CANDLE_INTERVAL_MONTH),
                         IndicatorInterval.INDICATOR_INTERVAL_MONTH)

    def test_cast_money(self):
        t1 = perf_counter()
        self.assertEqual(utils_funcs.cast_money(Quotation(92, 156000000)), 92.156)  # add assertion here
        t2 = perf_counter()
        print(f"\nTime of work cast_money(): {t2-t1:.9f} sec\n")


    def test_reverse_money(self):
        # Аргументы для теста
        sum = 123.456
        expected_units = 123
        expected_nano = 456000000

        # Вызов функции и получение результата
        result = utils_funcs.reverse_money(sum)

        # Проверка результата
        self.assertIsInstance(result, Quotation)
        self.assertEqual(result.units, expected_units)
        self.assertEqual(result.nano, expected_nano)

    def test_reverse_money_mv(self):
        # Аргументы для теста
        sum = 123.456
        expected_units = 123
        expected_nano = 456000000

        # Вызов функции и получение результата
        result = utils_funcs.reverse_money_mv(sum)

        # Проверка результата
        self.assertIsInstance(result, MoneyValue)
        self.assertEqual(result.units, expected_units)
        self.assertEqual(result.nano, expected_nano)
        self.assertEqual(result.currency, 'RUB')

    def test_get_candles(self):
        request = "/get_candles 2024-05-23 10:00:00 2024-05-26 10:00:00_1 MIN"
        utils_funcs.get_candles(request)

if __name__ == '__main__':
    unittest.main()