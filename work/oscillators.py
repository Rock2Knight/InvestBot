# Модуль, хранящий классы, реализующие технические индикаторы-осцилляторы
from tinkoff.invest.schemas import HistoricCandle

import core_bot
from MA_indicator import EMA_indicator


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

        EMA_up, EMA_close = 0, 0  # EMA роста и EMA падения
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
                for j in range(i - self.RSI_interval + 1, i + 1):

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
        candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)
        up_candles = list([])
        gen_up_candle = formatCandle(size, candles)

        # todo исправить аргументы вызова методов класса EMA_indicator
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