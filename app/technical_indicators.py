# Модуль, содержащий реализацию индикатора скользящей средней
from imports import *

from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.schemas import *

def analyze_interval(timeframe: CandleInterval):
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


def getSMA(uid_instrument, time_from, time_to, timeframe, interval=10):
    """ Получение покзателя SMA с длиной interval за указнный период """
    timeframe = utils_funcs.candle_to_indicator(timeframe)
    request = GetTechAnalysisRequest(
        indicator_type=IndicatorType.INDICATOR_TYPE_SMA,
        instrument_uid=uid_instrument,
        from_ = time_from,
        to= time_to,
        interval=timeframe,
        type_of_price=TypeOfPrice.TYPE_OF_PRICE_CLOSE,
        length=interval,
        smoothing=Smoothing.fast_length
    )

    response = None
    with SandboxClient(TOKEN) as client:
        response = client.market_data.get_tech_analysis(request=request)
    techs = response.technical_indicators
    return techs


def getEMA(uid_instrument: str, time_from, time_to, timeframe, interval=10):
    """ Получение покзателя EMA с длиной interval за указнный период """
    timeframe = utils_funcs.candle_to_indicator(timeframe)
    request = GetTechAnalysisRequest(
        indicator_type=IndicatorType.INDICATOR_TYPE_EMA,
        instrument_uid=uid_instrument,
        from_ = time_from,
        to= time_to,
        interval=timeframe,
        type_of_price=TypeOfPrice.TYPE_OF_PRICE_CLOSE,
        length=interval,
        smoothing=Smoothing.fast_length
    )

    response = None
    with SandboxClient(TOKEN) as client:
        response = client.market_data.get_tech_analysis(request=request)
    techs = response.technical_indicators
    return techs

def getRSI(uid_instrument: str, time_from, time_to, timeframe, interval=14):
    """ Получение покзателя RSI с длиной interval за указнный период """
    timeframe = utils_funcs.candle_to_indicator(timeframe)
    request = GetTechAnalysisRequest(
        indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
        instrument_uid=uid_instrument,
        from_ = time_from,
        to= time_to,
        interval=timeframe,
        type_of_price=TypeOfPrice.TYPE_OF_PRICE_CLOSE,
        length=interval,
        smoothing=Smoothing.fast_length
    )

    response = None
    with SandboxClient(TOKEN) as client:
        response = client.market_data.get_tech_analysis(request=request)
    techs = response.technical_indicators
    return techs


def getMACD(uid_instrument: str, time_from, time_to, timeframe, interval=10):
    """ Получение покзателя MACD с длиной interval за указнный период """
    timeframe = utils_funcs.candle_to_indicator(timeframe)
    request = GetTechAnalysisRequest(
        indicator_type=IndicatorType.INDICATOR_TYPE_MACD,
        instrument_uid=uid_instrument,
        from_ = time_from,
        to= time_to,
        interval=timeframe,
        type_of_price=TypeOfPrice.TYPE_OF_PRICE_CLOSE,
        length=interval,
        smoothing=Smoothing.fast_length
    )

    response = None
    with SandboxClient(TOKEN) as client:
        response = client.market_data.get_tech_analysis(request=request)
    techs = response.technical_indicators
    return techs