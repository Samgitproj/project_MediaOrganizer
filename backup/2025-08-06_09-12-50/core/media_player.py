import os
import logging
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaContent
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QLabel


class MediaPlayer:
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
        logging.debug("MediaPlayer: geïnitialiseerd")

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

    def play_next_media(self):
        if not self.media_paths:
            logging.info("MediaPlayer: geen media te tonen")
            return

        self.current_media_index = (self.current_media_index + 1) % len(
            self.media_paths
        )
        volgende_pad = self.media_paths[self.current_media_index]
        self.play_media(volgende_pad)
