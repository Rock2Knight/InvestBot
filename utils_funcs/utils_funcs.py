from functools import cache
import math
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import pytz

from tinkoff.invest import RequestError
from tinkoff.invest.schemas import (
    MoneyValue, InstrumentStatus, Quotation,
    InstrumentIdType, AssetType, InstrumentType,
    CandleSource, Quotation, MoneyValue,
    CandleInterval, SubscriptionInterval,
    IndicatorInterval
)
from tinkoff.invest.sandbox.client import SandboxClient

load_dotenv()
TOKEN = os.getenv('TINKOFF_TOKEN')

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"

@cache
def get_str_type(value, is_asset=True):

    if is_asset:
        match value:
            case AssetType.ASSET_TYPE_UNSPECIFIED:
                return "UNSPECIFIED"
            case AssetType.ASSET_TYPE_COMMODITY:
                return "COMMODITY"
            case AssetType.ASSET_TYPE_CURRENCY:
                return "CURRENCY"
            case AssetType.ASSET_TYPE_INDEX:
                return "INDEX"
            case AssetType.ASSET_TYPE_SECURITY:
                return "SECURITY"
    else:
        match value:
            case InstrumentType.INSTRUMENT_TYPE_SHARE:
                return "SHARE"
            case InstrumentType.INSTRUMENT_TYPE_BOND:
                return "BOND"
            case InstrumentType.INSTRUMENT_TYPE_ETF:
                return "ETF"
            case InstrumentType.INSTRUMENT_TYPE_SP:
                return "SP"

@cache
def get_timeframe_by_name(value: str) -> CandleInterval:
    """
    Получение значения типа CandleInterval по его строковому аналогу
    :param value - строковое представление таймфрейма
    :return - значение CandleInterval, соотвестствующее нужному таймфрейму
    """
    match value:
        case 'UNSPECIFIED':
            return CandleInterval.CANDLE_INTERVAL_UNSPECIFIED
        case '1_MIN':
            return CandleInterval.CANDLE_INTERVAL_1_MIN
        case '5_MIN':
            return CandleInterval.CANDLE_INTERVAL_5_MIN
        case '15_MIN':
            return CandleInterval.CANDLE_INTERVAL_15_MIN
        case 'HOUR':
            return CandleInterval.CANDLE_INTERVAL_HOUR
        case 'DAY':
            return CandleInterval.CANDLE_INTERVAL_DAY
        case '2_MIN':
            return CandleInterval.CANDLE_INTERVAL_2_MIN
        case '3_MIN':
            return CandleInterval.CANDLE_INTERVAL_3_MIN
        case '10_MIN':
            return CandleInterval.CANDLE_INTERVAL_10_MIN
        case '30_MIN':
            return CandleInterval.CANDLE_INTERVAL_30_MIN
        case '2_HOUR':
            return CandleInterval.CANDLE_INTERVAL_2_HOUR
        case '4_HOUR':
            return CandleInterval.CANDLE_INTERVAL_4_HOUR
        case 'WEEK':
            return CandleInterval.CANDLE_INTERVAL_WEEK
        case 'MONTH':
            return CandleInterval.CANDLE_INTERVAL_MONTH

@cache
def get_sub_timeframe_by_name(timeframe_str: str) -> SubscriptionInterval:
    match timeframe_str:
        case '1_MIN':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
        case '2_MIN':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_2_MIN
        case '5_MIN':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIVE_MINUTES
        case '10_MIN':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_10_MIN
        case '15_MIN':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIFTEEN_MINUTES
        case '30_MIN':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_30_MIN
        case 'HOUR':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_HOUR
        case '2_HOUR':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_2_HOUR
        case '4_HOUR':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_4_HOUR
        case 'DAY':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_DAY
        case 'WEEK':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_WEEK
        case 'MONTH':
            return SubscriptionInterval.SUBSCRIPTION_INTERVAL_MONTH

@cache
def get_name_by_timeframe(frame: CandleInterval) -> str:
    """
    Получение значения строкового аналога объекта CandleInterval
    :param frame - значение CandleInterval, соотвестствующее нужному таймфрейму
    :return - строковое представление таймфрейма
    """
    match frame:
        case CandleInterval.CANDLE_INTERVAL_UNSPECIFIED:
            return 'UNSPECIFIED'
        case CandleInterval.CANDLE_INTERVAL_1_MIN:
            return '1_MIN'
        case CandleInterval.CANDLE_INTERVAL_5_MIN:
            return '5_MIN'
        case CandleInterval.CANDLE_INTERVAL_15_MIN:
            return '15_MIN'
        case CandleInterval.CANDLE_INTERVAL_HOUR:
            return 'HOUR'
        case CandleInterval.CANDLE_INTERVAL_DAY:
            return 'DAY'
        case CandleInterval.CANDLE_INTERVAL_2_MIN:
            return '2_MIN'
        case CandleInterval.CANDLE_INTERVAL_3_MIN:
            return "3_MIN"
        case CandleInterval.CANDLE_INTERVAL_10_MIN:
            return '10_MIN'
        case CandleInterval.CANDLE_INTERVAL_30_MIN:
            return '30_MIN'
        case CandleInterval.CANDLE_INTERVAL_2_HOUR:
            return '2_HOUR'
        case CandleInterval.CANDLE_INTERVAL_4_HOUR:
            return '4_HOUR'
        case CandleInterval.CANDLE_INTERVAL_WEEK:
            return 'WEEK'
        case CandleInterval.CANDLE_INTERVAL_MONTH:
            return 'MONTH'

