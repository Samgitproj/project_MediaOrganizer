# [SECTION: IMPORTS]
import os
import sys
import logging
import argparse
import shutil
from datetime import datetime
# [END: SECTION: IMPORTS]

# Zorg dat 'core/' en 'gui/' importeerbaar zijn (main.py staat in de project-root)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.logging_setup import init_logging  # centrale logging
from core.app_controller import MediaAppController
from core.create_database import create_database
from core.db_interface import DbService

PROJECT_NAME = "MediaOrganizer"
LOG_DIR = "logs"  # logging_setup maakt/benut deze map

# Laat DbService het standaard pad bepalen; kan worden overschreven met env var MEDIA_ORG_DB
DEFAULT_DB_PATH = DbService.DEFAULT_DB_PATH

# [FUNC: def parse_args]
def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=PROJECT_NAME, description="Start de MediaOrganizer applicatie."
    )
    parser.add_argument(
        "--db",
        dest="db_path",
        help="Pad naar het SQLite databasebestand (overrulet ENV MEDIA_ORG_DB).",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Stel het logniveau in (standaard: vanuit logging_setup of INFO).",
    )
    parser.add_argument(
        "--no-backup",
        dest="no_backup",
        action="store_true",
        help="Sla de dagelijkse DB-backup bij opstart over.",
    )
    return parser.parse_args(argv)

# [END: FUNC: def parse_args]

# [FUNC: def setup_global_excepthook]
def setup_global_excepthook() -> None:
    """
    Zorgt dat ongehandelede exceptions netjes gelogd worden i.p.v. stille crash.
    """

    def _hook(exc_type, exc, tb):
        logger = logging.getLogger(__name__)
        logger.exception("Ongehandelde uitzondering", exc_info=(exc_type, exc, tb))
        # Daarna alsnog de default laten lopen (handig voor dev)
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook

# [END: FUNC: def setup_global_excepthook]

# [FUNC: def ensure_daily_backup]
def ensure_daily_backup(db_path: str) -> None:
    """
    Maak 1x per dag een backup van de DB in ./backup/YYYY-MM-DD/filename.db
    (idempotent: overschrijft niet als bestand al bestaat).
    """
    try:
        if not db_path or not os.path.exists(db_path):
            return
        today = datetime.now().strftime("%Y-%m-%d")
        backup_dir = os.path.join(project_root, "backup", today)
        os.makedirs(backup_dir, exist_ok=True)
        dest = os.path.join(backup_dir, os.path.basename(db_path))
        if not os.path.exists(dest):
            shutil.copy2(db_path, dest)
            logging.getLogger(__name__).info("DB-backup gemaakt: %s", dest)
    except Exception:
        logging.getLogger(__name__).warning("DB-backup mislukt", exc_info=True)

# [END: FUNC: def ensure_daily_backup]

# [FUNC: def main]
def main(argv: list[str] | None = None) -> int:
    """
    Entrypoint van de applicatie:
    - CLI-args (db-pad, log-level, backup-skip)
    - Initialiseert centrale logging (txt + jsonl)
    - Globale excepthook voor nette crashlogs
    - Initialiseert database (schema aanmaken/updaten)
    - Maakt DbService en start de controller (Qt-app + GUI)
    """
    args = parse_args(argv or [])

    # Logging opzetten
    init_logging(log_dir=LOG_DIR)
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
    logger = logging.getLogger(__name__)
    logger.info("Logging initialised → %s", PROJECT_NAME)

    # Globale excepthook
    setup_global_excepthook()

    try:
        # 1) Database-pad bepalen (CLI > ENV > DEFAULT)
        db_path = args.db_path or os.environ.get("MEDIA_ORG_DB", DEFAULT_DB_PATH)
        os.environ["MEDIA_ORG_DB"] = db_path  # consistent voor submodules
        logger.info("Database-pad: %s", db_path)

        # 2) Database klaarzetten (idempotent)
        create_database(db_path)
        logger.info("Database klaar/opgedateerd.")

        # 3) Dagelijkse backup (tenzij overgeslagen)
        if not args.no_backup:
            ensure_daily_backup(db_path)

        # 4) Service maken
        db_service = DbService(db_path=db_path)
        logger.debug("DbService gemaakt met pad: %s", db_service.db_path)

        # 5) Controller starten (flexibel constructor: met of zonder db_service)
        try:
            controller = MediaAppController(db_service=db_service)
        except TypeError:
            # Backward-compat: oudere controller zonder parameter
            logger.warning(
                "MediaAppController accepteert geen 'db_service'; val terug op no-arg constructor."
            )
            controller = MediaAppController()

        logger.info("Start %s", PROJECT_NAME)
        controller.start()
        logger.info("Stop %s", PROJECT_NAME)
        return 0
    except Exception:
        logger.exception("Onverwachte fout in main()")
        return 1

# [END: FUNC: def main]

# [SECTION: MAIN]
if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
# [END: SECTION: MAIN]

