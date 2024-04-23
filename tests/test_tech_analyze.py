import asyncio
import os

import pandas as pd

from work import *
from work.tech_analyze import HistoryTrain

from api.database import SessionLocal
import api.crud as crud
import api.models as models


async def modelResTradesCmp(dfTrades, etDfTrades):
    """
    Проверяет, что датафрейм сделок равен эталонному датафрейму сделок
    :param dfTrades: проверяемый датафрейм сделок
    :param etDfTrades: эталонный датафрейм сделок
    :return: True, если dfTrades = etDfTrades, False, если нет
    """
    if type(None) == type(dfTrades) and type(None) == type(etDfTrades):
        return True

    sizeEtalon = etDfTrades.shape[0]
    sizeObject = dfTrades.shape[0]

    if sizeObject != sizeEtalon:
        return False

    for i in range(sizeEtalon):
        tEtalon = etDfTrades.iloc[i]['time']
        tObject = dfTrades.iloc[i]['time']
        if tObject != tEtalon:
            return False
        if dfTrades.iloc[i]['trade_direct'] != etDfTrades.iloc[i]['trade_direct']:
            return False
        if dfTrades.iloc[i]['position_size'] != etDfTrades.iloc[i]['position_size']:
            return False
        if dfTrades.iloc[i]['stop_loss_size'] != etDfTrades.iloc[i]['stop_loss_size']:
            return False
        if dfTrades.iloc[i]['active_cast'] != etDfTrades.iloc[i]['active_cast']:
            return False
        if dfTrades.iloc[i]['lot_size'] != etDfTrades.iloc[i]['lot_size']:
            return False
        if dfTrades.iloc[i]['lot_cast'] != etDfTrades.iloc[i]['lot_cast']:
            return False
        if dfTrades.iloc[i]['position_size_real'] != etDfTrades.iloc[i]['position_size_real']:
            return False
        if dfTrades.iloc[i]['lot_cnt'] != etDfTrades.iloc[i]['lot_cnt']:
            return False

    return True


async def modelResPrtfCmp(dfPortfolio, etDfPortfolio):
    """
    Проверяет, что датафрейм с портфеля равен эталонному датафрейму портфеля
    :param dfPortfolio: портфель, который мы проверяем
    :param etDfPortfolio: эталонный портфель, с которым мы сравниваем
    :return:
    """
    if type(None) == type(dfPortfolio) and type(None) == type(etDfPortfolio):
        return True

    sizeEtalon = etDfPortfolio.shape[0]
    sizeObject = dfPortfolio.shape[0]

    if sizeObject != sizeEtalon:
        return False

    for i in range(sizeEtalon):
        tEtalon = etDfPortfolio.iloc[i]['time']
        tObject = dfPortfolio.iloc[i]['time']
        if tObject != tEtalon:
            return False
        if dfPortfolio.iloc[i]['cur_full_sum'] != etDfPortfolio.iloc[i]['cur_full_sum']:
            return False
        if dfPortfolio.iloc[i]['cur_free_sum'] != etDfPortfolio.iloc[i]['cur_free_sum']:
            return False
        if dfPortfolio.iloc[i]['cur_cnt_lots'] != etDfPortfolio.iloc[i]['cur_cnt_lots']:
            return False
        if dfPortfolio.iloc[i]['profit_in_rub'] != etDfPortfolio.iloc[i]['profit_in_rub']:
            return False
        if dfPortfolio.iloc[i]['profit_in_percent'] != etDfPortfolio.iloc[i]['profit_in_percent']:
            return False
        if dfPortfolio.iloc[i]['SM_SELL_sum'] != etDfPortfolio.iloc[i]['SM_SELL_sum']:
            return False

    return True

