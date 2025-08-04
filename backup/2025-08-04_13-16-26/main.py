import logging
import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow
from gui.MediaOrganizerGui import Ui_Dialog
from gui.MainWindow import Ui_MainWindow

# Logging instellen
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


# Klasse voor het tweede venster (MainWindow)
class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


try:
    logging.info("main.py gestart")

    app = QtWidgets.QApplication(sys.argv)

    # Start met MediaOrganizerGui
    media_window = QtWidgets.QMainWindow()
    ui = Ui_Dialog()
    ui.setupUi(media_window)

    # Koppel knop aan openen van MainWindow
    def open_main_window():
        logging.info("btnStartMainwindow geklikt – hoofdvenster openen")
        main_win = MainAppWindow()
        main_win.show()
        open_main_window.main_win_ref = main_win  # voorkomt garbage collection

    ui.btnStartMainwindow.clicked.connect(open_main_window)

    media_window.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
    media_window.show()

    sys.exit(app.exec())

except Exception as e:
    logging.exception("Er trad een fout op in main.py:")
