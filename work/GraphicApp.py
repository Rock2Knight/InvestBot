# Модуль для построения статистики по торговому роботу
from datetime import datetime
import asyncio
import numpy as np
from functools import wraps
import threading
import os
import logging

from PyQt5.QtWidgets import (
    QMainWindow, QDateTimeEdit,
    QMessageBox)

import matplotlib.dates as matdates
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

import pandas as pd

import work
from api import database, crud
from GUI3 import Ui_MainWindow
#import work
import tech_analyze, core_bot
from config import program_config
from tests import test_tech_analyze


logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

resData = None

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
        raw_filename = path + "/" + tools_uid[i] + "_" + str_time_from + "_" + str_time_to + ".csv"
        filename = raw_filename.replace(":", "_")
        if os.path.isfile(filename):
            continue
        dfTool = pd.DataFrame(resData[i])
        dfTool.to_csv(filename)


def syncRequestHandler(reqs, tools_uid, frame, str_time_from, str_time_to):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(asyncRequestHandler(reqs, tools_uid, frame, str_time_from, str_time_to))


class GraphicApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(GraphicApp, self).__init__()
        self.setupUi(self)
        self.__config = program_config.ProgramConfiguration('../settings.ini')
        self.RadioNumber = 1

        self.addFigure()   # Создаем область для графика в интерфейсе

        self.account_portfolio = self.__config.start_portfolio  # Размер портфеля в рублях
        self.cnt_lots = self.__config.start_lot_count           # Количество лотов по инструменту
        self.__excel_filename = self.__config.excel_filename    # имя файла для сводной таблицы
        self.successTrades = 0              # Количество прибыльных сделок
        self.failTrades = 0                 # Количество убыточных сделок
        self.__resTrading = None            # результаты мульти-моделирования торговли
        self.__tools_uid = list([])         # Список инструментов
        self.__uid_links = dict()
        self.dataTrades = None              # результаты торговли
        self.tools_data = list([])          # Список с информацие о каждом инструменте из базы
        self.str_time_from = ''             # Дата начала моделирования
        self.str_time_to = ''               # Дата конца моделирования
        self.frame = ''                     # Таймфрейм моделирования
        self.visualData = dict()

        self.get_all_instruments()          # Загружаем uid торговых инструментов в память программы

        #self.countTrades()                  # Подсчитываем прибыльные и убыточные сделки
        self.btnGetData.clicked.connect(self.getCandles)
        self.btnModel.clicked.connect(self.setupModelThread)
        self.btnDraw.clicked.connect(self.controlDraw)     # Если была нажата кнопка рисования, проверяем, какой тип график выбран
        self.btnClear.clicked.connect(self.clear_graph)
        self.btnGenTable.clicked.connect(self.setupGenModelThread)   # Запускает поток по созданию сводной таблице по результатам моделирования
        self.btnTest.clicked.connect(self.setupTestModelThread)


    async def AsyncHistoryTrain(self, uid: str, tool_name: str, tool_lot: int):
        """
        Моделирует торговлю по инструменту с идентификатором uid за заданный период асинхронно
        :param uid: идентификатор торгового инструмента
        :return:
        """
        instruments = self.__config.strategies
        target_instrument = None
        for instrument, info in instruments.items():
            if info['uid'] == uid:
                target_instrument = instrument
                break
        return await tech_analyze.HistoryTrain(uid, self.cnt_lots,
                                                self.account_portfolio, ma_interval=self.__config.strategies[target_instrument]['ma_interval'],
                                                rsi_interval=self.__config.strategies[target_instrument]['rsi_interval'],
                                                lot=tool_lot, stopAccount=self.__config.stop_account, stopLoss=self.__config.strategies[target_instrument]['stop_loss'],
                                                time_from=self.str_time_from, time_to=self.str_time_to,
                                                timeframe=self.frame, name=tool_name)

    async def AsyncHistTrainMany(self):
        """
        Моделирует торговлю по иструментам за заданный период асинхронно
        :return
        """

        tasks = list([])
        for i in range(len(self.__tools_uid)):
            task = asyncio.create_task(self.AsyncHistoryTrain(self.__tools_uid[i], self.tools_data[i].name, self.tools_data[i].lot))
            tasks.append(task)

        self.__resTrading = await asyncio.gather(*tasks)


    def setupHistTrain(self):
        """
        Синхронный метод, обертывающий метод асинхронного моделирования
        :return:
        """
        if not self.__tools_uid:
            logging.warning("Необходимо загрузить инструменты")
            QMessageBox.information(self, "Информация по моделированию торговли", "Инструменты не загружены")
            exit()
        if not self.str_time_from and not self.str_time_to:
            self.str_time_from = self.edit_time_to.toPlainText()
            self.str_time_to = self.edit_time_from.toPlainText()
            if not self.str_time_from and self.str_time_to:
                logging.warning("Необходимо указать период моделирования")
                QMessageBox.information(self, "Информация по моделированию торговли",
                                        "Необходимо указать период моделирования")
                exit()
        if not self.frame:
            self.frame = self.tfComboBox.currentText()  # Получаем активный таймфрейм из combobox
            if not self.frame:
                logging.warning("Необходимо указать таймфрейм моделирования")
                QMessageBox.information(self, "Информация по моделированию торговли",
                                        "Необходимо указать таймфрейм моделирования")
                exit()

        loop = asyncio.new_event_loop()
        return loop.run_until_complete(self.AsyncHistTrainMany())


    async def asyncGenTable(self):
        excelHandler = None
        # Блок проверки на наличие необходимых аттрибутов
        try:
            excelHandler = work.excel_handler.ExcelHandler(self.__excel_filename)
        except Exception as e:
            logging.error(f"Ошибка при создании обработчика таблицы\n {e.args}")
            print(f"Ошибка при создании обработчика таблицы\n {e.args}")
            exit()

        if not self.str_time_from:
            logging.error("Нет начальной даты и времени")
            print("Нет начальной даты и времени")
            exit()
        if not self.str_time_to:
            logging.error("Нет конечной даты и времени")
            print("Нет конечной даты и времени")
            exit()
        if not self.frame:
            logging.error("Нет таймфрейма")
            print("Нет таймфрейма")
            exit()

        try:
            task = asyncio.create_task(excelHandler.writeStats(self.str_time_from, self.str_time_to, self.frame))
            await asyncio.gather(task)
            while not task.done():
                continue
            excelHandler.saveWorkbook()
        except Exception as e:
            logging.error(f"Произошла ошибка во время составления сводной таблицы: {e.args}")
            print(f"Произошла ошибка во время составления сводной таблицы: {e.args}")
            QMessageBox.information(self, 'Information', 'Извините. Во время составления сводной таблицы произошла ошибка')
            exit()


    def setupModelThread(self):
        logging.info(threading.enumerate())
        print(threading.enumerate(), '\n\n')
        threadModel = threading.Thread(target=self.setupHistTrain)
        threadModel.start()
        threadModel.join()
        del threadModel
        logging.info("\n\nМоделироавние успешно завершено")
        print("\n\nМоделироавние успешно завершено")
        QMessageBox.information(self, "Информация по моделированию", "Моделирование торговли успешно завршено")

    def syncTestHistModeling(self):
        self.str_time_from = self.edit_time_to.toPlainText()
        self.str_time_to = self.edit_time_from.toPlainText()
        self.frame = self.tfComboBox.currentText()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(test_tech_analyze.asyncHistTradingMany(self.str_time_from, self.str_time_to, self.frame))

    def setupTestModelThread(self):
        if not self.testRadioBtn.isChecked():
            logging.error("Неверно указана радиокнопка")
            QMessageBox.information(self, "Неверно указана кнопка", "Вы нажали не ту радиокнопку!")
            return
        thread1 = threading.Thread(self.syncTestHistModeling())
        thread1.start()
        thread1.join()

        self.frame = self.tfComboBox.currentText()

        files = os.listdir("../test_history_data/" + self.frame + "/")
        for file in files:
            l = file.split('_')
            if len(l[0]) < len(self.__tools_uid[0]):
                continue
            else:
                for i in range(len(self.__tools_uid)):
                    if l[0] == self.__tools_uid[i]:
                        self.__uid_links[self.__tools_uid[i]] = file
                        name = self.tools_data[i].name
                        self.testComboBox.addItem(name)

        QMessageBox.information(self, "Тестирование", "Данные тестирования успешно загружены!")


    def setupSetLoopGenTable(self):
        loop2 = asyncio.new_event_loop()
        loop2.run_until_complete(self.asyncGenTable())

    def setupGenModelThread(self):
        """
        Запускает поток, в котором генерируется сводная таблица Excel
        :return:
        """
        self.str_time_from = self.edit_time_to.toPlainText()
        self.str_time_to = self.edit_time_from.toPlainText()
        self.frame = self.tfComboBox.currentText()
        if not self.str_time_from or not self.str_time_to:
            QMessageBox.information(self, 'Не указаны границы периода', 'Вы не указали границы периода моделирования')
            logging.warning('Вы не указали границы периода моделирования')
            return

        logging.info(threading.enumerate())
        print(threading.enumerate(), '\n\n')

        thread2 = threading.Thread(target=self.setupSetLoopGenTable)
        thread2.start()
        thread2.join()
        del thread2
        # Отображаем окно с сообщением
        QMessageBox.information(self, 'Information', 'Построение сводной таблицы успешно завершено')


    def getCandles(self):
        """ Функция для получения котировок по инструментам, указанным в instruments.txt """
        self.str_time_from = self.edit_time_to.toPlainText()
        self.str_time_to = self.edit_time_from.toPlainText()
        reqs = list([])

        if not self.str_time_from or not self.str_time_to:
            logging.error("Не указаны границы периода моделирования")
            QMessageBox.information(self, "Информация по выгрузке котировок", "Не указаны границы периода моделирования")
            return
        time_from = datetime.strptime(self.str_time_from, "%Y-%m-%d_%H:%M:%S")
        time_to = datetime.strptime(self.str_time_to, "%Y-%m-%d_%H:%M:%S")
        if not time_from < time_to:
            logging.error("Неправильно указан границы периода моделирования")
            QMessageBox.information(self, "Информация по выгрузке котировок",
                                    "Неправильно указаны границы периода моделирования")
            return

        try:
            self.frame = self.tfComboBox.currentText() # Получаем активный таймфрейм из combobox
        except Exception as e:
            print(e.args)
            raise e

        tasks = list([])    # Задачи по выгрузке котировок по бумагам
        dataTrades = None   # Результат выполнения core_bot.async_get_candles

        try:
            for i in range(len(self.__tools_uid)):
                uid = self.__tools_uid[i]
                reqs.append(f"get_candles {uid} {self.str_time_from} {self.str_time_to} {self.frame}")
            thread1 = threading.Thread(target=syncRequestHandler, args=(reqs, self.__tools_uid, self.frame, self.str_time_from, self.str_time_to,))
            thread1.start()
            thread1.join()
            del thread1
            print('All data have been written\n')
            QMessageBox.information(self, "Информация по выгрузке котировок", "Котировки по инструментам успешно выгружены!")
        except IndexError as e:
            logging.error(f"\ne.args = {e.args}\n")
            print(f"\ne.args = {e.args}\n")
            QMessageBox.information(self, "Информация по выгрузке котировок",
                                    "Неправильны указаны аттрибуты для выгрузки")
        except BaseException as e:
            logging.error(f"\nType of exception: {type(e)}\ne.args = {e.args}\n")
            print(f"\nType of exception: {type(e)}\ne.args = {e.args}\n")
            QMessageBox.information(self, "Информация по выгрузке котировок",
                                    "Ошибка во время выгрузки котировок")


    def controlDraw(self):
        """
        Контролирует процесс отрисовки графиков
        :return:
        """
        if not self.cntTradesRadioBtn.isChecked() and not self.profitRadioBtn.isChecked() and not self.testRadioBtn.isChecked():
            QMessageBox.information(self, "Не выбран тип графика", "Вы не выбрали тип графика!")
            return

        if self.testRadioBtn.isChecked():
            df = None
            name = self.testComboBox.currentText()
            for i in range(len(self.tools_data)):
                if self.tools_data[i].name == name:
                    uid = self.tools_data[i].uid
                    filename = "../test_history_data/" + self.tfComboBox.currentText() + "/" + self.__uid_links[uid]
                    if not os.path.isfile(filename):
                        logging.error(f"Не обнаружено файла с названием: {filename}")
                        QMessageBox.information(self, "Нет пути к файлу", f"Данных моделирования по {name}\n не обнаружено")
                        return
                    df = pd.read_csv(filename)
                    break
            self.drawTestPlot(df, name)
        else:
            self.getVisualData()   # Получаем данные для отрисовки
            if self.cntTradesRadioBtn.isChecked():
                self.drawHistTrades()           # Рисуем гистограмму успешных и провльных сделок
            else:
                self.drawProfitPlot()           # Рисуем линейный график доходности по инструментам


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

    async def getVisualDataInstrument(self, tradeUidFile: str, prtfUidFile: str, name: str):
        """
        Считает количество прибыльных и убыточных сделок по инструменту, предоставляет массив с моментами времени (X) и
        массив с прибылью/убытком портфеля в каждый момент времени в процентах

        :param tradeUidFile: имя файла с результатами сделок по инструменту UID
        :param prtfUidFile: имя файла с информацией о состоянии портфеля по инструменту UID
        :param name: название торгового инструмента
        :return:
        """
        cntSuccess, cntFail = 0, 0
        dfPortfolio = pd.read_csv(prtfUidFile)
        dfTrades = None
        if tradeUidFile != "NOFILE":
            dfTrades = pd.read_csv(tradeUidFile)
        profitListTime = list(dfPortfolio['time'])
        profitListValues = list(dfPortfolio['profit_in_percent'])

        if tradeUidFile == "NOFILE":
            self.visualData[name] = (cntSuccess, cntFail, profitListTime, profitListValues)
            return

        tradeMoments = list(dfTrades['time'])

        for i in range(dfPortfolio.shape[0]):
            if dfPortfolio.iloc[i]['time'] in tradeMoments:
                # Если в этот момент времени была совершена сделка, то рассчитываем разницу между текущим состоянием
                # портфеля, и тем, что было на тот момент
                diffFullSum = dfPortfolio.iloc[-1]['cur_full_sum'] - dfPortfolio.iloc[i]['cur_full_sum']
                if diffFullSum >= 0:
                    cntSuccess += 1
                elif diffFullSum < 0:
                    cntFail += 1

        self.visualData[name] = (cntSuccess, cntFail, profitListTime, profitListValues)


    async def asyncSetupGenVisualData(self, trFilenames, prtfFilenames):
        """
        В асинхронном режиме считываем результаты моделирования по каждому инструменту

        :param trFilenames: Список файлов с информацией по сделкам
        :param prtfFilenames: Список файлов с информацией о состоянии портфеля
        """
        tasks = list([])
        for i in range(len(trFilenames)):
            logging.info(f"Filename of trades: {trFilenames[i]}")
            logging.info(f"Filename of portfolio: {prtfFilenames[i]}")
            instrument = self.tools_data[i]
            name = instrument.name
            await self.getVisualDataInstrument(trFilenames[i], prtfFilenames[i], name)

    def setupGenVisualData(self, trFilenames, prtfFilenames):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.asyncSetupGenVisualData(trFilenames, prtfFilenames))

    def getVisualData(self):
        """ Здесь считаются успешные и провальные сделки за каждый период моделирования торговли """
        cntTools = 10
        trFilenames = list([])
        prtfFilenames = list([])

        pathTrades, pathPrtf = None, None
        try:
            pathTrades, pathPrtf = self.checkPath()
        except Exception:
            QMessageBox.information(self, "Неправильный путь", "Нет пути к папке с котировками")

        self.str_time_from = self.edit_time_to.toPlainText()
        self.str_time_to = self.edit_time_from.toPlainText()

        # Формируем список с файлами результатов моделирования
        for uid in self.__tools_uid:
            tradeFile1 = pathTrades + '/' + uid + '_' + self.str_time_from + '_' + self.str_time_to + ".csv"
            pathPrtf1 = pathPrtf + '/' + uid + '_' + self.str_time_from + '_' + self.str_time_to + ".csv"
            tradeFile1 = tradeFile1.replace(':', '_')
            pathPrtf1 = pathPrtf1.replace(':', '_')
            noTrades = 0
            if not os.path.exists(tradeFile1):
                logging.info(f"Не существует файла с именем: {tradeFile1}")
                notTrades = 1
            if not os.path.exists(pathPrtf1):
                logging.info(f"Не существует файла с именем: {pathPrtf1}")
                continue

            if noTrades:
                trFilenames.append("NOFILE")
            else:
                trFilenames.append(tradeFile1)
            prtfFilenames.append(pathPrtf1)

        # Запускаем поток, получающий необходимые данные
        threadGetData = threading.Thread(target=self.setupGenVisualData, args=(trFilenames, prtfFilenames))
        threadGetData.start()
        threadGetData.join()


    def checkPath(self):
        pathTrades = "../history_data/trades_stats"
        pathPrtf = "../history_data/portfolio_stats"
        if not os.path.exists(pathTrades):
            logging.error("Не существует папки ../history_data/trades_stats")
            raise Exception("Не существует папки ../history_data/trades_stats")
        if not os.path.exists(pathPrtf):
            logging.error("Не существует папки ../history_data/portfolio_stats")
            raise Exception("Не существует папки ../history_data/portfolio_stats")

        self.frame = self.tfComboBox.currentText()
        pathTrades = pathTrades + "/" + self.frame
        pathPrtf = pathPrtf + "/" + self.frame

        if not os.path.exists(pathTrades):
            logging.error(f"Не существует папки {pathTrades}")
            raise Exception(f"Не существует папки {pathTrades}")
        if not os.path.exists(pathPrtf):
            logging.error(f"Не существует папки {pathPrtf}")
            raise Exception(f"Не существует папки {pathPrtf}")

        return pathTrades, pathPrtf

    # Построение гистограммы прибыльных и убыточных сделок
    def drawHistTrades(self):
        if not self.visualData:
            logging.warning('Нет данных для визуализации')
            QMessageBox.information(self, "Нет данных для визуализации", "Нет данных для визуализации")

        bw = 0.2
        bin = 0.6

        colors = ['b', 'g', 'r', 'aqua', 'magenta', 'maroon', 'orange', 'darkblue', 'plum', 'grey']
        y_values = list([])
        cnt_list = list([])
        keys = list([])
        for key in self.visualData.keys():
            keys.append(key)
            y_values.append(list(self.visualData[key][:2]))
            cnt_list.append(self.visualData[key][0])
            cnt_list.append(self.visualData[key][1])

        inx = len(keys)
        dw = bin / inx
        bin = dw * 4
        x_ticks = np.arange(2)
        x_ticklabels = ['Прибыльные', 'Убыточные']

        # Цикл построения
        new_bin = 0
        for i in range(inx):
            name = keys[i]
            new_bin = bin * i * bw
            self.axes.bar(x_ticks + new_bin, y_values[i], dw, color=colors[i], label=name)

        y_ticks = [t+1 for t in list(range(0, max(cnt_list)))]
        y_ticklabels = [str(y) for y in y_ticks]
        #self.axes.bar([0, 1], [self.successTrades, self.failTrades])
        self.axes.set_title("Столбчатая диаграмма соотношения \nприбыльных и убыточных сделок", fontsize=16, fontweight='bold')
        self.axes.yaxis.grid(True)
        self.axes.set_ylabel("Количество сделок, шт.", fontsize=16)
        self.axes.set_xticks(x_ticks+new_bin/2)
        self.axes.set_xticklabels(x_ticklabels, fontsize=16)
        self.axes.set_yticks(y_ticks)
        self.axes.set_yticklabels(y_ticklabels, fontsize=16)
        self.axes.legend(keys)
        self.canvas.draw()


    def drawProfitPlot(self):
        """
        Метод для рисования линейного графика доходности портфеля по результатам
        тестирования на исторических данных
        """
        colors = ['b', 'g', 'r', 'aqua', 'magenta', 'maroon', 'orange', 'darkblue', 'plum', 'grey']

        if not self.visualData:
            logging.warning('Нет данных для визуализации')
            QMessageBox.information(self, "Нет данных для визуализации", "Нет данных для визуализации")
            return
        x_list = dict()
        keys = list([])
        sizeX = 0
        main_x_set_raw = list([])
        main_x_set = None
        for key in self.visualData.keys():
            keys.append(key)
            x_list[key] = list([])
            for i in range(len(self.visualData[key][2])):
                x = datetime.strptime(self.visualData[key][2][i], '%Y-%m-%d_%H:%M:%S') # дата и время в python-datetime
                main_x_set_raw.append(x)
                x_list[key].append(matdates.date2num(x)) # дата и время в matplotlib-datetime
            if len(self.visualData[key][2]) > sizeX:
                sizeX = len(self.visualData[key][2])
                main_x_set = x_list[key]

        '''
        x_set_str = list(self.dfPortfolio['time'])                             # таймфреймы в строковом формате
        x_set_raw = [datetime.strptime(x, '%Y-%m-%d_%H:%M:%S') for x in x_set_str] # таймфреймы в python-datetime
        x_set = [matdates.date2num(x) for x in x_set_raw]                      # таймфреймы в matplotlib-datetime
        y_set = list(self.dfPortfolio['profit_in_percent'])
        '''

        candle_interval = self.tfComboBox.currentText()

        cnt_ticks = 0
        tick_step = 0
        x_ticks = list([])
        x_ticklabels = list([])

        if sizeX > self.__config.max_cnt_ticks:
            # Если количество таймфреймов больше 10, формируем массив
            # тиков так, чтобы подписи по оси X отображались нормально
            if sizeX % 10 != 0:
                cnt_ticks = (sizeX // 10) * 10 + 10
            else:
                cnt_ticks = sizeX + 1
            tick_step = cnt_ticks // 10

            for i in range(0, cnt_ticks, tick_step):
                index = None
                if i == len(main_x_set):
                    index = i - 1
                elif i > len(main_x_set):
                    break
                else:
                    index = i

                x_ticks.append(main_x_set[index])

                match candle_interval:
                    case '1_MIN' | '2_MIN' | '3_MIN' | '5_MIN' | '10_MIN' | '15_MIN':
                        label = main_x_set_raw[index].strftime("%H:%M")
                        x_ticklabels.append(label)
                    case '30_MIN' | 'HOUR' | '2_HOUR' | '4_HOUR':
                        label = main_x_set_raw[index].strftime("%d %b, %H:%M")
                        x_ticklabels.append(label)
                    case 'DAY' | 'WEEK':
                        label = main_x_set_raw[index].strftime("%d.%m.%Y")
                        x_ticklabels.append(label)
                    case 'MONTH':
                        label = main_x_set_raw[index].strftime("%Y, %b")
                        x_ticklabels.append(label)
        else:
            x_ticks = [elem for elem in main_x_set]
            for raw in main_x_set_raw:
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

        ind = 0
        for key in keys:
            self.axes.plot(x_list[key], self.visualData[key][3], color=colors[ind], label=key)
            ind += 1
        self.axes.set_xticks(x_ticks)
        self.axes.set_xticklabels(x_ticklabels, fontsize=14, rotation=25)
        self.axes.set_title(f"Доходность по торговым инструментам в \nпериод моделирования, интервал = {candle_interval}", fontsize=16, fontweight='bold')
        self.axes.set_ylabel("Доходность, %", fontsize=16)
        self.axes.set_xlabel("Время", fontsize=16)
        self.axes.set_position([0.1, 0.2, 0.8, 0.7])
        self.axes.grid(True)
        self.axes.legend(keys)
        self.canvas.draw()


    def drawTestPlot(self, profitDF, name):
        if type(profitDF) == type(None):
            logging.info(f"None profit dataframe for instrument {name}")
            QMessageBox.information(self, "None dataframe", "Для текущего датафрейма нет данных для рисования!")
            return

        time_str = profitDF['time'].to_list()

        x_list = list([])
        keys = list([])
        columns = profitDF.columns.to_list()
        sizeX = 0
        main_x_set_raw = list([])
        main_x_set = None

        for i in range(len(time_str)):
            x = datetime.strptime(time_str[i], '%Y-%m-%d_%H:%M:%S')  # дата и время в python-datetime
            main_x_set_raw.append(x)
            x_list.append(matdates.date2num(x))  # дата и время в matplotlib-datetime

        sizeX = len(x_list)
        x_ticks = list([])
        x_ticklabels = list([])
        candle_interval = self.tfComboBox.currentText()

        if sizeX > self.__config.max_cnt_ticks:
            # Если количество таймфреймов больше 10, формируем массив
            # тиков так, чтобы подписи по оси X отображались нормально
            if sizeX % 10 != 0:
                cnt_ticks = (sizeX // 10) * 10 + 10
            else:
                cnt_ticks = sizeX + 1
            tick_step = cnt_ticks // 10

            for i in range(0, cnt_ticks, tick_step):
                index = None
                if i == len(x_list):
                    index = i - 1
                elif i > len(x_list):
                    break
                else:
                    index = i

                x_ticks.append(x_list[index])

                match candle_interval:
                    case '1_MIN' | '2_MIN' | '3_MIN' | '5_MIN' | '10_MIN' | '15_MIN':
                        label = main_x_set_raw[index].strftime("%H:%M")
                        x_ticklabels.append(label)
                    case '30_MIN' | 'HOUR' | '2_HOUR' | '4_HOUR':
                        label = main_x_set_raw[index].strftime("%d %b, %H:%M")
                        x_ticklabels.append(label)
                    case 'DAY' | 'WEEK':
                        label = main_x_set_raw[index].strftime("%d.%m.%Y")
                        x_ticklabels.append(label)
                    case 'MONTH':
                        label = main_x_set_raw[index].strftime("%Y, %b")
                        x_ticklabels.append(label)
        else:
            x_ticks = [elem for elem in x_list]
            for raw in main_x_set_raw:
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



        #tests = list([])
        columns = profitDF.columns.to_list()
        columns.remove('time')
        columns.remove('Unnamed: 0')
        base_width = 5
        sm = 0
        for column in columns:
            test = profitDF[column]
            width = base_width + sm
            self.axes.plot(x_list, test, label=column, linewidth=width)
            sm -= 0.4
        self.axes.set_xticks(x_ticks)
        self.axes.set_xticklabels(x_ticklabels, fontsize=14, rotation=25)
        self.axes.set_title(f"Тест {name} за интервал {candle_interval}", fontsize=16,
            fontweight='bold')
        self.axes.set_ylabel("Доходность, %", fontsize=16)
        self.axes.set_xlabel("Время", fontsize=16)
        self.axes.set_position([0.1, 0.2, 0.8, 0.7])
        self.axes.grid(True)
        self.axes.legend(columns)
        self.canvas.draw()


    def get_all_instruments(self):
        """ Метод для получения информации о доступных активах в Тинькофф Инвестиции """
        instruments = self.__config.strategies
        db = database.SessionLocal()     # Соединение с базой данных
        try:
            i = 0
            for instrument in instruments.values():
                self.__tools_uid.append(instrument['uid'].rstrip("\n"))
                info = crud.get_instrument_uid(db, instrument_uid=self.__tools_uid[i])
                self.tools_data.append(info)
                i += 1
        except IndexError as e:
            raise e