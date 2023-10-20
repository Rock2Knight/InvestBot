# Модуль отладки инструментов тех. анализа
from datetime import datetime
import core_bot

MA_INTERVALS = {'5_DAY': 5, '10_DAY': 10, '20_DAY': 20}

# Отладочный метод, вычисляющий MA для каждого момента времени из интервала
# MA_interval - интервал усреднения для скользящей средней
def MA_build(MA_interval: str, param_list: str):

    global MA_INTERVALS
    if MA_interval not in MA_INTERVALS.keys():
        raise ValueError                         # Передали в качестве периода скользящей средней некорректное значение

    candles = core_bot.getCandles(param_list)  # Лишняя работа, так-как вывается метод, обращающийся к API
    size = len(candles)
    up_candles = list([])

    for i in range(size):
        up_candle = dict()
        up_candle['close'] = core_bot.cast_money(candles[i].close)
        up_candle['time'] = core_bot.string_data(candles[i].time)

        up_candles.append(up_candle)

    day_data = dict()                 # словарь с ценами закрытия за каждый день
    cnt_candles = len(up_candles)
    for i in range(cnt_candles):
        time_candle = datetime.strptime(up_candles[i]['time'], '%Y-%m-%d-%H-%M-%S')

        # Преобразуем датафрейм из datetime в строку для хранения в словаре как ключа
        time_str = str(time_candle.year)
        time_str += '-' + str(time_candle.month)
        time_str += '-' + str(time_candle.day)
        if not time_str in day_data.keys():
            day_data[time_str] = list([])

        day_data[time_str].append(up_candles[i]['close'])

    days = day_data.keys()
    day_close_cast = dict()
    print('\nTime       Cast')
    for day in days:
        close_cast = sum(day_data[day])/len(day_data[day])
        day_close_cast[day] = list([])
        day_close_cast[day].append(close_cast)
        day_close_cast[day].append(0.0)
        print(f'{day} '+'%.2f' % close_cast + ' RUB')

    del day_data

    list_day = list(day_close_cast.keys())
    for i, moment in enumerate(list_day):
        if i >= MA_INTERVALS[MA_interval]-1:
            sum_cast = 0.0
            for j in range(i-MA_INTERVALS[MA_interval]+1, i+1):
                sum_cast += day_close_cast[list_day[j]][0]
            aver = sum_cast / MA_INTERVALS[MA_interval]
            day_close_cast[moment][1] = aver


    return day_close_cast


if __name__ == '__main__':

    MA_intervals = None      # Словарь со свечами с показателями MA
    param_list = '/get_candles BBG004730N88 2022-07-16_00:00:00 2022-10-16_00:00:00 HOUR'
    MA_intervals = MA_build('10_DAY', param_list)   # Получаем словарь с ценами закрытия за день и MA
    candles = core_bot.getCandles(param_list)       # Список свечей

    size = len(candles)           # Размер списка свечей
    up_candles = list([])         # Свечи отфармотированные (с MA)

    # Создаем список таймфреймов для MA
    MA_keys = MA_intervals.keys()
    MA_keys = list(MA_keys)
    MA_iter = 0                   # Итератор для MA ключей

    for i in range(size):
        up_candle = dict()
        up_candle['open'] = str(core_bot.cast_money(candles[i].open))
        up_candle['close'] = str(core_bot.cast_money(candles[i].close))
        up_candle['low'] = str(core_bot.cast_money(candles[i].low))
        up_candle['high'] = str(core_bot.cast_money(candles[i].high))
        up_candle['time'] = core_bot.string_data(candles[i].time)
        up_candle['volume'] = str(candles[i].volume)

        # Датафрейм за час
        dateframe_all = datetime.strptime(core_bot.string_data(candles[i].time), '%Y-%m-%d-%H-%M-%S')
        day = MA_keys[MA_iter] + ' 00:00:00'
        # Датафрейм за день
        dateframe_day = datetime.strptime(day, '%Y-%m-%d %H:%M:%S')
        if dateframe_day.day != dateframe_all.day:
            MA_iter += 1

        up_candle['ma'] = MA_intervals[MA_keys[MA_iter]][1]
        up_candles.append(up_candle)


    print('\nTime        Cast   10_DAY_MA')
    for key in MA_intervals.keys():
        close_cast = MA_intervals[key][0]
        ma = MA_intervals[key][1]
        print(f'{key} ' + '%.2f' % close_cast + ' RUB  ' + '%.2f' % ma + ' RUB')


    print('\n\n Candles for period with 5_day_MA values:\n')
    print('Time    Open   Close   Min   Max   5_DAY_MA')
    size = len(up_candles)
    for i in range(size):
        moment = up_candles[i]['time']
        open = up_candles[i]['open']
        close = up_candles[i]['close']
        low = up_candles[i]['low']
        high = up_candles[i]['high']
        ma = up_candles[i]['ma']

        print(f'{moment} {open} {close} {low} {high} ' + '%.2f' % ma)