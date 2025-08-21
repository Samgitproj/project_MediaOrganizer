# [SECTION: IMPORTS]
import logging


# [END: SECTION: IMPORTS]
logger = logging.getLogger(__name__)


# [FUNC: detecteer_donkerheid]
def detecteer_donkerheid(filepath: str) -> float:
    """
    Placeholder: retourneer een 'donkerheids-score' (0.0–1.0).
    """
    logger.debug("detecteer_donkerheid() gestart voor: %s", filepath)
    # TODO: implementeer analyse
    return 0.0

# [END: FUNC: detecteer_donkerheid]


# [SECTION: MAIN]
if __name__ == "__main__":
    logger.info("ai/detecteer_donkerheid.py standalone run — demo")
    score = detecteer_donkerheid("demo.jpg")
    logger.info("Donkerheidsscore: %.3f", score)
# [END: SECTION: MAIN]
