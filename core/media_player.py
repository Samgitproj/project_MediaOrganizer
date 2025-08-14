# [SECTION: Imports]
import os
import logging
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaContent
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QLabel


# [END: Imports]
# [CLASS: MediaPlayer]
class MediaPlayer:
# [FUNC: __init__]
    def __init__(
        self, media_label: QLabel, video_widget: QVideoWidget, player: QMediaPlayer
    ):
        self.media_label = media_label
        self.video_widget = video_widget
        self.player = player
        self.current_media_index = 0
        self.media_paths = []
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self.play_next_media)
        self.is_playing = False
        self.is_paused = False
        logging.debug("MediaPlayer: geïnitialiseerd")

# [END: __init__]
# [FUNC: play_media]
    def play_media(self, filepath: str):
        logging.debug(f"MediaPlayer: speelt af {filepath}")

        if filepath.lower().endswith((".jpg", ".jpeg", ".png")):
            self.player.stop()
            self.video_widget.hide()
            self.media_label.show()
            pixmap = QPixmap(filepath)
            self.media_label.setPixmap(pixmap)
        elif filepath.lower().endswith((".mp4", ".avi")):
            self.media_label.hide()
            self.video_widget.show()
            self.player.setSource(QMediaContent(filepath))
            self.player.play()
        else:
            logging.warning(f"Ongeldig mediabestand: {filepath}")

# [END: play_media]
# [FUNC: play_next_media]
    def play_next_media(self):
        if not self.media_paths:
            logging.info("MediaPlayer: geen media te tonen")
            return

        self.current_media_index = (self.current_media_index + 1) % len(
            self.media_paths
        )
        volgende_pad = self.media_paths[self.current_media_index]
        self.play_media(volgende_pad)

# [END: play_next_media]
# [FUNC: start_slideshow]
    def start_slideshow(self, interval_secs=5):
        if not self.media_paths:
            logging.info("Geen mediabestanden om slideshow te starten.")
            return

        self.is_playing = True
        self.is_paused = False
        self.slideshow_timer.start(interval_secs * 1000)
        self.play_media(self.media_paths[self.current_media_index])
        logging.info("Slideshow gestart.")

# [END: start_slideshow]
# [FUNC: pause_slideshow]
    def pause_slideshow(self):
        if self.is_playing:
            if self.is_paused:
                self.slideshow_timer.start()
                logging.info("Slideshow hervat.")
            else:
                self.slideshow_timer.stop()
                logging.info("Slideshow gepauzeerd.")
            self.is_paused = not self.is_paused

# [END: pause_slideshow]
# [FUNC: stop_slideshow]
    def stop_slideshow(self):
        self.slideshow_timer.stop()
        self.is_playing = False
        self.is_paused = False
        logging.info("Slideshow gestopt.")
# [END: MediaPlayer]
# [END: stop_slideshow]
