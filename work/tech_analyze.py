# Модуль отладки инструментов тех. анализа
import sys
import os
from dotenv import load_dotenv
from math import floor, fabs
from datetime import datetime
import logging
from typing import Optional
import asyncio

import pandas as pd
from tinkoff.invest.schemas import IndicatorType

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)
sys.path.append(main_path+'work\\')
sys.path.append(main_path+'app\\')

from app import technical_indicators
from utils_funcs import utils_funcs

# Раздел констант
COMMISION = 0.003 # коммисия брокера

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")


class StopMarketQueue:
    """
    Очередь стоп-маркет ордеров
    """

    def __init__(self):
        self.stop_market = list([])  # список стоп маркет цен
        self.count = list([])  # список количества лотов по заявкам
        self.size = 0  # количество заявок

    async def push(self, cast: float, cnt: int):
        """
        Создать стоп-маркет ордер

        :param cast: цена заявки
        :param cnt: количество лотов
        """
        self.stop_market.append(cast)
        self.count.append(cnt)
        self.size += 1

    def pop(self) -> Optional[tuple]:
        """
        Получить данные для самого раннего стоп-ордера
        """
        if not self.stop_market or not self.count:
            return None
        stop_market = self.stop_market.pop(0)
        cnt_lots = self.count.pop(0)
        self.size -= 1
        return stop_market, cnt_lots

    def get(self) -> Optional[tuple]:
        """
        Получение данных о первой заявке
        :return: (цена заявки, количество лотов)
        """
        if not self.stop_market or not self.count:
            return None
        return self.stop_market[0], self.count[0]


def getDateNow():
    cur_time = datetime.now()
    print(cur_time)


