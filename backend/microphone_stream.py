import asyncio
import numpy as np
import sounddevice as sd
from aiortc import MediaStreamTrack
from av import AudioFrame
import time


class MicrophoneStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, sample_rate=48000, channels=1, chunk=960):
        super().__init__()  # important!
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.chunk,
            dtype='int16',
            callback=self._callback,
        )
        self.buffer = asyncio.Queue()
        self.stream.start()

    def _callback(self, indata, frames, time_info, status):
        self.buffer.put_nowait(indata.copy())

    async def recv(self):
        data = await self.buffer.get()

        frame = AudioFrame.from_ndarray(data, format="s16", layout="mono")
        frame.pts = int(time.time() * self.sample_rate)
        frame.sample_rate = self.sample_rate
        return frame
