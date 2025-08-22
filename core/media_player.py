# [SECTION: IMPORTS]
import logging
import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QUrl
# [END: SECTION: IMPORTS]

# [SECTION: LOGGER]
logger = logging.getLogger(__name__)
# [END: SECTION: LOGGER]

# [CLASS: MediaPlayer]
class MediaPlayer:
# [FUNC: def __init__]
    def __init__(self, media_label, video_widget, player):
        logger.debug("MediaPlayer __init__ gestart")
        self.media_label = media_label
        self.video_widget = video_widget
        self.player = player

        self.media_list: list[str] = []
        self.current_index: int = -1  # vóór eerste item
        self.slideshow_running: bool = False
        self.loop_enabled: bool = False
        self.delay_ms: int = 3000

        # Timer voor afbeeldingen
        from PyQt6.QtCore import QTimer  # lokale import om globale imports intact te laten
        self._timer = QTimer(self.media_label)
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._on_timeout)

        # Bij video-einde → volgende item wanneer slideshow actief
        try:
            from PyQt6.QtMultimedia import QMediaPlayer as _QMP  # type: ignore
            self._QMP = _QMP
            self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        except Exception:
            self._QMP = None

# [END: FUNC: def __init__]

# [FUNC: def set_loop]
    def set_loop(self, enabled: bool) -> None:
        logger.info("Loop ingesteld → %s", enabled)
        self.loop_enabled = bool(enabled)

# [END: FUNC: def set_loop]

# [FUNC: def set_delay]
    def set_delay(self, ms: int) -> None:
        ms = max(250, int(ms))  # minimaal 250 ms
        logger.info("Delay ingesteld → %d ms", ms)
        self.delay_ms = ms
        if self._timer.isActive():
            self._timer.start(self.delay_ms)  # interval live bijstellen

# [END: FUNC: def set_delay]

# [FUNC: def start_slideshow]
    def start_slideshow(self):
        logger.info("Slideshow gestart")
        if not self.media_list:
            logger.warning("Slideshow kan niet starten: media_list is leeg")
            return
        self.slideshow_running = True
        self.play_next_media()

# [END: FUNC: def start_slideshow]

# [FUNC: def pause_slideshow]
    def pause_slideshow(self):
        logger.info("Slideshow gepauzeerd")
        self.slideshow_running = False
        self._timer.stop()
        try:
            self.player.pause()
        except Exception:
            pass

# [END: FUNC: def pause_slideshow]

# [FUNC: def stop_slideshow]
    def stop_slideshow(self):
        logger.info("Slideshow gestopt")
        self.slideshow_running = False
        self._timer.stop()
        try:
            self.player.stop()
        except Exception:
            pass
        self.media_label.clear()
        self.media_label.setVisible(False)
        self.video_widget.setVisible(False)

# [END: FUNC: def stop_slideshow]

# [FUNC: def play_next_media]
    def play_next_media(self):
        if not self.media_list:
            logger.warning("Geen media in de lijst om af te spelen")
            return

        # Zonder loop: stop aan het einde
        if not self.loop_enabled and self.current_index + 1 >= len(self.media_list):
            logger.info("Einde afspeellijst (loop uit) → stop slideshow")
            self.stop_slideshow()
            return

        self.current_index = (self.current_index + 1) % len(self.media_list)
        pad = self.media_list[self.current_index]
        logger.debug("Volgende media: idx=%d → %s", self.current_index, pad)
        self.play_media(pad)

# [END: FUNC: def play_next_media]

# [FUNC: def play_media]
    def play_media(self, pad: str):
        if not os.path.exists(pad):
            logger.error("Bestand bestaat niet: %s", pad)
            return

        # Afbeelding
        if pad.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp", ".heic")):
            logger.debug("Afbeelding tonen: %s", pad)
            self._timer.stop()  # straks herstarten met juiste delay
            self.video_widget.setVisible(False)

            pixmap = QPixmap(pad)
            self.media_label.setPixmap(
                pixmap.scaled(
                    self.media_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.media_label.setVisible(True)

            if self.slideshow_running:
                self._timer.start(self.delay_ms)

        # Video
        elif pad.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".mpeg", ".mpg")):
            logger.debug("Video afspelen: %s", pad)
            self._timer.stop()  # video bepaalt tempo
            self.media_label.setVisible(False)
            self.video_widget.setVisible(True)
            self.player.setSource(QUrl.fromLocalFile(pad))
            self.player.play()

        else:
            logger.warning("Niet-ondersteund mediabestand: %s", pad)

# [END: FUNC: def play_media]

# [FUNC: def _on_timeout]
    def _on_timeout(self):
        logger.debug("Slideshow-timeout → volgende media")
        if self.slideshow_running:
            self.play_next_media()
        else:
            self._timer.stop()

# [END: FUNC: def _on_timeout]

# [FUNC: def _on_media_status_changed]
    def _on_media_status_changed(self, status):
        """Bij video-einde automatisch volgende item indien slideshow actief."""
        try:
            if self._QMP and status == self._QMP.MediaStatus.EndOfMedia:
                logger.debug("Video EndOfMedia → volgende media (slideshow=%s)", self.slideshow_running)
                if self.slideshow_running:
                    self.play_next_media()
        except Exception:
            # Geen harde afhankelijkheid op QMediaPlayer-enums
            pass
# [END: CLASS: MediaPlayer]
# [END: FUNC: def _on_media_status_changed]

