from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudioFormat
from PyQt6.QtCore import QUrl, QBuffer, QIODevice
import sounddevice as sd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioManager:
    def __init__(self, sample_rate=48000, channels=2):
        self.sample_rate = sample_rate
        self.output_channels = channels
        self.input_stream = None
        self.audio_output = None
        self.audio_buffer = None
        self.ringtone_player = QMediaPlayer()
        self.ringtone_output = QAudioOutput()
        self.ringtone_player.setAudioOutput(self.ringtone_output)
        self.notification_player = QMediaPlayer()
        self.notification_output = QAudioOutput()
        self.notification_player.setAudioOutput(self.notification_output)

    def start_output_stream(self):
        if self.audio_output:
            logging.info("🔊 Аудиовыход уже запущен")
            return
        try:
            # Настройка формата аудио для QAudioOutput
            audio_format = QAudioFormat()
            audio_format.setSampleRate(self.sample_rate)
            audio_format.setChannelCount(self.output_channels)
            audio_format.setSampleFormat(QAudioFormat.SampleFormat.Float32)
            self.audio_output = QAudioOutput(audio_format)
            self.audio_output.setVolume(1.0)
            self.audio_buffer = QBuffer()
            self.audio_buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            logging.info("🔊 Аудиовыходной поток запущен через QAudioOutput")
        except Exception as e:
            logging.error(f"❌ Ошибка при запуске QAudioOutput: {type(e).__name__}: {e}")
            self.audio_output = None

    def play_audio_chunk(self, audio_chunk: np.ndarray):
        try:
            logging.debug(f"Воспроизведение аудио: shape={audio_chunk.shape}, dtype={audio_chunk.dtype}, max={np.max(np.abs(audio_chunk))}")
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            # Усиление сигнала (x20, с защитой от клиппинга)
            audio_chunk = np.clip(audio_chunk * 20.0, -1.0, 1.0)
            logging.debug(f"После усиления: max={np.max(np.abs(audio_chunk))}")
            # Проверка формы массива и преобразование в стерео
            if audio_chunk.ndim == 1:
                audio_chunk = np.repeat(audio_chunk[:, np.newaxis], self.output_channels, axis=1)
            elif audio_chunk.shape[1] != self.output_channels:
                audio_chunk = np.repeat(audio_chunk[:, :1], self.output_channels, axis=1)
            if self.audio_output and self.audio_output.state() != QAudioOutput.State.Stopped:
                # Конвертируем в байты для QAudioOutput
                audio_bytes = audio_chunk.tobytes()
                self.audio_buffer.write(audio_bytes)
                self.audio_output.start(self.audio_buffer)
                logging.debug(f"Аудио отправлено в QAudioOutput: shape={audio_chunk.shape}")
            else:
                logging.warning("⚠ QAudioOutput не запущен или остановлен")
        except Exception as e:
            logging.error(f"❌ Ошибка при воспроизведении аудио: {type(e).__name__}: {e}")

    def stop_output_stream(self):
        if self.audio_output:
            try:
                self.audio_output.stop()
                if self.audio_buffer:
                    self.audio_buffer.close()
                logging.info("🔇 Аудиовыходной поток остановлен")
            except Exception as e:
                logging.error(f"❌ Ошибка при остановке QAudioOutput: {type(e).__name__}: {e}")
            finally:
                self.audio_output = None
                self.audio_buffer = None

    def play_ringtone(self, path: str, loop: bool = True):
        try:
            self.ringtone_player.setSource(QUrl.fromLocalFile(path))
            self.ringtone_output.setVolume(0.8)
            self.ringtone_player.setLoops(-1 if loop else 1)
            self.ringtone_player.play()
            logging.info(f"📞 Воспроизведение рингтона: {path}")
        except Exception as e:
            logging.error(f"❌ Ошибка при воспроизведении рингтона: {type(e).__name__}: {e}")

    def stop_ringtone(self):
        try:
            self.ringtone_player.stop()
            logging.info("📴 Рингтон остановлен")
        except Exception as e:
            logging.error(f"❌ Ошибка при остановке рингтона: {type(e).__name__}: {e}")

    def play_notification(self, path: str):
        try:
            self.notification_player.setSource(QUrl.fromLocalFile(path))
            self.notification_output.setVolume(0.6)
            self.notification_player.play()
            logging.info(f"🔔 Воспроизведение уведомления: {path}")
        except Exception as e:
            logging.error(f"❌ Ошибка при воспроизведении уведомления: {type(e).__name__}: {e}")

    def start_microphone_stream(self, callback):
        try:
            devices = sd.query_devices()
            logging.info("Доступные аудиоустройства:")
            for i, dev in enumerate(devices):
                logging.info(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")
            # Используем устройство ввода по умолчанию
            device = sd.default.device[0]
            if device is None or device >= len(devices):
                raise RuntimeError("Не найдено устройство ввода по умолчанию")
            device_info = devices[device]
            if device_info['max_input_channels'] < 1:
                raise RuntimeError(f"Устройство {device_info['name']} не поддерживает входной звук")
            channels = min(2, device_info['max_input_channels'])
            sd.check_input_settings(
                device=device,
                samplerate=self.sample_rate,
                channels=channels,
                dtype='float32'
            )
            self.input_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=channels,
                blocksize=1024,
                callback=callback,
                device=device,
                dtype='float32'
            )
            self.input_stream.start()
            logging.info(f"🎙️ Микрофонный поток запущен: {device_info['name']} (каналы: {channels})")
        except Exception as e:
            logging.error(f"❌ Ошибка при запуске микрофона: {type(e).__name__}: {e}")
            self.stop_microphone_stream()

    def stop_microphone_stream(self):
        if self.input_stream:
            try:
                if self.input_stream.active:
                    self.input_stream.stop()
                self.input_stream.close()
                logging.info("🛑 Микрофонный поток остановлен")
            except Exception as e:
                logging.error(f"❌ Ошибка при остановке микрофона: {type(e).__name__}: {e}")
            finally:
                self.input_stream = None