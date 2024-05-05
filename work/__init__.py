resAsyncGetCandles = None
# Раздел констант
FIGI = "BBG00475KKY8"  # FIGI анализируемого инструемента
MAX_CNT_TICKS = 10     # Максимальное количество подписей по оси X
LOT = 1                # Лотность торгуемого инструмента
STOP_ACCOUNT = 0.01    # Риск для счета
STOP_LOSS = 0.05       # Стоп-лосс для актива
SMA_INTERVAL = 20
RSI_INTERVAL = 14
START_LOT_COUNT = 1000
START_ACCOUNT_PORTFOLIO = 1000000.00
excelFile = "excel_stats.xlsx" # Файл для записи статистики


__all__ = [
    "tech_analyze",
    "core_bot",
    "functional",
    "exceptions",
    "oscillators",
    "MA_indicator",
    "LOT",
    "STOP_ACCOUNT",
    "STOP_LOSS",
    "MAX_CNT_TICKS",
    "SMA_INTERVAL",
    "RSI_INTERVAL",
    "START_LOT_COUNT",
    "START_ACCOUNT_PORTFOLIO",
    "excelFile",
    "excel_handler"
]