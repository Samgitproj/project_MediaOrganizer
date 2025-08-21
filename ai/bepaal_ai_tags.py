# [SECTION: IMPORTS]
import logging
from typing import List


# [END: SECTION: IMPORTS]
logger = logging.getLogger(__name__)


# [FUNC: bepaal_ai_tags]
def bepaal_ai_tags(filepath: str) -> List[str]:
    """
    Placeholder: bepaal AI-tags voor een mediabestand.
    """
    logger.debug("bepaal_ai_tags() gestart voor: %s", filepath)
    # TODO: implementeer AI-tagging
    return []

# [END: FUNC: bepaal_ai_tags]


# [SECTION: MAIN]
if __name__ == "__main__":
    logger.info("ai/bepaal_ai_tags.py standalone run — demo")
    demo_tags = bepaal_ai_tags("demo.jpg")
    logger.info("Tags: %s", demo_tags)
# [END: SECTION: MAIN]
