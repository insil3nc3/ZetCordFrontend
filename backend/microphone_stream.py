import sounddevice as sd
from aiortc import MediaStreamTrack
import time
import fractions
import numpy as np
import asyncio
import logging
import threading
from av import AudioFrame

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AudioStreamTrack(MediaStreamTrack):
    """Трек для отправки аудио с микрофона"""
    kind = "audio"

    def __init__(self, sample_rate=48000, channels=1, frame_size=960):
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_size = frame_size  # Размер фрейма в сэмплах

        # Временные метки
        self._start = time.time()
        self._pts = 0
        self._time_base = fractions.Fraction(1, sample_rate)

        # Инициализация микрофона
        self.stream = None
        self._init_microphone()

        # Буфер для накопления аудиоданных (используем threading.Lock вместо asyncio.Lock)
        self._buffer = np.array([], dtype=np.float32)
        self._buffer_lock = threading.Lock()

    def _init_microphone(self):
        """Инициализация микрофона"""
        try:
            # Проверяем доступные устройства
            devices = sd.query_devices()
            logging.info("🎙️ Доступные аудиоустройства:")
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    logging.info(f"  {i}: {dev['name']} (входных каналов: {dev['max_input_channels']})")

            # Используем устройство по умолчанию
            device = sd.default.device[0]  # Устройство ввода по умолчанию

            if device is None:
                raise RuntimeError("Не найдено устройство ввода по умолчанию")

            device_info = devices[device]
            if device_info['max_input_channels'] < 1:
                raise RuntimeError(f"Устройство {device_info['name']} не поддерживает входной звук")

            # Проверяем поддержку формата
            sd.check_input_settings(
                device=device,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32'
            )

            # Создаем поток
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.frame_size,
                callback=self._audio_callback,
                device=device,
                dtype='float32'
            )

            self.stream.start()
            logging.info(f"🎙️ Микрофон запущен: {device_info['name']} ({self.sample_rate}Hz, {self.channels} каналов)")

        except Exception as e:
            logging.error(f"❌ Ошибка при инициализации микрофона: {e}")
            self.stream = None
            raise

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback для получения аудиоданных с микрофона"""
        if status:
            logging.warning(f"⚠️ Статус аудио: {status}")

        try:
            # Конвертируем в одномерный массив
            audio_data = indata.flatten().copy()

            # Добавляем в буфер синхронно (используем threading.Lock)
            self._add_to_buffer_sync(audio_data)

        except Exception as e:
            logging.error(f"❌ Ошибка в audio_callback: {e}")

    def _add_to_buffer_sync(self, audio_data):
        """Синхронное добавление данных в буфер"""
        with self._buffer_lock:
            self._buffer = np.concatenate([self._buffer, audio_data])

    async def recv(self):
        """Получение следующего аудиофрейма"""
        try:
            # Ждем накопления достаточного количества данных
            while True:
                with self._buffer_lock:
                    if len(self._buffer) >= self.frame_size:
                        # Извлекаем фрейм из буфера
                        frame_data = self._buffer[:self.frame_size].copy()
                        self._buffer = self._buffer[self.frame_size:]
                        break

                await asyncio.sleep(0.001)  # Маленькая пауза

            # Применяем простое шумоподавление
            frame_data = self._apply_noise_gate(frame_data)

            # Нормализация громкости
            frame_data = self._normalize_audio(frame_data)

            # Конвертируем в int16 для WebRTC
            frame_data_int16 = (frame_data * 32767).astype(np.int16)

            # Создаем AudioFrame
            frame = AudioFrame(format="s16", layout="mono", samples=self.frame_size)
            frame.planes[0].update(frame_data_int16.tobytes())
            frame.sample_rate = self.sample_rate

            # Устанавливаем временные метки
            frame.pts = self._pts
            frame.time_base = self._time_base
            self._pts += self.frame_size

            return frame

        except Exception as e:
            logging.error(f"❌ Ошибка в recv(): {e}")
            # Возвращаем тишину в случае ошибки
            return self._create_silence_frame()

    def _apply_noise_gate(self, audio_data, threshold=0.01):
        """Простое шумоподавление"""
        rms = np.sqrt(np.mean(audio_data ** 2))
        if rms < threshold:
            return audio_data * 0.1  # Сильно приглушаем тихие звуки
        return audio_data

    def _normalize_audio(self, audio_data, target_level=0.3):
        """Нормализация громкости"""
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 0:
            # Нормализуем до целевого уровня
            audio_data = audio_data * (target_level / max_amplitude)
        return np.clip(audio_data, -1.0, 1.0)

    def _create_silence_frame(self):
        """Создание фрейма тишины"""
        silence_data = np.zeros(self.frame_size, dtype=np.int16)

        frame = AudioFrame(format="s16", layout="mono", samples=self.frame_size)
        frame.planes[0].update(silence_data.tobytes())
        frame.sample_rate = self.sample_rate

        frame.pts = self._pts
        frame.time_base = self._time_base
        self._pts += self.frame_size

        return frame

    def stop(self):
        """Остановка микрофона"""
        if self.stream:
            try:
                if self.stream.active:
                    self.stream.stop()
                self.stream.close()
                print("🛑 Микрофон остановлен")
            except Exception as e:
                print(f"❌ Ошибка при остановке микрофона: {e}")
            finally:
                self.stream = None