async def asyncHistTradingMany(str_time_from: str, str_time_to: str, frame: str):

    tasks = dict()
    resTrading = dict()
    resTest = dict()
    uid_list = list([])
    #str_time_from = "2023-06-01_10:00:00"
    #str_time_to = "2024-03-31_23:00:00"
    names = list([])
    profitDict = dict()
    timeInedexDict = dict()
    db = SessionLocal()

    pathTest = "../test_history_data/" + frame
    if not os.path.exists(pathTest):
        os.mkdir(pathTest)

    with open("../work/instruments.txt", "r") as uid_file:
        for i in range(10):
            uid_list.append(uid_file.readline().rstrip('\n'))

    for i in range(10):
        resTrading[uid_list[i]] = list([])
        tasks[uid_list[i]] = list([])
        instrument = crud.get_instrument_uid(db, uid_list[i])
        instrument_lot = instrument.lot
        instrument_name = instrument.name
        names.append(instrument_name)
        profitDict[instrument_name] = dict()
        # Формируем задачу моделирования по одним параметрам
        task = asyncio.create_task(HistoryTrain(uid_list[i], START_LOT_COUNT, START_ACCOUNT_PORTFOLIO, is_test=True,
                                                lot=instrument_lot, ma_interval=SMA_INTERVAL, rsi_interval=RSI_INTERVAL,
                                                stopAccount=STOP_ACCOUNT, stopLoss=STOP_LOSS,
                                                time_from=str_time_from, time_to=str_time_to,
                                                timeframe=frame, name=instrument_name))

        # Формируем цикл, в котором много раз вызываем эту функцию
        for j in range(10):
            tasks[uid_list[i]].append(task)
        # Делаем множественный вызов функции моделирования с однми аргументами
        resTrading[uid_list[i]] = await asyncio.gather(*tasks[uid_list[i]])

        prtfTasks = list([])
        tradesTasks = list([])
        etResTrading = resTrading[uid_list[i]][0]
        size = len(resTrading[uid_list[i]])
        test_var = 'test'
        noneFlag = 0

        if type(None) == type(resTrading[uid_list[i]][0][1]):
            noneFlag = 1
        else:
            profitDict[names[i]]['time'] = resTrading[uid_list[i]][0][1]['time']

        # Формируем список задач на сравнение результатов моделирования с эталоном
        if not noneFlag:
            profitDict[names[i]][test_var+'_1'] = resTrading[uid_list[i]][0][1]['profit_in_percent']

        for j in range(1, size):
            dfTrades = resTrading[uid_list[i]][j][0]
            dfPortfolio = resTrading[uid_list[i]][j][1]
            if not noneFlag:
                profitDict[names[i]][test_var+'_'+str(j+1)] = resTrading[uid_list[i]][j][1]['profit_in_percent']
            tradesTasks.append(asyncio.create_task(modelResTradesCmp(dfTrades, etResTrading[0])))
            prtfTasks.append(asyncio.create_task(modelResPrtfCmp(dfPortfolio, etResTrading[1])))
        # Запускаем планировщики задач на сравнение результатов моделирования с эталоном
        resTradesCmp = await asyncio.gather(*tradesTasks)
        resPrtfCmp = await asyncio.gather(*prtfTasks)

        resTest[names[i]] = 0
        if False in resTradesCmp or False in resPrtfCmp:
            resTest[names[i]] = 0
        else:
            resTest[names[i]] = size

        # Формируем датафрейм доходности по тестам для инструмента
        if not noneFlag:
            dfTestPortfolio = pd.DataFrame(profitDict[names[i]])
            fileTestRes = pathTest + "/" + uid_list[i] + "_" + str_time_from.replace(":", "_")
            fileTestRes = fileTestRes + "_" + str_time_to.replace(":", "_") + ".csv"
            dfTestPortfolio.to_csv(fileTestRes)

    dfTest = pd.Series(resTest, index=names)
    fNameTest = pathTest + "/" + str_time_from + '_' + str_time_to + '.csv'
    fNameTest = fNameTest.replace(':', '_')
    dfTest.to_csv(fNameTest)
    print("Тестирование завершено!")
