# [SECTION: IMPORTS]
import os
import logging
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from gui.MainWindow import Ui_MainWindow
from gui.MediaOrganizerGui import Ui_MediaOrganizerGui
from core import media_utils
from core.media_player import MediaPlayer
from core.db_interface import DbService
from core.media_scanner import scan_folder_into_db

# [END: SECTION: IMPORTS]
logger = logging.getLogger(__name__)


# [CLASS: MediaAppController]
# [SECTION: CLASS: MediaAppController]
class MediaAppController:
# [FUNC: __init__]
    def __init__(self, db_service: "DbService | None" = None):
        logger.info("MediaAppController gestart")

        # DB-service (kan None zijn bij oudere aanroep)
        self.db = db_service

        # Start Qt-applicatie
        self.app = QtWidgets.QApplication([])

        self.main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        self.dialog = QtWidgets.QDialog()
        self.ui_dialog = Ui_MediaOrganizerGui()
        self.ui_dialog.setupUi(self.dialog)

        def _debug_list_buttons(ui_parent):
            try:
                for w in ui_parent.findChildren(QtWidgets.QAbstractButton):
                    logger.info("UI button: %s (%s)", w.objectName(), type(w).__name__)
            except Exception:
                pass

        _debug_list_buttons(self.ui_dialog)

        # Kolomnamen instellen voor boomstructuren
        self.ui_dialog.listFoundedItems.setHeaderLabels(
            ["📁 Map", "📸 Foto's", "🎬 Video's"]
        )
        self.ui_dialog.treeVirtueleFotos.setHeaderLabels(
            ["📅 Datum", "🖼️ Bestandsnaam", "📁 Map", "👤 Gezicht?", "📌 Tags?"]
        )

        # State
        self.folder_paths: list[str] = []
        self.last_found_files: list[str] = []
        self.search_thread = None  # wordt dynamisch gezet

        self.supported_photo_exts = tuple(media_utils.image_extensions)
        self.supported_video_exts = tuple(media_utils.video_extensions)

        # Multimedia
        self.player = QMediaPlayer(self.main_window)
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self.handle_media_status)

        self.video_widget = QVideoWidget(self.ui.mediaFrame)
        self.player.setVideoOutput(self.video_widget)

        self.image_label = QtWidgets.QLabel(self.ui.mediaFrame)
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Layout i.p.v. setGeometry voor automatische resize
        _frame_layout = QtWidgets.QVBoxLayout(self.ui.mediaFrame)
        _frame_layout.setContentsMargins(0, 0, 0, 0)
        _frame_layout.setSpacing(0)
        _frame_layout.addWidget(self.video_widget)
        _frame_layout.addWidget(self.image_label)

        # Start onzichtbaar
        self.video_widget.setVisible(False)
        self.image_label.setVisible(False)

        self.media_player = MediaPlayer(
            media_label=self.image_label,
            video_widget=self.video_widget,
            player=self.player,
        )

        # Hoofdvenster-knoppen
        self.ui.btnStart.clicked.connect(self._on_start_clicked)
        self.ui.btnPause.clicked.connect(self._on_pause_clicked)
        self.ui.btnStop.clicked.connect(self._on_stop_clicked)
        self.ui.btnNext.clicked.connect(self._on_next_clicked)
        self.ui.btnPrevious.clicked.connect(self.play_previous_media)
        self.ui.btnAddFolder.clicked.connect(self.add_folder)
        self.ui.btnRemoveFolder.clicked.connect(self.remove_selected_folder)

        # Koppeling instellingen → player
        self.ui.chkLoop.toggled.connect(self._on_loop_toggled)
        self.ui.spinPhotoDelay.valueChanged.connect(self._on_delay_changed)
        self.ui.comboSelectType.currentIndexChanged.connect(
            self._on_play_filter_changed
        )

        # Startdialoog-knoppen (tolerant op verschillende UI-namen)
        def _connect_btn(names: list[str], slot) -> None:
            for n in names:
                btn = getattr(self.ui_dialog, n, None)
                if btn is not None:
                    try:
                        btn.clicked.connect(slot)
                        logger.debug("UI: %s → gekoppeld", n)
                        return
                    except Exception:
                        pass
            logger.warning("UI: geen knop gevonden voor %s", names)

        _connect_btn(
            [
                "btnStartMainwindow",
                "btnStartMainWindow",
                "btnStartHoofdvenster",
                "btnStart",
            ],
            self.verwerk_selectie_en_start_mainwindow,
        )
        _connect_btn(
            [
                "btnBladerenLocation",
                "btnBrowseLocation",
                "btnBladerenLocatie",
                "btnSelectFolder",
            ],
            self.blader_naar_locatie,
        )
        _connect_btn(
            ["btnSearchSelectedLocation", "btnZoekGeselecteerdeMap", "btnSearch"],
            self.start_search_from_location,
        )

        # Stopknop (optioneel aanwezig)
        for n in ["btnStopSearch", "btnStopZoeken"]:
            try:
                btn = getattr(self.ui_dialog, n)
                btn.clicked.connect(self.stop_search)
                logger.debug("UI: %s → gekoppeld", n)
                break
            except Exception:
                pass

        _connect_btn(
            ["btnExportList", "btnExporteren", "btnExportCsv"],
            self.exporteer_gevonden_mappen_naar_csv,
        )

        # Ververs-lijst (zonder nieuwe scan)
        _connect_btn(["btnVerversLijst", "btnRefresh"], self._refresh_from_buffer)

        # Detecteer reeksen
        _connect_btn(
            ["btnDetecteerReeksen", "btnDetectSequences"], self._on_detect_sequences
        )

        # Interactieve selectie & file ops
        _connect_btn(
            ["btnStartInteractieveSelectie", "btnInteractiveSelect"],
            self._enable_multi_select,
        )
        _connect_btn(
            ["btnVerplaatsFotos", "btnMoveFiles"], self._on_move_selected_files
        )
        _connect_btn(
            ["btnVerwijderFotos", "btnDeleteFiles"], self._on_delete_selected_files
        )

        try:
            from PyQt6.QtCore import QSettings

            sett = QSettings("Vioprint", "MediaOrganizer")
            # Herstel eenvoudige prefs uit QSettings
            loc = sett.value("last_location", "", type=str)
            delay = sett.value("delay_s", None)
            loopv = sett.value("loop", None)

            # Mirror vanuit DB (heeft voorrang als beschikbaar)
            if self.db:
                db_loc = self.db.get_preference("last_location", None)
                db_delay = self.db.get_preference("delay_s", None)
                db_loop = self.db.get_preference("loop", None)

                if db_loc:
                    loc = db_loc
                if db_delay is not None:
                    delay = db_delay
                if db_loop is not None:
                    loopv = db_loop

            # Zet waarden in UI
            if loc:
                try:
                    self.ui_dialog.lineLocation.setText(str(loc))
                except Exception:
                    pass
            if delay is not None:
                try:
                    self.ui.spinPhotoDelay.setValue(int(delay))
                except Exception:
                    pass
            if loopv is not None:
                self.ui.chkLoop.setChecked(str(loopv).lower() in ("1", "true", "yes"))
        except Exception:
            pass
        # [END: QSETTINGS LOAD + DB PREFS]

        # Signalen om direct te bewaren (mirror naar QSettings + DB)
        def _save_prefs():
            try:
                from PyQt6.QtCore import QSettings

                s = QSettings("Vioprint", "MediaOrganizer")
                loc_val = getattr(self.ui_dialog, "lineLocation").text()
                delay_val = self.ui.spinPhotoDelay.value()
                loop_val = self.ui.chkLoop.isChecked()

                s.setValue("last_location", loc_val)
                s.setValue("delay_s", delay_val)
                s.setValue("loop", loop_val)

                if self.db:
                    # DB krijgt stringwaarden, consistent met DbService
                    self.db.set_preference("last_location", str(loc_val))
                    self.db.set_preference("delay_s", str(delay_val))
                    self.db.set_preference("loop", "1" if loop_val else "0")
            except Exception:
                pass

        try:
            self.ui_dialog.lineLocation.textChanged.connect(lambda *_: _save_prefs())
            self.ui.spinPhotoDelay.valueChanged.connect(lambda *_: _save_prefs())
            self.ui.chkLoop.toggled.connect(lambda *_: _save_prefs())
        except Exception:
            pass

        logger.info("MediaAppController: UI en componenten geïnitialiseerd.")

