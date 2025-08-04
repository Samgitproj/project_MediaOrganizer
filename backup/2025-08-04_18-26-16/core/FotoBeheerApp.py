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
from core.MediaSearchThread import MediaSearchThread
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

        self.search_thread = None

        self.dialog = QtWidgets.QDialog()
        self.ui_dialog = Ui_Dialog()
        self.ui_dialog.setupUi(self.dialog)

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
        self.ui.btnPrevious.clicked.connect(self.play_previous_media)

        self.ui_dialog.listFoundedItems.itemExpanded.connect(self.item_expanded)
        self.ui_dialog.btnBladerenLocation.clicked.connect(self.blader_naar_locatie)
        self.ui_dialog.btnSearchAll.clicked.connect(self.start_search_all)
        self.ui_dialog.btnSearchSelectedLocation.clicked.connect(
            self.start_search_from_location
        )
        self.ui_dialog.btnStartMainwindow.clicked.connect(self.toon_mainwindow)

        logging.info("FotoBeheerApp UI is geïnitialiseerd.")

    def toon_mainwindow(self):
        self.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.image_label.setGeometry(self.ui.mediaFrame.rect())
        self.video_widget.setGeometry(self.ui.mediaFrame.rect())

        # Als er al een afbeelding getoond wordt, herschalen we opnieuw
        if not self.image_label.pixmap().isNull():
            available_size = self.ui.mediaFrame.size()
            scaled = self.image_label.pixmap().scaled(
                available_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)

    def start_search_all(self):
        filter_gui = self.ui_dialog.comboSelectTypeMain.currentText()
        filtertype = self.vertaal_filter(filter_gui)
        self.start_zoekthread("C:\\", filtertype)

    def blader_naar_locatie(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.dialog, "Selecteer map"
        )
        if folder:
            self.ui_dialog.lineScriptLocationMedia.setText(folder)
            logging.info(f"Gekozen map: {folder}")

    def start_search_from_location(self):
        folder = self.ui_dialog.lineScriptLocationMedia.text().strip()
        if not folder:
            QtWidgets.QMessageBox.warning(
                self.dialog, "Geen map", "Selecteer eerst een map via de bladerknop."
            )
            logging.warning("Geen map opgegeven voor zoekactie.")
            return

        self.ui_dialog.listFoundedItems.clear()

        foto_count = 0
        video_count = 0
        for bestand in os.listdir(folder):
            full_path = os.path.join(folder, bestand)
            if not os.path.isfile(full_path):
                continue
            ext = os.path.splitext(bestand)[1].lower()
            if ext in self.supported_photo_exts:
                foto_count += 1
            elif ext in self.supported_video_exts:
                video_count += 1

        root_item = QtWidgets.QTreeWidgetItem()
        root_item.setText(0, folder)
        root_item.setText(1, str(foto_count))
        root_item.setText(2, str(video_count))

        # Voeg dummy toe om ⯈ zichtbaar te maken
        if any(os.path.isdir(os.path.join(folder, x)) for x in os.listdir(folder)):
            dummy = QtWidgets.QTreeWidgetItem()
            root_item.addChild(dummy)

        self.ui_dialog.listFoundedItems.addTopLevelItem(root_item)

    def vertaal_filter(self, keuze: str) -> str:
        if keuze == "Foto's":
            return "images"
        elif keuze == "Films":
            return "videos"
        else:
            return "all"

    def start_zoekthread(self, pad, filtertype):
        self.ui_dialog.listFoundedItems.clear()
        self.ui_dialog.listFoundedItemsNok.clear()
        self.ui_dialog.btnSearchAll.setEnabled(False)
        self.ui_dialog.btnSearchSelectedLocation.setEnabled(False)
        self.toon_statusdialoog("Bezig met zoeken...")

        # Stop oude thread als die nog draait
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait()

        # Start nieuwe zoekthread
        self.search_thread = MediaSearchThread(pad, filtertype)
        self.search_thread.searchCompleted.connect(self.verwerk_resultaten)
        self.search_thread.start()
        logging.info(f"Zoekthread gestart op pad: {pad}, filtertype: {filtertype}")

    def toon_statusdialoog(self, tekst="Bezig met zoeken..."):
        self.status_dialoog = QtWidgets.QDialog(self.dialog)
        self.status_dialoog.setWindowTitle("Status")
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(tekst)
        layout.addWidget(label)
        self.status_dialoog.setLayout(layout)
        self.status_dialoog.setModal(True)
        self.status_dialoog.setFixedSize(200, 80)
        self.status_dialoog.show()

    def sluit_statusdialoog(self):
        if hasattr(self, "status_dialoog"):
            self.status_dialoog.close()

    def laad_subfolders(self, ouder_item: QtWidgets.QTreeWidgetItem, pad: str):
        try:
            for naam in os.listdir(pad):
                volledige_map = os.path.join(pad, naam)
                if not os.path.isdir(volledige_map):
                    continue

                foto_count = 0
                video_count = 0
                for bestand in os.listdir(volledige_map):
                    full_path = os.path.join(volledige_map, bestand)
                    if not os.path.isfile(full_path):
                        continue
                    ext = os.path.splitext(bestand)[1].lower()
                    if ext in self.supported_photo_exts:
                        foto_count += 1
                    elif ext in self.supported_video_exts:
                        video_count += 1

                nieuw_item = QtWidgets.QTreeWidgetItem()
                nieuw_item.setText(0, volledige_map)
                nieuw_item.setText(1, str(foto_count))
                nieuw_item.setText(2, str(video_count))

                # Voeg dummy toe zodat ⯈ zichtbaar is
                if any(
                    os.path.isdir(os.path.join(volledige_map, x))
                    for x in os.listdir(volledige_map)
                ):
                    dummy = QtWidgets.QTreeWidgetItem()
                    nieuw_item.addChild(dummy)

                ouder_item.addChild(nieuw_item)
        except Exception as e:
            logging.warning(f"Fout bij laden subfolders van {pad}: {e}")

    def item_expanded(self, item: QtWidgets.QTreeWidgetItem):
        # Voorkom dat we subfolders telkens opnieuw laden
        if item.childCount() == 1 and item.child(0).text(0) == "":
            item.takeChildren()  # verwijder dummy
            pad = item.text(0)
            self.laad_subfolders(item, pad)

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

    def play_media(self, index: int):
        if not (0 <= index < len(self.media_items)):
            logging.warning("Index buiten bereik.")
            return

        self.current_index = index
        path = self.media_items[index]
        if not os.path.exists(path):
            logging.warning(f"Bestand niet gevonden: {path}")
            self.ui.lblStatus.setText(f"Bestand niet gevonden: {path}")
            return

        ext = os.path.splitext(path)[1].lower()
        self.image_label.hide()
        self.video_widget.hide()
        self.player.stop()
        self.timer.stop()

        # ⬇️ Dynamisch formaat instellen
        self.image_label.setGeometry(self.ui.mediaFrame.rect())
        self.video_widget.setGeometry(self.ui.mediaFrame.rect())

        if ext in self.supported_photo_exts:
            available_size = self.ui.mediaFrame.size()
            pixmap = QPixmap(path)
            scaled = pixmap.scaled(
                available_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.image_label.setVisible(True)
            logging.info(f"Foto getoond: {path}")
            self.ui.lblStatus.setText(f"Foto: {os.path.basename(path)}")
            if self.is_playing and not self.is_paused:
                self.timer.start(self.ui.spinPhotoDelay.value() * 1000)

        elif ext in self.supported_video_exts:
            self.video_widget.setVisible(True)
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()
            logging.info(f"Video afgespeeld: {path}")
            self.ui.lblStatus.setText(f"Video: {os.path.basename(path)}")

    def play_next_media(self):
        if not self.media_items:
            return
        if self.ui.chkLoop.isChecked():
            self.play_media(self.current_index)
        else:
            self.current_index = (self.current_index + 1) % len(self.media_items)
            self.play_media(self.current_index)

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
