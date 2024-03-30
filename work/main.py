import asyncio
import sys

from PyQt5 import QtWidgets
from work import *
from work import tech_analyze, core_bot
from GraphicApp import *

def main():
    app = QtWidgets.QApplication(sys.argv)
    Application = GraphicApp()
    return Application, app


async def async_main():
    Application, app = main()
    #await Application.ainit()
    Application.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    asyncio.run(async_main())