# Модуль для построения статистики по торговому роботу
from datetime import datetime
import asyncio
import numpy as np
from functools import wraps
import threading
import os

from PyQt5.QtWidgets import (
    QMainWindow,
    QDateTimeEdit,
    QMessageBox)

from tinkoff.invest.schemas import InstrumentStatus

import matplotlib.dates as matdates
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

import pandas as pd

from api import database, models, crud
from GUI3 import Ui_MainWindow
from work import *
import tech_analyze, exceptions, core_bot


resData = None

def printResData():
    global resData
    if not resData:
        raise ValueError("Нет котировок")

    cntShares = len(resData)
    for i in range(cntShares):
        size = len(resData[i]['open'])
        print(f"Info about resData[{i}] with timeframe DAY:\ntime_m\t\topen\tclose\thigh\tlow\n")
        for j in range(size):
            time_t = resData[i]['time'][j]
            open_t = resData[i]['open'][j]
            close_t = resData[i]['close'][j]
            high_t = resData[i]['high'][j]
            low_t = resData[i]['low'][j]
            volume_t = resData[i]['volume'][j]

            print(f"{time_t}\t\t{open_t}\t\t{close_t}\t\t{high_t}\t\t{low_t}\t\t{volume_t}")
        filename = "../instruments_info/tool_" + str(i) + ".csv"
        print('../instruments_info/')


async def asyncRequestHandler(reqs, tools_uid, frame, str_time_from, str_time_to):
    global resData

    tasks = list([])            # Очередь запросов
    for i in range(len(reqs)):
        task = asyncio.create_task(core_bot.async_get_candles(reqs[i]))
        tasks.append(task)
    resData = await asyncio.gather(*tasks)

    path = "../instruments_info/" + frame
    if not os.path.exists(path):
        os.mkdir(path)

    for i in range(len(resData)):
        filename = path + "/" + tools_uid[i] + "" + str_time_from + "_" + str_time_to + ".csv"
        dfTool = pd.DataFrame(resData[i])
        dfTool.to_csv(filename)


def syncRequestHandler(reqs, tools_uid, frame, str_time_from, str_time_to):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(asyncRequestHandler(reqs, tools_uid, frame, str_time_from, str_time_to))


class GraphicApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(GraphicApp, self).__init__()
        self.setupUi(self)
        self.RadioNumber = 1

        self.addFigure()   # Создаем область для графика в интерфейсе

        self.account_portfolio = 100000.00  # Размер портфеля в рублях
        self.cnt_lots = 1000                # Количество лотов акции FIGI
        self.successTrades = 0              # Количество прибыльных сделок
        self.failTrades = 0                 # Количество убыточных сделок
        self.dfTrades = None                # Статистика сделок
        self.dfPortfolio = None             # Статистика доходности портфеля
        self.tools_uid = list([])       # Список инструментов
        self.dataTrades = None              # результаты торговли
        self.tools_data = list([])

        self.get_all_instruments()          # Загружаем uid торговых инструментов в память программы

        # Моделируем торговлю на исторических данных
        '''
        self.dfTrades, self.dfPortfolio = tech_analyze.HistoryTrain(FIGI, self.cnt_lots,
                                                                    self.account_portfolio, ma_interval=5,
                                                                    lot=LOT, stopAccount=STOP_ACCOUNT,
                                                                    stopLoss=STOP_LOSS)
        '''

        #self.countTrades()                  # Подсчитываем прибыльные и убыточные сделки
        self.btnGetData.clicked.connect(self.getCandles)
        self.btnDraw.clicked.connect(self.checkRadio)     # Если была нажата кнопка рисования, проверяем, какой тип график выбран
        self.btnClear.clicked.connect(self.clear_graph)
        #self.btnGetActiveInfo.clicked.connect(self.get_all_instruments)
        # self.period.activated[str].connect(self.setCSVList)

    async def ainit(self):
        task = asyncio.create_task(self.AsyncHistoryTrain())
        res = await asyncio.gather(task)
        self.dfTrades, self.dfPortfolio = res[0][0], res[0][1]
        self.countTrades()                  # Подсчитываем прибыльные и убыточные сделки


    async def AsyncHistoryTrain(self):
        return await tech_analyze.HistoryTrain(FIGI, self.cnt_lots,
                                                self.account_portfolio, ma_interval=5,
                                                lot=LOT, stopAccount=STOP_ACCOUNT,
                                                stopLoss=STOP_LOSS)

    def getCandles(self):
        """ Функция для получения котировок по инструментам, указанным в instruments.txt """
        str_time_from = self.edit_time_to.toPlainText()
        str_time_to = self.edit_time_from.toPlainText()
        reqs = list([])

        frame = None
        try:
            frame = self.tfComboBox.currentText() # Получаем активный таймфрейм из combobox
        except Exception as e:
            print(e.args)
            raise e

        tasks = list([])    # Задачи по выгрузке котировок по бумагам
        dataTrades = None   # Результат выполнения core_bot.async_get_candles

        try:
            for i in range(len(self.tools_uid)):
                uid = self.tools_uid[i]
                reqs.append(f"get_candles {uid} {str_time_from} {str_time_to} {frame}")
            thread1 = threading.Thread(target=syncRequestHandler, args=(reqs, self.tools_uid, frame, str_time_from, str_time_to,))
            thread1.start()
            thread1.join()
            del thread1
            print('All data have been written\n')

            if resData:
                printResData()
        except IndexError as e:
            print(f"\ne.args = {e.args}\n")
            raise e
        except BaseException as e:
            print(f"\nType of exception: {type(e)}\ne.args = {e.args}\n")
            raise e


    def checkRadio(self):
        if self.cntTradesRadioBtn.isChecked():
            self.drawHistTrades()
        elif self.profitRadioBtn.isChecked():
            self.drawProfitPlot()

    # Метод, добавляющий область для рисования графика в GUI
    def addFigure(self):
        self.fig = Figure()  # Создаем область для фигуры
        self.axes = self.fig.add_subplot(111)  # Система координат
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Добавляем канву и меню навигации в виджет
        self.matlayout.addWidget(self.canvas)
        self.matlayout.addWidget(self.toolbar)

    def clear_graph(self):
        self.axes.clear()
        self.canvas.draw()

    def countTrades(self):
        """ Здесь считаются успешные и провальные сделки за каждый период моделирования торговли """
        if self.dfPortfolio.shape[0] == 0:
            self.successTrades, self.failTrades = 0, 0
            return
        curPortfolio = self.dfPortfolio.iloc[-1]

        tradeMoments = set(self.dfTrades['time'])  # Формируем множество моментов времени, когда совершались сделки

        for i in range(self.dfPortfolio.shape[0]):
            if self.dfPortfolio.iloc[i]['time'] in tradeMoments:
                # Если в этот момент времени была совершена сделка, то рассчитываем разницу между текущим состоянием
                # портфеля, и тем, что было на тот момент
                diffFullSum = curPortfolio['cur_full_sum'] - self.dfPortfolio.iloc[i]['cur_full_sum']
                if diffFullSum > 0:
                    self.successTrades += 1
                elif diffFullSum < 0:
                    self.failTrades += 1

    # Построение гистограммы прибыльных и убыточных сделок
    def drawHistTrades(self):
        if self.dfPortfolio.empty:
            raise exceptions.GuiError('Нет данных для визуализации')

        x_ticks = [0, 1]
        x_ticklabels = ['Success', 'Fail']
        y_ticks = list(range(0, max(self.successTrades, self.failTrades)+1))
        y_ticklabels = [str(y) for y in y_ticks]
        self.axes.bar([0, 1], [self.successTrades, self.failTrades])
        self.axes.grid(True)
        self.axes.set_xticks(x_ticks)
        self.axes.set_xticklabels(x_ticklabels, fontsize=16)
        self.axes.set_yticks(y_ticks)
        self.axes.set_yticklabels(y_ticklabels, fontsize=16)
        self.canvas.draw()

    def drawProfitPlot(self):
        """
        Метод для рисования линейного графика доходности портфеля по результатам
        тестирования на исторических данных
        """
        if self.dfPortfolio.empty:
            raise exceptions.GuiError('Нет данных для визуализации')

        x_set_str = list(self.dfPortfolio['time'])                             # таймфреймы в строковом формате
        x_set_raw = [datetime.strptime(x, '%Y-%m-%d_%H:%M:%S') for x in x_set_str] # таймфреймы в python-datetime
        x_set = [matdates.date2num(x) for x in x_set_raw]                      # таймфреймы в matplotlib-datetime
        y_set = list(self.dfPortfolio['profit_in_percent'])

        candle_interval = None
        with open("../candle_interval.txt", 'r', encoding='utf-8') as file:
            candle_interval = file.readline()   # Считываем из CSV длину таймфрейма

        sizeX = len(x_set)
        cnt_ticks = 0
        tick_step = 0
        x_ticks = list([])
        x_ticklabels = list([])

        if sizeX > MAX_CNT_TICKS:
            # Если количество таймфреймов больше 10, формируем массив
            # тиков так, чтобы подписи по оси X отображались нормально
            if sizeX % 10 != 0:
                cnt_ticks = (sizeX // 10) * 10 + 10
            else:
                cnt_ticks = sizeX + 1
            tick_step = cnt_ticks // 10

            for i in range(0, cnt_ticks, tick_step):
                index = None
                if i == len(x_set):
                    index = i - 1
                elif i > len(x_set):
                    break
                else:
                    index = i

                x_ticks.append(x_set[index])

                match candle_interval:
                    case '1_MIN' | '2_MIN' | '3_MIN' | '5_MIN' | '10_MIN' | '15_MIN':
                        label = x_set_raw[index].strftime("%H:%M")
                        x_ticklabels.append(label)
                    case '30_MIN' | 'HOUR' | '2_HOUR' | '4_HOUR':
                        label = x_set_raw[index].strftime("%d %b, %H:%M")
                        x_ticklabels.append(label)
                    case 'DAY' | 'WEEK':
                        label = x_set_raw[index].strftime("%d.%m.%Y")
                        x_ticklabels.append(label)
                    case 'MONTH':
                        label = x_set_raw[index].strftime("%Y, %b")
                        x_ticklabels.append(label)
        else:
            x_ticks = [elem for elem in x_set]
            for raw in x_set_raw:
                match candle_interval:
                    case '1_MIN' | '2_MIN' | '3_MIN' | '5_MIN' | '10_MIN' | '15_MIN':
                        label = raw.strftime("%H:%M")
                        x_ticklabels.append(label)
                    case '30_MIN' | 'HOUR' | '2_HOUR' | '4_HOUR':
                        label = raw.strftime("%d %b, %H:%M")
                        x_ticklabels.append(label)
                    case 'DAY' | 'WEEK':
                        label = raw.strftime("%d.%m.%Y")
                        x_ticklabels.append(label)
                    case 'MONTH':
                        label = raw.strftime("%Y, %b")
                        x_ticklabels.append(label)

        self.axes.plot(x_set, y_set)
        self.axes.set_xticks(x_ticks)
        self.axes.set_xticklabels(x_ticklabels, fontsize=14, rotation=25)
        self.axes.grid(True)
        self.canvas.draw()

    """ Метод для получения информации о доступных активах в Тинькофф Инвестиции """
    def get_all_instruments(self):

        with open("instruments.txt", 'r', encoding='utf-8') as file:
            instruments = file.readlines()
            db = database.SessionLocal()     # Соединение с базой данных
            try:
                for i in range(len(instruments)):
                    self.tools_uid.append(instruments[i].rstrip("\n"))
                    info = crud.get_instrument_uid(db, instrument_uid=self.tools_uid[i])
                    self.tools_data.append(info)
            except IndexError as e:
                raise e