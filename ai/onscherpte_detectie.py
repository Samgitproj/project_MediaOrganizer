# [SECTION: IMPORTS]
import logging


# [END: SECTION: IMPORTS]
logger = logging.getLogger(__name__)


# [FUNC: detecteer_onscherpte]
def detecteer_onscherpte(filepath: str) -> float:
    """
    Placeholder: retourneer een 'onscherpte-score' (0.0–1.0).
    """
    logger.debug("detecteer_onscherpte() gestart voor: %s", filepath)
    # TODO: implementeer analyse
    return 0.0

# [END: FUNC: detecteer_onscherpte]


# [SECTION: MAIN]
if __name__ == "__main__":
    logger.info("ai/onscherpte_detectie.py standalone run — demo")
    score = detecteer_onscherpte("demo.jpg")
    logger.info("Onscherptescore: %.3f", score)
# [END: SECTION: MAIN]
