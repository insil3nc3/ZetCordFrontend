from PyQt6.QtCore import QObject, QEvent, QUrl, QBuffer, QIODevice, QCoreApplication
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
    def __init__(self, sample_rate=44100, channels=2, parent=None):
        super().__init__(parent)
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
        self._output_stopped_intentionally = False
        self._pending_audio_chunks = []

    def customEvent(self, event):
        if event.type() == InitializeAudioEvent.EventType:
            self._initialize_audio_output()

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

    def play_audio_chunk(self, audio_chunk: np.ndarray):
        try:
            if audio_chunk.size == 0:
                logging.debug("Пустой аудиофрейм, пропускаем")
                return

            if not self.audio_output or self.audio_output.state() not in (QAudio.State.ActiveState, QAudio.State.IdleState):
                logging.warning("⚠ QAudioSink не активен, добавляем в очередь")
                self._pending_audio_chunks.append(audio_chunk)
                QCoreApplication.postEvent(self, InitializeAudioEvent())
                return

            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            audio_chunk = np.clip(audio_chunk * 10.0, -1.0, 1.0)

            if audio_chunk.ndim == 1:
                audio_chunk = np.repeat(audio_chunk[:, np.newaxis], self.output_channels, axis=1)
            elif audio_chunk.shape[1] != self.output_channels:
                audio_chunk = np.repeat(audio_chunk[:, :1], self.output_channels, axis=1)

            logging.debug(f"Получен аудиофрейм: shape={audio_chunk.shape}, max={np.max(np.abs(audio_chunk))}")

            audio_bytes = audio_chunk.tobytes()
            if not self.audio_buffer.isOpen():
                self.audio_buffer.open(QIODevice.OpenModeFlag.ReadWrite)

            if self.audio_buffer.pos() > 10 * 1024 * 1024:
                logging.warning("⚠ Буфер переполнен, сбрасываем")
                self.audio_buffer.seek(0)

            bytes_written = self.audio_buffer.write(audio_bytes)
            if bytes_written != len(audio_bytes):
                logging.warning(f"⚠ Не все аудиоданные записаны: {bytes_written}/{len(audio_bytes)} байт")
            else:
                logging.debug(f"Аудио отправлено: {len(audio_bytes)} байт, буфер pos={self.audio_buffer.pos()}")
        except Exception as e:
            logging.error(f"❌ Ошибка при воспроизведении аудио: {type(e).__name__}: {e}")
            if not self._output_stopped_intentionally:
                self.stop_output_stream()

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

    def play_ringtone(self, path: str, loop: bool = True):
        try:
            self.ringtone_player.setSource(QUrl.fromLocalFile(path))
            self.ringtone_output.setVolume(0.8)
            self.ringtone_player.setLoops(-1 if loop else 1)
            self.ringtone_player.play()
            logging.info(f"📞 Воспроизведение рингтона: {path}, состояние: {self.ringtone_player.mediaStatus()}")
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
            logging.info(f"🔔 Воспроизведение уведомления: {path}, состояние: {self.notification_player.mediaStatus()}")
        except Exception as e:
            logging.error(f"❌ Ошибка при воспроизведении уведомления: {type(e).__name__}: {e}")

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