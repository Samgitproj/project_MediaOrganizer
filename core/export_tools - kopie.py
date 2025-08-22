# [SECTION: IMPORTS]
import logging
import os
import shutil
from typing import Iterable, Tuple, List
# [END: SECTION: IMPORTS]

# Stille optionele prullenbak
try:
    from send2trash import send2trash  # type: ignore
except Exception:
    send2trash = None  # type: ignore

# [SECTION: LOGGER]
logger = logging.getLogger(__name__)
# [END: SECTION: LOGGER]

# [FUNC: def move_files]
def move_files(paths: Iterable[str], dest_dir: str) -> Tuple[int, List[str]]:
    """
    Verplaatst bestanden naar dest_dir. Retourneert (ok_count, errors)
    """
    ok = 0
    errors: List[str] = []
    os.makedirs(dest_dir, exist_ok=True)
    for p in paths:
        try:
            base = os.path.basename(p)
            target = os.path.join(dest_dir, base)
            # conflict: hernoem
            i = 1
            root, ext = os.path.splitext(target)
            while os.path.exists(target):
                target = f"{root}_{i}{ext}"
                i += 1
            shutil.move(p, target)
            ok += 1
        except Exception as e:
            errors.append(f"{p}: {e}")
    return ok, errors

# [END: FUNC: def move_files]

# [FUNC: def trash_or_delete]
def trash_or_delete(paths: Iterable[str]) -> Tuple[int, List[str]]:
    """
    Probeert items naar de prullenbak te sturen; als dat niet kan, delete.
    Retourneert (ok_count, errors)
    """
    ok = 0
    errors: List[str] = []
    for p in paths:
        try:
            if send2trash is not None:
                send2trash(p)  # type: ignore
            else:
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
            ok += 1
        except Exception as e:
            errors.append(f"{p}: {e}")
    return ok, errors

# [END: FUNC: def trash_or_delete]

# [SECTION: MAIN]
if __name__ == "__main__":
    logger.info("core/export_tools.py — selftest done")
# [END: SECTION: MAIN]

