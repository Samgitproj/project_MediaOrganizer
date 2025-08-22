# [SECTION: IMPORTS]
from __future__ import annotations

import logging
import os
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Tuple
# [END: SECTION: IMPORTS]

# [SECTION: LOGGER]
logger = logging.getLogger(__name__)
# [END: SECTION: LOGGER]

# [CLASS: DbService]
class DbService:
    """
    Lichtgewicht servicelaag rond SQLite.
    Houdt verbinding kortlevend per call om UI-blokkades te vermijden.
    """

    DEFAULT_DB_PATH = os.environ.get(
        "MEDIA_ORG_DB",
        os.path.join(
            "C:/OneDrive/Vioprint/OneDrive - Vioprint/software projecten/MediaOrganizer",
            "media_analyse.db",
        ),
    )

# [FUNC: def __init__]
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or self.DEFAULT_DB_PATH
        logger.debug("DbService init met pad: %s", self.db_path)

# [END: FUNC: def __init__]

# [FUNC: def _connect]
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

# [END: FUNC: def _connect]

# [FUNC: def add_folder]
    def add_folder(self, path: str) -> int:
        logger.debug("add_folder(%s)", path)
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO folders(path, is_active) VALUES(?, 1)", (path,)
            )
            conn.commit()
            cur.execute("SELECT id FROM folders WHERE path = ?", (path,))
            row = cur.fetchone()
            folder_id = int(row[0]) if row else 0
        logger.info("Folder geregistreerd id=%s path=%s", folder_id, path)
        return folder_id

# [END: FUNC: def add_folder]

# [FUNC: def upsert_media]
    def upsert_media(
        self,
        folder_id: int,
        path: str,
        filename: str,
        ext: str,
        size: Optional[int],
        mtime: Optional[float],
        mtype: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration_s: Optional[float] = None,
        file_hash: Optional[str] = None,
        created_exif: Optional[str] = None,
    ) -> int:
        """
        Upsert per uniek 'path'. Markeer missing=0 bij (her)vinden.
        """
        logger.debug("upsert_media(path=%s, type=%s)", path, mtype)
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO media(
                    folder_id, path, filename, ext, size, mtime, type,
                    width, height, duration_s, hash, created_exif, missing
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(path) DO UPDATE SET
                    folder_id=excluded.folder_id,
                    filename=excluded.filename,
                    ext=excluded.ext,
                    size=excluded.size,
                    mtime=excluded.mtime,
                    type=excluded.type,
                    width=excluded.width,
                    height=excluded.height,
                    duration_s=excluded.duration_s,
                    hash=excluded.hash,
                    created_exif=excluded.created_exif,
                    missing=0
                """,
                (
                    folder_id,
                    path,
                    filename,
                    ext,
                    size,
                    mtime,
                    mtype,
                    width,
                    height,
                    duration_s,
                    file_hash,
                    created_exif,
                ),
            )
            conn.commit()
            cur.execute("SELECT id FROM media WHERE path=?", (path,))
            row = cur.fetchone()
            media_id = int(row[0]) if row else 0
        logger.info("Media upsert id=%s path=%s", media_id, path)
        return media_id

# [END: FUNC: def upsert_media]

# [FUNC: def mark_missing_in_folder]
    def mark_missing_in_folder(
        self, folder_id: int, existing_paths: Iterable[str]
    ) -> int:
        """
        Zet missing=1 voor records in folder_id die niet in existing_paths zitten.
        """
        existing = set(existing_paths)
        logger.debug(
            "mark_missing_in_folder(folder_id=%s, keep=%s)", folder_id, len(existing)
        )
        with self._connect() as conn:
            cur = conn.cursor()
            # haal alle paden in folder
            cur.execute("SELECT path FROM media WHERE folder_id=?", (folder_id,))
            all_paths = [r[0] for r in cur.fetchall()]
            to_mark = [p for p in all_paths if p not in existing]
            for p in to_mark:
                cur.execute("UPDATE media SET missing=1 WHERE path=?", (p,))
            conn.commit()
        logger.info("Missing gemarkeerd: %s records", len(to_mark))
        return len(to_mark)

# [END: FUNC: def mark_missing_in_folder]

# [FUNC: def search_media]
    def search_media(
        self,
        *,
        folder_id: Optional[int] = None,
        mtype: Optional[str] = None,  # 'image' | 'video'
        favorite: Optional[bool] = None,
        hidden: Optional[bool] = None,
        tag_names: Optional[List[str]] = None,
        text: Optional[str] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Eenvoudige zoekfunctie met optionele filters.
        """
        logger.debug("search_media(filters...) start")
        params: List[Any] = []
        where: List[str] = ["1=1"]

        if folder_id is not None:
            where.append("m.folder_id = ?")
            params.append(folder_id)
        if mtype:
            where.append("m.type = ?")
            params.append(mtype)
        if favorite is not None:
            where.append("m.favorite = ?")
            params.append(1 if favorite else 0)
        if hidden is not None:
            where.append("m.hidden = ?")
            params.append(1 if hidden else 0)
        if text:
            where.append("(m.filename LIKE ? OR m.path LIKE ?)")
            like = f"%{text}%"
            params.extend([like, like])

        join = ""
        if tag_names:
            # Join op tags/media_tags en filter lijst van namen
            placeholders = ",".join("?" for _ in tag_names)
            join += (
                " JOIN media_tags mt ON mt.media_id = m.id"
                " JOIN tags t ON t.id = mt.tag_id"
            )
            where.append(f"t.name IN ({placeholders})")
            params.extend(tag_names)

        sql = (
            "SELECT m.id, m.path, m.filename, m.ext, m.size, m.mtime, m.type, m.favorite,"
            " m.hidden, m.missing FROM media m"
            f"{join} WHERE {' AND '.join(where)}"
            " GROUP BY m.id"
            " ORDER BY m.id DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

        results = [
            {
                "id": r[0],
                "path": r[1],
                "filename": r[2],
                "ext": r[3],
                "size": r[4],
                "mtime": r[5],
                "type": r[6],
                "favorite": r[7],
                "hidden": r[8],
                "missing": r[9],
            }
            for r in rows
        ]
        logger.info("search_media → %s resultaten", len(results))
        return results

# [END: FUNC: def search_media]

# [FUNC: def update_tags]
    def update_tags(self, media_id: int, tag_names: List[str]) -> None:
        """
        Zorgt dat media_id exact deze tag_names heeft (simpel sync-model).
        """
        logger.debug("update_tags(media_id=%s, tags=%s)", media_id, len(tag_names))
        with self._connect() as conn:
            cur = conn.cursor()

            # bestaande tags ophalen
            cur.execute(
                "SELECT t.name FROM tags t JOIN media_tags mt ON mt.tag_id=t.id WHERE mt.media_id=?",
                (media_id,),
            )
            existing = {r[0] for r in cur.fetchall()}
            desired = set(tag_names)

            to_add = desired - existing
            to_remove = existing - desired

            # ensure tags exist
            for name in to_add:
                cur.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (name,))
                cur.execute("SELECT id FROM tags WHERE name=?", (name,))
                tag_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT OR IGNORE INTO media_tags(media_id, tag_id) VALUES(?, ?)",
                    (media_id, tag_id),
                )

            if to_remove:
                placeholders = ",".join("?" for _ in to_remove)
                cur.execute(
                    f"DELETE FROM media_tags WHERE media_id=? AND tag_id IN (SELECT id FROM tags WHERE name IN ({placeholders}))",
                    (media_id, *to_remove),
                )

            conn.commit()
        logger.info("Tags geüpdatet voor media_id=%s", media_id)