# [END: FUNC: __init__]

# [FUNC: start]
    def start(self):
        logger.info("Toont startdialoog (MediaOrganizerGui)")
        self.dialog.show()
        self.app.exec()

# [END: FUNC: start]

# [FUNC: _on_start_clicked]
    def _on_start_clicked(self):
        logger.info("Klik: Start (slideshow)")

        # 1) Verzamel aangevinkte mappen uit de scan-lijst (indien aanwezig)
        checked_folders: list[str] = []
        try:
            for i in range(self.ui_dialog.listFoundedItems.topLevelItemCount()):
                it = self.ui_dialog.listFoundedItems.topLevelItem(i)
                if it.checkState(0) == QtCore.Qt.CheckState.Checked:
                    checked_folders.append(it.text(0))
        except Exception:
            pass  # lijst kan leeg zijn

        # 2) Kies bron: aangevinkte mappen > eerder gekozen folder_paths
        source_folders = checked_folders or self.folder_paths

        # 3) Bepaal huidig afspeelfilter uit de combobox van het hoofdvenster
        type_filter = self._current_play_filter()

        # 4) Bouw de afspeellijst (eerst DB, dan fallback naar filesystem)
        media_list: list[str] = []
        mtype = (
            "image"
            if type_filter == "images"
            else "video" if type_filter == "videos" else None
        )

        if self.db and source_folders:
            try:
                from itertools import chain

                results_all = []
                for base in source_folders:
                    if not base:
                        continue
                    # Zoek in DB op mtype en pad-fragment; filter hidden=0
                    res = self.db.search_media(
                        mtype=mtype,
                        hidden=False,
                        text=base,  # path-fragment filter
                        limit=100000,
                        offset=0,
                    )
                    # Exclude missing
                    res = [r for r in res if not r.get("missing")]
                    results_all.append(res)
                for r in chain.from_iterable(results_all):
                    p = str(r.get("path") or "")
                    if p and media_utils.is_media_file(p, type_filter):
                        media_list.append(p)
                logger.info("Afspeellijst via DB opgebouwd: %d items", len(media_list))
            except Exception:
                logger.exception(
                    "Fout tijdens DB-zoek voor afspeellijst; val terug op filesystem"
                )
                media_list = []

        if not media_list:
            # Fallback: filesystem walk
            for base in source_folders:
                if not base or not os.path.exists(base):
                    continue
                try:
                    for root, _, files in os.walk(base):
                        for name in files:
                            p = os.path.join(root, name)
                            if media_utils.is_media_file(p, type_filter):
                                media_list.append(p)
                except Exception:
                    continue  # ga door bij toegangsproblemen

        # 5) Controle: is er iets om af te spelen?
        if not media_list:
            QtWidgets.QMessageBox.information(
                self.main_window,
                "Geen media",
                "Geen geschikte media gevonden om af te spelen.",
            )
            logger.info(
                "Start geannuleerd: lege afspeellijst (folders=%d, filter=%s)",
                len(source_folders),
                type_filter,
            )
            return

        # 6) Zet lijst in de player en start
        self.media_player.media_list = media_list
        self.media_player.current_index = -1  # laat player bij next starten
        logger.info(
            "Afspeellijst opgebouwd: %d items (%s)", len(media_list), type_filter
        )

        self.media_player.start_slideshow()
        self._set_status("Afspelen gestart")

