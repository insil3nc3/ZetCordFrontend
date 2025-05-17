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
        # Инициализация микрофона с выбранным устройством
        self.microphone = MicrophoneStreamTrack(device=self.audio_device)
        self.pc.addTrack(self.microphone)

        self.pc.on("icecandidate", self.on_icecandidate)
        self.pc.on("track", self.on_track)
        self.pc.on("connectionstatechange", self.on_connectionstatechange)

    async def on_track(self, track):
        print(f"Получен трек: {track.kind}")
        if track.kind == "audio":
            self.remote_track = track
            self.audio_manager.start_output_stream()
            try:
                while True:
                    frame = await track.recv()
                    audio_data = frame.to_ndarray(format="flt")
                    print(
                        f"Получены аудиоданные: shape={audio_data.shape}, dtype={audio_data.dtype}, max={np.max(np.abs(audio_data))}")
                    if np.max(np.abs(audio_data)) > 1.0:
                        audio_data = audio_data / np.max(np.abs(audio_data))
                    self.audio_manager.play_audio_chunk(audio_data)
            except Exception as e:
                print(f"Ошибка при обработке аудио: {e}")
                await self.cleanup()

    async def cleanup(self):
        if self.microphone:
            self.microphone.stop()
        if self.remote_track:
            self.remote_track.stop()
        if self.pc:
            await self.pc.close()
        self.audio_manager.stop_output_stream()
        print("Соединение закрыто")

    async def on_connectionstatechange(self):
        print(f"Состояние соединения: {self.pc.connectionState}")
        if self.pc.connectionState == "failed":
            await self.cleanup()

    async def create_offer(self):
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        print("Оффер создан")
        return self.pc.localDescription

    async def set_remote_description(self, offer):
        desc = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        await self.pc.setRemoteDescription(desc)
        print(f"Установлено удаленное описание типа: {offer['type']}")

    async def create_answer(self):
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        print("Ответ создан")
        return self.pc.localDescription

    async def close(self):
        if self.remote_track:
            self.remote_track.stop()
        if self.microphone:  # Используем self.microphone, а не self.microphone_track
            self.microphone.stop()
        await self.pc.close()
        self.call_active = False
        self.audio_manager.stop_output_stream()
        print("Соединение закрыто")

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