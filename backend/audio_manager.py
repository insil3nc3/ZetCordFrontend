from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
import sounddevice as sd
import numpy as np

class AudioManager:
    def __init__(self, sample_rate=48000, channels=2):
        self.sample_rate = sample_rate
        self.output_channels = channels
        self.output_stream = None
        self.input_stream = None
        self.ringtone_player = QMediaPlayer()
        self.ringtone_output = QAudioOutput()
        self.ringtone_player.setAudioOutput(self.ringtone_output)
        self.notification_player = QMediaPlayer()
        self.notification_output = QAudioOutput()
        self.notification_player.setAudioOutput(self.notification_output)

    def start_output_stream(self):
        if self.output_stream:
            print("🔊 Аудиовыход уже запущен")
            return
        try:
            devices = sd.query_devices()
            print("Доступные аудиоустройства:")
            for i, dev in enumerate(devices):
                print(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")
            # Для Linux используем pulse (индекс 17), но проверяем доступность
            device = 17
            if device >= len(devices) or devices[device]['max_output_channels'] == 0:
                # Выбираем первое доступное устройство вывода
                device = next((i for i, d in enumerate(devices) if d['max_output_channels'] > 0), None)
                if device is None:
                    raise RuntimeError("Нет доступных устройств вывода")
            print(f"Выбрано устройство вывода: {devices[device]['name']} (индекс {device})")
            self.output_stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.output_channels,
                dtype='float32',
                blocksize=1024,
                device=device
            )
            self.output_stream.start()
            print(f"🔊 Аудиовыходной поток запущен: {devices[device]['name']} (каналы: {self.output_channels})")
        except Exception as e:
            print(f"❌ Ошибка при запуске OutputStream: {type(e).__name__}: {e}")
            self.output_stream = None

    def play_audio_chunk(self, audio_chunk: np.ndarray):
        try:
            print(f"Воспроизведение аудио: shape={audio_chunk.shape}, dtype={audio_chunk.dtype}, max={np.max(np.abs(audio_chunk))}")
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            # Усиление сигнала (x10, с защитой от клиппинга)
            audio_chunk = np.clip(audio_chunk * 10.0, -1.0, 1.0)
            # Проверка формы массива и преобразование в стерео, если необходимо
            if audio_chunk.ndim == 1:
                audio_chunk = np.repeat(audio_chunk[:, np.newaxis], self.output_channels, axis=1)
            elif audio_chunk.shape[1] != self.output_channels:
                audio_chunk = np.repeat(audio_chunk[:, :1], self.output_channels, axis=1)
            if self.output_stream and self.output_stream.active:
                self.output_stream.write(audio_chunk)
            else:
                print("⚠ OutputStream не запущен или неактивен")
        except Exception as e:
            print(f"❌ Ошибка при воспроизведении аудио: {type(e).__name__}: {e}")

    def stop_output_stream(self):
        if self.output_stream:
            try:
                self.output_stream.stop()
                self.output_stream.close()
                print("🔇 Аудиовыходной поток остановлен")
            except Exception as e:
                print(f"❌ Ошибка при остановке OutputStream: {type(e).__name__}: {e}")
            finally:
                self.output_stream = None

    def play_ringtone(self, path: str, loop: bool = True):
        try:
            self.ringtone_player.setSource(QUrl.fromLocalFile(path))
            self.ringtone_output.setVolume(0.8)
            self.ringtone_player.setLoops(-1 if loop else 1)
            self.ringtone_player.play()
            print(f"📞 Воспроизведение рингтона: {path}")
        except Exception as e:
            print(f"❌ Ошибка при воспроизведении рингтона: {type(e).__name__}: {e}")

    def stop_ringtone(self):
        try:
            self.ringtone_player.stop()
            print("📴 Рингтон остановлен")
        except Exception as e:
            print(f"❌ Ошибка при остановке рингтона: {type(e).__name__}: {e}")

    def play_notification(self, path: str):
        try:
            self.notification_player.setSource(QUrl.fromLocalFile(path))
            self.notification_output.setVolume(0.6)
            self.notification_player.play()
            print(f"🔔 Воспроизведение уведомления: {path}")
        except Exception as e:
            print(f"❌ Ошибка при воспроизведении уведомления: {type(e).__name__}: {e}")

    def start_microphone_stream(self, callback):
        try:
            devices = sd.query_devices()
            print("Доступные аудиоустройства:")
            for i, dev in enumerate(devices):
                print(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")
            device = next((i for i, d in enumerate(devices) if d['max_input_channels'] > 0), None)
            if device is None:
                raise RuntimeError("Не найдено устройство ввода")
            channels = min(2, devices[device]['max_input_channels'])
            self.input_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=channels,
                blocksize=1024,
                callback=callback,
                device=device,
                dtype='float32'
            )
            self.input_stream.start()
            print(f"🎙️ Микрофонный поток запущен: {devices[device]['name']} (каналы: {channels})")
        except Exception as e:
            print(f"❌ Ошибка при запуске микрофона: {type(e).__name__}: {e}")
            self.stop_microphone_stream()

    def stop_microphone_stream(self):
        if self.input_stream:
            try:
                self.input_stream.stop()
                self.input_stream.close_this()
                print("🛑 Микрофонный поток остановлен")
            except Exception as e:
                print(f"❌ Ошибка при остановке микрофона: {type(e).__name__}: {e}")
            finally:
                self.input_stream = None