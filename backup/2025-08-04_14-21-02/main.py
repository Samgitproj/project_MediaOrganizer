from core.FotoBeheerApp import FotoBeheerApp
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

image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".heic", ".webp"]
video_extensions = [
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mpeg",
    ".mpg",
]

# Folders die we bewust overslaan
excluded_folders = [
    r"C:\$Recycle.Bin",
    r"C:\System Volume Information",
    r"C:\Recovery",
    r"C:\Config.Msi",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Windows",
    r"C:\PerfLogs",
    r"C:\ProgramData",
    r"C:\Intel",
    r"C:\MSOCache",
]


# Detecteer of een bestand een media-item is op basis van filter (images/videos/all)
def is_media_file(filepath: str, filtertype: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    if filtertype == "images":
        return ext in image_extensions
    elif filtertype == "videos":
        return ext in video_extensions
    elif filtertype == "all":
        return ext in image_extensions or ext in video_extensions
    return False


# Klasse voor het tweede venster (MainWindow)
class MainAppWindow(FotoBeheerApp):
    def __init__(self):
        super().__init__()


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