""" Функция, моделирующая торговлю и формирующая выходные данные в виде датасета """
@utils_funcs.invest_api_retry(retry_count=10)
async def HistoryTrain(uid, cnt_lots, account_portfolio, is_test=False, **kwargs):
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
    :param ma_type - тип MA
    :param ma_interval - Интервал MA
    :param rsi_interval - Интервал RSI
    :param stopAccount - риск для счета в процентах
    :param stopLoss - стоп-лосс (максимальный риск для одной позиции) в процентах
    :param takeProfit - тейк-профит (максимальная доходность для одной позиции) в процентах
    :param time_from - время начала торговой стратегии в секундах
    :param time_to - время конца торговой стратегии в секундах
    :param timeframe - таймфрейм
    :param name - имя торгуеомого инструмента
    """

    active_cast = 0  # Текущая цена актива
    start_sum = account_portfolio
    lot = kwargs['lot']
    ma_interval = kwargs['ma_interval']
    trName = kwargs['name']   # Имя торгуемого инструмента
    BUY_Signal = False
    SELL_Signal = False

    # Условия расчета позиции
    stopAccount = kwargs['stopAccount']  # Риск для счета в процентах
    stopLoss = kwargs['stopLoss']  # Точка аннулирования для торговой стратегии в процентах
    takeProfit = kwargs['takeProfit']

    # Устанавливаем тип MA
    ma_type = 0
    if kwargs['ma_type']:
        if kwargs['ma_type'] == IndicatorType.INDICATOR_TYPE_EMA:
            ma_type = 1

    if not is_test:

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

    tf = kwargs['timeframe']
    if isinstance(tf, str):
        tf = utils_funcs.get_timeframe_by_name(tf)
    from_time = kwargs['time_from']
    if isinstance(from_time, str):
        from_time = datetime.strptime(from_time, '%Y-%m-%d_%H:%M:%S')
    to_time = kwargs['time_to']
    if isinstance(to_time, str):
        to_time = datetime.strptime(to_time, '%Y-%m-%d_%H:%M:%S')
    MA, RSI = None, None
    try:
        if ma_type == 0:
            MA = technical_indicators.getSMA(uid_instrument=uid, time_from=from_time,
                                          time_to=to_time,
                                          timeframe=tf)
        else:
            MA = technical_indicators.getEMA(uid_instrument=uid, time_from=from_time,
                                             time_to=to_time,
                                             timeframe=tf)
    except Exception as e:
        await asyncio.sleep(2)
        if ma_type == 0:
            MA = technical_indicators.getSMA(uid_instrument=uid, time_from=from_time,
                                          time_to=to_time,
                                          timeframe=tf)
        else:
            MA = technical_indicators.getEMA(uid_instrument=uid, time_from=from_time,
                                             time_to=to_time,
                                             timeframe=tf)
    try:
        RSI = technical_indicators.getRSI(uid_instrument=uid, time_from=from_time,
                                          time_to=to_time,
                                          timeframe=tf)
    except Exception as e:
        await asyncio.sleep(2)
        RSI = technical_indicators.getRSI(uid_instrument=uid, time_from=from_time,
                                          time_to=to_time,
                                          timeframe=tf)
    if not MA and not RSI:
        print("\nNo indicators\n")
        if not is_test:
            raise ValueError
        else:
            return None, None

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

    print(f"\n\ntype of lot_cast = {type(lot_cast)}")
    print(f"\n\ntype of cnt_lots = {type(cnt_lots)}")

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
                     "profit_in_rub": list([]), "profit_in_percent": list([]), "SM_SELL_sum": list([])}

    # Очередь стоп-маркет заявок
    stopLossQueue = StopMarketQueue()    # Очередь стоп-лосс заявок
    takeProfitQueue = StopMarketQueue()  # Очередь тейк-профит заявок
    realizedSM = 0.0
    # Анализируем свечи из выделенного интервала
    for i in range(CandlesDF.shape[0]):

        # Обновляем состояние портфеля с учетом текущих цен имеющихся активов
        if i >= CandlesDF.shape[0] or i < 0:
            break
        active_cast = CandlesDF.iloc[i]['close']  # Рыночная цена актива (типа)
        if cnt_lots != 0:
            totalSharePrice = active_cast * lot * cnt_lots  # Обновляем стоимость имеющихся активов

        fullPortfolio = account_portfolio + totalSharePrice
        profitInRub = fullPortfolio - start_sum  # Прибыль/убыток в рублях (по отношению к общей стоимости портфеля)
        profitInPercent = (profitInRub / start_sum) * 100  # Прибыль/убыток в процентах (по отношению к общей стоимости портфеля)
        if profitInPercent < 0 and fabs(profitInPercent) >= stopAccount * 100:
            # Если размер убытка достиг риска для счета, то делаем аварийное завершение торговли
            print(f"\n{trName}: FATAL_STOP")
            if tradeInfo and portfolioInfo:
                dfTrades = pd.DataFrame(tradeInfo)
                dfPortfolio = pd.DataFrame(portfolioInfo)
                if not is_test:
                    dfTrades.to_csv(statsTradesFilename)
                    dfPortfolio.to_csv(statsPortfolioFilename)
                return dfTrades, dfPortfolio
            elif not tradeInfo and portfolioInfo:
                dfPortfolio = pd.DataFrame(portfolioInfo)
                if not is_test:
                    dfPortfolio.to_csv(statsPortfolioFilename)
                return None, portfolioInfo

        # Цикл для проверки стоп-маркетов
        lot_cast_pr = active_cast * lot            # Текущая цена за лот
        # Проверка стоп-маркета
        sl_lot_cast, sl_lot_cnt = None, None
        sl, tp = stopLossQueue.get(), takeProfitQueue.get()
        if sl:
            if lot_cast_pr <= sl[0]:
                # Срабатывание стоп-лосса
                posStopMarket = sl[0] * sl[1]
                account_portfolio += posStopMarket
                cnt_lots -= sl[1]
                realizedSM += posStopMarket
                stopLossQueue.pop()
        if tp:
            if lot_cast_pr >= tp[0]:
                # Срабатывание тейк-профита
                posStopMarket = tp[0] * tp[1]
                account_portfolio -= posStopMarket
                cnt_lots += tp[1]
                realizedSM += posStopMarket
                takeProfitQueue.pop()

        # Обновляем информацию по портфелю
        portfolioInfo["time"].append(CandlesDF.iloc[i]['time'])
        portfolioInfo["start_full_sum"].append(start_sum)
        portfolioInfo["start_cnt_lots"].append(start_cnt_lots)
        portfolioInfo["cur_full_sum"].append(fullPortfolio)
        portfolioInfo["cur_free_sum"].append(account_portfolio)
        portfolioInfo["cur_cnt_lots"].append(cnt_lots)
        portfolioInfo["profit_in_rub"].append(profitInRub)
        portfolioInfo["profit_in_percent"].append(profitInPercent)
        portfolioInfo['SM_SELL_sum'].append(realizedSM)  # Общая сумма сработавших по стоп-маркету заявок

        # Если количество свеч для построения MA недостаточно, продолжаем цикл
        if i < ma_interval - 1:  # Если номер свечи меньше периода MA, то просто делаем итерацию без действий
            continue

        if i < 0:
            raise IndexError

        #sma_prev = MA.get_MA(i - 1)
        #sma_cur = MA.get_MA(i)
        if i >= len(MA) or i < 0:
            if not is_test:
                raise IndexError("Нет элементов в MA")
            else:
                return None, None
        sma_prev = utils_funcs.cast_money(MA[i-1].signal)
        sma_cur = utils_funcs.cast_money(MA[i].signal)
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
                # Считаем количество персечений MA в 10 предыдущих таймфреймах
                #sma_prev = MA.get_MA(j - 1)
                #sma_cur = MA.get_MA(j)
                if i >= len(MA) or i < 0:
                    if not is_test:
                        raise IndexError("Нет элементов в MA")
                    else:
                        return None, None
                sma_prev = utils_funcs.cast_money(MA[i - 1].signal)
                sma_cur = utils_funcs.cast_money(MA[i].signal)
                if CandlesDF.iloc[j - 1]['close'] < sma_prev and CandlesDF.iloc[j]['close'] > sma_cur:
                    cntInter += 1

            #rsi_val = rsiObject.get_RSI(i)  # Получаем значение RSI
            if i >= len(RSI) or i < 0:
                if not is_test:
                    raise IndexError("Нет элементов в MA")
                else:
                    return None, None
            rsi_val = utils_funcs.cast_money(RSI[i].signal)

            # Если количество пересечений не очень большое, то совершаем сделку
            if cntInter < MAXInter:
                positionSize = account_portfolio * stopAccount / stopLoss  # Расчитываем размер позиции (сделки)

                if BUY_Signal:
                    if rsi_val >= 70:  # Если сигнал на покупку и RSI в зоне перекупленности
                        continue  # то не совершаем покупку
                else:
                    if rsi_val <= 30:  # Если сигнал на покупку и RSI в зоне перепроданности
                        continue  # то не совершаем продажу
                lot_cast = lot * active_cast  # Рыночная цена одного лота торгового инструмента (типа)
                final_lot_cast = 0.0
                sl_cast = lot_cast * (1 - stopLoss)  # Рассчитываем стоп-цену за лот для стоп-лосса
                tp_cast = lot_cast * (1 + takeProfit)  # Рассчитываем стоп-цену за лот для тейк-профита

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
                    await stopLossQueue.push(sl_cast, cnt_tradeLots) # Фиксируем стоп-лосс заявку в журнале заявок
                    await takeProfitQueue.push(tp_cast, cnt_tradeLots)  # Фиксируем стоп-лосс заявку в журнале заявок
                else:
                    # Если размер позиции на продажу с учетом комиссии меньше рассчитываемого, то увеличиваем количество лотов
                    while positionReal > positionSize:
                        cnt_tradeLots += 1
                        positionReal = cnt_tradeLots * final_lot_cast

                    cnt_lots -= cnt_tradeLots  # Продаем лоты инструмента (акции Тинькофф) брокеру
                    account_portfolio += positionReal  # Получаем деньги за сделку от брокера в случае продажи

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
    if not is_test:
        dfTrades.to_csv(statsTradesFilename)
        dfPortfolio.to_csv(statsPortfolioFilename)
    return dfTrades, dfPortfolio        # возвращаем в вызывающую функцию