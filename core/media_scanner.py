# [SECTION: IMPORTS]
from __future__ import annotations

import logging
import os
import time
from typing import Dict, Iterable, List, Tuple

# Externe libs (PIL/ffprobe) bewust vermeden; we beperken ons tot mtime/size/ext.
from .db_interface import DbService
# [END: SECTION: IMPORTS]

# [SECTION: LOGGER]
logger = logging.getLogger(__name__)
# [END: SECTION: LOGGER]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".m4v", ".webm"}

# [FUNC: def _detect_type]
def _detect_type(ext: str) -> str:
    ext_l = ext.lower()
    if ext_l in IMAGE_EXTS:
        return "image"
    if ext_l in VIDEO_EXTS:
        return "video"
    return "other"

# [END: FUNC: def _detect_type]

# [FUNC: def iter_media_files]
def iter_media_files(root: str) -> Iterable[Tuple[str, str, str]]:
    """
    Yield (full_path, filename, ext) voor bestanden onder root.
    """
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            _, ext = os.path.splitext(fn)
            yield full, fn, ext

# [END: FUNC: def iter_media_files]

# [FUNC: def scan_folder_into_db]
def scan_folder_into_db(root: str, db: DbService) -> Dict[str, int]:
    """
    Scant een map en schrijft/actualiseert media in de DB.
    - Voegt folder toe (indien nieuw)
    - Upsert elk bestand
    - Markeert ontbrekende bestanden in DB als missing=1
    Return: dict met simpele statistiek.
    """
    logger.info("Start scan: %s", root)
    start = time.time()

    folder_id = db.add_folder(root)
    seen_paths: List[str] = []
    upserts = 0
    skipped = 0

    for full_path, filename, ext in iter_media_files(root):
        mtype = _detect_type(ext)
        if mtype == "other":
            skipped += 1
            continue

        try:
            stat = os.stat(full_path)
            size = int(stat.st_size)
            mtime = float(stat.st_mtime)
        except FileNotFoundError:
            # race condition: bestand verdween tijdens scan
            skipped += 1
            continue
        except Exception:
            logger.exception("Metadata ophalen mislukt: %s", full_path)
            skipped += 1
            continue

        db.upsert_media(
            folder_id=folder_id,
            path=full_path,
            filename=filename,
            ext=ext.lower(),
            size=size,
            mtime=mtime,
            mtype=mtype,
        )
        seen_paths.append(full_path)
        upserts += 1

    missing_marked = db.mark_missing_in_folder(folder_id, seen_paths)
    elapsed = time.time() - start
    stats = {
        "folder_id": folder_id,
        "upserts": upserts,
        "skipped": skipped,
        "missing_marked": missing_marked,
        "elapsed_s": int(elapsed),
    }
    logger.info("Scan klaar: %s", stats)
    return stats

# [END: FUNC: def scan_folder_into_db]

# [SECTION: MAIN]
if __name__ == "__main__":
    # Standalone demo
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    db = DbService()
    try:
        from .create_database import create_database  # type: ignore
    except ImportError:
        # fallback voor losse runs zonder package context
        from create_database import create_database  # type: ignore
    create_database(db.db_path)
    # Pas hieronder het pad aan voor een snelle test
    print(scan_folder_into_db("C:/Temp/MediaDemo", db))
# [END: SECTION: MAIN]

