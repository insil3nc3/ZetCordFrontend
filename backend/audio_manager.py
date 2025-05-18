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
            # Настройка формата аудио
            audio_format = QAudioFormat()
            audio_format.setSampleRate(self.sample_rate)
            audio_format.setChannelCount(self.output_channels)
            # Используем Float, fallback на Int16 при необходимости
            audio_format.setSampleFormat(QAudioFormat.Float)

            # Проверка поддержки формата устройством
            self.audio_output = QAudioOutput(audio_format)
            if not self.audio_output.isFormatSupported(audio_format):
                logging.warning("⚠ Формат Float не поддерживается, пробуем Int16")
                audio_format.setSampleFormat(QAudioFormat.Int16)
                self.audio_output = QAudioOutput(audio_format)
                if not self.audio_output.isFormatSupported(audio_format):
                    raise RuntimeError("Формат аудио не поддерживается устройством")

            self.audio_output.setVolume(1.0)
            self.audio_buffer = QBuffer()
            self.audio_buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            # Запускаем воспроизведение один раз
            self.audio_output.start(self.audio_buffer)
            logging.info("🔊 Аудиовыходной поток запущен через QAudioOutput")
        except Exception as e:
            logging.error(f"❌ Ошибка при запуске QAudioOutput: {type(e).__name__}: {e}")
            self.stop_output_stream()

    def play_audio_chunk(self, audio_chunk: np.ndarray):
        try:
            # Проверка входного формата
            if audio_chunk.size == 0:
                logging.debug("Пустой аудиофрейм, пропускаем")
                return
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            # Усиление сигнала (x10, с защитой от клиппинга)
            audio_chunk = np.clip(audio_chunk * 10.0, -1.0, 1.0)

            # Проверка формы массива
            if audio_chunk.ndim == 1:
                audio_chunk = np.repeat(audio_chunk[:, np.newaxis], self.output_channels, axis=1)
            elif audio_chunk.shape[1] != self.output_channels:
                audio_chunk = np.repeat(audio_chunk[:, :1], self.output_channels, axis=1)

            if self.audio_output and self.audio_output.state() in (QAudioOutput.State.Active, QAudioOutput.State.Idle):
                if not self.audio_buffer.isOpen():
                    self.audio_buffer.open(QIODevice.OpenModeFlag.ReadWrite)
                # Записываем данные в буфер
                audio_bytes = audio_chunk.tobytes()
                bytes_written = self.audio_buffer.write(audio_bytes)
                if bytes_written != len(audio_bytes):
                    logging.warning(f"⚠ Не все аудиоданные записаны: {bytes_written}/{len(audio_bytes)} байт")
                # Логируем только при первой записи или ошибке
                if self.audio_buffer.pos() < len(audio_bytes):
                    logging.info(f"Аудио отправлено в QAudioOutput: shape={audio_chunk.shape}")
            else:
                logging.warning("⚠ QAudioOutput не запущен или остановлен")
        except Exception as e:
            logging.error(f"❌ Ошибка при воспроизведении аудио: {type(e).__name__}: {e}")
            self.stop_output_stream()

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