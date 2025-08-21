
# [SECTION: IMPORTS]
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from PyQt6 import QtCore

# [END: SECTION: IMPORTS]
# Veronderstelde helpers (bestaan al in project)
# media_utils moet minimaal is_media_file(path: Path, type_filter: str) bevatten.
# optioneel: in_date_range(path: Path, start, end) voor EXIF/mtime-filter.
try:
    from core import media_utils  # type: ignore
except Exception:  # fallback pad
    import media_utils  # type: ignore


logger = logging.getLogger(__name__)


# [CLASS: MediaSearchThread]
# [SECTION: CLASS: MediaSearchThread]
class MediaSearchThread(QtCore.QThread):
    """
    Asynchrone scan van een startpad met filters.
    - type_filter: "images" | "videos" | "all"
    - date_range: (start_qdate, end_qdate) of None
    Signalen:
      - found(list_of_paths: list[str])
      - finished(total_count: int)
      - error(message: str)
      - progress(current_path: str, count: int)
    """

    found = QtCore.pyqtSignal(list)
    finished = QtCore.pyqtSignal(int)
    error = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(str, int)

    BATCH_SIZE = 50

# [FUNC: __init__]
    def __init__(
        self,
        start_path: str | Path,
        type_filter: str = "all",
        date_range: Optional[Tuple[object, object]] = None,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._root = Path(start_path).expanduser().resolve()
        self._type_filter = (type_filter or "all").lower()
        self._date_range = date_range
        self._count = 0
        logger.debug(
            "MediaSearchThread init: root=%s, type_filter=%s, date_range=%s",
            self._root,
            self._type_filter,
            self._date_range,
        )

# [END: FUNC: __init__]
# [FUNC: run]
    def run(self) -> None:
        try:
            if not self._root.exists():
                msg = f"Startpad bestaat niet: {self._root}"
                logger.error(msg)
                self.error.emit(msg)
                return

            self.progress.emit(str(self._root), 0)
            batch: List[str] = []
            for p in self._iter_media_paths(self._root):
                if self.isInterruptionRequested():
                    logger.info("Scan onderbroken door gebruiker.")
                    break

                if self._date_range and not self._match_date(p):
                    continue

                batch.append(str(p))
                self._count += 1

                if self._count % self.BATCH_SIZE == 0:
                    self.found.emit(batch)
                    self.progress.emit(str(p), self._count)
                    batch = []

            if batch:
                self.found.emit(batch)

            self.finished.emit(self._count)
            logger.info("Scan klaar: %s items gevonden.", self._count)

        except Exception as e:
            logger.exception("Fout tijdens scan: %s", e)
            self.error.emit(str(e))

# [END: FUNC: run]
# [FUNC: stop]
    def stop(self):
        """Publieke stopmethode voor controller: roept requestInterruption en wacht."""
        logger.info("Stopverzoek ontvangen voor zoekthread")
        self.requestInterruption()
        self.wait(2000)

# [END: FUNC: stop]
# [FUNC: _iter_media_paths]
    def _iter_media_paths(self, root: Path) -> Iterable[Path]:
        """
        Recursieve iteratie over mappen met correcte uitsluiting:
        - Neemt absolute uitsluitpaden uit media_utils.excluded_folders (of EXCLUDED_DIRS)
        - Vergelijkt case-insensitief op prefix (startswith) met genormaliseerde absolute paden
        """
        raw_excludes = (
            getattr(media_utils, "excluded_folders", None)
            or getattr(media_utils, "EXCLUDED_DIRS", [])
            or []
        )
    
        # Normaliseer uitgesloten paden naar lowercase absolute POSIX-strings
        def norm(p: Path) -> str:
            try:
                return str(Path(p).resolve()).replace("\\", "/").lower()
            except Exception:
                return str(p).replace("\\", "/").lower()
    
        exclude_prefixes = {norm(Path(x)) for x in raw_excludes}
    
        for dirpath, dirnames, filenames in os_walk(root):
            # Huidige map normaliseren
            current_abs = norm(Path(dirpath))
            # Sla hele subboom over als huidige map onder een uitgesloten prefix valt
            if any(current_abs.startswith(pref) for pref in exclude_prefixes):
                logger.debug("Map uitgesloten (prefix): %s", current_abs)
                continue
    
            # Filter child-mappen in-place, zodat os.walk ze niet meer inloopt
            if exclude_prefixes:
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not any(
                        norm(Path(dirpath) / d).startswith(pref)
                        for pref in exclude_prefixes
                    )
                ]
    
            # Bestanden toetsen op mediatype
            for name in filenames:
                p = Path(dirpath, name)
                try:
                    if media_utils.is_media_file(p, self._type_filter):
                        yield p
                except Exception:
                    # Veilig overslaan van onleesbare/rare bestanden
                    continue

# [END: FUNC: _iter_media_paths]
# [FUNC: _match_date]
    def _match_date(self, path: Path) -> bool:
        start, end = self._date_range  # type: ignore[assignment]
        in_range = None
        try:
            in_range = media_utils.in_date_range(path, start, end)  # type: ignore[attr-defined]
        except Exception:
            in_range = None

        if in_range is not None:
            return bool(in_range)

        try:
            mtime = path.stat().st_mtime
            from datetime import datetime, date
            dt = datetime.fromtimestamp(mtime)
            def to_date(x):
                try:
                    return date(x.year(), x.month(), x.day())
                except Exception:
                    return getattr(x, "date", lambda: x)()
            return to_date(start) <= dt.date() <= to_date(end)
        except Exception:
            return True
# [END: CLASS: MediaSearchThread]
# [END: FUNC: _match_date]
# [END: SECTION: CLASS: MediaSearchThread]


# [FUNC: os_walk]
def os_walk(root: Path):
    """
    Losse wrapper rond os.walk zodat we Path kunnen blijven gebruiken en
    testbaar blijven zonder directe os-import bovenin.
    """
    import os

    for dirpath, dirnames, filenames in os.walk(str(root)):
        yield dirpath, dirnames, filenames

# [END: FUNC: os_walk]

# [SECTION: MAIN]
if __name__ == "__main__":
    # Korte rooktest: alleen loggen, geen GUI.
    import sys
    logging.basicConfig(level=logging.INFO)
    from datetime import date

# [END: SECTION: MAIN]
    def _on_found(items): print(f"[found] {len(items)} items…")
    def _on_finished(n): print(f"[finished] totaal: {n}")
    def _on_error(msg): print(f"[error] {msg}")
    def _on_progress(p, n): print(f"[progress] {n}: {p}")

    app = QtCore.QCoreApplication(sys.argv)
    t = MediaSearchThread(
        start_path=".",
        type_filter="all",
        date_range=(date(2000,1,1), date(2100,1,1)),
    )
    t.found.connect(_on_found)
    t.finished.connect(_on_finished)
    t.error.connect(_on_error)
    t.progress.connect(_on_progress)
    t.start()
    sys.exit(app.exec())
