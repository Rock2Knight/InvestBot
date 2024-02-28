# Модуль, содержащий реализацию индикатора скользящей средней
from abc import ABC, abstractmethod  # Для абстрактных классов и интерфейсов
from typing import Union
import pandas as pd

# Интерфейс для индикатора MA
class MAIndicator(ABC):
    """
    Интерфейс для реализации индикатора "Скользящая средняя" (MA).
    Индикатор вычисляется как среднее значение за N последних таймфреймов

    Methods
    -------
    ma_build(ma_interval: int, param_list: str) - Построение MA по каждому таймфрейму
    MA_signal(bars_MA: list[dict[str, Union[float, str]]]) - формирование торговых сигналов
    по значениям скользящей средней
    """

    @abstractmethod
    def __init__(self, ma_interval: int):
        pass

    @abstractmethod
    def ma_build(self, ma_interval: int, cntOfCandles: int) -> dict[str, list]:
        pass

    @staticmethod
    @abstractmethod
    def ma_signal(bars_MA: list[dict[str, Union[float, str]]]):
        pass


# Обычная MA
class SMAIndicator(MAIndicator):

    def __init__(self, ma_interval: int, CandlesDF):
        self.keyName = 'SMA_' + str(ma_interval)
        self.smaValues = dict()  # Словарь для значений SMA
        self.smaValues['time'] = list([])  # Список времени
        self.smaValues[self.keyName] = list([])  # Список значений SMA
        self.ma_interval = ma_interval
        self.dfSMA = None

        #up_candles = pd.read_csv("../share_history.csv")      # Свечи из опр. периода

        sma_val = 0.0  # SMA значение

        for i in range(CandlesDF.shape[0]):
            if i >= self.ma_interval - 1:
                start_bar = i - self.ma_interval + 1  # Первая свеча из интервала для расчета SMA
                end_bar = i + 1  # Последняя свеча из интервала для расчета SMA
                sum_bar = 0.0
                for j in range(start_bar, end_bar):
                    sum_bar += CandlesDF.iloc[j]['close']
                sma_val = sum_bar / self.ma_interval  # Расчет SMA

            # Добавляем рассчитаное значение в словарь SMA
            self.smaValues['time'].append(CandlesDF.iloc[i]['time'])
            self.smaValues[self.keyName].append(sma_val)

        self.dfSMA = pd.DataFrame(self.smaValues)
        self.dfSMA.to_csv("../sma_history.csv")

    def get_SMA(self, index: int):
        return self.dfSMA.iloc[index][self.keyName]

    # Метод, вычисляющий MA для каждого момента времени из интервала
    # ma_interval - интервал усреднения для скользящей средней
    def ma_build(self, ma_interval: int, cntOfCandles: int) -> dict[str, list]:

        if ma_interval <= 0:
            raise ValueError(
                'Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        #candles = core_bot.getCandles(param_list)  # Получаем исторические свечи через метод API
        up_candles = pd.read_csv("../share_history.csv")
        size = cntOfCandles
        left = 0                 # Номер свечи, с которой строим SMA

        if size < 50:
            left = 0
        else:
            left = size - 50

        smaValues = dict()                               # Словарь для значений SMA
        smaValues['time'] = list([])                     # Список времени
        smaValues['SMA_'+str(ma_interval)] = list([])    # Список значений SMA

        sma_val = 0.0   # SMA

        for i in range(left, size):
            if i - left >= ma_interval - 1:
                start_bar = i - left - ma_interval + 1  # Первая свеча из интервала для расчета SMA
                end_bar = i + 1                         # Последняя свеча из интервала для расчета SMA
                sum_bar = 0.0
                for j in range(start_bar, end_bar):
                    sum_bar += up_candles.iloc[j]['close']
                    #sum_bar += up_candles[j]['close']
                sma_val = sum_bar / ma_interval         # Расчет SMA

            # Добавляем рассчитаное значение в словарь SMA
            smaValues['time'].append(up_candles.iloc[i]['time'])
            smaValues['SMA_'+str(ma_interval)].append(sma_val)

        return smaValues        # Возвращаем таблицу значений SMA

    '''
    Метод, выдающий торговые сигналы для прошедших моментов времени :)
    bars_MA - словарь, где ключ - момент времени
    значение - список:
    0-ой элемент списка - цена закрытия
    1-ый элемент списка - значение MA для данного момента времени
    '''

    @staticmethod
    def ma_signal(bars_MA: list[dict[str, Union[float, str]]]):
        cmp_close: list[float] = list([0.0, 0.0])  # Список для сравнения цен закрытия
        cmp_ma: list[float] = list([0.0, 0.0])  # Список для сравнения значений MA
        signal = ' '  # Торговый сигнал
        bars_MA[0]['signal'] = ''
        cur_time = None

        sizeTimeList = len(bars_MA)  # Количество свечек
        for i in range(1, sizeTimeList):
            cmp_close[0] = bars_MA[i - 1]['close']
            cmp_close[1] = bars_MA[i]['close']
            cmp_ma[0] = bars_MA[i - 1]['sma']
            cmp_ma[1] = bars_MA[i]['sma']

            if bars_MA[i - 1]['close'] < bars_MA[i - 1]['sma'] and bars_MA[i]['close'] > bars_MA[i]['sma']:
                signal = 'BUY'  # График цен пересек SMA снизу вверх
            elif bars_MA[i - 1]['close'] > bars_MA[i - 1]['sma'] and bars_MA[i]['close'] < bars_MA[i]['sma']:
                signal = 'SELL'  # График цен пересек SMA сверху вниз

            if bars_MA[i - 1]['sma'] == 0.0:
                signal = ' '
            bars_MA[i]['signal'] = signal
            signal = ' '


# Экспоненциальная MA
class EMAIndicator(MAIndicator):

    @staticmethod
    def ma_build(ma_interval: int, cntOfCandles: int):
        pass
        '''
        if ma_interval <= 0:
            raise ValueError(
                'Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        #candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = cntOfCandles
        #up_candles = list([])
        ema_val = 0.0

        Weight = 2 / (ma_interval + 1)  # Вычисляем вес EMA
        #gen_up_candle = formatCandle(size, candles)

        i = 0
        print('Time                   Close   EMA')
        for up_candle in gen_up_candle:
            if i == 0:
                up_candle['ema'] = up_candle['close']
            else:
                up_candle['ema'] = (up_candles[i - 1]['close'] * Weight) + (
                        up_candles[i - 1]['ema'] * (1 - Weight))  # Рассчитываем EMA в конкретной точке по формуле
            close = up_candle['close']
            ema_val = up_candle['ema']
            time_val = up_candle['time']
            print(f'{time_val} ', '%.2f' % close, '%.2f' % ema_val)
            up_candles.append(up_candle)
            i += 1

        print('\n\n')
        return up_candles
        '''

    @staticmethod
    def ma_signal(bars_MA: list[dict[str, Union[float, str]]]):
        cmp_close: list[float] = list([0.0, 0.0])  # Список для сравнения цен закрытия
        cmp_ma: list[float] = list([0.0, 0.0])  # Список для сравнения значений MA
        signal = ' '  # Торговый сигнал
        bars_MA[0]['signal'] = ''
        cur_time = None

        sizeTimeList = len(bars_MA)  # Количество свечек
        for i in range(1, sizeTimeList):
            cmp_close[0] = bars_MA[i - 1]['close']
            cmp_close[1] = bars_MA[i]['close']
            cmp_ma[0] = bars_MA[i - 1]['ema']
            cmp_ma[1] = bars_MA[i]['ema']

            if bars_MA[i - 1]['close'] < bars_MA[i - 1]['ema'] and bars_MA[i]['close'] > bars_MA[i]['ema']:
                signal = 'BUY'  # График цен пересек SMA снизу вверх
            elif bars_MA[i - 1]['close'] > bars_MA[i - 1]['ema'] and bars_MA[i]['close'] < bars_MA[i]['ema']:
                signal = 'SELL'  # График цен пересек SMA сверху вниз

            if bars_MA[i - 1]['ema'] == 0.0:
                signal = ' '
            bars_MA[i]['signal'] = signal
            signal = ' '