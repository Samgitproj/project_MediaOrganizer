# [SECTION: IMPORTS]
import os
import logging
from datetime import datetime, date
from typing import Optional, Iterable

# [END: SECTION: IMPORTS]
# Pillow optioneel voor EXIF
try:
    from PIL import Image, ExifTags  # type: ignore
except Exception:
    Image = None  # type: ignore
    ExifTags = None  # type: ignore

logger = logging.getLogger(__name__)

# Vaste extensies voor afbeeldingen
image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".heic", ".webp"]

# Vaste extensies voor video's
video_extensions = [
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mpeg",
    ".mpg",
]

# Folders die bewust worden overgeslagen bij zoekacties
excluded_folders = [
    r"C:\$Recycle.Bin",
    r"C:\System Volume Information",
    r"C:\Recovery",
    r"C:\Config.Msi",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Windows",
    r"C:\PerfLogs",
    r"C:\ProgramData",
    r"C:\Intel",
    r"C:\MSOCache",
]


# [FUNC: _file_mtime_datetime]
def _file_mtime_datetime(path: str) -> Optional[datetime]:
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts)
    except Exception:
        return None

# [END: FUNC: _file_mtime_datetime]

# [FUNC: get_exif_datetime]
def get_exif_datetime(path: str) -> Optional[datetime]:
    """
    Retourneert opnametijd (EXIF DateTimeOriginal) indien mogelijk,
    anders None. Werkt alleen voor images en als Pillow beschikbaar is.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in image_extensions or Image is None:
        return None
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            if not exif:
                return None
            # Zoek key voor DateTimeOriginal
            tag_map = (
                {ExifTags.TAGS.get(k, k): k for k in exif.keys()} if ExifTags else {}
            )
            key = tag_map.get("DateTimeOriginal")
            value = exif.get(key) if key is not None else None
            if not value:
                return None
            # Verwacht formaat "YYYY:MM:DD HH:MM:SS"
            try:
                return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
            except Exception:
                return None
    except Exception:
        return None

# [END: FUNC: get_exif_datetime]

# [FUNC: in_date_range]
def in_date_range(path: str, start, end) -> Optional[bool]:
    """
    True/False als we zeker zijn dat path binnen/ buiten de range valt.
    None als we het niet kunnen bepalen.
    - start/end mogen QDate, datetime.date of datetime.datetime zijn.
    """

    def to_date(obj) -> Optional[date]:
        try:
            # QDate heeft year(), month(), day()
            y = getattr(obj, "year")()
            m = getattr(obj, "month")()
            d = getattr(obj, "day")()
            return date(y, m, d)
        except Exception:
            pass
        try:
            if isinstance(obj, datetime):
                return obj.date()
            if isinstance(obj, date):
                return obj
        except Exception:
            pass
        return None

    sd, ed = to_date(start), to_date(end)
    if sd is None or ed is None:
        return None

    ex = get_exif_datetime(path)
    dt = ex or _file_mtime_datetime(path)
    if dt is None:
        return None
    return sd <= dt.date() <= ed

# [END: FUNC: in_date_range]



# [FUNC: _file_datetime_for_sequence]
def _file_datetime_for_sequence(path: str) -> Optional[datetime]:
    return get_exif_datetime(path) or _file_mtime_datetime(path)

# [END: FUNC: _file_datetime_for_sequence]

# [FUNC: detect_sequences]
def detect_sequences(files: Iterable[str], gap_seconds: int) -> list[list[str]]:
    """
    Sorteert files op tijd en groepeert in reeksen zodra de kloof > gap_seconds is.
    Retourneert lijst van lijsten (reeksen).
    """
    items = []
    for f in files:
        dt = _file_datetime_for_sequence(f)
        if dt is None:
            continue
        items.append((dt, f))
    items.sort(key=lambda x: x[0])

    sequences: list[list[str]] = []
    current: list[str] = []
    prev_dt: Optional[datetime] = None
    from datetime import timedelta

    for dt, f in items:
        if prev_dt is None or (dt - prev_dt) <= timedelta(seconds=gap_seconds):
            current.append(f)
        else:
            if current:
                sequences.append(current)
            current = [f]
        prev_dt = dt
    if current:
        sequences.append(current)
    return sequences

# [END: FUNC: detect_sequences]



# [FUNC: is_media_file]
def is_media_file(filepath: str, filtertype: str) -> bool:
    """
    Bepaal of een pad een media-item is volgens het gekozen filtertype:
    - "images" → alleen afbeeldingen
    - "videos" → alleen video's
    - "all"    → beide
    """
    ext = os.path.splitext(filepath)[1].lower()
    logger.debug("is_media_file: %s (ext=%s, filter=%s)", filepath, ext, filtertype)

    if filtertype == "images":
        match = ext in image_extensions
    elif filtertype == "videos":
        match = ext in video_extensions
    elif filtertype == "all":
        match = ext in image_extensions or ext in video_extensions
    else:
        match = False

    logger.debug("is_media_file → match=%s", match)
    return match

# [END: FUNC: is_media_file]

