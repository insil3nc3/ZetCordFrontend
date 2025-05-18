import av
from aiortc.codecs.opus import OpusEncoder


class SafeOpusEncoder(OpusEncoder):
    def __init__(self):
        super().__init__()
        # Устанавливаем правильную кодировку для аудио
        self.resampler = av.AudioResampler(
            format='s16',
            layout='mono',
            rate=48000
        )

    def encode(self, frame, force_keyframe=False):
        try:
            # Преобразуем данные в bytes, если это необходимо
            if isinstance(frame, str):
                frame = frame.encode('utf-8')
            return super().encode(frame, force_keyframe)
        except UnicodeError:
            # Возвращаем пустой фрейм в случае ошибки
            return [], frame.pts


# Патчим оригинальный кодек
from aiortc import codecs

codecs.opus.OpusEncoder = SafeOpusEncoder