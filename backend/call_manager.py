import asyncio
import logging
from backend.call_session import CallSession

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class CallManager:
    def __init__(self, audio_manager, send_ws_callback):
        self.audio_manager = audio_manager
        self.send_ws_callback = send_ws_callback
        self.active_calls = {}
        self.pending_ice_candidates = {}

    async def start_outgoing_call(self, user_id):
        """Start an outgoing call"""
        if user_id in self.active_calls:
            logging.warning(f"⚠️ Call to {user_id} already exists")
            return

        session = CallSession(
            audio_manager=self.audio_manager,
            send_ice_callback=self.send_ice_candidate,
            user_id=user_id
        )

        self.active_calls[user_id] = {
            "session": session,
            "direction": "outgoing",
            "status": "connecting"
        }

        try:
            # Create and send offer
            offer = await session.create_offer()
            await self.send_ws_callback({
                "type": "offer",
                "to": user_id,
                "offer": {
                    "type": offer.type,
                    "sdp": offer.sdp
                }
            })
            session.call_active = True
            logging.info(f"📤 Offer sent to {user_id}")
        except Exception as e:
            logging.error(f"❌ Error starting call: {e}")
            await self.end_call(user_id)

    async def handle_incoming_offer(self, from_user_id, offer):
        """Handle incoming call offer"""
        if from_user_id in self.active_calls:
            logging.warning(f"⚠️ Already in call with {from_user_id}")
            return

        session = CallSession(
            audio_manager=self.audio_manager,
            send_ice_callback=self.send_ice_candidate,
            user_id=from_user_id
        )

        self.active_calls[from_user_id] = {
            "session": session,
            "direction": "incoming",
            "status": "ringing"
        }

        try:
            # Set remote description and send answer
            await session.set_remote_description(offer)
            answer = await session.create_answer()
            await self.send_ws_callback({
                "type": "answer",
                "to": from_user_id,
                "answer": {
                    "type": answer.type,
                    "sdp": answer.sdp
                }
            })
            session.call_active = True
            logging.info(f"📨 Answer sent to {from_user_id}")
        except Exception as e:
            logging.error(f"❌ Error handling offer: {e}")
            await self.end_call(from_user_id)

    async def handle_answer(self, from_user_id, answer):
        """Handle call answer"""
        if from_user_id not in self.active_calls:
            logging.warning(f"⚠️ No active call with {from_user_id}")
            return

        session = self.active_calls[from_user_id]["session"]
        try:
            await session.set_remote_description(answer)
            logging.info(f"✅ Answer processed for {from_user_id}")
        except Exception as e:
            logging.error(f"❌ Error handling answer: {e}")
            await self.end_call(from_user_id)

    async def handle_ice_candidate(self, from_user_id, candidate):
        """Handle ICE candidate"""
        # Add candidate to session if exists
        if from_user_id in self.active_calls:
            session = self.active_calls[from_user_id]["session"]
            await session.add_ice_candidate(candidate)
            logging.info(f"🧊 ICE candidate added for {from_user_id}")
        else:
            # Store for future use
            if from_user_id not in self.pending_ice_candidates:
                self.pending_ice_candidates[from_user_id] = []
            self.pending_ice_candidates[from_user_id].append(candidate)
            logging.info(f"⏳ Queuing ICE candidate for {from_user_id}")

    async def end_call(self, user_id):
        """End a call"""
        if user_id in self.active_calls:
            session = self.active_calls[user_id]["session"]
            await session.close()
            del self.active_calls[user_id]
            logging.info(f"📴 Call with {user_id} ended")

        # Send end call notification
        await self.send_ws_callback({
            "type": "end_call",
            "to": user_id
        })

    async def send_ice_candidate(self, candidate_data):
        """Send ICE candidate via WebSocket"""
        await self.send_ws_callback(candidate_data)