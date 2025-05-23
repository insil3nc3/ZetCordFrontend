import asyncio
import traceback
from fractions import Fraction
import numpy as np
import sounddevice as sd
from aiortc import MediaStreamTrack
from av import AudioFrame
import logging
import faulthandler
faulthandler.enable()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MicrophoneStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, device=None, sample_rate=44100, chunk=960, channels=None):
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.buffer = asyncio.Queue()
        self._timestamp = 0
        self._running = True

        devices = sd.query_devices()
        logging.info("Доступные аудиоустройства:")
        for i, dev in enumerate(devices):
            logging.info(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")

        device = device if device is not None else sd.default.device[0]
        if device is None or device >= len(devices):
            logging.warning("⚠ Указано недопустимое устройство. Используется устройство по умолчанию")
            device = sd.default.device[0]

        device_info = devices[device]
        input_channels = device_info['max_input_channels']
        if input_channels < 1:
            raise RuntimeError(f"Устройство {device_info['name']} не поддерживает входной звук")

        self.channels = channels if channels else min(2, input_channels)
        logging.info(
            f"Используется устройство: {device_info['name']} (индекс {device}), channels={self.channels}, default_samplerate={device_info['default_samplerate']}")

        try:
            sd.check_input_settings(
                device=device,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32'
            )
            self.stream = sd.InputStream(
                device=device,
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.chunk,
                dtype='float32',
                callback=self._callback,
            )
            self.stream.start()
            logging.info("✅ Микрофонный поток запущен")
        except Exception as e:
            logging.error(f"❌ Ошибка при запуске микрофонного потока: {type(e).__name__}: {e}")
            raise

    def _callback(self, indata, frames, time, status):
        if status:
            logging.warning(f"🎤 callback: status={status}")
        logging.debug(
            f"🎤 callback: indata.shape={indata.shape}, frames={frames}, max={np.max(np.abs(indata))}, status={status}, C_CONTIGUOUS={indata.flags['C_CONTIGUOUS']}")
        if self._running:
            self.buffer.put_nowait(indata.copy())

    async def recv(self):
        try:
            print(">> recv() called")

            if not self._running or not self.stream.active:
                raise RuntimeError("Микрофонный поток остановлен или неактивен")

            # Получаем данные
            try:
                data = await asyncio.wait_for(self.buffer.get(), timeout=1.0)
            except asyncio.TimeoutError:
                logging.warning("⚠️ recv() timeout: no data in buffer")
                data = np.zeros((1, self.chunk), dtype=np.int16)

            # Если float32, приводим в диапазон -1..1
            if data.dtype == np.float32:
                data = np.clip(data, -1.0, 1.0)

            # Моно
            if data.ndim > 1:
                data = np.mean(data, axis=1)  # стерео → моно

            # Усиление и перевод в int16
            data = np.clip(data * 32768.0, -32768, 32767).astype(np.int16)
            data = np.ascontiguousarray(data.reshape(1, -1))

            # Создаем безопасный аудиофрейм
            frame = AudioFrame.from_ndarray(data, format='s16', layout='mono')
            frame.pts = self._timestamp
            frame.time_base = Fraction(1, self.sample_rate)
            self._timestamp += frame.samples

            # 🛡️ Обязательно очищаем metadata
            frame.metadata.clear()

            return frame

        except Exception as e:
            logging.error(f"recv() error: {e}", exc_info=True)
            silent = np.zeros((1, self.chunk), dtype=np.int16)
            frame = AudioFrame.from_ndarray(silent, format='s16', layout='mono')
            frame.pts = self._timestamp
            frame.time_base = Fraction(1, self.sample_rate)
            self._timestamp += frame.samples
            return frame


    def stop(self):
        logging.info("🛑 Вызов stop() из: %s", ''.join(traceback.format_stack()[:-1]))
        self._running = False
        if hasattr(self, 'stream') and self.stream:
            if self.stream.active:
                self.stream.stop()
            self.stream.close()
            logging.info("🛑 Микрофонный поток остановлен")