from imports import *

from PyQt5.QtWidgets import *

from api import crud, models
from api.database import *

import bot
import app_gui
import info_service

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

investBot = None
isFilled = False

def setup_bot(stop_event1: mp.Event, stop_event2: mp.Event, id_account: str, config_file: str, is_autofill: bool = False):
    global investBot
    global isFilled
    investBot = bot.InvestBot(account_id=id_account, filename=config_file, autofill=is_autofill)
    if is_autofill:
        isFilled = True
        return
    loop = asyncio.new_event_loop()
    loop.run_until_complete(investBot.run(stop_event1, stop_event2))

class InvestBotGui(QMainWindow, app_gui.Ui_MainWindow):

    def __init__(self):
        super(InvestBotGui, self).__init__()
        self.setupUi(self)
        self.setupBtn.clicked.connect(self.setupTrading)
        self.exitBtn.clicked.connect(self.stopTrading)
        self.pid_bot = None       # PID процесса торгового робота
        self.pid_stream = None    # PID процесса стрима
        self.__token = os.getenv('TINKOFF_TOKEN')
        self.stopBot = mp.Event()     # Событие остановки бота
        self.stopStream = mp.Event()  # Событие остановки стрима

        try:
            self.__setupBoxes()
        except Exception as e:
            p = 3

        # Связываем кнопки с событиями
        self.getAccountsBtn.clicked.connect(self.__getAccounts) # Триггер на получение счетов
        self.openAccountBtn.clicked.connect(self.__openAccount) # Триггер на открытие счета
        self.closeAccountBtn.clicked.connect(self.__closeAccount)  # Триггер на закрытие счета
        self.payInBtn.clicked.connect(self.__payIn)  # Триггер на пополнение счета
        self.getPortfolioBtn.clicked.connect(self.__get_portfolio) # Триггер на получение баланса счета
        self.getToolsBtn.clicked.connect(self.__get_tools) # Триггер на получение торговых инструментов
        self.getPosBtn.clicked.connect(self.__get_positions) # Триггер на получение позиций на счете

    def __setupBoxes(self):
        db = SessionLocal()
        sectors = crud.get_sectors_list(db)
        size = len(sectors)
        self.sectorBox.addItem('undefined')
        for i in range(size):
            self.sectorBox.addItem(sectors[i].name)
        currencies = crud.get_currency_list(db)
        size = len(currencies)
        for i in range(size):
            self.currencyBox.addItem(currencies[i].name)
        exchanges = crud.get_exchange_list(db)
        size = len(exchanges)
        self.exchangeBox.addItem('undefined')
        for i in range(size):
            self.exchangeBox.addItem(exchanges[i].name)

    def __getAccounts(self):
        """
        Получение списка счетов при нажатии на кнопку
        :return:
        """
        accounts = info_service.get_accounts()
        if not accounts:
            return
        newRow = self.accountsTable.rowCount()
        self.accountsTable.clearContents()
        while newRow:
            for i in range(newRow):
                self.accountsTable.removeRow(i)
            newRow = self.accountsTable.rowCount()
        for account in accounts:
            newRow = self.accountsTable.rowCount()
            self.accountsTable.insertRow(newRow)
            self.accountsTable.setItem(newRow, 0, QTableWidgetItem(account.id_account))
            self.accountsTable.setItem(newRow, 1, QTableWidgetItem(account.status))

    def __openAccount(self):
        account = info_service.open_account()
        QMessageBox.information(self, "Информация по созданию счета",
                                f"Создан счет с ID = {account.id_account}")

    def __closeAccount(self):
        id_list = self.accountsTable.selectedItems()
        id_list = [id.text() for id in id_list]
        if id_list:
            info_service.close_account(id_list)
            QMessageBox.information(self, "Информация по закрытию счета",
                                    "Счета успешно закрыты!")
        else:
            QMessageBox.information(self, "Информация по закрытию счета",
                                    "Вы не выбрали счета для закрытия!")

    def __payIn(self):
        sum = float(self.sumPayInEdit.toPlainText())
        id = self.idAccountEdit.toPlainText()
        info_service.pay_in(sum, id)
        QMessageBox.information(self, "Информация по пополнению",
                                f"Счет {id} пополнен на {sum:.2f} руб")

    def __get_portfolio(self):
        id_account = self.idAccountInp.toPlainText()
        balance = info_service.get_portfolio(id_account)
        self.fullSumDisp.setText(f"{balance.full_amount:.2f}")
        self.freeMoneyDisp.setText(f"{balance.free_money:.2f}")
        self.sharesSumDisp.setText(f"{balance.shares_amount:.2f}")
        self.bondsSumDisp.setText(f"{balance.bonds_amount:.2f}")
        self.etfSumDisp.setText(f"{balance.etf_amount:.2f}")
        self.profitDisp.setText(f"{balance.profit:.5f}")

    def __get_tools(self):
        '''
        self.sectorBox
        self.currencyBox
        self.exchangeBox
        '''
        sector = self.sectorBox.currentText()
        currency = self.currencyBox.currentText()
        exchange = self.exchangeBox.currentText()
        tools_list = info_service.get_instruments(sector_name=sector, exchange_name=exchange, currency_name=currency)
        if not tools_list:
            QMessageBox.information(self, "По инструментам",
                                    "Не нашлось торговых инструментов по запросу")
            return

        newRow = self.toolsTable.rowCount()
        self.toolsTable.clearContents()
        while newRow:
            for i in range(newRow):
                self.toolsTable.removeRow(i)
            newRow = self.toolsTable.rowCount()
        for tool in tools_list:
            newRow = self.toolsTable.rowCount()
            self.toolsTable.insertRow(newRow)
            self.toolsTable.setItem(newRow, 0, QTableWidgetItem(tool.ticker))
            self.toolsTable.setItem(newRow, 1, QTableWidgetItem(tool.uid))
            self.toolsTable.setItem(newRow, 2, QTableWidgetItem(tool.name))
            self.toolsTable.setItem(newRow, 3, QTableWidgetItem(tool.exchange))
            self.toolsTable.setItem(newRow, 4, QTableWidgetItem(tool.currency))
            self.toolsTable.setItem(newRow, 5, QTableWidgetItem(tool.sector))
            self.toolsTable.setItem(newRow, 6, QTableWidgetItem(tool.tool_type))

    def __get_positions(self):
        account_id = self.idAccount2.toPlainText()
        positions = info_service.get_postions(account_id)
        if not positions:
            QMessageBox.information(self, "По позициям",
                                    "На данном счете нет открытых позиций")
            return
        newRow = self.positionsTable.rowCount()
        self.toolsTable.clearContents()
        while newRow:
            for i in range(newRow):
                self.positionsTable.removeRow(i)
            newRow = self.positionsTable.rowCount()
        for pos in positions:
            newRow = self.positionsTable.rowCount()
            self.positionsTable.insertRow(newRow)
            self.positionsTable.setItem(newRow, 0, QTableWidgetItem(pos.ticker))
            self.positionsTable.setItem(newRow, 1, QTableWidgetItem(pos.uid))
            self.positionsTable.setItem(newRow, 2, QTableWidgetItem(pos.name))
            self.positionsTable.setItem(newRow, 3, QTableWidgetItem(f'{pos.price:.2f}'))
            self.positionsTable.setItem(newRow, 4, QTableWidgetItem(str(pos.count_of_lots)))
            self.positionsTable.setItem(newRow, 5, QTableWidgetItem(str(pos.cnt)))
            self.positionsTable.setItem(newRow, 6, QTableWidgetItem(f'{pos.total_amount:.2f}'))

    def setupTrading(self):
        global isFilled
        self.__process_trade = None
        account_id = None
        config_file = os.getenv('CONFIG_FILE')
        id_list = self.accountsTable.selectedItems()
        if id_list:
            id_list = [id.text() for id in id_list]
            account_id = id_list[0]
        else:
            QMessageBox.information(self, "InvestBot",
                                    "Вы не выбрали торговый счет!")
            return
        if self.autofillBox.isChecked():
            self.__process_trade = mp.Process(target=setup_bot, args=[self.stopBot, self.stopStream,
                                                                      account_id, config_file, True])
        else:
            self.__process_trade = mp.Process(target=setup_bot, args=[self.stopBot, self.stopStream, account_id,
                                                                      config_file])
        self.__process_trade.start()
        QMessageBox.information(self, "InvestBot",
                                    "Торговля запущена!")
        if self.autofillBox.isChecked():
            while self.__process_trade.is_alive():
                a = 1
            QMessageBox.information(self, "Информация о заполнении базы",
                                    "База данных успешно заполнена")
            self.__setupBoxes()

    def stopTrading(self):
        self.stopBot.set()
        self.stopStream.set()
        QMessageBox.information(self, "InvestBot", "Торговля успешно завершена!")
        self.stopBot.clear()
        self.stopStream.clear()