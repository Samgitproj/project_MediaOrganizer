import logging
import math
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

        # ✅ Kolomnamen instellen voor boomstructuren
        self.ui_dialog.listFoundedItems.setHeaderLabels(
            ["📁 Map", "📸 Foto's", "🎬 Video's"]
        )
        self.ui_dialog.treeVirtueleFotos.setHeaderLabels(
            ["📅 Datum", "🖼️ Bestandsnaam", "📁 Map", "👤 Gezicht?", "📌 Tags?"]
        )

        # ✅ Voorbeelditem met checkbox (later dynamisch vullen)
        voorbeeld_item = QtWidgets.QTreeWidgetItem(["C:/foto’s/reis", "120", "4"])
        voorbeeld_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        self.ui_dialog.listFoundedItems.addTopLevelItem(voorbeeld_item)

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
        self.ui.btnRemoveFolder.clicked.connect(self.remove_selected_folder)
        self.ui.btnPrevious.clicked.connect(self.play_previous_media)
        self.ui_dialog.btnStartMainwindow.clicked.connect(
            self.verwerk_selectie_en_start_mainwindow
        )
        self.ui_dialog.btnBladerenLocation.clicked.connect(self.blader_naar_locatie)
        self.ui_dialog.btnSearchSelectedLocation.clicked.connect(
            self.start_search_from_location
        )
        self.ui_dialog.btnExportList.clicked.connect(
            self.exporteer_gevonden_mappen_naar_csv
        )

        logging.info("MediaAppController: UI en componenten geïnitialiseerd.")

    def start(self):
        logging.info("Toont startdialoog (MediaOrganizerGui)")
        self.dialog.show()
        self.app.exec()

    # Dummy-methode voor connectie
    def play_next_media(self):
        logging.info("play_next_media")

        pass

    def handle_media_status(self, status):
        logging.info("handle_media_status")

        pass

    def add_folder(self):
        logging.info("add_folder")

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.main_window, "Selecteer map"
        )
        if folder and folder not in self.folder_paths:
            self.folder_paths.append(folder)
            self.ui.listFolders.addItem(folder)
            logging.info(f"Map toegevoegd: {folder}")
        else:
            logging.info("Geen nieuwe map toegevoegd.")

    def remove_selected_folder(self):
        logging.info("remove_selected_folder")

        selected_items = self.ui.listFolders.selectedItems()
        for item in selected_items:
            folder = item.text()
            if folder in self.folder_paths:
                self.folder_paths.remove(folder)
            self.ui.listFolders.takeItem(self.ui.listFolders.row(item))
            logging.info(f"Map verwijderd: {folder}")

    def play_previous_media(self):
        logging.info("play_previous_media")

        if not self.media_items:
            logging.info("Geen media om terug te gaan.")
            return

        self.current_index = (self.current_index - 1) % len(self.media_items)
        pad = self.media_items[self.current_index]
        self.media_player.play_media(pad)

    def verwerk_selectie_en_start_mainwindow(self):
        logging.info("verwerk_selectie_en_start_mainwindow")

        if not self.folder_paths:
            QtWidgets.QMessageBox.warning(
                self.dialog, "Geen mappen", "Selecteer minstens één map."
            )
            return

        # TODO: hier kan later preprocessing komen
        self.dialog.close()
        self.main_window.show()

    def blader_naar_locatie(self):
        logging.info("blader_naar_locatie")

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.dialog, "Selecteer map om te doorzoeken"
        )
        if folder:
            self.ui_dialog.lineLocation.setText(folder)
            logging.info(f"Zoeklocatie ingesteld op: {folder}")

    def start_search_from_location(self):
        logging.info("start_search_from_location")

        location = self.ui_dialog.lineLocation.text()
        if location and os.path.exists(location):
            logging.info(f"Start zoekactie vanuit: {location}")
            # TODO: start thread of scanfunctie
        else:
            QtWidgets.QMessageBox.warning(
                self.dialog,
                "Ongeldige map",
                "Selecteer een geldige map om te doorzoeken.",
            )

    def exporteer_gevonden_mappen_naar_csv(self):
        logging.info("exporteer_gevonden_mappen_naar_csv")

        if not self.folder_paths:
            QtWidgets.QMessageBox.information(
                self.dialog, "Geen mappen", "Geen mappen om te exporteren."
            )
            return

        bestand, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.dialog, "CSV opslaan", "", "CSV-bestanden (*.csv)"
        )
        if bestand:
            try:
                with open(bestand, "w", encoding="utf-8") as f:
                    f.write("Map\n")
                    for folder in self.folder_paths:
                        f.write(f"{folder}\n")
                logging.info(f"CSV opgeslagen: {bestand}")
            except Exception as e:
                logging.exception("Fout bij opslaan van CSV:")
