from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
import os
import tempfile
import platform

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
        self.temp_wav_file = os.path.join(tempfile.gettempdir(), "zetcord_audio.wav")

    def start_output_stream(self):
        print("Подготовка воспроизведения через QMediaPlayer")

    def play_audio_chunk(self, audio_chunk: np.ndarray):
        try:
            print(f"Воспроизведение аудио: shape={audio_chunk.shape}, dtype={audio_chunk.dtype}, max={np.max(np.abs(audio_chunk))}")
            if audio_chunk.shape[1] != self.output_channels:
                audio_chunk = np.repeat(audio_chunk[:, :1], self.output_channels, axis=1)
            # Нормализация для WAV (int16)
            audio_chunk = (audio_chunk * 32767).astype(np.int16)
            wavfile.write(self.temp_wav_file, self.output_sample_rate, audio_chunk)
            self.remote_audio_player.setSource(QUrl.fromLocalFile(self.temp_wav_file))
            self.remote_audio_output.setVolume(1.0)
            self.remote_audio_player.play()
            print(f"Воспроизведен аудиофрагмент: {self.temp_wav_file}")
        except Exception as e:
            print(f"Ошибка при воспроизведении аудио: {e}")

    def stop_output_stream(self):
        self.remote_audio_player.stop()
        if os.path.exists(self.temp_wav_file):
            try:
                os.remove(self.temp_wav_file)
            except Exception as e:
                print(f"Ошибка при удалении временного файла: {e}")
        print("Аудиовыходной поток остановлен")

    def play_ringtone(self, path: str, loop: bool = True):
        try:
            self.ringtone_player.setSource(QUrl.fromLocalFile(path))
            self.ringtone_output.setVolume(0.8)
            self.ringtone_player.setLoops(-1 if loop else 1)
            self.ringtone_player.play()
            print(f"Воспроизведение рингтона: {path}")
        except Exception as e:
            print(f"Ошибка при воспроизведении рингтона: {e}")

    def stop_ringtone(self):
        try:
            self.ringtone_player.stop()
            print("Рингтон остановлен")
        except Exception as e:
            print(f"Ошибка при остановке рингтона: {e}")

    def play_notification(self, path: str):
        try:
            self.notification_player.setSource(QUrl.fromLocalFile(path))
            self.notification_output.setVolume(0.6)
            self.notification_player.play()
            print(f"Воспроизведение уведомления: {path}")
        except Exception as e:
            print(f"Ошибка при воспроизведении уведомления: {e}")

    def play_remote_audio(self, path: str):
        try:
            self.remote_audio_player.setSource(QUrl.fromLocalFile(path))
            self.remote_audio_output.setVolume(1.0)
            self.remote_audio_player.play()
            print(f"Воспроизведение удаленного аудио: {path}")
        except Exception as e:
            print(f"Ошибка при воспроизведении удаленного аудио: {e}")

    def start_microphone_stream(self, callback):
        try:
            devices = sd.query_devices()
            device = None
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0 and "fifine" in dev['name'].lower():
                    device = i
                    break
            if device is None:
                for i, dev in enumerate(devices):
                    if dev['max_input_channels'] > 0:
                        device = i
                        break
                else:
                    raise ValueError("Не найдено устройство ввода")
            channels = min(2, devices[device]['max_input_channels'])
            sd.default.device = device
            self.input_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=channels,
                blocksize=self.chunk_size,
                callback=callback,
                device=device
            )
            self.input_stream.start()
            print(f"Микрофонный поток запущен (AudioManager): {devices[device]['name']} (каналы: {channels})")
        except Exception as e:
            print(f"Ошибка при запуске микрофонного потока (AudioManager): {e}")
            self.stop_microphone_stream()

    def stop_microphone_stream(self):
        if self.input_stream:
            try:
                self.input_stream.stop()
                self.input_stream.close()
                print("Микрофонный поток остановлен (AudioManager)")
            except Exception as e:
                print(f"Ошибка при остановке микрофонного потока (AudioManager): {e}")
            finally:
                self.input_stream = None