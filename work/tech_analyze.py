# Модуль отладки инструментов тех. анализа
from math import floor, fabs
from contextlib import redirect_stdout
from datetime import datetime
import asyncio
import os

import pandas as pd

from MA_indicator import SMAIndicator
from oscillators import RSI

# Раздел констант
ACCOUNT_ID = "0a475568-a650-449d-b5a8-ebab32e6b5ce"
MAX_MIN_INTERVAL = 14                                  # Интервал поиска максимумов и минимумов
COMMISION = 0.003                                      # коммисия брокера


class Queue:

    def __init__(self):
        self.stop_market = list([])
        self.count = list([])
        self.size = 0

    def push(self, cast: float, cnt: int):
        self.stop_market.append(cast)
        self.count.append(cnt)
        self.size += 1

    def pop(self):
        stop_market = self.stop_market.pop(0)
        cnt_lots = self.count.pop(0)
        self.size -= 1
        return stop_market, cnt_lots

    def get_cast(self, index: int):
        return self.stop_market[index]

    def remove(self, index: int):
        stop_market = self.stop_market[index]
        cnt_lots = self.count[index]
        self.stop_market.pop(index)
        self.count.pop(index)
        self.size -= 1
        return stop_market, cnt_lots

def getDateNow():
    cur_time = datetime.now()
    print(cur_time)

