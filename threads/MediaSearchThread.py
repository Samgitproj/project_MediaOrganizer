# [SECTION: Imports]
import os
from PyQt6.QtCore import QThread, pyqtSignal
from core.media_utils import is_media_file, excluded_folders


# [END: Imports]
# [CLASS: MediaSearchThread]
class MediaSearchThread(QThread):
    # Signalen naar GUI: lijsten met resultaten en fouten
    searchCompleted = pyqtSignal(list, list)

# [FUNC: __init__]
    def __init__(self, start_path: str, filter_type: str):
        super().__init__()
        self.start_path = start_path
        self.filter_type = filter_type
        self.gevonden_mappen = set()
        self.foutmeldingen = []

# [END: __init__]
# [FUNC: run]
    def run(self):
        for root, dirs, files in os.walk(self.start_path):
            # Normaliseer pad voor vergelijking
            normalized_root = os.path.abspath(root)

            # Sla uitgesloten folders over
            if any(
                normalized_root.lower().startswith(excl.lower())
                for excl in excluded_folders
            ):
                continue

            try:
                if any(
                    is_media_file(os.path.join(root, f), self.filter_type)
                    for f in files
                ):
                    self.gevonden_mappen.add(normalized_root)
            except Exception as e:
                self.foutmeldingen.append(
                    f"Fout bij toegang tot {normalized_root}: {str(e)}"
                )

        # Sorteer en zend resultaten terug naar GUI
        self.searchCompleted.emit(sorted(self.gevonden_mappen), self.foutmeldingen)
# [END: MediaSearchThread]
# [END: run]