# [END: FUNC: _on_start_clicked]

# [FUNC: _on_pause_clicked]
    def _on_pause_clicked(self):
        logger.info("Klik: Pauze")
        self.media_player.pause_slideshow()
        self._set_status("Gepauzeerd")

# [END: FUNC: _on_pause_clicked]

# [FUNC: _on_stop_clicked]
    def _on_stop_clicked(self):
        logger.info("Klik: Stop")
        self.media_player.stop_slideshow()
        self._set_status("Gestopt")

# [END: FUNC: _on_stop_clicked]

# [FUNC: _on_next_clicked]
    def _on_next_clicked(self):
        logger.info("Klik: Volgende")
        self.media_player.play_next_media()
        self._set_status("Volgende")

# [END: FUNC: _on_next_clicked]

# [FUNC: play_previous_media]
    def play_previous_media(self):
        logger.info("play_previous_media")
        lst = getattr(self.media_player, "media_list", [])
        if not lst:
            logger.info("Geen media om terug te gaan.")
            return
        self.media_player.current_index = (self.media_player.current_index - 1) % len(
            lst
        )
        pad = lst[self.media_player.current_index]
        self.media_player.play_media(pad)
        self._set_status("Vorige")

# [END: FUNC: play_previous_media]

# [FUNC: handle_media_status]
    def handle_media_status(self, status):
        # Eenvoudige statusweergave (optioneel: map enum naar tekst)
        self._set_status(f"Media status: {int(status)}")

