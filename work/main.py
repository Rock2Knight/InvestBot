from GraphicApp import *
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Application = GraphicApp()
    Application.show()
    sys.exit(app.exec_())