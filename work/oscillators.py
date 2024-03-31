# Модуль, хранящий классы, реализующие технические индикаторы-осцилляторы
from datetime import datetime

from tinkoff.invest.schemas import HistoricCandle

import pandas as pd
from MA_indicator import EMAIndicator
from functional import cast_money
import core_bot


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
        up_candle['open'] = cast_money(candles[i].open)
        up_candle['close'] = cast_money(candles[i].close)
        up_candle['min'] = cast_money(candles[i].low)
        up_candle['max'] = cast_money(candles[i].high)
        yield up_candle
        i += 1


# Индекс относительной силы (RSI)
class RSI:

    def __init__(self, filename: str, RSI_interval: int = 14):
        self.RSI_interval = RSI_interval
        self.RSI_df = None

        if self.RSI_interval <= 0:
            raise ValueError(
                'Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        EMA_up, EMA_close = 0, 0  # EMA роста и EMA падения
        self.CandlesDF = pd.read_csv(filename)
        rsiValues = dict()
        rsiValues['time'] = list([])
        rsiValues['RSI'] = list([])

        for i in range(self.CandlesDF.shape[0]):

            # Рассчитываем EMA роста и EMA падения
            rsiValues['time'].append(self.CandlesDF.iloc[i]['time'])
            if i < self.RSI_interval - 1:
                rsi_value = 0.0
                rsiValues['RSI'].append(0.0)
            else:
                for j in range(i - self.RSI_interval + 1, i):

                    change = 0.0
                    if j != i:
                        change = self.CandlesDF.iloc[j]['close'] - self.CandlesDF.iloc[j]['open']

                    if change > 0:
                        EMA_up += abs(change)
                    else:
                        EMA_close += abs(change)
                RS = EMA_up / EMA_close
                rsi_value = 100 - 100 / (1 + RS)
                rsiValues['RSI'].append(rsi_value)
                EMA_up, EMA_close = 0.0, 0.0

            if len(rsiValues['RSI']) == 0:
                continue

        self.RSI_df = pd.DataFrame(rsiValues)
        self.RSI_df.to_csv("rsi_history.csv")

    def get_RSI(self, index: int):
        return self.RSI_df.iloc[index]['RSI']


    def build(self, param_list: str, filename: str):
        if self.RSI_interval <= 0:
            raise ValueError(
                'Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        EMA_up, EMA_close = 0, 0  # EMA роста и EMA падения
        #candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        CandlesDF = pd.read_csv(filename)
        rsiValues = dict()
        rsiValues['time'] = list([])
        rsiValues['RSI'] = list([])
        rsi_value = 0.0

        #size = len(candles)

        #gen_up_candle = formatCandle(size, candles)

        #i = 0
        print('Time          Close    RSI')
        for i in range(CandlesDF.shape[0]):

            # Рассчитываем EMA роста и EMA падения
            if i < self.RSI_interval - 1:
                rsi_value = 0.0
            else:
                for j in range(i - self.RSI_interval + 1, i):

                    change = 0.0
                    if j != i:
                        change = CandlesDF.iloc[j]['close'] - CandlesDF.iloc[j]['open']

                    if change > 0:
                        EMA_up += abs(change)
                    else:
                        EMA_close += abs(change)
                RS = EMA_up / EMA_close
                rsi_value = 100 - 100 / (1 + RS)
                rsiValues['time'].append(CandlesDF.iloc[i]['time'])
                rsiValues['RSI'].append(rsi_value)
                EMA_up, EMA_close = 0.0, 0.0

            close = CandlesDF.iloc[i]['close']
            time_val = rsiValues['time'][-1]
            rsi_val_view = rsiValues['RSI'][-1]
            print(f'{time_val}  ', '%.2f' % close, '%.2f' % rsi_val_view)

        self.RSI_df = pd.DataFrame(rsiValues)
        self.RSI_df.to_csv("rsi_history.csv")

        print('\n\n')


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
        candles = core_bot.get_candles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)  # Количество исторических свечей
        gen_up_candle = formatCandle(size, candles)  # Генератор форматированных свечей
        # up_candles = list([])

        for up_candle in gen_up_candle:
            self.prev_trend = self.cur_trend  # Предыдущий тренд равен текущему
            self.up_candles.append(up_candle)  # Добавляем свечу в список свечей
            if len(self.up_candles) >= 50:  # Нельзя, чтобы свечей было много
                self.up_candles.pop(0)

            # Когда свечей больше, чем 2
            if len(self.up_candles) >= 2:
                if self.up_candles[-1]['min'] > self.up_candles[-2]['min']:  # Если MIN последней свечи больше MIN
                    self.cur_trend = "BULL"  # предыдущей, то тренд бычий
                elif self.up_candles[-1]['max'] < self.up_candles[-2]['max']:  # Если MAX последней меньше MAX
                    self.cur_trend = "BEAR"  # предыдущей, то тренд медвежий

            # Если предыдущий тренд НЕ флэтовый (НЕ самые первые свечи)
            if self.prev_trend != 'FLAT':
                if self.cur_trend == "BEAR" and self.prev_trend == "BULL":  # Если локальный MAX

                    # Если мы нашли плечо и разница между этим плечом и текущим MAX больше 5
                    if len(self.shoulders) != 0 and abs(self.up_candles[-2] - self.shoulders[0]) > 5:
                        self.head = self.up_candles[-2]  # Значит мы нашли голову
                    elif len(self.shoulders) == 0 or abs(self.up_candles[-2] - self.shoulders[
                        0]) <= 5:  # Если плеч нет или есть левое плечо и разница
                        self.shoulders.append(self.up_candles[
                                                  -2])  # между текущим MAX и левым плечом меньше 0, то значит мы нашли правое плечо
                elif self.cur_trend == "BULL" and self.prev_trend == "BEAR":  # Если локальный MIN
                    if len(self.neck) == 0:  # Если нет уровня шеи
                        self.neck.append(self.up_candles[-2])  # То регистрируем его
                    elif len(self.neck) == 1 and abs(self.up_candles[-2] - self.neck[0]) < 5:  # Достигаем уровня шеи
                        self.neck.append(self.up_candles[-2])  # второй раз перед возврщением к плечу
                    elif self.up_candles[-1].close < self.neck[
                        1]:  # Если цена закрытия последней свечи меньше уровня шеи
                        signal = 'SELL'  # То кидаем сигнал на продажу
                        return signal


# Индикатор MACD
class MACD:

    def __init__(self):
        self.MACD = list([])  # Значения MACD
        self.signal = list([])  # Значения линии Signal
        self.EMA_S = list([])  # Значения EMA_s
        self.EMA_I = list([])  # Значения EMA_i
        self.EMA_A = list([])  # Значения EMA_a

    def build(self, param_list: str):
        candles = core_bot.get_candles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)
        up_candles = list([])
        gen_up_candle = formatCandle(size, candles)

        # исправить аргументы вызова методов класса EMAIndicator
        ema_candles_9 = EMAIndicator.ma_build(9, param_list=param_list)
        i = 0
        for elem in ema_candles_9:
            self.EMA_A.append(ema_candles_9[i]['ema'])
            i += 1
        del ema_candles_9

        ema_candles_12 = EMAIndicator.ma_build(12, param_list=param_list)
        i = 0
        for elem in ema_candles_12:
            self.EMA_S.append(ema_candles_12[i]['ema'])
            i += 1
        del ema_candles_12

        ema_candles_26 = EMAIndicator.ma_build(26, param_list=param_list)
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

if __name__=='__main__':
    rsi_df = RSI()