# [END: FUNC: handle_media_status]

# [FUNC: _on_loop_toggled]
    def _on_loop_toggled(self, checked: bool):
        logger.info("Loop toggled → %s", checked)
        try:
            self.media_player.set_loop(bool(checked))
        except Exception:
            logger.exception("set_loop() gaf een fout")

# [END: FUNC: _on_loop_toggled]

# [FUNC: _on_delay_changed]
    def _on_delay_changed(self, seconds: int):
        ms = int(seconds) * 1000
        logger.info("Delay veranderd → %d s (%d ms)", seconds, ms)
        try:
            self.media_player.set_delay(ms)
        except Exception:
            logger.exception("set_delay() gaf een fout")

# [END: FUNC: _on_delay_changed]

# [FUNC: _on_play_filter_changed]
    def _on_play_filter_changed(self):
        text = (self.ui.comboSelectType.currentText() or "").strip().lower()
        logger.debug("Afspeelfilter gewijzigd: %s", text)
        # Bronmappen: aangevinkte mappen > folder_paths
        checked_folders: list[str] = []
        try:
            for i in range(self.ui_dialog.listFoundedItems.topLevelItemCount()):
                it = self.ui_dialog.listFoundedItems.topLevelItem(i)
                if it.checkState(0) == QtCore.Qt.CheckState.Checked:
                    checked_folders.append(it.text(0))
        except Exception:
            pass
        source_folders = checked_folders or self.folder_paths
        if not source_folders:
            return

        type_filter = self._current_play_filter()
        media_list: list[str] = []
        mtype = (
            "image"
            if type_filter == "images"
            else "video" if type_filter == "videos" else None
        )

        if self.db and source_folders:
            try:
                from itertools import chain

                results_all = []
                for base in source_folders:
                    if not base:
                        continue
                    res = self.db.search_media(
                        mtype=mtype,
                        hidden=False,
                        text=base,
                        limit=100000,
                        offset=0,
                    )
                    res = [r for r in res if not r.get("missing")]
                    results_all.append(res)
                for r in chain.from_iterable(results_all):
                    p = str(r.get("path") or "")
                    if p and media_utils.is_media_file(p, type_filter):
                        media_list.append(p)
                logger.info(
                    "Afspeellijst via DB vernieuwd (filter=%s): %d items",
                    type_filter,
                    len(media_list),
                )
            except Exception:
                logger.exception("Fout tijdens DB-zoek; val terug op filesystem")
                media_list = []

        if not media_list:
            for base in source_folders:
                if not base or not os.path.exists(base):
                    continue
                try:
                    for root, _, files in os.walk(base):
                        for name in files:
                            p = os.path.join(root, name)
                            if media_utils.is_media_file(p, type_filter):
                                media_list.append(p)
                except Exception:
                    continue

        self.media_player.media_list = media_list
        self.media_player.current_index = -1
        logger.info(
            "Afspeellijst vernieuwd (filter=%s): %d items", type_filter, len(media_list)
        )

# [END: FUNC: _on_play_filter_changed]

