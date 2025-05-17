import asyncio
import numpy as np
from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription
from backend.microphone_stream import MicrophoneStreamTrack

class CallSession:
    def __init__(self, send_ice_callback, audio_manager, audio_device=None):
        self.pc = RTCPeerConnection()
        self.send_ice_callback = send_ice_callback
        self.audio_manager = audio_manager
        self.audio_device = audio_device
        self.microphone = None
        self.remote_track = None
        self.call_active = False
        self._initialize()

    def _initialize(self):
        self.microphone = MicrophoneStreamTrack(device=self.audio_device)
        self.pc.addTrack(self.microphone)
        self.pc.on("icecandidate", self.on_icecandidate)
        self.pc.on("track", self.on_track)
        self.pc.on("connectionstatechange", self.on_connectionstatechange)
        self.pc.on("datachannel", lambda event: print(f"Получен DataChannel: {event.channel.label}"))
        self.pc.on("iceconnectionstatechange", lambda: print(f"ICE connection state: {self.pc.iceConnectionState}"))
        self.pc.on("signalingstatechange", lambda: print(f"Signaling state: {self.pc.signalingState}"))
        print("CallSession инициализирован")

    async def on_track(self, track):
        print(f"Получен трек: {track.kind}, id={track.id}, enabled={track.enabled}")
        if track.kind == "audio":
            self.remote_track = track
            self.call_active = True  # Устанавливаем явно
            self.audio_manager.start_output_stream()
            try:
                while self.call_active and self.pc.connectionState == "connected":
                    try:
                        print("Ожидание AudioFrame...")
                        frame = await track.recv()
                        print(f"Получен AudioFrame: samples={frame.samples}, sample_rate={frame.sample_rate}, format={frame.format}, layout={frame.layout}")
                        audio_data = frame.to_ndarray(format="flt")
                        print(f"Получены аудиоданные: shape={audio_data.shape}, dtype={audio_data.dtype}, max={np.max(np.abs(audio_data))}")
                        # Приведение к стерео
                        if audio_data.ndim == 1:
                            audio_data = np.repeat(audio_data.reshape(-1, 1), 2, axis=1)
                        elif audio_data.shape[1] == 1:
                            audio_data = np.repeat(audio_data, 2, axis=1)
                        max_amplitude = np.max(np.abs(audio_data))
                        if max_amplitude > 1.0:
                            audio_data = audio_data / max_amplitude
                            print(f"Нормализация выполнена: новый max={np.max(np.abs(audio_data))}")
                        self.audio_manager.play_audio_chunk(audio_data)
                    except Exception as e:
                        print(f"Ошибка при получении AudioFrame: {e}")
                        continue
            except Exception as e:
                print(f"Критическая ошибка в on_track: {e}")
            finally:
                print("Завершение обработки трека")
                await self.cleanup()

    async def cleanup(self):
        print(f"Cleanup вызван, call_active={self.call_active}")
        if self.microphone:
            print("Остановка микрофона")
            self.microphone.stop()
        if self.remote_track:
            print("Остановка удаленного трека")
            self.remote_track.stop()
        if self.pc:
            print("Закрытие RTCPeerConnection")
            await self.pc.close()
        self.audio_manager.stop_output_stream()
        self.call_active = False
        print("Соединение закрыто")

    async def close(self):
        print("Вызов CallSession.close")
        self.call_active = False
        if self.remote_track:
            print("Остановка удаленного трека")
            self.remote_track.stop()
        if self.microphone:
            print("Остановка микрофона")
            self.microphone.stop()
        await self.pc.close()
        self.audio_manager.stop_output_stream()
        print("Соединение закрыто")

    async def on_connectionstatechange(self):
        print(f"Состояние соединения: {self.pc.connectionState}")
        if self.pc.connectionState in ["failed", "disconnected", "closed"]:
            self.call_active = False
            await self.cleanup()

    async def create_offer(self):
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        sdp = offer.sdp.replace("opus/48000/2", "opus/48000/1")
        offer.sdp = sdp
        print("Оффер создан")
        return self.pc.localDescription

    async def create_answer(self):
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        sdp = answer.sdp.replace("opus/48000/2", "opus/48000/1")
        answer.sdp = sdp
        print("Ответ создан")
        return self.pc.localDescription

    async def set_remote_description(self, offer):
        desc = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        await self.pc.setRemoteDescription(desc)
        print(f"Установлено удаленное описание типа: {offer['type']}")

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
        ice_candidate = RTCIceCandidate(
            candidate=candidate["candidate"],
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"]
        )
        await self.pc.addIceCandidate(ice_candidate)
        print("Добавлен ICE-кандидат")