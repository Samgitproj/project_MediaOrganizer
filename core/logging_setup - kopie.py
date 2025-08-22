# [SECTION: IMPORTS]
from __future__ import annotations
import json
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
# [END: SECTION: IMPORTS]

DEFAULT_TEXT_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s"
DEFAULT_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# [CLASS: _JsonLineFormatter]
class _JsonLineFormatter(logging.Formatter):
    """Formateert elk logrecord als één JSON-regel (JSONL)."""
# [FUNC: def format]
    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "ts": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record.levelname,
            "name": record.name,
            "func": record.funcName,
            "line": record.lineno,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            obj["exc"] = self.formatException(record.exc_info)
        return json.dumps(obj, ensure_ascii=False)

# [END: FUNC: def format]

# [END: CLASS: _JsonLineFormatter]
# [FUNC: def init_logging]
def init_logging(
    log_dir: str | os.PathLike = "logs",
    level: str = "INFO",
    text_filename: str = "log.txt",
    json_filename: str = "log.jsonl",
    rotate: str = "size",            # "size" of "daily"
    max_bytes: int = 2_000_000,
    backup_count: int = 5
) -> logging.Logger:
    """
    Initialiseert logging met:
      • Tekstlog met rotatie (size of daily)
      • JSONL-log (1 event per regel)
      • Console-output
    Retourneert een toepassingslogger.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Tekstlog (rotating)
    text_file = log_path / text_filename
    if rotate == "daily":
        th = logging.handlers.TimedRotatingFileHandler(
            text_file, when="midnight", backupCount=backup_count, encoding="utf-8"
        )
    else:
        th = logging.handlers.RotatingFileHandler(
            text_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
    th.setFormatter(logging.Formatter(DEFAULT_TEXT_FMT, datefmt=DEFAULT_DATE_FMT))
    root.addHandler(th)

    # JSONL-log
    jh = logging.FileHandler(log_path / json_filename, encoding="utf-8")
    jh.setFormatter(_JsonLineFormatter())
    root.addHandler(jh)

    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
    root.addHandler(ch)

    app_logger = logging.getLogger("app")
    app_logger.info("logging initialised → %s", log_path)
    return app_logger

# [END: FUNC: def init_logging]

# [SECTION: MAIN]
if __name__ == "__main__":
    log = init_logging()
    log.debug("demo: debug")
    log.info("demo: info")
    log.warning("demo: warning")
# [END: SECTION: MAIN]