# [FUNC: _enable_multi_select]
    def _enable_multi_select(self):
        try:
            self.ui_dialog.treeVirtueleFotos.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
            )
            self._set_status("Selectiemodus actief (Ctrl/Shift selecties)")
        except Exception:
            pass

# [END: FUNC: _enable_multi_select]

# [FUNC: _selected_file_paths_from_tree]
    def _selected_file_paths_from_tree(self) -> list[str]:
        res: list[str] = []
        try:
            for it in self.ui_dialog.treeVirtueleFotos.selectedItems():
                # Verwacht kolommen: [datum, naam, folder, ...]
                name = it.text(1)
                folder = it.text(2)
                if folder and name:
                    res.append(os.path.join(folder, name))
        except Exception:
            pass
        return res

# [END: FUNC: _selected_file_paths_from_tree]

# [FUNC: _on_move_selected_files]
    def _on_move_selected_files(self):
        paths = self._selected_file_paths_from_tree()
        if not paths:
            QtWidgets.QMessageBox.information(
                self.dialog, "Geen selectie", "Selecteer eerst één of meer bestanden."
            )
            return
        dest = QtWidgets.QFileDialog.getExistingDirectory(self.dialog, "Kies doelmap")
        if not dest:
            return
        from core import export_tools

        ok, errors = export_tools.move_files(paths, dest)
        msg = f"Verplaatst: {ok}/{len(paths)}"
        if errors:
            msg += f"\nFouten: {len(errors)}"
        QtWidgets.QMessageBox.information(self.dialog, "Verplaatsen", msg)
        # UI bijwerken: verwijder verplaatste items uit tree + buffer
        if ok:
            self._remove_paths_from_tree(paths)
            self.last_found_files = [p for p in self.last_found_files if p not in paths]
            self._refresh_from_buffer()

# [END: FUNC: _on_move_selected_files]

# [FUNC: _on_delete_selected_files]
    def _on_delete_selected_files(self):
        paths = self._selected_file_paths_from_tree()
        if not paths:
            QtWidgets.QMessageBox.information(
                self.dialog, "Geen selectie", "Selecteer eerst één of meer bestanden."
            )
            return
        if (
            QtWidgets.QMessageBox.question(
                self.dialog, "Bevestigen", f"{len(paths)} item(s) verwijderen?"
            )
            != QtWidgets.QMessageBox.StandardButton.Yes
        ):
            return
        from core import export_tools

        ok, errors = export_tools.trash_or_delete(paths)
        msg = f"Verwijderd: {ok}/{len(paths)}"
        if errors:
            msg += f"\nFouten: {len(errors)}"
        QtWidgets.QMessageBox.information(self.dialog, "Verwijderen", msg)
        if ok:
            self._remove_paths_from_tree(paths)
            self.last_found_files = [p for p in self.last_found_files if p not in paths]
            self._refresh_from_buffer()

# [END: FUNC: _on_delete_selected_files]

# [FUNC: _remove_paths_from_tree]
    def _remove_paths_from_tree(self, paths: list[str]):
        pathset = set(paths)
        root = self.ui_dialog.treeVirtueleFotos
        to_delete = []
        # top-level nodes en children (ivm reeksen)
        for i in range(root.topLevelItemCount()):
            top = root.topLevelItem(i)
            if top.childCount() == 0:
                # gewone items op top-level
                name = top.text(1)
                folder = top.text(2)
                full = os.path.join(folder, name) if folder and name else ""
                if full in pathset:
                    to_delete.append((None, i))
            else:
                # children doorlopen
                for j in range(top.childCount() - 1, -1, -1):
                    ch = top.child(j)
                    name = ch.text(1)
                    folder = ch.text(2)
                    full = os.path.join(folder, name) if folder and name else ""
                    if full in pathset:
                        top.removeChild(ch)
                # als reeks leeg raakt, verwijder parent
                if top.childCount() == 0:
                    to_delete.append((None, i))
        # Verwijder gemarkeerde top-level items (achteraf om index te behouden)
        for parent, idx in sorted(to_delete, key=lambda x: x[1], reverse=True):
            root.takeTopLevelItem(idx)

# [END: FUNC: _remove_paths_from_tree]

