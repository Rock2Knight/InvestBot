resAsyncGetCandles = None
# Раздел констант
FIGI = "BBG00475KKY8"  # FIGI анализируемого инструемента
MAX_CNT_TICKS = 10     # Максимальное количество подписей по оси X
LOT = 1                # Лотность торгуемого инструмента
STOP_ACCOUNT = 0.01    # Риск для счета
STOP_LOSS = 0.05       # Стоп-лосс для актива]

__all__ = [
    "tech_analyze",
    "core_bot",
    "MA_indicator",
    "LOT",
    "STOP_ACCOUNT",
    "STOP_LOSS",
    "MAX_CNT_TICKS"
]