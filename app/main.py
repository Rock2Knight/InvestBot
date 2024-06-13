from imports import *
from bot_gui import InvestBotGui, QApplication

import bot
import stream_client

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")

# Раздел констант
ACCOUNT_ID = "2ba038af-dbd8-46e4-9838-a49c30583a49"
CONFIG_FILE = "settings.ini"
MAX_MIN_INTERVAL = 14                                  # Интервал поиска максимумов и минимумов
COMMISION = 0.003                                      # коммисия брокера

if __name__ == '__main__':
    app = QApplication(sys.argv)
    Application = InvestBotGui()
    Application.show()
    sys.exit(app.exec_())