# [FUNC: verwerk_selectie_en_start_mainwindow]
    def verwerk_selectie_en_start_mainwindow(self):
        logger.info("verwerk_selectie_en_start_mainwindow")

        if not self.folder_paths:
            QtWidgets.QMessageBox.warning(
                self.dialog, "Geen mappen", "Selecteer minstens één map."
            )
            return

        self.dialog.close()
        self.main_window.show()
        self._set_status("Hoofdvenster gestart")

# [END: FUNC: verwerk_selectie_en_start_mainwindow]

# [FUNC: blader_naar_locatie]
    def blader_naar_locatie(self):
        logger.info("blader_naar_locatie")

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.dialog, "Selecteer map om te doorzoeken"
        )
        if folder:
            # Let op: naam van het veld in deze UI is 'lineLocation'
            self.ui_dialog.lineLocation.setText(folder)
            logger.info("Zoeklocatie ingesteld op: %s", folder)

# [END: FUNC: blader_naar_locatie]

# [FUNC: start_search_from_location]
    def start_search_from_location(self):
        logger.info("start_search_from_location")

        # Eerdere thread veilig stoppen
        st = getattr(self, "search_thread", None)
        if st:
            try:
                if hasattr(st, "stop"):
                    st.stop()
                else:
                    st.requestInterruption()
                    st.wait(1500)
            except Exception:
                logger.exception("Fout bij stoppen vorige zoekthread")

        location = self.ui_dialog.lineLocation.text().strip()
        if not (location and os.path.exists(location)):
            QtWidgets.QMessageBox.warning(
                self.dialog,
                "Ongeldige map",
                "Selecteer een geldige map om te doorzoeken.",
            )
            return

        type_filter = self._current_play_filter()

        # Datumfilter (optioneel aanwezig in UI)
        date_range = None
        try:
            if self.ui_dialog.checkFilterDatum.isChecked():
                s = self.ui_dialog.dateEditStartDatum.date()
                e = self.ui_dialog.dateEditEindDatum.date()
                date_range = (s, e)
        except Exception:
            date_range = None

        # Thread importeren (ondersteun beide importpaden)
        try:
            from threads.MediaSearchThread import MediaSearchThread
        except Exception:
            from MediaSearchThread import MediaSearchThread  # type: ignore

        # Thread aanmaken (ondersteun verschillende ctor-namen)
        try:
            self.search_thread = MediaSearchThread(
                start_path=location, type_filter=type_filter, date_range=date_range
            )
        except TypeError:
            try:
                self.search_thread = MediaSearchThread(
                    start_path=location, filter_type=type_filter, date_range=date_range
                )
            except TypeError:
                # laatste fallback zonder date_range
                self.search_thread = MediaSearchThread(
                    start_path=location, type_filter=type_filter
                )

        # Signalen verbinden (found/finished/error/progress)
        if hasattr(self.search_thread, "found"):
            self.search_thread.found.connect(self._on_found_items)
        if hasattr(self.search_thread, "finished"):
            self.search_thread.finished.connect(self._on_scan_finished)
        if hasattr(self.search_thread, "error"):
            self.search_thread.error.connect(self._on_scan_error)
        if hasattr(self.search_thread, "progress"):
            self.search_thread.progress.connect(self._on_scan_progress)

        # UI voorbereiden
        self._toggle_search_ui(True)
        self.ui_dialog.listFoundedItems.clear()
        self.ui_dialog.treeVirtueleFotos.clear()
        self.last_found_files.clear()
        self._set_status("Scannen…")
        logger.info("Zoekthread starten: %s (%s)", location, type_filter)
        self.search_thread.start()

# [END: FUNC: start_search_from_location]

# [FUNC: stop_search]
    def stop_search(self):
        st = getattr(self, "search_thread", None)
        if st:
            try:
                if hasattr(st, "stop"):
                    st.stop()
                else:
                    st.requestInterruption()
                    st.wait(2000)
                self._set_status("Zoekactie gestopt")
            except Exception:
                logger.exception("Fout bij stoppen van zoekthread")
        self._toggle_search_ui(False)

