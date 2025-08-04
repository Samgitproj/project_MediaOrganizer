import sys
import logging
from PyQt6 import QtWidgets, QtCore
from gui.MediaOrganizerGui import Ui_Dialog
from gui.MainWindow import Ui_MainWindow

# Loggingconfiguratie
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