# [END: FUNC: def update_tags]

# [FUNC: def log_history]
    def log_history(self, media_id: int, action: str) -> None:
        logger.debug("log_history(media_id=%s, action=%s)", media_id, action)
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO history(media_id, action) VALUES(?, ?)", (media_id, action)
            )
            if action == "viewed":
                cur.execute(
                    "UPDATE media SET last_played_at=datetime('now') WHERE id=?",
                    (media_id,),
                )
            if action == "liked":
                cur.execute("UPDATE media SET favorite=1 WHERE id=?", (media_id,))
            conn.commit()
        logger.info("History gelogd (%s) voor media_id=%s", action, media_id)

# [END: FUNC: def log_history]

# [FUNC: def set_preference]
    def set_preference(self, key: str, value: str) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO preferences(key, value) VALUES(?, ?)",
                (key, value),
            )
            conn.commit()
        logger.debug("Preference set %s=%s", key, value)

# [END: FUNC: def set_preference]

# [FUNC: def get_preference]
    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM preferences WHERE key=?", (key,))
            row = cur.fetchone()
        return row[0] if row else default

# [END: FUNC: def get_preference]

# [FUNC: def set_thumbnail]
    def set_thumbnail(
        self, media_id: int, kind: str, thumb_path: str, width: int, height: int
    ) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO thumbnails(media_id, kind, thumb_path, width, height)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(media_id, kind) DO UPDATE SET
                    thumb_path=excluded.thumb_path,
                    width=excluded.width,
                    height=excluded.height,
                    generated_at=datetime('now')
                """,
                (media_id, kind, thumb_path, width, height),
            )
            conn.commit()
        logger.debug("Thumbnail gezet media_id=%s kind=%s", media_id, kind)

# [END: FUNC: def set_thumbnail]

# [END: CLASS: DbService]

# [SECTION: MAIN]
if __name__ == "__main__":
    # Standalone demo
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    svc = DbService()
    from create_database import create_database  # lazy import om cycli te vermijden

    create_database(svc.db_path)
    folder_id = svc.add_folder("C:/Demo/Foto’s")
    print("folder_id:", folder_id)
# [END: SECTION: MAIN]

