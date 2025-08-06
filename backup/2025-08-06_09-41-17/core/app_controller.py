import logging
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, QUrl

from gui.MainWindow import Ui_MainWindow
from gui.MediaOrganizerGui import Ui_MediaOrganizerGui
from core import media_utils


class MediaAppController:
    def __init__(self):
        logging.info("MediaAppController gestart")

        # Start Qt-applicatie
        self.app = QtWidgets.QApplication([])

        # --- GUI-opbouw ---
        self.main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        self.dialog = QtWidgets.QDialog()
        self.ui_dialog = Ui_MediaOrganizerGui()
        self.ui_dialog.setupUi(self.dialog)

        # --- Data-opslag ---
        self.folder_paths: list[str] = []
        self.media_items: list[str] = []

        # --- Ondersteunde extensies ---
        self.supported_photo_exts = tuple(media_utils.image_extensions)
        self.supported_video_exts = tuple(media_utils.video_extensions)

        # --- MediaPlayer setup ---
        self.player = QMediaPlayer(self.main_window)
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self.handle_media_status)

        # --- Widgets in hoofdvenster ---
        self.video_widget = QVideoWidget(self.ui.mediaFrame)
        self.video_widget.setGeometry(self.ui.mediaFrame.rect())
        self.video_widget.setVisible(False)
        self.player.setVideoOutput(self.video_widget)

        self.image_label = QtWidgets.QLabel(self.ui.mediaFrame)
        self.image_label.setGeometry(self.ui.mediaFrame.rect())
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.setVisible(False)

        # --- MediaPlayer aanmaken ---
        self.media_player = MediaPlayer(
            media_label=self.image_label,
            video_widget=self.video_widget,
            player=self.player,
        )

        # --- Koppeling knoppen ---
        self.ui.btnStart.clicked.connect(lambda: self.media_player.start_slideshow())
        self.ui.btnPause.clicked.connect(self.media_player.pause_slideshow)
        self.ui.btnStop.clicked.connect(self.media_player.stop_slideshow)
        self.ui.btnNext.clicked.connect(self.media_player.play_next_media)
        self.ui.btnAddFolder.clicked.connect(self.add_folder)

        logging.info("MediaAppController: UI en componenten geïnitialiseerd.")

    def start(self):
        logging.info("Toont startdialoog (MediaOrganizerGui)")
        self.dialog.show()
        self.app.exec()

    # Dummy-methode voor connectie
    def play_next_media(self):
        pass

    def handle_media_status(self, status):
        pass

    def add_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.main_window, "Selecteer map"
        )
        if folder and folder not in self.folder_paths:
            self.folder_paths.append(folder)
            self.ui.listFolders.addItem(folder)
            logging.info(f"Map toegevoegd: {folder}")
        else:
            logging.info("Geen nieuwe map toegevoegd.")
