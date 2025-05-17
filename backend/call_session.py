import asyncio
from aiortc import RTCPeerConnection, RTCIceCandidate
from backend.microphone_stream import MicrophoneStreamTrack

class CallSession:
    def __init__(self, send_ice_callback):
        self.pc = RTCPeerConnection()
        self.send_ice_callback = send_ice_callback
        self.pc.on("icecandidate", self.on_icecandidate)

        # добавляй аудио трек
        self.audio_track = MicrophoneStreamTrack()
        self.pc.addTrack(self.audio_track)

    async def create_offer(self):
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        return self.pc.localDescription

    async def set_remote_description(self, sdp, type_):
        from aiortc import RTCSessionDescription
        desc = RTCSessionDescription(sdp=sdp, type=type_)
        await self.pc.setRemoteDescription(desc)

    async def create_answer(self):
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        return self.pc.localDescription

    async def close(self):
        await self.pc.close()
        self.call_active = False

    def start_call(self):
        self.call_active = True

    def end_call(self):
        self.call_active = False
        # Здесь можно добавить остановку аудио, очистку и т.д.

    def on_icecandidate(self, event):
        if event.candidate is not None:
            asyncio.create_task(self.send_ice_callback({
                "type": "ice_candidate",
                "candidate": {
                    "candidate": event.candidate.candidate,
                    "sdpMid": event.candidate.sdpMid,
                    "sdpMLineIndex": event.candidate.sdpMLineIndex,
                }
            }))

    async def add_ice_candidate(self, candidate):
        from aiortc import RTCIceCandidate
        ice_candidate = RTCIceCandidate(
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"],
            candidate=candidate["candidate"]
        )
        await self.pc.addIceCandidate(ice_candidate)
