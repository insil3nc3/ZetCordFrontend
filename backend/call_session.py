import asyncio
import numpy as np
import sounddevice as sd
from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription
from backend.microphone_stream import MicrophoneStreamTrack

class CallSession:
    def __init__(self, send_ice_callback, audio_manager, audio_device=None):
        self.pc = None
        self.send_ice_callback = send_ice_callback
        self.audio_manager = audio_manager
        self.audio_device = audio_device
        self.microphone = None
        self.remote_track = None
        self.call_active = False
        self._initialize()

    def _initialize(self):
        try:
            self.pc = RTCPeerConnection()
            devices = sd.query_devices()
            print("Доступные аудиоустройства:")
            for i, dev in enumerate(devices):
                print(f"{i}: {dev['name']} (in:{dev['max_input_channels']} out:{dev['max_output_channels']})")

            # Выбираем устройство с входными каналами
            selected_device = None
            if self.audio_device is not None:
                device_info = sd.query_devices(self.audio_device)
                if device_info['max_input_channels'] >= 1:
                    selected_device = self.audio_device
                else:
                    print(f"Устройство с индексом {self.audio_device} не поддерживает входной звук")
            if selected_device is None:
                for i, dev in enumerate(devices):
                    if dev['max_input_channels'] >= 1:
                        selected_device = i
                        break
                else:
                    raise ValueError("Не найдено устройство с поддержкой входного звука")

            self.audio_device = selected_device
            device_info = sd.query_devices(self.audio_device)
            print(f"Выбрано устройство ввода: {device_info['name']} (индекс {self.audio_device})")
            channels = min(2, device_info['max_input_channels'])
            try:
                self.microphone = MicrophoneStreamTrack(device=self.audio_device, channels=channels)
            except Exception as e:
                raise RuntimeError(f"Не удалось создать MicrophoneStreamTrack: {e}")

            # Очищаем старые отправители перед добавлением нового трека
            for sender in self.pc.getSenders():
                if sender.track:
                    self.pc.removeTrack(sender)
            sender = self.pc.addTrack(self.microphone)
            print(f"📡 RTCRtpSender добавлен: track={sender.track}, stream_id={sender._stream_id}")
            self.pc.on("icecandidate", self.on_icecandidate)
            self.pc.on("track", self._handle_track)
            self.pc.on("connectionstatechange", self.on_connectionstatechange)
            self.pc.on("datachannel", lambda event: print(f"Получен DataChannel: {event.channel.label}"))
            self.pc.on("iceconnectionstatechange", lambda: print(f"ICE connection state: {self.pc.iceConnectionState}"))
            self.pc.on("signalingstatechange", lambda: print(f"Signaling state: {self.pc.signalingState}"))
            print("CallSession инициализирован")
        except Exception as e:
            print(f"Ошибка при инициализации CallSession: {type(e).__name__}: {e}")
            asyncio.create_task(self.cleanup())
            raise  # Прерываем инициализацию при любой ошибке

    def _handle_track(self, track):
        print(f"Получен трек: {track.kind}, id={track.id}")
        if track.kind == "audio":
            self.remote_track = track
            self.call_active = True
            asyncio.create_task(self._receive_audio(track))

    async def _receive_audio(self, track):
        try:
            self.audio_manager.start_output_stream()
            print("🔁 Начат приём аудиофреймов")
            timeout = 10
            elapsed = 0
            while self.pc.connectionState != "connected" and elapsed < timeout:
                print(f"⏳ Ожидание соединения... (текущее: {self.pc.connectionState})")
                await asyncio.sleep(0.1)
                elapsed += 0.1
            if self.pc.connectionState != "connected":
                raise RuntimeError(f"Не удалось установить соединение: {self.pc.connectionState}")
            print("✅ Соединение установлено")
            while self.call_active and self.pc and self.pc.connectionState == "connected":
                try:
                    frame = await track.recv()
                    audio_data = frame.to_ndarray(format="flt")
                    print(
                        f"🎧 Получен фрейм: shape={audio_data.shape}, dtype={audio_data.dtype}, max={np.max(np.abs(audio_data))}, samples={frame.samples}, sample_rate={frame.sample_rate}")
                    if audio_data.dtype != np.float32:
                        audio_data = audio_data.astype(np.float32)
                    if audio_data.ndim == 1:
                        audio_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
                    elif audio_data.shape[1] == 1:
                        audio_data = np.repeat(audio_data, 2, axis=1)
                    max_amplitude = np.max(np.abs(audio_data))
                    if max_amplitude > 1.0:
                        audio_data = audio_data / max_amplitude
                        print(f"Нормализация выполнена: новый max={np.max(np.abs(audio_data))}")
                    self.audio_manager.play_audio_chunk(audio_data)
                except Exception as e:
                    print(f"❌ Ошибка при приёме аудио: {type(e).__name__}: {e}")
                    if isinstance(e, (StopAsyncIteration, asyncio.CancelledError)):
                        print("Завершение цикла получения аудио")
                        break
                    await asyncio.sleep(0.05)
                    continue
        except Exception as e:
            print(f"❌ Критическая ошибка в _receive_audio: {type(e).__name__}: {e}")
        finally:
            print("🛑 Завершена обработка аудиотрека")
            if self.call_active:
                self.call_active = False
                await self.cleanup()

    async def cleanup(self):
        print(
            f"🧹 cleanup() вызван, call_active={self.call_active}, состояние={self.pc.connectionState if self.pc else 'нет соединения'}")
        if self.microphone:
            print("Остановка микрофона")
            self.microphone.stop()
            self.microphone = None
        if self.remote_track:
            print("Остановка удаленного трека")
            self.remote_track.stop()
            self.remote_track = None
        if self.pc:
            print("Закрытие RTCPeerConnection")
            try:
                for sender in self.pc.getSenders():
                    if sender.track:
                        self.pc.removeTrack(sender)
                await self.pc.close()
            except Exception as e:
                print(f"Ошибка при закрытии RTCPeerConnection: {type(e).__name__}: {e}")
            self.pc = None
        self.audio_manager.stop_output_stream()
        print("Соединение закрыто")

    async def close_this(self):
        print("Вызов CallSession.close")
        self.call_active = False
        await self.cleanup()

    def on_connectionstatechange(self):
        if self.pc:
            state = self.pc.connectionState
            print(f"Состояние соединения: {state}")
            if state in ["failed", "closed"] and self.call_active:
                self.call_active = False
                asyncio.create_task(self.cleanup())

    async def create_offer(self):
        try:
            if not self.pc:
                raise RuntimeError("RTCPeerConnection не инициализирован или закрыт")
            if not self.microphone:
                raise RuntimeError("Микрофон не инициализирован")
            for sender in self.pc.getSenders():
                if sender.track:
                    self.pc.removeTrack(sender)
            if not any(sender.track == self.microphone for sender in self.pc.getSenders()):
                sender = self.pc.addTrack(self.microphone)
                print(f"📡 RTCRtpSender добавлен в create_offer: track={sender.track}, stream_id={sender._stream_id}")
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            print("Оффер создан")
            return self.pc.localDescription
        except Exception as e:
            print(f"Ошибка при создании оффера: {type(e).__name__}: {e}")
            raise

    async def create_answer(self):
        try:
            if not self.pc:
                raise RuntimeError("RTCPeerConnection закрыт или не инициализирован")
            for sender in self.pc.getSenders():
                if sender.track:
                    self.pc.removeTrack(sender)
            if not any(sender.track == self.microphone for sender in self.pc.getSenders()):
                sender = self.pc.addTrack(self.microphone)
                print(f"📡 RTCRtpSender добавлен в create_answer: track={sender.track}, stream_id={sender._stream_id}")
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            print("Ответ создан")
            return self.pc.localDescription
        except Exception as e:
            print(f"Ошибка при создании ответа: {type(e).__name__}: {e}")
            raise

    async def set_remote_description(self, desc):
        try:
            if isinstance(desc, dict):
                if "type" not in desc or "sdp" not in desc:
                    raise ValueError("Словарь SDP должен содержать ключи 'type' и 'sdp'")
                desc = RTCSessionDescription(sdp=desc["sdp"], type=desc["type"])
            print(f"📥 Установка удаленного описания: type={desc.type}, sdp={desc.sdp[:100]}...")
            await self.pc.setRemoteDescription(desc)
            print(f"✅ Установлено удаленное описание типа: {desc.type}")
        except Exception as e:
            print(f"❌ Ошибка при установке удаленного описания: {type(e).__name__}: {e}")
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
            print(f"Отправлен ICE-кандидат: {event.candidate.candidate[:50]}...")

    async def add_ice_candidate(self, candidate):
        try:
            ice_candidate = RTCIceCandidate(
                candidate=candidate["candidate"],
                sdpMid=candidate["sdpMid"],
                sdpMLineIndex=candidate["sdpMLineIndex"]
            )
            await self.pc.addIceCandidate(ice_candidate)
            print("Добавлен ICE-кандидат")
        except Exception as e:
            print(f"Ошибка при добавлении ICE-кандидата: {type(e).__name__}: {e}")