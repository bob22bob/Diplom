from PyQt5.QtWidgets import QApplication
import sys

from view import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = View()
    win.show()
    sys.exit(app.exec_())
