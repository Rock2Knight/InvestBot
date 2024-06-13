from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1349, 803)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(40, 30, 931, 711))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.matlayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.matlayout.setContentsMargins(0, 0, 0, 0)
        self.matlayout.setObjectName("matlayout")
        self.layoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget.setGeometry(QtCore.QRect(990, 30, 360, 421))
        self.layoutWidget.setObjectName("layoutWidget")
        self.toolsVLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.toolsVLayout.setContentsMargins(0, 0, 0, 0)
        self.toolsVLayout.setObjectName("toolsVLayout")

        # Настройка кнопки для получения котировок
        self.btnGetData = QtWidgets.QPushButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnGetData.sizePolicy().hasHeightForWidth())
        self.btnGetData.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.btnGetData.setFont(font)
        self.btnGetData.setObjectName("btnGetData")
        self.toolsVLayout.addWidget(self.btnGetData)

        # Настройка кнопки для моделирования торговли
        self.btnModel = QtWidgets.QPushButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnModel.sizePolicy().hasHeightForWidth())
        self.btnModel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.btnModel.setFont(font)
        self.btnModel.setObjectName("btnModel")
        self.toolsVLayout.addWidget(self.btnModel)

        # Настройка кнопки для рисования
        self.btnDraw = QtWidgets.QPushButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnDraw.sizePolicy().hasHeightForWidth())
        self.btnDraw.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.btnDraw.setFont(font)
        self.btnDraw.setObjectName("btnDraw")
        self.toolsVLayout.addWidget(self.btnDraw)

        ''' Настройка кнопки для очистки графика '''
        self.btnClear = QtWidgets.QPushButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnDraw.sizePolicy().hasHeightForWidth())
        self.btnClear.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.btnClear.setFont(font)
        self.btnClear.setObjectName("btnDraw")
        self.toolsVLayout.addWidget(self.btnClear)

        ''' Настройка кнопки создания сводной таблицы '''
        self.btnGenTable = QtWidgets.QPushButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnGenTable.sizePolicy().hasHeightForWidth())
        self.btnGenTable.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.btnGenTable.setFont(font)
        self.btnGenTable.setObjectName("btnDraw")
        self.toolsVLayout.addWidget(self.btnGenTable)

        ''' Настройка кнопки для тестирования '''
        self.btnTest = QtWidgets.QPushButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnTest.sizePolicy().hasHeightForWidth())
        self.btnTest.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.btnTest.setFont(font)
        self.btnTest.setObjectName("btnTest")
        self.toolsVLayout.addWidget(self.btnTest)

        self.cntTradesRadioBtn = QtWidgets.QRadioButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cntTradesRadioBtn.sizePolicy().hasHeightForWidth())
        self.cntTradesRadioBtn.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.cntTradesRadioBtn.setFont(font)
        self.cntTradesRadioBtn.setObjectName("cntTradesRadioBtn")
        self.toolsVLayout.addWidget(self.cntTradesRadioBtn)

        self.profitRadioBtn = QtWidgets.QRadioButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.profitRadioBtn.sizePolicy().hasHeightForWidth())
        self.profitRadioBtn.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.profitRadioBtn.setFont(font)
        self.profitRadioBtn.setObjectName("profitRadioBtn")

        self.toolsVLayout.addWidget(self.profitRadioBtn)

        self.testRadioBtn = QtWidgets.QRadioButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.testRadioBtn.sizePolicy().hasHeightForWidth())
        self.testRadioBtn.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.testRadioBtn.setFont(font)
        self.testRadioBtn.setObjectName("profitRadioBtn")

        self.toolsVLayout.addWidget(self.testRadioBtn)

        self.tfComboBox = QtWidgets.QComboBox()
        self.tfComboBox.addItems(["1_MIN", "2_MIN", "3_MIN", "5_MIN",
                                  "10_MIN", "15_MIN", "30_MIN", "HOUR",
                                  "2_HOUR", "4_HOUR", "DAY", "WEEK", "MONTH"])
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.tfComboBox.setFont(font)
        self.tfComboBox.setObjectName("tfComboBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tfComboBox.sizePolicy().hasHeightForWidth())

        self.toolsVLayout.addWidget(self.tfComboBox)

        self.testComboBox = QtWidgets.QComboBox()
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.testComboBox.setFont(font)
        self.testComboBox.setObjectName("testComboBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.testComboBox.sizePolicy().hasHeightForWidth())

        self.toolsVLayout.addWidget(self.testComboBox)


        self.timeFromLayout = QtWidgets.QHBoxLayout()
        self.timeFromLayout.setObjectName("timeFromLayout")

        self.time_to = QtWidgets.QLabel(self.layoutWidget) # Time to label
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.time_to.sizePolicy().hasHeightForWidth())
        self.time_to.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.time_to.setFont(font)
        self.time_to.setObjectName("time_to")
        self.timeFromLayout.addWidget(self.time_to)

        self.edit_time_to = QtWidgets.QPlainTextEdit(self.layoutWidget) # Текстовое поле time_to
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edit_time_to.sizePolicy().hasHeightForWidth())
        self.edit_time_to.setSizePolicy(sizePolicy)
        self.edit_time_to.setMaximumSize(QtCore.QSize(16777215, 50000))
        self.edit_time_to.setObjectName("edit_time_to")
        self.timeFromLayout.addWidget(self.edit_time_to)

        self.toolsVLayout.addLayout(self.timeFromLayout)

        self.timeToLayout = QtWidgets.QHBoxLayout()
        self.timeToLayout.setObjectName("timeToLayout")
        self.time_from = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.time_from.setFont(font)
        self.time_from.setObjectName("time_from")
        self.timeToLayout.addWidget(self.time_from)


        self.edit_time_from = QtWidgets.QPlainTextEdit(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edit_time_from.sizePolicy().hasHeightForWidth())
        self.edit_time_from.setSizePolicy(sizePolicy)
        self.edit_time_from.setMaximumSize(QtCore.QSize(16777215, 1000))
        self.edit_time_from.setObjectName("edit_time_from")


        self.timeToLayout.addWidget(self.edit_time_from)

        self.toolsVLayout.addLayout(self.timeToLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1349, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.btnGetData.setText(_translate("MainWindow", "Получить данные"))
        self.btnModel.setText(_translate("MainWindow", "Промоделировать торговлю"))
        self.btnDraw.setText(_translate("MainWindow", "Нарисовать"))
        self.btnClear.setText(_translate("MainWindow", "Очистить"))
        self.btnGenTable.setText(_translate("MainWindow", "Создать сводную таблицу"))
        self.btnTest.setText(_translate("MainWindow", "Тест F_модель"))
        self.cntTradesRadioBtn.setText(_translate("MainWindow", "Гистограмма сделок"))
        self.profitRadioBtn.setText(_translate("MainWindow", "График доходности"))
        self.testRadioBtn.setText(_translate("MainWindow", "Тестовый график доходности"))
        self.time_to.setText(_translate("MainWindow", "T (начала):"))
        self.time_from.setText(_translate("MainWindow", "T (конца):"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
