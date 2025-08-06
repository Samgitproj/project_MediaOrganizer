# Nieuw script: FotoBeheerApp
import logging
import os
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from gui.MainWindow import Ui_MainWindow
from gui.MediaOrganizerGui import Ui_Dialog
from core import media_utils

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


class FotoBeheerApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.folder_paths: list[str] = []
        self.supported_photo_exts = tuple(media_utils.image_extensions)
        self.supported_video_exts = tuple(media_utils.video_extensions)
        self.media_items: list[str] = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False

        # Timer voor foto's
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_next_media)

        # MediaPlayer en widgets
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self.handle_media_status)

        self.video_widget = QVideoWidget(self.ui.mediaFrame)
        self.video_widget.setGeometry(self.ui.mediaFrame.rect())
        self.video_widget.setVisible(False)
        self.player.setVideoOutput(self.video_widget)

        self.image_label = QtWidgets.QLabel(self.ui.mediaFrame)
        self.image_label.setGeometry(self.ui.mediaFrame.rect())
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.setVisible(False)

        # Knoppen koppelen
        self.ui.btnAddFolder.clicked.connect(self.add_folder)
        self.ui.btnRemoveFolder.clicked.connect(self.remove_selected_folder)
        self.ui.btnStart.clicked.connect(self.start_slideshow)
        self.ui.btnPause.clicked.connect(self.pause_slideshow)
        self.ui.btnStop.clicked.connect(self.stop_slideshow)
        self.ui.btnNext.clicked.connect(self.play_next_media)
        self.ui_dialog.btnExportList.clicked.connect(
            self.exporteer_gevonden_mappen_naar_csv
        )
        self.ui.btnPrevious.clicked.connect(self.play_previous_media)
        self.ui_dialog.btnBladerenLocation.clicked.connect(self.blader_naar_locatie)
        self.ui_dialog.btnSearchSelectedLocation.clicked.connect(
            self.start_search_from_location
        )
        self.ui_dialog.btnStartMainwindow.clicked.connect(
            self.verwerk_selectie_en_start_mainwindow
        )

        logging.info("FotoBeheerApp UI is geïnitialiseerd.")

    def toon_mainwindow(self):
        self.show()

    def blader_naar_locatie(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.dialog, "Selecteer map"
        )
        if folder:
            self.ui_dialog.lineScriptLocationMedia.setText(folder)
            logging.info(f"Gekozen map: {folder}")

    def zoek_media_in_map(self, map_pad):
        resultaten = []
        reeds_verwerkt = set()

        try:
            for root, dirs, files in os.walk(map_pad):
                foto_count = 0
                video_count = 0

                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in self.supported_photo_exts:
                        foto_count += 1
                    elif ext in self.supported_video_exts:
                        video_count += 1

                if (foto_count + video_count) > 0:
                    abs_pad = os.path.abspath(root)
                    if abs_pad not in reeds_verwerkt:
                        resultaten.append((abs_pad, foto_count, video_count))
                        reeds_verwerkt.add(abs_pad)

        except Exception as e:
            logging.warning(f"Fout bij het lezen van {map_pad}: {e}")

        return resultaten

    def verwerk_selectie_en_start_mainwindow(self):
        geselecteerde_items = self.ui_dialog.listFoundedItems.selectedItems()
        if not geselecteerde_items:
            QtWidgets.QMessageBox.warning(
                self.dialog, "Geen selectie", "Selecteer eerst een map."
            )
            return

        geselecteerde_pad = geselecteerde_items[0].text(0)
        self.folder_paths.append(geselecteerde_pad)
        self.ui.listFolders.addItem(geselecteerde_pad)
        self.show()

    def start_search_from_location(self):
        folder = self.ui_dialog.lineScriptLocationMedia.text().strip()
        if not folder or not os.path.isdir(folder):
            QtWidgets.QMessageBox.warning(
                self.dialog,
                "Geen map",
                "Selecteer eerst een geldige map via de bladerknop.",
            )
            logging.warning("Geen map opgegeven voor zoekactie.")
            return

        self.ui_dialog.listFoundedItems.clear()
        resultaten = self.zoek_media_in_map(folder)
        for pad, foto_count, video_count in resultaten:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, pad)
            item.setText(1, str(foto_count))
            item.setText(2, str(video_count))
            self.ui_dialog.listFoundedItems.addTopLevelItem(item)
        logging.info(f"Zoekactie voltooid – {len(resultaten)} resultaten gevonden")

    def exporteer_gevonden_mappen_naar_csv(self):
        pad, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Exporteer naar CSV", "", "CSV-bestanden (*.csv)"
        )
        if not pad:
            return

        try:
            with open(pad, "w", encoding="utf-8") as f:
                f.write("Map,Aantal foto's,Aantal video's\n")
                for i in range(self.ui_dialog.listFoundedItems.topLevelItemCount()):
                    item = self.ui_dialog.listFoundedItems.topLevelItem(i)
                    map_naam = item.text(0)
                    aantal_fotos = item.text(1)
                    aantal_videos = item.text(2)
                    regel = f'"{map_naam}",{aantal_fotos},{aantal_videos}\n'
                    f.write(regel)
            logging.info(f"CSV succesvol opgeslagen naar: {pad}")
            QtWidgets.QMessageBox.information(self, "Export", "Export voltooid.")
        except Exception as e:
            logging.error(f"Fout bij export: {e}")
            QtWidgets.QMessageBox.critical(self, "Fout", f"Export mislukt:\n{e}")

    def add_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Selecteer een map")
        if folder and folder not in self.folder_paths:
            self.folder_paths.append(folder)
            self.ui.listFolders.addItem(folder)
            logging.info(f"Map toegevoegd: {folder}")
        elif folder:
            logging.info(f"Map al aanwezig: {folder}")
        else:
            logging.info("Geen map geselecteerd.")

    def remove_selected_folder(self):
        selected_items = self.ui.listFolders.selectedItems()
        for item in selected_items:
            row = self.ui.listFolders.row(item)
            self.folder_paths.remove(item.text())
            self.ui.listFolders.takeItem(row)
            logging.info(f"Map verwijderd: {item.text()}")

    def scan_folders_for_media(self):
        self.media_items.clear()
        selected_type = self.ui.comboSelectType.currentText()
        logging.info(f"Filtertype geselecteerd: {selected_type}")
        for folder in self.folder_paths:
            if not os.path.isdir(folder):
                logging.warning(f"Geen geldige map: {folder}")
                self.ui.lblStatus.setText(f"Map niet leesbaar: {folder}")
                continue
            for entry in os.listdir(folder):
                full_path = os.path.join(folder, entry)
                if not os.path.isfile(full_path):
                    continue
                ext = os.path.splitext(entry)[1].lower()
                if selected_type == "Foto's" and ext in self.supported_photo_exts:
                    self.media_items.append(full_path)
                elif selected_type == "Films" and ext in self.supported_video_exts:
                    self.media_items.append(full_path)
                elif selected_type == "Beide" and (
                    ext in self.supported_photo_exts or ext in self.supported_video_exts
                ):
                    self.media_items.append(full_path)
        logging.info(f"Totaal gevonden bestanden: {len(self.media_items)}")
        for path in self.media_items:
            logging.info(f" → {path}")

    def play_previous_media(self):
        if not self.media_items:
            return
        self.current_index = (self.current_index - 1) % len(self.media_items)
        self.play_media(self.current_index)

    def start_slideshow(self):
        self.scan_folders_for_media()
        if not self.media_items:
            logging.warning("Geen media om af te spelen.")
            self.ui.lblStatus.setText("Geen media gevonden.")
            return
        self.is_playing = True
        self.is_paused = False
        self.play_media(self.current_index)

    def pause_slideshow(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.player.pause()
            self.timer.stop()
            logging.info("Afspeellijst gepauzeerd.")
            self.ui.lblStatus.setText("Gepauzeerd.")
        else:
            if self.player.mediaStatus() == QMediaPlayer.MediaStatus.PausedMedia:
                self.player.play()
            else:
                self.timer.start(self.ui.spinPhotoDelay.value() * 1000)
            logging.info("Afspeellijst hervat.")
            self.ui.lblStatus.setText("Hervat.")

    def stop_slideshow(self):
        self.is_playing = False
        self.is_paused = False
        self.player.stop()
        self.timer.stop()
        self.image_label.hide()
        self.video_widget.hide()
        logging.info("Afspeellijst gestopt.")
        self.ui.lblStatus.setText("Gestopt.")

    def handle_media_status(self, status):
        if (
            status == QMediaPlayer.MediaStatus.EndOfMedia
            and self.is_playing
            and not self.is_paused
        ):
            self.play_next_media()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            logging.error("Mediabestand is ongeldig of kan niet worden afgespeeld.")
            self.ui.lblStatus.setText("Fout: mediabestand ongeldig")


def main():
    logging.info("Script FotoBeheerApp is gestart.")
    app = QtWidgets.QApplication([])
    main_window = FotoBeheerApp()
    main_window.setWindowState(
        QtWidgets.QMainWindow().windowState()
        | QtWidgets.QMainWindow().windowState().WindowMaximized
    )
    main_window.show()
    app.exec()


if __name__ == "__main__":
    main()
