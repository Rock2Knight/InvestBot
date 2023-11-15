# Модуль отладки инструментов тех. анализа
from abc import ABC, abstractmethod         # Для абстрактных классов и интерфейсов
from datetime import datetime
from typing import Union
from math import floor

import core_bot


# Интерфейс для индикатора MA
class MA_indicator(ABC):

    @staticmethod
    @abstractmethod
    def MA_build(MA_interval: int, param_list: str) -> list[dict[str, Union[float, str]]]:
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
    def MA_build(MA_interval: int, param_list: str) -> list[dict[str, Union[float, str]]]:

        if MA_interval <= 0:
            raise ValueError('Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)
        up_candles = list([])
        sma_val = 0.0

        for i in range(size):
            up_candle = dict()
            up_candle['time'] = candles[i].time.strftime('%Y-%m-%d_%H:%M:%S')
            up_candle['open'] = core_bot.cast_money(candles[i].close)
            up_candle['close'] = core_bot.cast_money(candles[i].close)
            up_candle['min'] = core_bot.cast_money(candles[i].low)
            up_candle['max'] = core_bot.cast_money(candles[i].high)
            up_candle['sma'] = sma_val
            up_candles.append(up_candle)

            if i >= MA_interval - 1:
                start_bar = i - MA_interval + 1
                end_bar = i + 1
                sum_bar = 0.0
                for j in range(start_bar, end_bar):
                    sum_bar += up_candles[j]['close']
                sma_val = sum_bar / MA_interval
                up_candles[i]['sma'] = sma_val

        return up_candles


    '''
    Метод, выдающий торговые сигналы для прошедших моментов времени :)
    bars_MA - словарь, где ключ - момент времени
    значение - список:
    0-ой элемент списка - цена закрытия
    1-ый элемент списка - значение MA для данного момента времени
    '''
    @staticmethod
    def MA_signal(bars_MA: list[dict[str, Union[float, str]]]):
        cmp_close: list[float] = list([0.0, 0.0])               # Список для сравнения цен закрытия
        cmp_ma: list[float] = list([0.0, 0.0])                  # Список для сравнения значений MA
        signal = ' '                                    # Торговый сигнал
        bars_MA[0]['signal'] = ''
        cur_time = None

        sizeTimeList = len(bars_MA)                # Количество свечек
        for i in range(1, sizeTimeList):
            cmp_close[0] = bars_MA[i-1]['close']
            cmp_close[1] = bars_MA[i]['close']
            cmp_ma[0] = bars_MA[i-1]['sma']
            cmp_ma[1] = bars_MA[i]['sma']

            if bars_MA[i-1]['close'] < bars_MA[i-1]['sma'] and bars_MA[i]['close'] > bars_MA[i]['sma']:
                signal = 'BUY'                                               # График цен пересек SMA снизу вверх
            elif bars_MA[i-1]['close'] > bars_MA[i-1]['sma'] and bars_MA[i]['close'] < bars_MA[i]['sma']:
                signal = 'SELL'                                              # График цен пересек SMA сверху вниз

            if bars_MA[i-1]['sma'] == 0.0:
                signal = ' '
            bars_MA[i]['signal'] = signal
            signal = ' '



# Экспоненциальная MA
class EMA_indicator(MA_indicator):

    @staticmethod
    def MA_build(MA_interval: int, param_list: str) -> list[dict[str, Union[float, str]]]:
        if MA_interval <= 0:
            raise ValueError(
                'Invalid value of MA interval')  # Передали в качестве периода скользящей средней некорректное значение

        candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
        size = len(candles)
        up_candles = list([])
        ema_val = 0.0

        up_candle_0 = dict()
        up_candle_0['time'] = candles[0].time.strftime('%Y-%m-%d_%H:%M:%S')
        up_candle_0['open'] = core_bot.cast_money(candles[0].close)
        up_candle_0['close'] = core_bot.cast_money(candles[0].close)
        up_candle_0['min'] = core_bot.cast_money(candles[0].low)
        up_candle_0['max'] = core_bot.cast_money(candles[0].high)
        up_candle_0['ema'] = up_candle_0['close']                   # EMA для первого таймфрейма равна цене актива
        up_candles.append(up_candle_0)

        close = up_candle_0['close']
        ema_val = up_candle_0['ema']
        print(f'Close     EMA')
        print('%.2f' % close, '%.2f' % ema_val)

        Weight = 2 / (MA_interval + 1)        # Вычисляем вес EMA

        for i in range(1, size):
            up_candle = dict()
            up_candle['time'] = candles[i].time.strftime('%Y-%m-%d_%H:%M:%S')
            up_candle['open'] = core_bot.cast_money(candles[i].close)
            up_candle['close'] = core_bot.cast_money(candles[i].close)
            up_candle['min'] = core_bot.cast_money(candles[i].low)
            up_candle['max'] = core_bot.cast_money(candles[i].high)
            up_candle['ema'] = (up_candles[i-1]['close'] * Weight) + (up_candles[i-1]['ema'] * (1 - Weight)) # Рассчитываем EMA в конкретной точке по формуле
            up_candles.append(up_candle)

            close = up_candle['close']
            ema_val = up_candle['ema']
            print('%.2f' % close, '%.2f' % ema_val)

        return up_candles

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


if __name__ == '__main__':
    figi = 'BBG004730N88'          # Фиги торгуемого инструемента (СберБанк)
    lot = 10                       # лотность инструмента
    cnt_lots = 0                   # Количество лотов Sber в портфеле
    account_portfolio = 100000     # Размер портфеля в рублях
    start_sum = account_portfolio
    stop_loss = 0.05               # Точка аннулирования для торговой стратегии в процентах
    ping = 1                       # задержка в сек
    ping_interval = ping / (60*4)  # задержка, выраженная относительно интервала (размер интервала = 4 ч)
    start_time = '2022-07-16_00:00:00'   # Стартовое время моделирования
    ModelTime = 1000               # Время моделирования в временных интервалах

    request = '/get_candles BBG004730N88 2023-10-02_00:00:00 2023-11-03_19:00:00 HOUR'
    ema_period = 5

    up_candles = EMA_indicator.MA_build(MA_interval=ema_period, param_list=request)  # Запрашиваем исторические данные за период
    print('\n\n')
    EMA_indicator.MA_signal(up_candles)   # строим SMA и по ней выставляем торговые сигналы
    print('\n\nModeling trading\n')
    start_time = up_candles[0]['time']
    orderType = 'NO'                      # Тип сделки
    order_cnt_lot: int = 0                # Количество лотов по последней сделке
    position = 0                          # Количество
    stop_loss_cast, take_profit_cast = 0.0, 0.0   # Суммы срабатывания стоп-лосса и тейк-профита
    signal = ' '

    cntCandles = len(up_candles)
    for i in range(cntCandles):

        market_cast = (up_candles[i]['open'] + up_candles[i]['close']) / 2  # Расчет рыночной цены

        if orderType == 'BUY' and market_cast * order_cnt_lot <= stop_loss_cast:       # Срабатывание стоп-лосса
            if cnt_lots < order_cnt_lot:
                continue
            cnt_lots -= order_cnt_lot
            account_portfolio +=  market_cast
            cur_time = up_candles[i]['time']
            signal = up_candles[i]['signal']

            print(f'TIME={cur_time} ACCOUNT_SUM=', '%.2f ' % account_portfolio,
                  f'POSITION=%2.f ' % position,
                  f'ORDER_TYPE=BUY BUY_LOT={order_cnt_lot} CUR_LOT={cnt_lots} ',
                  f'STOP-LOSS SIGNAL={signal}')

        elif orderType == 'SELL' and market_cast * order_cnt_lot >= take_profit_cast:   # Срабатывание тейк-профита
            if account_portfolio < position:
                continue
            account_portfolio -= market_cast
            cnt_lots += order_cnt_lot
            cur_time = up_candles[i]['time']
            signal = up_candles[i]['signal']

            print(f'TIME={cur_time} ACCOUNT_SUM=', '%.2f ' % account_portfolio,
                  f'POSITION=%2.f ' % position,
                  f'ORDER_TYPE=BUY SELL_LOT={order_cnt_lot} CUR_LOT={cnt_lots} ',
                  f'TAKE-PROFIT SIGNAL={signal}')

        position = (account_portfolio * 0.01) / stop_loss   # Размер торговой позиции
        order_cnt_lot = int(floor(position / market_cast))              # Расчет количества лотов для сделки
        stop_loss_cast = position - position * stop_loss    # Расчет суммы срабатывания стоп-лосса
        take_profit_cast = position + position * stop_loss  # Расчет суммы срабатывания тейк-профита

        if up_candles[i]['signal'] in ['BUY', 'SELL']:

            if up_candles[i]['signal'] == 'BUY':
                if account_portfolio < position:
                    continue
                account_portfolio -= position     # Свободная сумма на счете уменьшается
                cnt_lots += order_cnt_lot         # Количество лотов акции SBER увеличивается на счете
                orderType = 'BUY'
                cur_time = up_candles[i]['time']
                signal = up_candles[i]['signal']

                print(
                    f'TIME={cur_time} ',
                    'ACCOUNT_SUM=%.2f ' % account_portfolio,
                    f'POSITION=%2.f ' % position,
                    f'ORDER_TYPE=BUY BUY_LOT={order_cnt_lot} ',
                    f'CUR_LOT={cnt_lots} SIGNAL={signal}')
            elif up_candles[i]['signal'] == 'SELL':
                if cnt_lots < order_cnt_lot:
                    continue
                account_portfolio += position     # Свободная сумма на счете увеличивается
                cnt_lots -= order_cnt_lot         # Количество лотов акции SBER уменьшается на счете
                orderType = 'SELL'
                cur_time = up_candles[i]['time']
                signal = up_candles[i]['signal']

                print(
                    f'TIME={cur_time} ',
                    'ACCOUNT_SUM=%.2f ' % account_portfolio,
                    f'POSITION=%2.f ' % position,
                    f'ORDER_TYPE=SELL SELL_LOT={order_cnt_lot} ',
                    f'CUR_LOT={cnt_lots} SIGNAL={signal}')

    print(f'\n\nCur portfolio sum: {account_portfolio} RUB')
    print(f'Count of SBER lots: {cnt_lots}')
    print(f'Profit/loss: {account_portfolio - start_sum} RUB')