import asyncio
from fractions import Fraction
import numpy as np
import sounddevice as sd
from aiortc import MediaStreamTrack
from av import AudioFrame

class MicrophoneStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, device=0, sample_rate=48000, channels=1, chunk=960):
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.buffer = asyncio.Queue()
        self._timestamp = 0
        self._running = True

        devices = sd.query_devices()
        print("Доступные аудиоустройства:")
        for i, dev in enumerate(devices):
            print(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")

        if device is None:
            device = 0
            print(f"Используется устройство fifine Microphone: USB Audio (индекс 0)")
        else:
            print(f"Используется устройство: {devices[device]['name']} (индекс {device})")

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
            print("Микрофонный поток запущен")
        except Exception as e:
            print(f"Ошибка при запуске микрофонного потока: {e}")
            raise

    def _callback(self, indata, frames, time_info, status):
        if not self._running:
            return
        if status:
            print(f"Audio input status: {status}")
        print(f"Микрофонные данные: shape={indata.shape}, dtype={indata.dtype}, max={np.max(np.abs(indata))}")
        self.buffer.put_nowait(indata.copy())

    async def recv(self):
        if not self._running:
            raise RuntimeError("Микрофонный поток остановлен")
        data = await self.buffer.get()
        print(f"Отправка аудиоданных: shape={data.shape}, dtype={data.dtype}, max={np.max(np.abs(data))}")

        frame = AudioFrame.from_ndarray(
            data.T if data.ndim > 1 else data.reshape(-1, 1),
            format='flt',
            layout='mono'
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
            print("Микрофонный поток остановлен")