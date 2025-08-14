# [SECTION: Imports]
import os

# [END: Imports]
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


# Controleer of een bestand een media-item is volgens opgegeven filtertype
# [FUNC: is_media_file]
def is_media_file(filepath: str, filtertype: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    print(f"[DEBUG] Bestand: {filepath}, extensie: {ext}, filtertype: {filtertype}")

    if filtertype == "images":
        match = ext in image_extensions
    elif filtertype == "videos":
        match = ext in video_extensions
    elif filtertype == "all":
        match = ext in image_extensions or ext in video_extensions
    else:
        match = False

    print(f"[DEBUG] → match: {match}")
    return match
# [END: is_media_file]
