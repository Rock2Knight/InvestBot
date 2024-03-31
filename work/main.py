import asyncio
import sys
import logging

from PyQt5 import QtWidgets
from work import *
from work import tech_analyze, core_bot
from GraphicApp import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

def main():
    app = QtWidgets.QApplication(sys.argv)
    Application = GraphicApp()
    Application.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()