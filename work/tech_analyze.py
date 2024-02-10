# Модуль отладки инструментов тех. анализа
from abc import ABC, abstractmethod  # Для абстрактных классов и интерфейсов
from datetime import datetime
from typing import Union
from math import floor
import pandas as pd

from tinkoff.invest.schemas import HistoricCandle

import core_bot

Trend = "FLAT"      # Текущий тренд

def formatCandle(size: int, candles: list[HistoricCandle]):
    """
    Генерирует форматирунную историческую свечу, переводя исходную
    в словарь со стрковыми и вещественными значениями

    :param size:    Количество исторических свечей в исходном массиве
    :param candles: Массив исторических свечей
    :return:        Форматированная историческая свеча
    """
    i = 0

    while i != size:
        up_candle = dict()
        up_candle['time'] = candles[i].time.strftime('%Y-%m-%d_%H:%M:%S')
        up_candle['open'] = core_bot.cast_money(candles[i].open)
        up_candle['close'] = core_bot.cast_money(candles[i].close)
        up_candle['min'] = core_bot.cast_money(candles[i].low)
        up_candle['max'] = core_bot.cast_money(candles[i].high)
        yield up_candle
        i += 1


# Интерфейс для индикатора MA
class MA_indicator(ABC):
    """
    Интерфейс для реализации индикатора "Скользящая средняя" (MA).
    Индикатор вычисляется как среднее значение за N последних таймфреймов

    Methods
    -------
    MA_build(MA_interval: int, param_list: str) - Построение MA по каждому таймфрейму
    MA_signal(bars_MA: list[dict[str, Union[float, str]]]) - формирование торговых сигналов
    по значениям скользящей средней
    """

    @staticmethod
    @abstractmethod
    def MA_build(MA_interval: int, cntOfCandles: int):
        pass

    @staticmethod
    @abstractmethod
    def MA_signal(bars_MA: list[dict[str, Union[float, str]]]):
        pass


