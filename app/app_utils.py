from functools import cache

from tinkoff.invest.schemas import (
    AssetType,
    InstrumentType,
    CandleInterval
)

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