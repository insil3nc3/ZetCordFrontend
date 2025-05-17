import asyncio
from fractions import Fraction
import numpy as np
import sounddevice as sd
from aiortc import MediaStreamTrack
from av import AudioFrame

class MicrophoneStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, device=0, sample_rate=48000, chunk=960):
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.buffer = asyncio.Queue()
        self._timestamp = 0
        self._running = True

        devices = sd.query_devices()
        print("Доступные аудиоустройства:")
        for i, dev in enumerate(devices):
            print(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")

        if device is None or device >= len(devices):
            print("⚠ Указано недопустимое устройство. Используется устройство по умолчанию (индекс 0)")
            device = 0

        input_channels = devices[device]['max_input_channels']
        if input_channels < 1:
            raise RuntimeError(f"Устройство {devices[device]['name']} не поддерживает входной звук")

        self.channels = min(2, input_channels)  # выбираем максимум 2 канала
        print(f"Используется устройство: {devices[device]['name']} (индекс {device}), channels={self.channels}")

        try:
            self.stream = sd.InputStream(
                device=device,
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.chunk,
                dtype='float32',
                callback=self._callback,
            )
            self.stream.start()
            print("✅ Микрофонный поток запущен")
        except Exception as e:
            print(f"❌ Ошибка при запуске микрофонного потока: {e}")
            raise

    def _callback(self, indata, frames, time_info, status):
        if not self._running:
            return
        if status:
            print(f"⚠ Audio input status: {status}")
        self.buffer.put_nowait(indata.copy())

    async def recv(self):
        if not self._running:
            raise RuntimeError("Микрофонный поток остановлен")
        data = await self.buffer.get()

        frame = AudioFrame.from_ndarray(
            data.T if data.ndim > 1 else data.reshape(-1, 1),
            format='flt',
            layout='mono' if self.channels == 1 else 'stereo'
        )
        frame.pts = self._timestamp
        frame.sample_rate = self.sample_rate
        frame.time_base = Fraction(1, self.sample_rate)
        self._timestamp += frame.samples
        return frame

    def stop(self):
        self._running = False
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop()
            self.stream.close()
            print("🛑 Микрофонный поток остановлен")
