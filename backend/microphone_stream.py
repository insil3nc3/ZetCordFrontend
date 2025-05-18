import asyncio
import traceback
from fractions import Fraction
import numpy as np
import sounddevice as sd
from aiortc import MediaStreamTrack
from av import AudioFrame
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MicrophoneStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, device=None, sample_rate=48000, chunk=960, channels=None):
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

        # Используем устройство ввода по умолчанию
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
            if not self._running or not self.stream.active:
                raise RuntimeError("Микрофонный поток остановлен или неактивен")
            data = await self.buffer.get()
            logging.debug(
                f"🎙️ recv(): shape={data.shape}, max={np.max(np.abs(data))}, running={self._running}, C_CONTIGUOUS={data.flags['C_CONTIGUOUS']}")
            # Преобразование стерео в моно
            if data.ndim > 1 and data.shape[1] == 2:
                data = np.mean(data, axis=1)
            elif data.ndim > 1:
                data = data[:, 0]
            # Усиление сигнала (x20, с защитой от клиппинга)
            data = np.clip(data * 20.0, -1.0, 1.0)
            logging.debug(f"🎙️ После усиления: max={np.max(np.abs(data))}")
            # Преобразуем float32 в int16
            data = np.clip(data * 32768, -32768, 32767).astype(np.int16)
            data = np.ascontiguousarray(data.reshape(1, -1), dtype=np.int16)
            logging.debug(
                f"🎙️ После обработки: shape={data.shape}, C_CONTIGUOUS={data.flags['C_CONTIGUOUS']}, dtype={data.dtype}")

            try:
                frame = AudioFrame.from_ndarray(
                    data,
                    format='s16',
                    layout='mono'
                )
            except Exception as e:
                logging.error(f"❌ Ошибка в AudioFrame: {type(e).__name__}: {e}")
                raise

            frame.pts = self._timestamp
            frame.sample_rate = self.sample_rate
            frame.time_base = Fraction(1, self.sample_rate)
            self._timestamp += frame.samples
            logging.debug(
                f"🎙️ Возвращен фрейм: samples={frame.samples}, layout={frame.layout}, sample_rate={frame.sample_rate}, format={frame.format.name}")
            return frame
        except Exception as e:
            logging.error(f"❌ Ошибка в MicrophoneStreamTrack.recv: {type(e).__name__}: {e}")
            frame = AudioFrame.from_ndarray(
                np.ascontiguousarray(np.zeros((1, self.sample_rate // 100), dtype=np.int16)),
                format='s16',
                layout='mono'
            )
            frame.pts = self._timestamp
            frame.sample_rate = self.sample_rate
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