import logging
import os

import openpyxl as pyxl
import pandas as pd
import numpy as np
from numba import jit

from work import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

class ExcelHandler:
    """
    Класс для работы с Excel
    """

    def __init__(self):
        self.wb = pyxl.load_workbook()
        self.sheets = list([])
        self.sheets.append(self.wb.active)
        self.sheets[0].title = "1"
        self.tools_uid = np.empty(shape=(10), dtype=str)  # numpy-массив uid инструментов

    @jit
    async def writeStats(self, time_from: str, time_to: str, timeframe: str):
        """
        Метод для записи статистики в виде сводных таблиц в Excel
        :param time_from - время начала моделирования. Нужно для поиска нужного файла
        :param time_to - время конца моделирования. Нужно для поиска нужного файла
        :param timeframe - таймфрейм моделирования. Нужно для поиска нужного файла
        :return:
        """

        if not time_from or not time_to:
            logging.error("в методе ExcelHandler.writeStatus: не указаны границы периода моделирования")
            raise ValueError("в методе ExcelHandler.writeStatus: не указаны границы периода моделирования")
        if not timeframe:
            logging.error("в методе ExcelHandler.writeStatus: не указан таймфрейм моделирования")
            raise ValueError("в методе ExcelHandler.writeStatus: не указан таймфрейм моделирования")

        async with open("instruments.txt") as tools_file:
            lines = tools_file.readlines()
            for i in range(self.tools_uid.shape[0]):
                self.tools_uid[i] = lines[i].rstrip('\n')

        self.sheets[0]['A1'] = 'Риск для счета'
        self.sheets[0]['B1'] = STOP_ACCOUNT
        self.sheets[0]['A2'] = 'STOP_LOSS'
        self.sheets[0]['B2'] = STOP_LOSS
        self.sheets[0]['A3'] = 'TAKE_PROFIT'
        self.sheets[0]['B3'] = 0
        self.sheets[0]['A4'] = 'Интервал SMA'
        self.sheets[0]['B4'] = SMA_INTERVAL
        self.sheets[0]['A5'] = 'Интервал RSI'
        self.sheets[0]['B5'] = RSI_INTERVAL
        self.sheets[0]['A6'] = 'Таймфрейм'
        self.sheets[0]['B6'] = timeframe
        self.sheets[0]['A7'] = 'Время начала моделирования'
        self.sheets[0]['B7'] = time_from
        self.sheets[0]['A8'] = 'Время конца моделирования'
        self.sheets[0]['B8'] = time_to
        self.sheets[0]['A9'] = 'Начальное количество лотов в портфеле'
        self.sheets[0]['B9'] = START_LOT_COUNT
        self.sheets[0]['A10'] = 'Начальная сумма свободных денег в портфеле'
        self.sheets[0]['B10'] = START_ACCOUNT_PORTFOLIO

        pathTrades = "../history_data/trades_stats"
        pathPrtf = "../history_data/portfolio_stats"
        if not os.path.exists(pathTrades):
            logging.error("Нет папки trades_stats")
            raise Exception("Нет папки trades_stats")
        if not os.path.exists(pathPrtf):
            logging.error("Нет папки portfolio_stats")
            raise Exception("Нет папки portfolio_stats")

        pathTrades = pathTrades + "/" + timeframe
        pathPrtf = pathPrtf + "/" + timeframe
        if not os.path.exists(pathTrades):
            logging.error(f"Нет папки trades_stats/{timeframe}")
            raise Exception(f"Нет папки trades_stats/{timeframe}")
        if not os.path.exists(pathPrtf):
            logging.error(f"Нет папки portfolio_stats/{timeframe}")
            raise Exception(f"Нет папки portfolio_stats/{timeframe}")


        '''
        # Получаем исторические свечи
        raw_tr_name = pathTrades + "/" + str(uid) + "_" + kwargs['time_from'] + "_" + kwargs['time_to'] + ".csv"
        raw_prtf_name = pathPrtf + "/" + str(uid) + "_" + kwargs['time_from'] + "_" + kwargs['time_to'] + ".csv"
        statsTradesFilename = raw_tr_name.replace(":", "_")
        statsPortfolioFilename = raw_prtf_name.replace(":", "_")
        '''