# Обычная MA
class SMA_indicator(MA_indicator):

    # Отладочный метод, вычисляющий MA для каждого момента времени из интервала
    # MA_interval - интервал усреднения для скользящей средней
    @staticmethod
    def MA_build(MA_interval: int, cntOfCandles: int) -> dict[str, float]:

        if MA_interval <= 0:
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
        smaValues['SMA_'+str(MA_interval)] = list([])    # Список значений SMA

        sma_val = 0.0   # SMA

        for i in range(left, size):
            if i - left >= MA_interval - 1:
                start_bar = i - left - MA_interval + 1  # Первая свеча из интервала для расчета SMA
                end_bar = i + 1                         # Последняя свеча из интервала для расчета SMA
                sum_bar = 0.0
                for j in range(start_bar, end_bar):
                    sum_bar += up_candles.iloc[j]['close']
                    #sum_bar += up_candles[j]['close']
                sma_val = sum_bar / MA_interval         # Расчет SMA

            # Добавляем рассчитаное значение в словарь SMA
            smaValues['time'].append(up_candles.iloc[i]['time'])
            smaValues['SMA_'+str(MA_interval)].append(sma_val)

        return smaValues        # Возвращаем таблицу значений SMA

    '''
    Метод, выдающий торговые сигналы для прошедших моментов времени :)
    bars_MA - словарь, где ключ - момент времени
    значение - список:
    0-ой элемент списка - цена закрытия
    1-ый элемент списка - значение MA для данного момента времени
    '''

    @staticmethod
    def MA_signal(bars_MA: list[dict[str, Union[float, str]]]):
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
class EMA_indicator(MA_indicator):

    @staticmethod
    def MA_build(MA_interval: int, cntOfCandles: int):
        pass
        '''
        if MA_interval <= 0:
            raise ValueError(
                'Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        #candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = cntOfCandles
        #up_candles = list([])
        ema_val = 0.0

        Weight = 2 / (MA_interval + 1)  # Вычисляем вес EMA
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
    def MA_signal(bars_MA: list[dict[str, Union[float, str]]]):
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


# Индекс относительной силы (RSI)
class RSI:

    def __init__(self, RSI_interval: int = 14):
        self.RSI_interval = RSI_interval
        self.EMA_up = list([])
        self.EMA_close = list([])

        # Первые N EMA_up и EMA_close нулевые
        for i in range(RSI_interval):   
            self.EMA_up.append(0.0)
            self.EMA_close.append(0.0)



    def build(self, param_list: str):
        if self.RSI_interval <= 0:
            raise ValueError(
                'Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        EMA_up, EMA_close = 0, 0                   # EMA роста и EMA падения
        candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)
        up_candles = list([])

        gen_up_candle = formatCandle(size, candles)

        i = 0
        print('Time          Close    RSI')
        for up_candle in gen_up_candle:

            # Рассчитываем EMA роста и EMA падения
            if i < self.RSI_interval - 1:
                up_candle['RSI'] = 0.0
            else:
                for j in range(i-self.RSI_interval+1, i+1):

                    change = 0.0
                    if j != i:
                        change = up_candles[j]['close'] - up_candles[j]['open']
                    else:
                        change = up_candle['close'] - up_candle['open']

                    if change > 0:
                        EMA_up += abs(change)
                    else:
                        EMA_close += abs(change)
                RS = EMA_up / EMA_close
                up_candle['RSI'] = 100 - 100 / (1 + RS)
                EMA_up, EMA_close = 0.0, 0.0
 
            up_candles.append(up_candle)
            time_val = up_candles[i]['time']
            close = up_candles[i]['close']
            rsi = up_candles[i]['RSI']
            print(f'{time_val}  ', '%.2f' % close, '%.2f' % rsi)
            i += 1

        print('\n\n')
        return up_candles

# Модель "Голова и плечи" (Перевернутые голова и плечи)
class HAS_model:

    def __init__(self):
        global Trend

        self.type = "BULL"
        self.prev_trend = Trend
        self.cur_trend = Trend
        self.shoulders = list([])
        self.head = 0.0
        self.neck = list([])
        self.up_candles = list([])

    # Поиск модели ГиП и выставление торговых сигналов
    def build(self, param_list: str):
        candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)                          # Количество исторических свечей
        gen_up_candle = formatCandle(size, candles)  # Генератор форматированных свечей
        #up_candles = list([])

        for up_candle in gen_up_candle:
            self.prev_trend = self.cur_trend         # Предыдущий тренд равен текущему
            self.up_candles.append(up_candle)        # Добавляем свечу в список свечей
            if len(self.up_candles) >= 50:           # Нельзя, чтобы свечей было много
                self.up_candles.pop(0)

            # Когда свечей больше, чем 2
            if len(self.up_candles) >= 2:
                if self.up_candles[-1]['min'] > self.up_candles[-2]['min']: # Если MIN последней свечи больше MIN
                    self.cur_trend = "BULL"                                # предыдущей, то тренд бычий
                elif self.up_candles[-1]['max'] < self.up_candles[-2]['max']:  # Если MAX последней меньше MAX
                    self.cur_trend = "BEAR"                                # предыдущей, то тренд медвежий

           # Если предыдущий тренд НЕ флэтовый (НЕ самые первые свечи)
            if self.prev_trend != 'FLAT':
               if self.cur_trend == "BEAR" and self.prev_trend == "BULL":  # Если локальный MAX

                   # Если мы нашли плечо и разница между этим плечом и текущим MAX больше 5
                   if len(self.shoulders) != 0 and abs(self.up_candles[-2] - self.shoulders[0]) > 5:
                       self.head = self.up_candles[-2]         # Значит мы нашли голову
                   elif len(self.shoulders) == 0 or abs(self.up_candles[-2] - self.shoulders[0]) <= 5: # Если плеч нет или есть левое плечо и разница
                       self.shoulders.append(self.up_candles[-2])       # между текущим MAX и левым плечом меньше 0, то значит мы нашли правое плечо
               elif self.cur_trend == "BULL" and self.prev_trend == "BEAR":   # Если локальный MIN
                   if len(self.neck) == 0:                    # Если нет уровня шеи
                       self.neck.append(self.up_candles[-2])  # То регистрируем его
                   elif len(self.neck) == 1 and abs(self.up_candles[-2] - self.neck[0]) < 5: # Достигаем уровня шеи
                       self.neck.append(self.up_candles[-2])   # второй раз перед возврщением к плечу
                   elif self.up_candles[-1].close < self.neck[1]:    # Если цена закрытия последней свечи меньше уровня шеи
                       signal = 'SELL'          # То кидаем сигнал на продажу
                       return signal


# Индикатор MACD
class MACD:

    def __init__(self):
        self.MACD = list([])     # Значения MACD
        self.signal = list([])   # Значения линии Signal
        self.EMA_S = list([])    # Значения EMA_s
        self.EMA_I = list([])    # Значения EMA_i
        self.EMA_A = list([])    # Значения EMA_a


    def build(self, param_list: str):
        candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)
        up_candles = list([])
        gen_up_candle = formatCandle(size, candles)

        ema_candles_9 = EMA_indicator.MA_build(9, param_list=param_list)
        i = 0
        for elem in ema_candles_9:
            self.EMA_A.append(ema_candles_9[i]['ema'])
            i += 1
        del ema_candles_9

        ema_candles_12 = EMA_indicator.MA_build(12, param_list=param_list)
        i = 0
        for elem in ema_candles_12:
            self.EMA_S.append(ema_candles_12[i]['ema'])
            i += 1
        del ema_candles_12

        ema_candles_26 = EMA_indicator.MA_build(26, param_list=param_list)
        i = 0
        for elem in ema_candles_26:
            self.EMA_I.append(ema_candles_26[i]['ema'])
            i += 1
        del ema_candles_26

        i = 0
        print('Time          Close    RSI')

        for up_candle in gen_up_candle:
            up_candles.append(up_candle)
            macd = self.EMA_S[i] - self.EMA_I[i]
            signal = self.EMA_A[i] * macd
            macd_dict = {'macd': macd}
            self.MACD.append(macd_dict)
            self.signal.append(signal)
            i += 1

        return up_candles

    def macd_signal(self, bars):

        print("\n\nOpen Close Change MACD Signal")
        for i in range(-10, 0):
            change = bars[i]['close'] - bars[i]['open']
            print("Open = %.2f RUB" % bars[i]['open'] + " Close = %.2f RUB " % bars[i]['close'] +
                  "%.2f RUB" % change + " %.2f " % self.MACD[i]['macd'] + " %.2f" % self.signal[i])

        if len(self.MACD) > 2 and len(self.signal) > 2:
            if type(self.MACD[-1]) != type(dict()):
                raise TypeError('Element of MACD must be a dict')
            if self.MACD[-1]['macd'] > self.signal[-1] and self.MACD[-2]['macd'] < self.signal[-2]:
                self.MACD[-1]['signal'] = 'BUY'
                return 1
            elif self.MACD[-1]['macd'] < self.signal[-1] and self.MACD[-2]['macd'] > self.signal[-2]:
                self.MACD[-1]['signal'] = 'SELL'
                return -1
            else:
                return 0

# Цикл, моделирующиц торговлю
def run_main():
    figi = 'TCS7238U2033'  # Фиги торгуемого инструемента (Тинькофф)
    lot = 1  # лотность инструмента
    cnt_lots = 1000  # Количество лотов Tinkoff в портфеле
    account_portfolio = 100000.00  # Размер портфеля в рублях
    start_sum = account_portfolio
    ma_interval = 5
    ma_key = 'SMA_' + str(ma_interval)

    # Условия расчета позиции
    stopAccount = 0.01  # Риск для счета в процентах
    stopLoss = 0.05     # Точка аннулирования для торговой стратегии в процентах

    CandlesDF = pd.read_csv("../share_history.csv")       # 1. Получаем готовый датафрейм исторических свечей
    MAXInter = 3                                          # Max количество пересечений на интервал
    CNT_timeframe = 10                                    # Длина проверяемого интервала
    cntInter = 0                                          # Количество пересечений
    lot_cast = (CandlesDF.iloc[0]['close'] + CandlesDF.iloc[0]['open']) / 2  # Рыночная цена одного лота (типа)
    positionSize = 0.0                                    # Размер позиции
    totalSharePrice = lot_cast * cnt_lots                 # Общая стоимость акций Тинькофф в портфеле
    getLots = 0

    iter_sma = 0    # Итератор для SMA значений
    cnt50 = 0

    print("INFO\n-------------\n\nStart sum on account: %.2f RUB " % start_sum +
          f"\nTime: {CandlesDF.iloc[0]['time']}" +
          "\nStart count of Tinkoff lots: " + str(cnt_lots) +
          "\nCast per Tinkoff lot: %.2f RUB" % lot_cast +
          "\nTotal instrument price: %.2f RUB" % floor(totalSharePrice) +
          "\nAccountant max loss: %.2f" % stopAccount +
          "\nStop loss: %.2f\n" % stopLoss +
          "--------------------------\n")

    # Анализируем свечи из выделенного интервала
    for i in range(CandlesDF.shape[0]):
        BUY_Signal = False
        SELL_Signal = False

        # Вывод информации об аккаунте
        print("INFO ABOUT ACCOUNT\n--------------------------\n" +
              f"\nTime: {CandlesDF.iloc[i]['time']}" +
              "\nStart sum on account: %.2f RUB " % start_sum +
              "\nCurrent sum on account: %.2f RUB " % account_portfolio +
              "\nCurrent count of Tinkoff lots: " + str(cnt_lots) +
              "\nCast per Tinkoff lot: %.2f RUB" % lot_cast +
              "\nTotal instrument price: %.2f RUB" % floor(totalSharePrice) +
              "--------------------------\n")

        # Если количество свеч для построения SMA недостаточно, продолжаем цикл
        if i < ma_interval - 1:                                         # Если номер свечи меньше периода SMA, то просто делаем итерацию без действий
            iter_sma += 1
            continue

        SMA_Values = SMA_indicator.MA_build(MA_interval=ma_interval, cntOfCandles=i+1)

        # Обновляем счетчик для SMA
        if i != 0 and i % 50 == 0:
            cnt50 += 1
            iter_sma = iter_sma - cnt50 * 50

        if i < 0:
            raise IndexError

        BUY_Signal = CandlesDF.iloc[i - 1]['close'] < SMA_Values[ma_key][iter_sma - 1] and CandlesDF.iloc[i]['close'] > SMA_Values[ma_key][iter_sma]
        SELL_Signal = CandlesDF.iloc[i - 1]['close'] > SMA_Values[ma_key][iter_sma - 1] and CandlesDF.iloc[i]['close'] < SMA_Values[ma_key][iter_sma]

        if BUY_Signal or SELL_Signal:
            # Торговый сигнал  сработал, проверяем
            start_frame = 0
            if i < CNT_timeframe:
                start_frame = 0
            else:
                start_frame = i - CNT_timeframe

            iter_smaPrev = list([iter_sma, iter_sma + 1])

            for j in range(start_frame + 1, i + 1):
                # Считаем количество персечений SMA в 10 предыдущих таймфреймах
                if CandlesDF.iloc[j - 1]['close'] < SMA_Values[ma_key][iter_smaPrev[0]] and CandlesDF.iloc[j]['close'] > SMA_Values[ma_key][iter_smaPrev[1]]:
                    cntInter += 1
                iter_smaPrev[0] += 1
                iter_smaPrev[1] += 1

            # Если количество пересечений не очень большое, то совершаем сделку
            if cntInter < MAXInter:
                positionSize = account_portfolio * stopAccount / stopLoss   # Расчитываем размер позиции (сделки)

                if BUY_Signal:
                    account_portfolio -= positionSize             # Перечисляем деньги за сделку брокеру в случае покупки
                else:
                    account_portfolio += positionSize             # Получаем деньги за сделку от брокера в случае продажи

                lot_cast = (CandlesDF.iloc[j]['close'] + CandlesDF.iloc[j]['open']) / 2 # Рыночная цена одного лота (типа)
                getLots = floor(positionSize / lot_cast)

                if BUY_Signal:
                    cnt_lots += getLots  # Получаем лоты инструмента (акции Тинькофф) на счет
                else:
                    cnt_lots -= getLots  # Продаем лоты инструмента (акции Тинькофф) брокеру

                totalSharePrice = lot_cast * cnt_lots                       # Общая стоимость акций Тинькофф в портфеле

                # Вывод информации о сделке
                if BUY_Signal:
                    print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                          "\nBUY - %2.f RUB" % positionSize + "\n+ " + str(getLots) + " Tinkoff lots" +
                          "--------------------------\n")
                else:
                    print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                          "\nSELL + %2.f RUB" % positionSize + "\n- " + str(getLots) + " Tinkoff lots" +
                          "--------------------------\n")

        iter_sma += 1


if __name__ == '__main__':
    run_main()