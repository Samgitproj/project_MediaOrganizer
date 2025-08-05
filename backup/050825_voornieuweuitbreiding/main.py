from core.FotoBeheerApp import FotoBeheerApp
import logging
import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow


# Logging instellen
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

try:
    logging.info("main.py gestart")

    app = QtWidgets.QApplication(sys.argv)
    app_controller = FotoBeheerApp()
    app_controller.dialog.show()

    sys.exit(app.exec())

except Exception as e:
    logging.exception("Er trad een fout op in main.py:")
