import asyncio
import sys
import os
from dotenv import load_dotenv

import pandas as pd

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)
sys.path.append(main_path+'work\\')
sys.path.append(main_path+'app\\')

from work import *
from work.tech_analyze import HistoryTrain
from .sync_tech_analyze import SyncHistoryTrain
from config.program_config import ProgramConfiguration
from utils_funcs import utils_funcs

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

@utils_funcs.test_retry()
async def asyncHistTradingMany(str_time_from: str, str_time_to: str, frame: str, config: ProgramConfiguration, no_exec=False):

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

    pathTest = main_path + "test_history_data\\" + frame
    if not os.path.exists(pathTest):
        os.mkdir(pathTest)

    if not config:
        config = ProgramConfiguration(main_path+"settings.ini")

    tools = config.strategies
    i = 0
    for ticker, info in tools.items():
        resTrading[info['uid']] = list([])
        tasks[info['uid']] = list([])
        instrument = crud.get_instrument_uid(db, info['uid'])
        instrument_lot = instrument.lot
        instrument_name = instrument.name
        names.append(instrument_name)
        profitDict[instrument_name] = dict()
        # Формируем задачу моделирования по одним параметрам
        task = asyncio.create_task(HistoryTrain(info['uid'], config.start_lot_count, config.start_portfolio, is_test=True,
                                                lot=instrument_lot, ma_type=info['ma_type'], ma_interval=info['ma_interval'],
                                                rsi_interval=info['rsi_interval'], stopAccount=config.stop_account,
                                                stopLoss=info['stop_loss'], takeProfit=info['take_profit'],
                                                time_from=str_time_from, time_to=str_time_to,
                                                timeframe=frame, name=instrument_name))
        # Формируем цикл, в котором много раз вызываем эту функцию
        for j in range(10):
            tasks[info['uid']].append(task)
        # Делаем множественный вызов функции моделирования с однми аргументами
        resTrading[info['uid']] = None
        done, pending = None, None
        try:
            resTrading[info['uid']] = await asyncio.gather(*tasks[info['uid']])
            resTrading[info['uid']], pending = await asyncio.wait(tasks[info['uid']])
        except Exception as e:
            print(f"\nError during testing strategy on {ticker} instrument")
            i += 1
            continue

        prtfTasks = list([])
        tradesTasks = list([])
        while pending:
            continue
        etResTrading = resTrading[info['uid']][0]
        size = len(resTrading[info['uid']])
        test_var = 'test'
        noneFlag = 0

        if type(None) == type(resTrading[info['uid']][0][1]):
            noneFlag = 1
        else:
            profitDict[names[i]]['time'] = resTrading[info['uid']][0][1]['time']

        # Формируем список задач на сравнение результатов моделирования с эталоном
        if not noneFlag:
            profitDict[names[i]][test_var + '_1'] = resTrading[info['uid']][0][1]['profit_in_percent']

        for j in range(1, size):
            dfTrades = resTrading[info['uid']][j][0]
            dfPortfolio = resTrading[info['uid']][j][1]
            if not noneFlag:
                profitDict[names[i]][test_var + '_' + str(j + 1)] = resTrading[info['uid']][j][1]['profit_in_percent']
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
        i += 1

    dfTest = pd.Series(resTest, index=names)
    fNameTest = pathTest + "\\" + str_time_from + '_' + str_time_to + '.csv'
    fNameTest = fNameTest.replace(':', '_')
    dfTest.to_csv(fNameTest)
    print("Тестирование завершено!")
