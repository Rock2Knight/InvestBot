# Модуль для построения статистики по торговому роботу
from datetime import datetime

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QMainWindow,
    QDateTimeEdit,
    QMessageBox)

import matplotlib.dates as matdates
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from GUI import Ui_MainWindow
from work import tech_analyze

# Раздел констант
FIGI = "BBG00475KKY8"  # FIGI анализируемого инструемента
MAX_CNT_TICKS = 10     # Максимальное количество подписей по оси X

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

        # Моделируем торговлю на исторических данных
        self.dfTrades, self.dfPortfolio = tech_analyze.HistoryTrain(FIGI, self.cnt_lots,
                                                                    self.account_portfolio, ma_interval=5)
        self.countTrades()                  # Подсчитываем прибыльные и убыточные сделки
        self.btnDraw.clicked.connect(self.checkRadio)     # Если была нажата кнопка рисования, проверяем, какой тип график выбран
        self.btnClear.clicked.connect(self.clear_graph)
        # self.period.activated[str].connect(self.setCSVList)


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
        start_trade_moment = self.dfTrades.iloc[0]['time']   # Региструем момент первой сделки
        start_index = 0
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
        x_set_str = list(self.dfPortfolio['time'])                             # таймфреймы в строковом формате
        x_set_raw = [datetime.strptime(x, '%Y-%m-%d_%H:%M:%S') for x in x_set_str] # таймфреймы в python-datetime
        x_set = [matdates.date2num(x) for x in x_set_raw]                      # таймфреймы в matplotlib-datetime
        y_set = list(self.dfPortfolio['profit_in_percent'])

        print(f"Type of date: {type(x_set[0])}")
        print(f"Count of dates: {len(x_set)}")
        print("Dates:")
        for i in range(10):
            print(x_set[i])
        print("\n")

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
                x_ticks.append(x_set[i])

                match candle_interval:
                    case '1_MIN' | '2_MIN' | '3_MIN' | '5_MIN' | '10_MIN' | '15_MIN':
                        label = x_set_raw[i].strftime("%H:%M")
                        x_ticklabels.append(label)
                    case '30_MIN' | 'HOUR' | '2_HOUR' | '4_HOUR':
                        label = x_set_raw[i].strftime("%d %b, %H:%M")
                        x_ticklabels.append(label)
                    case 'DAY' | 'WEEK':
                        label = x_set_raw[i].strftime("%d.%m.%Y")
                        x_ticklabels.append(label)
                    case 'MONTH':
                        label = x_set_raw[i].strftime("%Y, %b")
                        x_ticklabels.append(label)

        self.axes.plot(x_set, y_set)
        self.axes.set_xticks(x_ticks)
        self.axes.set_xticklabels(x_ticklabels, fontsize=14, rotation=25)
        self.axes.grid(True)
        self.canvas.draw()