# [END: FUNC: stop_search]

# [FUNC: _on_detect_sequences]
    def _on_detect_sequences(self):
        """
        Groepeert self.last_found_files in reeksen en toont die als top-level nodes.
        """
        try:
            gap = int(self.ui_dialog.spinTijdsintervalReeks.value())
        except Exception:
            gap = 60

        seqs = media_utils.detect_sequences(self.last_found_files, gap)
        self.ui_dialog.treeVirtueleFotos.clear()

        for idx, group in enumerate(seqs, start=1):
            top = QtWidgets.QTreeWidgetItem([f"Reeks {idx}", "", "", "", ""])
            self.ui_dialog.treeVirtueleFotos.addTopLevelItem(top)
            for f in group:
                folder = os.path.dirname(f)
                name = os.path.basename(f)
                # optioneel: datum tonen
                dt = media_utils.get_exif_datetime(f) or None
                date_str = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
                child = QtWidgets.QTreeWidgetItem([date_str, name, folder, "", ""])
                top.addChild(child)

# [END: FUNC: _on_detect_sequences]

# [FUNC: _on_found_items]
    def _on_found_items(self, files: list):
        """Ontvangt batches met bestands-paden en vult de fotolijst."""
        if not files:
            return
        self.last_found_files.extend(files)

        for f in files:
            folder = os.path.dirname(f)
            name = os.path.basename(f)
            # Datum via helper (EXIF of fallback mtime)
            try:
                dt = media_utils.get_exif_datetime(f) or None
            except Exception:
                dt = None
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
            item = QtWidgets.QTreeWidgetItem([date_str, name, folder, "", ""])
            self.ui_dialog.treeVirtueleFotos.addTopLevelItem(item)

# [END: FUNC: _on_found_items]

# [FUNC: _on_scan_finished]
    def _on_scan_finished(self, total: int):
        logger.info("Scan klaar: %d items", total)
        # Mappenoverzicht opbouwen met tellingen
        counts: dict[str, tuple[int, int]] = {}  # map -> (photos, videos)
        for f in self.last_found_files:
            ext = os.path.splitext(f)[1].lower()
            folder = os.path.dirname(f)
            p, v = counts.get(folder, (0, 0))
            if ext in self.supported_photo_exts:
                p += 1
            elif ext in self.supported_video_exts:
                v += 1
            counts[folder] = (p, v)

        self.ui_dialog.listFoundedItems.clear()
        for folder, (p, v) in sorted(counts.items()):
            it = QtWidgets.QTreeWidgetItem([folder, str(p), str(v)])
            it.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            self.ui_dialog.listFoundedItems.addTopLevelItem(it)

        self._toggle_search_ui(False)
        self._set_status(f"Scan klaar: {total} items")

# [END: FUNC: _on_scan_finished]

# [FUNC: _on_scan_error]
    def _on_scan_error(self, message: str):
        logger.error("Scan fout: %s", message)
        QtWidgets.QMessageBox.critical(self.dialog, "Fout bij zoeken", message)
        self._toggle_search_ui(False)
        self._set_status("Fout bij zoeken")

# [END: FUNC: _on_scan_error]

# [FUNC: _on_scan_progress]
    def _on_scan_progress(self, current_path: str, count: int):
        # Live statusupdate tijdens scan
        self._set_status(f"Scannen… {count} items")

# [END: FUNC: _on_scan_progress]

# [FUNC: add_folder]
    def add_folder(self):
        logger.info("add_folder")
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.main_window, "Selecteer map"
        )
        if folder and folder not in self.folder_paths:
            self.folder_paths.append(folder)
            self.ui.listFolders.addItem(folder)
            logger.info("Map toegevoegd: %s", folder)
            # Registreer ook in DB (geen blocking scan hier)
            try:
                if self.db:
                    self.db.add_folder(folder)
            except Exception:
                logger.exception("Kon map niet registreren in DB")
        else:
            logger.info("Geen nieuwe map toegevoegd.")

# [END: FUNC: add_folder]

