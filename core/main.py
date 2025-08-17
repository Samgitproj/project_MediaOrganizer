# [SECTION: IMPORTS]
import os
import sys
import logging

# Zorg dat 'core/' en 'gui/' importeerbaar zijn (main.py staat in de project-root)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.logging_setup import init_logging  # centrale logging
from core.app_controller import MediaAppController
# [END: SECTION: IMPORTS]


# [SECTION: CONSTANTS]
PROJECT_NAME = "MediaOrganizer"
LOG_DIR = "logs"  # logging_setup maakt/benut deze map
# [END: SECTION: CONSTANTS]


# [FUNC: main]
def main() -> int:
    """
    Entrypoint van de applicatie:
    - Initialiseert centrale logging (txt + jsonl)
    - Start de controller (Qt-app + GUI)
    """
    init_logging(PROJECT_NAME, LOG_DIR)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Start %s", PROJECT_NAME)
        controller = MediaAppController()
        controller.start()
        logger.info("Stop %s", PROJECT_NAME)
        return 0
    except Exception:
        logger.exception("Onverwachte fout in main()")
        return 1
# [END: FUNC: main]


# [SECTION: MAIN]
if __name__ == "__main__":
    raise SystemExit(main())
# [END: SECTION: MAIN]
