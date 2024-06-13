import asyncio
import sys
import logging
import sys
import os
from dotenv import load_dotenv

from PyQt5 import QtWidgets

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)
sys.path.append(main_path+'work/')

from work import *
from work import tech_analyze, core_bot
from GraphicApp import *

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

CONFIG_FILE = "settings.ini"

def main():
    global CONFIG_FILE
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) > 1:
        CONFIG_FILE = sys.argv[1]
    Application = GraphicApp(filename=CONFIG_FILE)
    Application.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()