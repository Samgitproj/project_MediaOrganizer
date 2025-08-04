import logging
import sys
from PyQt6 import QtWidgets, QtCore
from gui.MainWindow import Ui_MainWindow

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

try:
    logging.info("main.py gestart")

    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    main_window.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
    main_window.show()
    sys.exit(app.exec())

except Exception as e:
    logging.exception("Er trad een fout op in main.py:")