""" Функция, моделирующая торговлю и формирующая выходные данные в виде датасета """
async def HistoryTrain(uid, cnt_lots, account_portfolio, **kwargs):
    """ Моделирует торговую активность по историческим данным
    в соответствии с заданной торговой стратегией.

    :param uid: FIGI-идентификатор торгового инструемнта
    :param cnt_lots: количество лотов торгуемого иснструмента в портфеле
    :param account_portfolio: сумма свободных денег в портфеле

    :return:
    - dfTrades - Pandas-датафрейм со всеми совершенными сделками
    - dfPortfolio - Pandas-датафрейм с состоянием портфеля в каждый момент времени

    Keyword arguments:
    :param lot - лотность инструмента
    :param ma_interval - Интервал SMA
    :param stopAccount - риск для счета в процентах
    :param stopLoss - стоп-лосс (максимальный риск для одной позиции) в процентах
    :param time_from - время начала торговой стратегии в секундах
    :param time_to - время конца торговой стратегии в секундах
    :param timeframe - таймфрейм
    """

    active_cast = 0  # Текущая цена актива
    start_sum = account_portfolio
    lot = kwargs['lot']
    ma_interval = kwargs['ma_interval']

    # Условия расчета позиции
    stopAccount = kwargs['stopAccount']  # Риск для счета в процентах
    stopLoss = kwargs['stopLoss']  # Точка аннулирования для торговой стратегии в процентах

    # Создаем файлы для сохранения статистики и проверяем на наличие этих данных.
    # Если файлы с нужными именам существуют, выходим из функции
    pathTrades = "../history_data/trades_stats"
    pathPrtf = "../history_data/portfolio_stats"
    if not os.path.exists(pathTrades):
        os.mkdir(pathTrades)
    if not os.path.exists(pathPrtf):
        os.mkdir(pathPrtf)

    pathTrades = pathTrades + "/" + kwargs['timeframe']
    pathPrtf = pathPrtf + "/" + kwargs['timeframe']
    if not os.path.exists(pathTrades):
        os.mkdir(pathTrades)
    if not os.path.exists(pathPrtf):
        os.mkdir(pathPrtf)

    # Получаем исторические свечи
    raw_tr_name = pathTrades + "/" + str(uid) + "_" + kwargs['time_from'] + "_" + kwargs['time_to'] + ".csv"
    raw_prtf_name = pathPrtf + "/" + str(uid) + "_" + kwargs['time_from'] + "_" + kwargs['time_to'] + ".csv"
    statsTradesFilename = raw_tr_name.replace(":", "_")
    statsPortfolioFilename = raw_prtf_name.replace(":", "_")

    if os.path.exists(statsTradesFilename) and os.path.exists(statsPortfolioFilename):
        dfTrades = pd.read_csv(statsTradesFilename)
        dfPortfolio = pd.read_csv(statsPortfolioFilename)
        return dfTrades, dfPortfolio

    # 1. Получаем готовый датафрейм исторических свечей
    raw_filename = "../instruments_info/" + kwargs['timeframe'] + "/" + uid + "_"
    raw_filename = raw_filename + kwargs['time_from'] + "_" + kwargs['time_to'] + ".csv"
    filename = raw_filename.replace(":", "_")
    CandlesDF = pd.read_csv(filename)

    if CandlesDF.empty:
        dfTrades, dfPortfolio = None, None
        return dfTrades, dfPortfolio

    rsiObject = RSI()  # Добавляем RSI индикатор с интервалом 14
    SMA_5 = SMAIndicator(ma_interval=ma_interval, CandlesDF=CandlesDF)  # Добавляем SMA с интервалом 5

    # Локальные минимумы и максимумы (по свечам и по RSI)
    minMaxDict = {'time': list([]), 'minC': list([]), 'maxC': list([]), 'minR': list([]), 'maxR': list([])}
    maxClose = max(list(CandlesDF['close']))
    locMinC, locMinR = maxClose, maxClose
    locMaxC, locMaxR = 0, 0

    MAXInter = 5  # Max количество пересечений на интервал
    CNT_timeframe = 10  # Длина проверяемого интервала
    cntInter = 0  # Количество пересечений
    active_cast = CandlesDF.iloc[0]['close']  # Рыночная цена актива (типа)
    lot_cast = active_cast * lot  # Рыночная цена одного лота (типа)
    positionSize = 0.0  # Размер позиции
    totalSharePrice = lot_cast * cnt_lots  # Общая стоимость акций Новатэк в портфеле
    start_sum = account_portfolio + totalSharePrice
    start_cnt_lots = cnt_lots
    cnt_tradeLots = 0
    positionReal = 0.0        # Реальный размер позиции с учетом комиссии
    stopLossSize = 0.0        # Размер стоп-лосса

    # Словарь с информацией по сделкам
    tradeInfo = {"time": list([]), "trade_direct": list([]), "uid": list([]),
                 "position_size": list([]), "stop_loss_size": list([]), "active_cast": list([]),
                 "lot_size": list([]), "lot_cast": list([]), "position_size_real": list([]),
                 "lot_cnt": list([]), "order_type": list([])}

    # Словарь с информацией по портфелю
    portfolioInfo = {"time": list([]), "start_full_sum": list([]), "start_cnt_lots": list([]),
                     "cur_full_sum": list([]), "cur_free_sum": list([]), "cur_cnt_lots": list([]),
                     "profit_in_rub": list([]), "profit_in_percent": list([])}

    # Очередь стоп-маркет заявок
    stopMarketQueue = Queue()

    # Анализируем свечи из выделенного интервала
    for i in range(CandlesDF.shape[0]):
        BUY_Signal = False
        SELL_Signal = False

        # Обновляем состояние портфеля с учетом текущих цен имеющихся активов
        active_cast = CandlesDF.iloc[i]['close']  # Рыночная цена актива (типа)
        if cnt_lots != 0:
            totalSharePrice = active_cast * lot * cnt_lots  # Обновляем стоимость имеющихся активов

        fullPortfolio = account_portfolio + totalSharePrice
        profitInRub = fullPortfolio - start_sum  # Прибыль/убыток в рублях (по отношению к общей стоимости портфеля)
        profitInPercent = (profitInRub / start_sum) * 100  # Прибыль/убыток в процентах (по отношению к общей стоимости портфеля)

        # Цикл для проверки стоп-маркетов
        lot_cast_pr = active_cast * lot
        for j in range(stopMarketQueue.size):
            try:
                if active_cast <= stopMarketQueue.get_cast(j):
                    # Срабатывание стоп-маркета на продажу (защита от риска)
                    rel_stop_market, rel_cnt = stopMarketQueue.remove(j)
                    final_lot_cast = lot_cast_pr * (1 - COMMISION)
                    positionReal = rel_cnt * final_lot_cast
                    cnt_lots -= rel_cnt
                    account_portfolio += positionReal
            except IndexError:
                print(f"Access to stopMarketQueue {j} element error")


        with open("historyTradingLog.txt", 'a', encoding="utf-8") as f, redirect_stdout(f):
            # Вывод информации об аккаунте
            print("INFO ABOUT ACCOUNT\n--------------------------\n" +
                  f"\nTime: {CandlesDF.iloc[i]['time']}" +
                  "\nStart sum on account(full): %.2f RUB " % start_sum +
                  "\nCurrent sum on account(free): %.2f RUB " % account_portfolio +
                  "\nCurrent sum on account(full): %.2f RUB " % fullPortfolio +
                  "\nProfit in RUB: %.2f RUB " % profitInRub +
                  "\nProfit in percent: %.2f %%" % profitInPercent +
                  "\nCurrent count of NOVATEK lots: " + str(cnt_lots) +
                  "\nCast per NOVATEK lot: %.2f RUB" % lot_cast +
                  "\nTotal instrument price: %.2f RUB" % floor(totalSharePrice) +
                  "--------------------------\n")

        print("INFO ABOUT ACCOUNT\n--------------------------\n" +
              f"\nTime: {CandlesDF.iloc[i]['time']}" +
              "\nStart sum on account(full): %.2f RUB " % start_sum +
              "\nCurrent sum on account(free): %.2f RUB " % account_portfolio +
              "\nCurrent sum on account(full): %.2f RUB " % fullPortfolio +
              "\nProfit in RUB: %.2f RUB " % profitInRub +
              "\nProfit in percent: %.2f %%" % profitInPercent +
              "\nCurrent count of NOVATEK lots: " + str(cnt_lots) +
              "\nCast per NOVATEK lot: %.2f RUB" % lot_cast +
              "\nTotal instrument price: %.2f RUB" % floor(totalSharePrice) +
              "--------------------------\n")

        # Обновляем информацию по портфелю
        portfolioInfo["time"].append(CandlesDF.iloc[i]['time'])
        portfolioInfo["start_full_sum"].append(start_sum)
        portfolioInfo["start_cnt_lots"].append(start_cnt_lots)
        portfolioInfo["cur_full_sum"].append(fullPortfolio)
        portfolioInfo["cur_free_sum"].append(account_portfolio)
        portfolioInfo["cur_cnt_lots"].append(cnt_lots)
        portfolioInfo["profit_in_rub"].append(profitInRub)
        portfolioInfo["profit_in_percent"].append(profitInPercent)

        # Если количество свеч для построения SMA недостаточно, продолжаем цикл
        if i < ma_interval - 1:  # Если номер свечи меньше периода SMA, то просто делаем итерацию без действий
            continue

        # SMA_Values = SMA_indicator.MA_build(MA_interval=ma_interval, cntOfCandles=i+1)

        if i < 0:
            raise IndexError

        if i >= MAX_MIN_INTERVAL:
            # Ищем локальные максимумы и минимумы

            for j in range(i - MAX_MIN_INTERVAL + 1, i):
                if CandlesDF.iloc[j]['close'] < locMinC:
                    locMinC = CandlesDF.iloc[j]['close']
                if CandlesDF.iloc[j]['close'] > locMaxC:
                    locMaxC = CandlesDF.iloc[j]['close']
                if rsiObject.get_RSI(j) < locMinR:
                    locMinR = rsiObject.get_RSI(j)
                if rsiObject.get_RSI(j) > locMaxR:
                    locMaxR = rsiObject.get_RSI(j)

            minMaxDict['time'].append(CandlesDF.iloc[i]['time'])
            minMaxDict['minC'].append(locMinC)
            minMaxDict['maxC'].append(locMaxC)
            minMaxDict['minR'].append(locMinR)
            minMaxDict['maxR'].append(locMaxR)
            locMinC, locMinR = 10000, 10000
            locMaxC, locMaxR = 0, 0

        sma_prev = SMA_5.get_SMA(i - 1)
        sma_cur = SMA_5.get_SMA(i)
        BUY_Signal = CandlesDF.iloc[i - 1]['close'] < sma_prev and CandlesDF.iloc[i]['close'] > sma_cur
        SELL_Signal = CandlesDF.iloc[i - 1]['close'] > sma_prev and CandlesDF.iloc[i]['close'] < sma_cur

        if BUY_Signal or SELL_Signal:
            # Торговый сигнал  сработал, проверяем
            start_frame = 0
            if i < CNT_timeframe:
                start_frame = 0
            else:
                start_frame = i - CNT_timeframe

            for j in range(start_frame + 1, i + 1):
                # Считаем количество персечений SMA в 10 предыдущих таймфреймах
                sma_prev = SMA_5.get_SMA(j - 1)
                sma_cur = SMA_5.get_SMA(j)
                if CandlesDF.iloc[j - 1]['close'] < sma_prev and CandlesDF.iloc[j]['close'] > sma_cur:
                    cntInter += 1

            rsi_val = rsiObject.get_RSI(i)  # Получаем значение RSI

            # Если количество пересечений не очень большое, то совершаем сделку
            if cntInter < MAXInter:
                positionSize = account_portfolio * stopAccount / stopLoss  # Расчитываем размер позиции (сделки)

                if BUY_Signal:
                    if rsi_val >= 70:  # Если сигнал на покупку и RSI в зоне перекупленности
                        continue  # то не совершаем покупку
                else:
                    if rsi_val <= 30:  # Если сигнал на покупку и RSI в зоне перепроданности
                        continue  # то не совершаем продажу


                #active_cast = CandlesDF.iloc[i]['close']  # Рыночная цена актива (типа)
                lot_cast = lot * active_cast  # Рыночная цена одного лота актива (типа)
                final_lot_cast = 0.0
                stop_cast = active_cast * (1 - stopLoss)  # Рассчитываем стоп-цену для стоп-маркета

                if BUY_Signal:
                    final_lot_cast = lot_cast * (1 + COMMISION) # Рыночная цена одного лота актива с учетом комиссии брокера
                else:
                    final_lot_cast = lot_cast * (1 - COMMISION)

                cnt_tradeLots = floor(positionSize / final_lot_cast)  # Количество покупаемых/продаваемых лотов
                positionReal = cnt_tradeLots * final_lot_cast         # Реальный размер позиции

                # Если размер позиции с учетом комиссии больше рассчитываемого, то уменьшаем количество лотов
                while positionReal > positionSize:
                    cnt_tradeLots -= 1
                    positionReal = cnt_tradeLots * cnt_tradeLots * (1 + COMMISION)

                if BUY_Signal:
                    # Если размер позиции на покупку с учетом комиссии больше рассчитываемого, то уменьшаем количество лотов
                    while positionReal > positionSize:
                        cnt_tradeLots -= 1
                        positionReal = cnt_tradeLots * final_lot_cast

                    cnt_lots += cnt_tradeLots  # Получаем лоты инструмента (акции Тинькофф) на счет
                    account_portfolio -= positionReal  # Перечисляем деньги за сделку брокеру в случае покупки
                    stopMarketQueue.push(stop_cast, cnt_tradeLots) # Фиксируем стоп-маркет заявку в журнале заявок

                    with open("historyTradingLog.txt", 'a', encoding="utf-8") as f, redirect_stdout(f):
                        print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                              "\nBUY - %2.f RUB" % positionReal + "\n+ " + str(cnt_tradeLots) + " NOVATEK lots" +
                            "--------------------------\n")
                    print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                          "\nBUY - %2.f RUB" % positionReal + "\n+ " + str(cnt_tradeLots) + " NOVATEK lots" +
                          "--------------------------\n")
                else:
                    # Если размер позиции на продажу с учетом комиссии меньше рассчитываемого, то увеличиваем количество лотов
                    while positionReal > positionSize:
                        cnt_tradeLots += 1
                        positionReal = cnt_tradeLots * final_lot_cast

                    cnt_lots -= cnt_tradeLots  # Продаем лоты инструмента (акции Тинькофф) брокеру
                    account_portfolio += positionReal  # Получаем деньги за сделку от брокера в случае продажи
                    with open("historyTradingLog.txt", 'a', encoding="utf-8") as f, redirect_stdout(f):
                        print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                            "\nSELL + %2.f RUB" % positionReal + "\n- " + str(cnt_tradeLots) + " NOVATEK lots" +
                            "--------------------------\n")
                    print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                          "\nSELL + %2.f RUB" % positionReal + "\n- " + str(cnt_tradeLots) + " NOVATEK lots" +
                          "--------------------------\n")


                stopLossSize = positionReal * stopLoss  # Рассчитываем размер стоп-лосса (max убытка от позиции)

                # Формируем информацию о сделке
                tradeInfo['time'].append(CandlesDF.iloc[i]['time'])  # время сделки
                tradeInfo['uid'].append(uid)                       # FIGI инструмента
                tradeInfo['position_size'].append(positionSize)      # Расчетный размер позиции

                if BUY_Signal:
                    tradeInfo['trade_direct'].append('BUY')
                else:
                    tradeInfo['trade_direct'].append('SELL')
                tradeInfo['stop_loss_size'].append(stopLossSize)     # Размер стоп-лосса (рассчитывается от фактического размера позиции)
                tradeInfo['active_cast'].append(active_cast)         # Цена актива
                tradeInfo['lot_size'].append(lot)                    # Лотность актива
                tradeInfo['lot_cast'].append(lot_cast)               # Цена лота
                tradeInfo['position_size_real'].append(positionReal) # Фактический размер позиции
                tradeInfo['lot_cnt'].append(cnt_tradeLots)           # Количество реализованных лотов
                tradeInfo['order_type'].append('MARKET')             # Тип заявки (рыночная)

                totalSharePrice = lot_cast * cnt_lots  # Общая стоимость акций Тинькофф в портфеле

    # Формируем датафреймы из словарей
    dfTrades = pd.DataFrame(tradeInfo)
    dfPortfolio = pd.DataFrame(portfolioInfo)
    # записываем их в CSV

    dfTrades.to_csv(statsTradesFilename)
    dfPortfolio.to_csv(statsPortfolioFilename)
    return dfTrades, dfPortfolio        # возвращаем в вызывающую функцию