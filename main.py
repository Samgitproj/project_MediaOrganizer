
import logging
from core.FotoBeheerApp import main  # Start de applicatie via de juiste klasse

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

try:
    logging.info("main.py gestart via FotoBeheerApp")
    main()

except Exception as e:
    logging.exception("Er trad een fout op in main.py:")

