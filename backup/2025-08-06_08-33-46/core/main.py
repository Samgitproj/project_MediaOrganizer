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