def invest_api_retry(retry_count: int = 5, exceptions: tuple = ( RequestError, ValueError )):
    def errors_retry(func):

        def errors_wrapper(*args, **kwargs):
            attempts = 0

            while attempts < retry_count - 1:
                attempts += 1

                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if isinstance(exceptions, ValueError):
                        print(f"\n\nNo candles by instrument with uid = {args[0]}")
                    print(f"\nRetry exception attempt: {attempts}\n\n")

            return func(*args, **kwargs)

        return errors_wrapper

    return errors_retry

# Decorator retries api requests for some kind of exceptions
def candle_to_indicator(timeframe: CandleInterval):
    """ Сопоставление IndicatorInterval с CandleInterval """
    match timeframe:
        case CandleInterval.CANDLE_INTERVAL_1_MIN:
            return IndicatorInterval.INDICATOR_INTERVAL_ONE_MINUTE
        case CandleInterval.CANDLE_INTERVAL_2_MIN:
            return IndicatorInterval.INDICATOR_INTERVAL_2_MIN
        case CandleInterval.CANDLE_INTERVAL_5_MIN:
            return IndicatorInterval.INDICATOR_INTERVAL_FIVE_MINUTES
        case CandleInterval.CANDLE_INTERVAL_10_MIN:
            return IndicatorInterval.INDICATOR_INTERVAL_10_MIN
        case CandleInterval.CANDLE_INTERVAL_15_MIN:
            return IndicatorInterval.INDICATOR_INTERVAL_FIFTEEN_MINUTES
        case CandleInterval.CANDLE_INTERVAL_30_MIN:
            return IndicatorInterval.INDICATOR_INTERVAL_30_MIN
        case CandleInterval.CANDLE_INTERVAL_HOUR:
            return IndicatorInterval.INDICATOR_INTERVAL_ONE_HOUR
        case CandleInterval.CANDLE_INTERVAL_2_HOUR:
            return IndicatorInterval.INDICATOR_INTERVAL_2_HOUR
        case CandleInterval.CANDLE_INTERVAL_4_HOUR:
            return IndicatorInterval.INDICATOR_INTERVAL_4_HOUR
        case CandleInterval.CANDLE_INTERVAL_DAY:
            return IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY
        case CandleInterval.CANDLE_INTERVAL_WEEK:
            return IndicatorInterval.INDICATOR_INTERVAL_WEEK
        case CandleInterval.CANDLE_INTERVAL_MONTH:
            return IndicatorInterval.INDICATOR_INTERVAL_MONTH

@cache
def cast_money(sum: Quotation | MoneyValue) -> float:
    return sum.units + sum.nano / 1e9

@cache
def reverse_money(sum: float) -> Quotation:
    zsum = math.floor(sum)
    drob = sum - zsum
    drob = drob * 1e9
    itog_sum = Quotation(units=zsum, nano=int(drob))
    return itog_sum

@cache
def reverse_money_mv(sum: float) -> MoneyValue:
    zsum = math.floor(sum)
    drob = sum - zsum
    drob = drob * 1e9
    itog_sum = MoneyValue(units=zsum, nano=int(drob), currency='RUB')
    return itog_sum

""" На основе запроса пользователя формирует кортеж аргументов для вызова функции get_all_candles сервиса котировок """
def candles_formatter(paramList: list[str]):

    moment1_raw = None
    moment1 = None
    try:
        moment1_raw = datetime.strptime(paramList[2], '%Y-%m-%d_%H:%M:%S')
    except ValueError:
        logging.error("Invalid format of start datetime object\n")
        raise ValueError("Invalid format of start datetime object")
    finally:
        hour_value = 0
        if UTC_OFFSET == "Europe/Moscow":
            hour_value = moment1_raw.hour - 3
            if hour_value < 0:
                hour_value = 0
        moment1 = datetime(year=moment1_raw.year, month=moment1_raw.month, day=moment1_raw.day,
                       hour=hour_value, minute=moment1_raw.minute, second=moment1_raw.second,
                       tzinfo=timezone.utc)

    moment2_raw = None
    moment2 = None
    try:
        moment2_raw = datetime.strptime(paramList[3], '%Y-%m-%d_%H:%M:%S').replace(tzinfo=pytz.timezone('Europe/Moscow'))
    except ValueError:
        logging.error("Invalid format of end datetime object\n")
    finally:
        hour_value = 0
        if UTC_OFFSET == "Europe/Moscow":
            hour_value = moment2_raw.hour - 3
            if hour_value < 0:
                hour_value = 0
        moment2 = datetime(year=moment2_raw.year, month=moment2_raw.month, day=moment2_raw.day,
                        hour=hour_value, minute=moment2_raw.minute, second = moment2_raw.second,
                        tzinfo = timezone.utc)

    # Определение интервала свечи
    CI_str = paramList[4]
    candle_interval = get_timeframe_by_name(CI_str)

    return paramList[1], moment1, moment2, candle_interval


def get_candles(param_list: str):

    param_list = param_list.split(' ')    # Список параметров
    candlesParams = None                  # Список параметров для get_candles

    try:
        candlesParams = candles_formatter(param_list)
    except ValueError as error:
        logging.error(f"Ошибка во время выполнения метода core_bot.get_candles: {error.msg}\n")


    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы

        candles = list([])
        candles_raw = None
        try:
            candles_raw = client.market_data.get_candles(
                instrument_id=candlesParams[0],
                from_=candlesParams[1],
                to=candlesParams[2],
                interval=candlesParams[3]
            )
        except Exception as irerror:
            print('\n\n', irerror.args, '\n')
            raise irerror
        finally:
            for candle in candles_raw.candles:
                candles.append(candle)

    return candles