# [FUNC: remove_selected_folder]
    def remove_selected_folder(self):
        logger.info("remove_selected_folder")
        selected_items = self.ui.listFolders.selectedItems()
        for item in selected_items:
            folder = item.text()
            if folder in self.folder_paths:
                self.folder_paths.remove(folder)
            self.ui.listFolders.takeItem(self.ui.listFolders.row(item))
            logger.info("Map verwijderd: %s", folder)

# [END: FUNC: remove_selected_folder]

# [FUNC: exporteer_gevonden_mappen_naar_csv]
    def exporteer_gevonden_mappen_naar_csv(self):
        logger.info("exporteer_gevonden_mappen_naar_csv")

        # Neem mappen uit de huidige lijst; val terug op folder_paths
        rows = []
        for i in range(self.ui_dialog.listFoundedItems.topLevelItemCount()):
            it = self.ui_dialog.listFoundedItems.topLevelItem(i)
            rows.append((it.text(0), it.text(1), it.text(2)))
        if not rows and self.folder_paths:
            rows = [(p, "", "") for p in self.folder_paths]

        if not rows:
            QtWidgets.QMessageBox.information(
                self.dialog, "Geen data", "Geen mappen om te exporteren."
            )
            return

        bestand, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.dialog, "CSV opslaan", "", "CSV-bestanden (*.csv)"
        )
        if bestand:
            try:
                with open(bestand, "w", encoding="utf-8") as f:
                    f.write("Map;Fotos;Videos\n")
                    for folder, fotos, videos in rows:
                        f.write(f"{folder};{fotos};{videos}\n")
                logger.info("CSV opgeslagen: %s", bestand)
            except Exception:
                logger.exception("Fout bij opslaan van CSV:")

# [END: FUNC: exporteer_gevonden_mappen_naar_csv]

# [FUNC: _toggle_search_ui]
    def _toggle_search_ui(self, is_scanning: bool):
        """
        Zet de juiste knoppen aan/uit tijdens het scannen. Ondersteunt meerdere
        mogelijke namen zodat het bestand met verschillende UI-versies werkt.
        """
        for name in ("btnSearchSelectedLocation", "btnSearchAll"):
            try:
                getattr(self.ui_dialog, name).setEnabled(not is_scanning)
            except Exception:
                pass
        for name in ("btnStopSearch",):
            try:
                getattr(self.ui_dialog, name).setEnabled(is_scanning)
            except Exception:
                pass

# [END: FUNC: _toggle_search_ui]

# [FUNC: _refresh_from_buffer]
    def _refresh_from_buffer(self):
        """
        Herbouwt listFoundedItems vanuit self.last_found_files, met foto/video-tellingen.
        """
        counts: dict[str, tuple[int, int]] = {}
        for f in self.last_found_files:
            ext = os.path.splitext(f)[1].lower()
            folder = os.path.dirname(f)
            p, v = counts.get(folder, (0, 0))
            if ext in self.supported_photo_exts:
                p += 1
            elif ext in self.supported_video_exts:
                v += 1
            counts[folder] = (p, v)

        self.ui_dialog.listFoundedItems.clear()
        for folder, (p, v) in sorted(counts.items()):
            it = QtWidgets.QTreeWidgetItem([folder, str(p), str(v)])
            it.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            self.ui_dialog.listFoundedItems.addTopLevelItem(it)

# [END: FUNC: _refresh_from_buffer]

# [FUNC: _current_play_filter]
    def _current_play_filter(self) -> str:
        """
        Leest de huidige filter uit de combobox van het hoofdvenster:
        'Foto's' → images, 'Films' → videos, 'Beide' → all.
        """
        t = (self.ui.comboSelectType.currentText() or "").strip().lower()
        if "foto" in t:
            return "images"
        if "film" in t or "video" in t:
            return "videos"
        return "all"

# [END: FUNC: _current_play_filter]

# [FUNC: _set_status]
    def _set_status(self, text: str):
        try:
            self.ui.lblStatus.setText(f"Status: {text}")
        except Exception:
            pass
        logger.debug("STATUS → %s", text)

# [END: FUNC: _set_status]
# [END: SECTION: CLASS: MediaAppController]


# [END: CLASS: MediaAppController]
