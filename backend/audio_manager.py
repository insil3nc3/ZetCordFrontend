from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
import sounddevice as sd
import numpy as np


class AudioManager:
    def __init__(self, sample_rate=48000, channels=2):
        self.ringtone_player = QMediaPlayer()
        self.ringtone_output = QAudioOutput()
        self.ringtone_player.setAudioOutput(self.ringtone_output)
        self.notification_player = QMediaPlayer()
        self.notification_output = QAudioOutput()
        self.notification_player.setAudioOutput(self.notification_output)
        self.remote_audio_player = QMediaPlayer()
        self.remote_audio_output = QAudioOutput()
        self.remote_audio_player.setAudioOutput(self.remote_audio_output)
        self.input_stream = None
        self.sample_rate = sample_rate
        self.chunk_size = 1024
        self.output_stream = None
        self.output_sample_rate = sample_rate
        self.output_channels = channels

    def start_output_stream(self):
        if self.output_stream is None:
            try:
                devices = sd.query_devices()
                print("Доступные аудиоустройства:")
                for i, dev in enumerate(devices):
                    print(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")

                # Linux: используем device=5 (hw:2,0)
                # Windows: используем device=None (по умолчанию)
                import platform
                device = 5 if platform.system() == "Linux" else None

                sd.default.device = device
                sd.default.samplerate = self.output_sample_rate
                sd.default.channels = self.output_channels
                sd.default.dtype = 'float32'

                self.output_stream = sd.OutputStream(
                    samplerate=self.output_sample_rate,
                    channels=self.output_channels,
                    blocksize=self.chunk_size,
                    dtype='float32',
                    device=device
                )
                self.output_stream.start()
                device_name = sd.query_devices(device=device)['name'] if device is not None else "default"
                print(f"Аудиовыходной поток запущен на устройстве: {device_name}")
            except Exception as e:
                print(f"Ошибка при запуске аудиовыходного потока: {e}")

    def play_audio_chunk(self, audio_chunk: np.ndarray):
        if self.output_stream:
            try:
                print(
                    f"Воспроизведение аудио: shape={audio_chunk.shape}, dtype={audio_chunk.dtype}, max={np.max(np.abs(audio_chunk))}")
                if audio_chunk.shape[1] != self.output_channels:
                    audio_chunk = np.repeat(audio_chunk[:, :1], self.output_channels, axis=1)
                self.output_stream.write(audio_chunk)
            except Exception as e:
                print(f"Ошибка при воспроизведении аудио: {e}")

    def play_ringtone(self, path: str, loop: bool = True):
        self.ringtone_player.setSource(QUrl.fromLocalFile(path))
        self.ringtone_output.setVolume(0.8)
        self.ringtone_player.setLoops(-1 if loop else 1)
        self.ringtone_player.play()

    def stop_ringtone(self):
        self.ringtone_player.stop()

    def play_notification(self, path: str):
        self.notification_player.setSource(QUrl.fromLocalFile(path))
        self.notification_output.setVolume(0.6)
        self.notification_player.play()

    def play_remote_audio(self, path: str):
        self.remote_audio_player.setSource(QUrl.fromLocalFile(path))
        self.remote_audio_output.setVolume(1.0)
        self.remote_audio_player.play()

    def start_microphone_stream(self, callback):
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

    def stop_output_stream(self):
        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()
            self.output_stream = None
            print("Аудиовыходной поток остановлен")