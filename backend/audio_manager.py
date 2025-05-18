from PyQt6.QtCore import QObject, QEvent, QUrl, QBuffer, QIODevice, QCoreApplication, QThread, QMetaObject, Qt, \
    pyqtSignal, pyqtSlot
from PyQt6.QtMultimedia import QMediaPlayer, QAudioSink, QAudioFormat, QAudio, QAudioOutput, QMediaDevices
import sounddevice as sd
import numpy as np
import logging
from scipy import signal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class InitializeAudioEvent(QEvent):
    EventType = QEvent.Type(QEvent.registerEventType())

    def __init__(self):
        super().__init__(self.EventType)


class AudioManager(QObject):
    # Правильное объявление сигналов (на уровне класса)
    play_ringtone_signal = pyqtSignal(str, bool)
    play_notification_signal = pyqtSignal(str)
    play_audio_chunk_signal = pyqtSignal(np.ndarray)
    init_signal = pyqtSignal()  # Добавлен сигнал для инициализации

    def __init__(self, sample_rate=44100, channels=2, parent=None):
        super().__init__(parent)

        if not QCoreApplication.instance():
            raise RuntimeError("QApplication must be created before AudioManager")

        self.moveToThread(QCoreApplication.instance().thread())

        self.sample_rate = sample_rate
        self.output_channels = channels
        self.input_stream = None
        self.audio_output = None
        self.audio_buffer = None

        # Подключаем сигналы (должно быть после super().__init__())
        self.init_signal.connect(self._init_media_players)
        self.play_ringtone_signal.connect(self._play_ringtone)
        self.play_notification_signal.connect(self._play_notification)
        self.play_audio_chunk_signal.connect(self._play_audio_chunk_handler)

        # Запускаем инициализацию через сигнал
        self.init_signal.emit()

        self._output_stopped_intentionally = False
        self._pending_audio_chunks = []

    @pyqtSlot()
    def _init_media_players(self):
        """Инициализация медиа-плееров"""
        try:
            self.ringtone_player = QMediaPlayer()
            self.ringtone_output = QAudioOutput()
            self.ringtone_player.setAudioOutput(self.ringtone_output)

            self.notification_player = QMediaPlayer()
            self.notification_output = QAudioOutput()
            self.notification_player.setAudioOutput(self.notification_output)
            logging.info("Медиа-плееры инициализированы")
        except Exception as e:
            logging.error(f"Ошибка инициализации медиа-плееров: {e}")

    # Все методы ниже автоматически будут вызываться в главном потоке

    def customEvent(self, event):
        if event.type() == InitializeAudioEvent.EventType:
            self._initialize_audio_output()

    def _play_ringtone(self, path: str, loop: bool):
        try:
            self.ringtone_player.setSource(QUrl.fromLocalFile(path))
            self.ringtone_output.setVolume(0.8)
            self.ringtone_player.setLoops(-1 if loop else 1)
            self.ringtone_player.play()
        except Exception as e:
            logging.error(f"Ошибка рингтона: {e}")

    def play_ringtone(self, path: str, loop: bool = True):
        """Потокобезопасная версия"""
        self.play_ringtone_signal.emit(path, loop)

    def _play_notification(self, path: str):
        try:
            self.notification_player.setSource(QUrl.fromLocalFile(path))
            self.notification_output.setVolume(0.6)
            self.notification_player.play()
        except Exception as e:
            logging.error(f"Ошибка уведомления: {e}")

    def play_notification(self, path: str):
        """Потокобезопасная версия"""
        self.play_notification_signal.emit(path)

    def _play_audio_chunk_handler(self, audio_chunk: np.ndarray):
        """Обработчик аудио-чанков в главном потоке"""
        try:
            if not self.audio_output or self.audio_output.state() not in (
            QAudio.State.ActiveState, QAudio.State.IdleState):
                self._pending_audio_chunks.append(audio_chunk)
                QCoreApplication.postEvent(self, InitializeAudioEvent())
                return

            # Остальная логика обработки аудио...
            audio_bytes = audio_chunk.tobytes()
            self.audio_buffer.write(audio_bytes)
        except Exception as e:
            logging.error(f"Ошибка воспроизведения: {e}")

    def play_audio_chunk(self, audio_chunk: np.ndarray):
        """Потокобезопасная версия"""
        self.play_audio_chunk_signal.emit(audio_chunk.copy())


    def _initialize_audio_output(self, audio_format=None):
        """Initialize or reinitialize QAudioSink with a given format."""
        try:
            if self.audio_output and self.audio_output.state() in (QAudio.State.ActiveState, QAudio.State.IdleState):
                return True

            self.stop_output_stream()

            if audio_format is None:
                audio_format = QAudioFormat()
                audio_format.setSampleRate(self.sample_rate)
                audio_format.setChannelCount(self.output_channels)
                audio_format.setSampleFormat(QAudioFormat.SampleFormat.Float)

            formats_to_try = [
                audio_format,
                QAudioFormat(audio_format),
                QAudioFormat(audio_format),
            ]
            formats_to_try[1].setSampleFormat(QAudioFormat.SampleFormat.Int16)
            formats_to_try[2].setSampleRate(44100)
            formats_to_try[2].setSampleFormat(QAudioFormat.SampleFormat.Int16)

            for fmt in formats_to_try:
                logging.info(f"Попытка формата: {fmt.sampleRate()}Hz, {fmt.channelCount()} каналов, {fmt.sampleFormat()}")
                self.audio_output = QAudioSink(QMediaDevices.defaultAudioOutput(), fmt)
                if self.audio_output.format().sampleFormat() in (
                    QAudioFormat.SampleFormat.UInt8,
                    QAudioFormat.SampleFormat.Int16,
                    QAudioFormat.SampleFormat.Int32,
                    QAudioFormat.SampleFormat.Float
                ):
                    logging.info(f"Формат принят: {self.audio_output.format().sampleRate()}Hz, {self.audio_output.format().sampleFormat()}")
                    break
            else:
                self.audio_output = QAudioSink(QMediaDevices.defaultAudioOutput())
                fmt = self.audio_output.format()
                logging.info(f"Используется формат устройства: {fmt.sampleRate()}Hz, {fmt.channelCount()} каналов, {fmt.sampleFormat()}")

            self.audio_output.setVolume(1.0)
            self.audio_output.setBufferSize(1024 * 16)
            self.audio_buffer = QBuffer()
            self.audio_buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            self.audio_output.start(self.audio_buffer)
            logging.info(f"🔊 Аудиовыходной поток запущен: {fmt.sampleRate()}Hz, {fmt.channelCount()} каналов, {fmt.sampleFormat()}")
            self._output_stopped_intentionally = False

            self._process_pending_chunks()
            return True
        except Exception as e:
            logging.error(f"❌ Ошибка при инициализации QAudioSink: {type(e).__name__}: {e}")
            self.stop_output_stream()
            return False

    def _process_pending_chunks(self):
        while self._pending_audio_chunks:
            chunk = self._pending_audio_chunks.pop(0)
            self.play_audio_chunk(chunk)

    def start_output_stream(self):
        if self.audio_output and self.audio_output.state() in (QAudio.State.ActiveState, QAudio.State.IdleState):
            logging.info("🔊 Аудиовыход уже запущен")
            return
        QCoreApplication.postEvent(self, InitializeAudioEvent())


    def stop_output_stream(self):
        if self.audio_output:
            try:
                self.audio_output.stop()
                if self.audio_buffer:
                    self.audio_buffer.close()
                logging.info("🔇 Аудиовыходной поток остановлен")
            except Exception as e:
                logging.error(f"❌ Ошибка при остановке QAudioSink: {type(e).__name__}: {e}")
            finally:
                self.audio_output = None
                self.audio_buffer = None
                self._output_stopped_intentionally = True
                self._pending_audio_chunks.clear()


    def stop_ringtone(self):
        try:
            self.ringtone_player.stop()
            logging.info("📴 Рингтон остановлен")
        except Exception as e:
            logging.error(f"❌ Ошибка при остановке рингтона: {type(e).__name__}: {e}")


    def start_microphone_stream(self, callback):
        try:
            devices = sd.query_devices()
            logging.info("Доступные аудиоустройства:")
            for i, dev in enumerate(devices):
                logging.info(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")
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
                dtype='float32',
                extra_settings={
                    'encoding': 'latin1',
                    'dtype_unicode': 'float32'
                }
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

class AudioReceiverTrack:
    def __init__(self, track, audio_manager):
        self.track = track
        self.audio_manager = audio_manager
        self.running = True

    async def receive_audio(self):
        try:
            self.audio_manager.start_output_stream()
            logging.info("🔁 Начат приём аудиофреймов через AudioReceiverTrack")

            while self.running and self.track.readyState == "live":
                frame = await self.track.recv()
                audio_data = frame.to_ndarray().astype(np.float32) / 32768.0
                audio_data = np.clip(audio_data * 20.0, -1.0, 1.0)

                if frame.sample_rate != self.audio_manager.sample_rate:
                    logging.debug(f"Ресэмплинг: {frame.sample_rate}Hz -> {self.audio_manager.sample_rate}Hz")
                    num_samples = int(len(audio_data) * self.audio_manager.sample_rate / frame.sample_rate)
                    audio_data = signal.resample(audio_data, num_samples)

                if audio_data.ndim == 1:
                    audio_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
                elif audio_data.shape[1] == 1:
                    audio_data = np.repeat(audio_data, 2, axis=1)

                max_amplitude = np.max(np.abs(audio_data))
                if max_amplitude > 1.0:
                    audio_data = audio_data / max_amplitude

                self.audio_manager.play_audio_chunk(audio_data)

        except Exception as e:
            logging.error(f"❌ Ошибка в AudioReceiverTrack: {e}")
        finally:
            self.audio_manager.stop_output_stream()

    async def stop(self):
        self.running = False