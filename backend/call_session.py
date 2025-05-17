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
            if self.audio_device is None:
                for i, dev in enumerate(devices):
                    if dev["max_input_channels"] >= 1:
                        self.audio_device = i
                        break
                else:
                    raise ValueError("Не найдено устройство ввода")
            print(f"Выбрано устройство ввода: {devices[self.audio_device]['name']} (индекс {self.audio_device})")
            device_info = sd.query_devices(self.audio_device)
            channels = min(2, device_info['max_input_channels'])
            self.microphone = MicrophoneStreamTrack(device=self.audio_device, channels=channels)

            self.pc.addTrack(self.microphone)
            self.pc.on("icecandidate", self.on_icecandidate)
            self.pc.on("track", self._handle_track)

            self.pc.on("connectionstatechange", self.on_connectionstatechange)
            self.pc.on("datachannel", lambda event: print(f"Получен DataChannel: {event.channel.label}"))
            self.pc.on("iceconnectionstatechange", lambda: print(f"ICE connection state: {self.pc.iceConnectionState}"))
            self.pc.on("signalingstatechange", lambda: print(f"Signaling state: {self.pc.signalingState}"))
            print("CallSession инициализирован")
        except Exception as e:
            print(f"Ошибка при инициализации CallSession: {e}")
            asyncio.create_task(self.cleanup())

    def _handle_track(self, track):
        print(f"Получен трек: {track.kind}, id={track.id}")
        if track.kind == "audio":
            self.remote_track = track
            self.call_active = True
            asyncio.create_task(self._receive_audio(track))  # ✅ запускаем асинхронно в фоне

    async def _receive_audio(self, track):
        try:
            self.audio_manager.start_output_stream()
            print("🔁 Начат приём аудиофреймов")

            # 🔒 Ждём, пока соединение реально установится
            while self.pc.connectionState != "connected":
                print(f"⏳ Ожидание соединения... (текущее: {self.pc.connectionState})")
                await asyncio.sleep(0.1)

            while self.call_active and self.pc and self.pc.connectionState == "connected":
                try:
                    frame = await track.recv()
                    audio_data = frame.to_ndarray(format="flt")
                    print(f"🎧 Получен фрейм: shape={audio_data.shape}, max={np.max(np.abs(audio_data))}")

                    # Приведение к stereo, если нужно
                    if audio_data.ndim == 1:
                        audio_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
                    elif audio_data.shape[1] == 1:
                        audio_data = np.repeat(audio_data, 2, axis=1)

                    self.audio_manager.play_audio_chunk(audio_data)
                except Exception as e:
                    print(f"❌ Ошибка при приёме аудио: {e}")
                    await asyncio.sleep(0.05)  # ⏳ Задержка, чтобы не зациклиться
        except Exception as e:
            print(f"❌ Ошибка в _receive_audio: {e}")
        finally:
            print("🛑 Завершена обработка аудиотрека")
            self.call_active = False

    async def cleanup(self):
        print(f"Cleanup вызван, call_active={self.call_active}")
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
                await self.pc.close()
            except Exception as e:
                print(f"Ошибка при закрытии RTCPeerConnection: {e}")
            self.pc = None
        self.audio_manager.stop_output_stream()
        self.call_active = False
        print("Соединение закрыто")

    async def close(self):
        print("Вызов CallSession.close")
        self.call_active = False
        await self.cleanup()

    async def on_connectionstatechange(self):
        if self.pc:
            print(f"Состояние соединения: {self.pc.connectionState}")
            if self.pc.connectionState in ["failed", "disconnected", "closed"]:
                self.call_active = False
                await self.cleanup()

    async def create_offer(self):
        try:
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            sdp = offer.sdp.replace("opus/48000/2", "opus/48000/1")
            offer.sdp = sdp
            print("Оффер создан")
            return self.pc.localDescription
        except Exception as e:
            print(f"Ошибка при создании оффера: {e}")
            raise

    async def create_answer(self):
        try:
            if not self.pc:
                raise RuntimeError("RTCPeerConnection закрыт или не инициализирован")
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            sdp = answer.sdp.replace("opus/48000/2", "opus/48000/1")
            answer.sdp = sdp
            print("Ответ создан")
            return self.pc.localDescription
        except Exception as e:
            print(f"Ошибка при создании ответа: {e}")
            raise

    async def set_remote_description(self, offer):
        try:
            desc = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
            await self.pc.setRemoteDescription(desc)
            print(f"Установлено удаленное описание типа: {offer['type']}")
        except Exception as e:
            print(f"Ошибка при установке удаленного описания: {e}")
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
            print(f"Ошибка при добавлении ICE-кандидата: {e}")