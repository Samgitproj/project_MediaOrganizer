# [SECTION: IMPORTS]
from __future__ import annotations

import os
import sqlite3
import logging
from typing import Optional


# [END: SECTION: IMPORTS]
# Je kunt dit pad overschrijven met env var MEDIA_ORG_DB.
DEFAULT_DB_PATH = os.environ.get(
    "MEDIA_ORG_DB",
    os.path.join(
        "C:/OneDrive/Vioprint/OneDrive - Vioprint/software projecten/MediaOrganizer",
        "media_analyse.db",
    ),
)
SCHEMA_VERSION = "1.0"

logger = logging.getLogger(__name__)


# [FUNC: _ensure_folder]
def _ensure_folder(db_path: str) -> None:
    folder = os.path.dirname(db_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

# [END: FUNC: _ensure_folder]



# [FUNC: create_database]
def create_database(db_path: Optional[str] = None) -> None:
    """
    Maakt (indien nodig) de database en alle tabellen aan.
    Idempotent: gebruikt IF NOT EXISTS.
    """
    db_path = db_path or DEFAULT_DB_PATH
    _ensure_folder(db_path)
    logger.info("Start create_database → %s", db_path)

    conn = sqlite3.connect(db_path)
    try:
        c = conn.cursor()

        # Kern-tabellen
        c.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                added_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                path TEXT NOT NULL UNIQUE,
                filename TEXT,
                ext TEXT,
                size INTEGER,
                mtime REAL,
                type TEXT, -- 'image' | 'video' | 'other'
                width INTEGER,
                height INTEGER,
                duration_s REAL,
                hash TEXT,
                created_exif TEXT,
                imported_at TEXT DEFAULT (datetime('now')),
                rating INTEGER,
                favorite INTEGER DEFAULT 0,
                hidden INTEGER DEFAULT 0,
                missing INTEGER DEFAULT 0,
                last_played_at TEXT,
                FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS media_tags (
                media_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (media_id, tag_id),
                FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER NOT NULL,
                x INTEGER, y INTEGER, w INTEGER, h INTEGER,
                person_id INTEGER NULL,
                embedding BLOB,
                FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE,
                FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS playlist_items (
                playlist_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (playlist_id, position),
                FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER NOT NULL,
                played_at TEXT DEFAULT (datetime('now')),
                action TEXT NOT NULL, -- 'viewed' | 'skipped' | 'liked'
                FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS thumbnails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER NOT NULL,
                kind TEXT NOT NULL, -- 'small' | 'medium'
                thumb_path TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                generated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(media_id, kind),
                FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )

        # Indexen
        c.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_media_path ON media(path);
            CREATE INDEX IF NOT EXISTS idx_media_folder_type ON media(folder_id, type);
            CREATE INDEX IF NOT EXISTS idx_media_tags_tag ON media_tags(tag_id);
            CREATE INDEX IF NOT EXISTS idx_history_media_played ON history(media_id, played_at);
            """
        )

        # schema_version bijhouden in preferences
        c.execute(
            "INSERT OR REPLACE INTO preferences(key, value) VALUES('schema_version', ?)",
            (SCHEMA_VERSION,),
        )

        conn.commit()
        logger.info("Database schema up-to-date op: %s", db_path)
    except Exception:
        logger.exception("Fout tijdens create_database()")
        raise
    finally:
        conn.close()
        logger.debug("Databaseverbinding gesloten")

# [END: FUNC: create_database]



# [FUNC: main]
def main() -> int:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
        )
    try:
        create_database()
        return 0
    except Exception:
        return 1

# [END: FUNC: main]



# [SECTION: MAIN]
if __name__ == "__main__":
    raise SystemExit(main())
# [END: SECTION: MAIN]
