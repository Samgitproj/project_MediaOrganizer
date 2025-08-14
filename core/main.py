# [SECTION: Imports]
import sys
import os

# [END: Imports]
# Voeg projectroot toe aan sys.path (maakt core/ importeerbaar)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.app_controller import MediaAppController
import logging
import sys

# Logging instellen
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

try:
    logging.info("main.py gestart")

    controller = MediaAppController()
    controller.start()

except Exception as e:
    logging.exception("Er trad een fout op in main.py:")
