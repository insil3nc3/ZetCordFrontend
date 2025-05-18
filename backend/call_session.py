import asyncio
import numpy as np
import sounddevice as sd
from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription
from aiortc.contrib.media import MediaStreamError
from backend.microphone_stream import MicrophoneStreamTrack
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CallSession:
    def __init__(self, send_ice_callback, audio_manager, audio_device=None):
        self.pc = None
        self.send_ice_callback = send_ice_callback
        self.audio_manager = audio_manager
        self.audio_device = audio_device
        self.microphone = None
        self.remote_track = None
        self.receiver = None
        self.call_active = False
        self._initialize()

    def _initialize(self):
        try:
            self.pc = RTCPeerConnection()
            devices = sd.query_devices()
            logging.info("Доступные аудиоустройства:")
            for i, dev in enumerate(devices):
                logging.info(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")

            selected_device = self.audio_device if self.audio_device is not None else sd.default.device[0]
            if selected_device is None or selected_device >= len(devices):
                selected_device = next((i for i, d in enumerate(devices) if d['max_input_channels'] >= 1), None)
                if selected_device is None:
                    raise ValueError("Не найдено устройство с поддержкой входного звука")
            self.audio_device = selected_device
            if self.audio_device < 0 or self.audio_device >= len(devices):
                self.audio_device = sd.default.device[1]
            device_info = sd.query_devices(self.audio_device)
            logging.info(f"Выбрано устройство ввода: {device_info['name']} (индекс {self.audio_device})")
            channels = min(2, device_info['max_input_channels'])
            try:
                self.microphone = MicrophoneStreamTrack(device=self.audio_device, channels=channels, sample_rate=44100)
            except Exception as e:
                raise RuntimeError(f"Не удалось создать MicrophoneStreamTrack: {e}")

            existing_sender = None
            for sender in self.pc.getSenders():
                if sender.track:
                    existing_sender = sender
                    break
            if existing_sender:
                try:
                    asyncio.get_event_loop().run_until_complete(existing_sender.replaceTrack(self.microphone))
                    logging.info(f"📡 RTCRtpSender обновлен: track={self.microphone}, stream_id={existing_sender._stream_id}")
                except Exception as e:
                    logging.error(f"Ошибка при замене трека в _initialize: {type(e).__name__}: {e}")
                    sender = self.pc.addTrack(self.microphone)
                    logging.info(f"📡 RTCRtpSender добавлен вместо замены: track={sender.track}, stream_id={sender._stream_id}")
            else:
                sender = self.pc.addTrack(self.microphone)
                logging.info(f"📡 RTCRtpSender добавлен: track={sender.track}, stream_id={sender._stream_id}")
            self.pc.on("icecandidate", self.on_icecandidate)
            self.pc.on("track", self._handle_track)
            self.pc.on("connectionstatechange", self.on_connectionstatechange)
            self.pc.on("datachannel", lambda event: logging.info(f"Получен DataChannel: {event.channel.label}"))
            self.pc.on("iceconnectionstatechange", lambda: logging.info(f"ICE connection state: {self.pc.iceConnectionState}"))
            self.pc.on("signalingstatechange", lambda: logging.info(f"Signaling state: {self.pc.signalingState}"))
            logging.info("CallSession инициализирован")
        except Exception as e:
            logging.error(f"Ошибка при инициализации CallSession: {type(e).__name__}: {e}")
            asyncio.create_task(self.cleanup())
            raise

    def _handle_track(self, track):
        from backend.audio_manager import AudioReceiverTrack
        logging.info(f"Получен трек: {track.kind}, id={track.id}, readyState={track.readyState}")
        if track.kind == "audio":
            self.remote_track = track
            self.receiver = AudioReceiverTrack(track, self.audio_manager)
            self.call_active = True
            asyncio.create_task(self._start_receiver())

    async def _start_receiver(self):
        if self.receiver:
            try:
                # Получаем event loop явно
                loop = asyncio.get_event_loop()

                # Запускаем в отдельном потоке с помощью run_in_executor
                await loop.run_in_executor(
                    None,  # Используем стандартный executor
                    lambda: self.audio_manager.start_output_stream()
                )
                await self.receiver.receive_audio()
            except Exception as e:
                logging.error(f"Ошибка в _start_receiver: {e}")
                raise

    async def cleanup(self):
        logging.info(
            f"🧹 cleanup() вызван, call_active={self.call_active}, состояние={self.pc.connectionState if self.pc else 'нет соединения'}")

        try:
            # Получаем event loop
            loop = asyncio.get_event_loop()

            if self.receiver:
                # Останавливаем output stream через run_in_executor
                await loop.run_in_executor(
                    None,
                    lambda: self.audio_manager.stop_output_stream()
                )

            if self.microphone:
                logging.info("Остановка микрофона")
                self.microphone.stop()
                self.microphone = None

            if self.remote_track:
                logging.info("Остановка удаленного трека")
                try:
                    self.remote_track.stop()
                except Exception as e:
                    logging.error(f"Ошибка при остановке remote_track: {type(e).__name__}: {e}")
                self.remote_track = None

            if self.receiver:
                logging.info("Остановка AudioReceiverTrack")
                await self.receiver.stop()
                self.receiver = None

            if self.pc:
                logging.info("Закрытие RTCPeerConnection")
                try:
                    await self.pc.close()
                except Exception as e:
                    logging.error(f"Ошибка при закрытии RTCPeerConnection: {type(e).__name__}: {e}")
                self.pc = None

            # Останавливаем остальные компоненты audio_manager
            await loop.run_in_executor(
                None,
                lambda: (
                    self.audio_manager.stop_output_stream(),
                    self.audio_manager.stop_microphone_stream()
                )
            )

            logging.info("Соединение закрыто")
        except Exception as e:
            logging.error(f"Ошибка в cleanup: {e}")
            raise

    async def close_this(self):
        logging.info("Вызов CallSession.close")
        self.call_active = False
        await self.cleanup()

    def on_connectionstatechange(self):
        if self.pc:
            state = self.pc.connectionState
            logging.info(f"Состояние соединения: {state}")
            if state in ["failed", "closed"] and self.call_active:
                self.call_active = False
                asyncio.create_task(self.cleanup())

    async def create_offer(self):
        try:
            if not self.pc:
                raise RuntimeError("RTCPeerConnection не инициализирован или закрыт")
            if not self.microphone:
                raise RuntimeError("Микрофон не инициализирован")
            track_already_added = False
            for sender in self.pc.getSenders():
                if sender.track == self.microphone:
                    track_already_added = True
                    logging.info(f"📡 Трек уже добавлен в RTCRtpSender: track={self.microphone}, stream_id={sender._stream_id}")
                    break
            if not track_already_added:
                sender = self.pc.addTrack(self.microphone)
                logging.info(f"📡 RTCRtpSender добавлен в create_offer: track={sender.track}, stream_id={sender._stream_id}")
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            logging.info(f"Оффер создан: {offer.sdp[:100]}...")
            return self.pc.localDescription
        except Exception as e:
            logging.error(f"Ошибка при создании оффера: {type(e).__name__}: {e}")
            raise

    async def create_answer(self):
        try:
            if not self.pc:
                raise RuntimeError("RTCPeerConnection закрыт или не инициализирован")
            track_already_added = False
            for sender in self.pc.getSenders():
                if sender.track == self.microphone:
                    track_already_added = True
                    logging.info(f"📡 Трек уже добавлен в RTCRtpSender: track={self.microphone}, stream_id={sender._stream_id}")
                    break
            if not track_already_added:
                sender = self.pc.addTrack(self.microphone)
                logging.info(f"📡 RTCRtpSender добавлен в create_answer: track={sender.track}, stream_id={sender._stream_id}")
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            logging.info(f"Ответ создан: {answer.sdp[:100]}...")
            return self.pc.localDescription
        except Exception as e:
            logging.error(f"Ошибка при создания ответа: {type(e).__name__}: {e}")
            raise

    async def set_remote_description(self, desc):
        try:
            if isinstance(desc, dict):
                if "type" not in desc or "sdp" not in desc:
                    raise ValueError("Словарь SDP должен содержать ключи 'type' и 'sdp'")
                desc = RTCSessionDescription(sdp=desc["sdp"], type=desc["type"])
            logging.info(f"📥 Установка удаленного описания: type={desc.type}, sdp={desc.sdp[:100]}...")
            await self.pc.setRemoteDescription(desc)
            logging.info(f"✅ Установлено удаленное описание типа: {desc.type}")
        except Exception as e:
            logging.error(f"❌ Ошибка при установке удаленного описания: {type(e).__name__}: {e}")
            raise

    async def on_icecandidate(self, event):
        if event.candidate:
            await self.send_ice_callback({
                "type": "ice_candidate",
                "candidate": {
                    "candidate": event.candidate.candidate,
                    "sdpMid": event.candidate.sdpMid,
                    "sdpMLineIndex": event.candidate.sdpMLineIndex,
                }
            })
            logging.info(f"Отправлен ICE-кандидат: {event.candidate.candidate[:50]}...")

    async def add_ice_candidate(self, candidate):
        try:
            ice_candidate = RTCIceCandidate(
                candidate=candidate["candidate"],
                sdpMid=candidate["sdpMid"],
                sdpMLineIndex=candidate["sdpMLineIndex"]
            )
            await self.pc.addIceCandidate(ice_candidate)
            logging.info("Добавлен ICE-кандидат")
        except Exception as e:
            logging.error(f"Ошибка при добавлении ICE-кандидата: {type(e).__name__}: {e}")