from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
import sounddevice as sd
import numpy as np


class AudioManager:
    def __init__(self):
        # === Звук звонка ===
        self.ringtone_player = QMediaPlayer()
        self.ringtone_output = QAudioOutput()
        self.ringtone_player.setAudioOutput(self.ringtone_output)

        # === Уведомления ===
        self.notification_player = QMediaPlayer()
        self.notification_output = QAudioOutput()
        self.notification_player.setAudioOutput(self.notification_output)

        # === Воспроизведение голоса собеседника ===
        self.remote_audio_player = QMediaPlayer()
        self.remote_audio_output = QAudioOutput()
        self.remote_audio_player.setAudioOutput(self.remote_audio_output)

        # === Запись с микрофона (ввод речи) ===
        self.input_stream = None
        self.sample_rate = 44100
        self.chunk_size = 1024

    # ───── Звонок ─────
    def play_ringtone(self, path: str, loop: bool = True):
        self.ringtone_player.setSource(QUrl.fromLocalFile(path))
        self.ringtone_output.setVolume(0.8)
        self.ringtone_player.setLoops(-1 if loop else 1)
        self.ringtone_player.play()

    def stop_ringtone(self):
        self.ringtone_player.stop()

    # ───── Уведомление ─────
    def play_notification(self, path: str):
        self.notification_player.setSource(QUrl.fromLocalFile(path))
        self.notification_output.setVolume(0.6)
        self.notification_player.play()

    # ───── Воспроизведение собеседника ─────
    def play_remote_audio(self, path: str):
        self.remote_audio_player.setSource(QUrl.fromLocalFile(path))
        self.remote_audio_output.setVolume(1.0)
        self.remote_audio_player.play()

    # ───── Микрофон (ввод речи) ─────
    def start_microphone_stream(self, callback):
        """
        callback(audio_data: np.ndarray, frames: int, time, status)
        """
        self.input_stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            blocksize=self.chunk_size,
            callback=callback,
        )
        self.input_stream.start()

    def stop_microphone_stream(self):
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None
