import asyncio
import logging

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, RTCConfiguration, RTCIceServer

from backend.audio_manager import AudioReceiverTrack
from backend.microphone_stream import AudioStreamTrack

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class CallSession:
    def __init__(self, audio_manager, send_ice_callback, user_id):
        # Конфигурация с STUN серверами для обхода NAT
        # Добавьте резервные серверы
        self.config = RTCConfiguration([
            RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun1.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun2.l.google.com:19302"])
        ])

        self.pc = RTCPeerConnection(configuration=self.config)
        self.audio_manager = audio_manager
        self.send_ice_callback = send_ice_callback
        self.user_id = user_id
        self.call_active = False
        self.receiver_track = None
        self.audio_track = None
        self.ice_candidates_queue = []  # Очередь для ICE кандидатов

        # Обработчики событий WebRTC
        self.pc.on("icecandidate", lambda c: asyncio.create_task(self.on_icecandidate(c)))
        self.pc.on("track", self.on_track)
        self.pc.on("connectionstatechange", self.on_connection_state_change)
        self.pc.on("icegatheringstatechange", self.on_ice_gathering_state_change)
        self.pc.on("iceconnectionstatechange", self.on_ice_connection_state_change)
        print("CallSession экземпляр создан")
        # Добавляем локальный аудио-трек (микрофон)
        try:
            self.audio_track = AudioStreamTrack()
            self.pc.addTrack(self.audio_track)
            print("🎙️ Аудио-трек микрофона добавлен")
        except Exception as e:
            print(f"❌ Ошибка при добавлении аудио-трека: {e}")

    async def on_icecandidate(self, candidate):
        print(f"on_icecandidate called with: {candidate}")
        if candidate and candidate.candidate:
            logging.info(f"🧊 Новый ICE кандидат: {candidate.candidate}")
            try:
                candidate_data = {
                    "type": "ice_candidate",
                    "to": self.user_id,  # Добавлено поле получателя
                    "candidate": {
                        "candidate": candidate.candidate,
                        "sdpMid": candidate.sdpMid,
                        "sdpMLineIndex": candidate.sdpMLineIndex
                    }
                }
                await self.send_ice_callback(candidate_data)  # Отправка кандидата
                logging.info("✅ ICE кандидат отправлен")
            except Exception as e:
                logging.error(f"❌ Ошибка при отправке ICE кандидата: {e}")

    def on_track(self, track):
        """Обработка входящих треков"""
        print(f"📻 Получен трек: {track.kind}")
        if track.kind == "audio":
            try:
                # Создаем приемник аудио
                self.receiver_track = AudioReceiverTrack(track, self.audio_manager)
                asyncio.create_task(self.receiver_track.receive_audio())
                print("🔊 Аудио-приемник запущен")
            except Exception as e:
                print(f"❌ Ошибка при создании аудио-приемника: {e}")

    def on_connection_state_change(self):
        """Обработка изменения состояния соединения"""
        state = self.pc.connectionState
        print(f"🔌 Состояние соединения: {state}")

        if state == "connected":
            print("✅ WebRTC соединение установлено")
            self.call_active = True
        elif state == "failed":
            print("❌ WebRTC соединение не удалось")
            self.call_active = False
            print(self.close())
        elif state == "disconnected":
            print("📴 WebRTC соединение разорвано")
            self.call_active = False
        elif state == "closed":
            print("🔒 WebRTC соединение закрыто")
            self.call_active = False

    def on_ice_gathering_state_change(self):
        """Обработка изменения состояния сбора ICE кандидатов"""
        state = self.pc.iceGatheringState
        print(f"🧊 ICE Gathering State: {state}")

        if state == "complete":
            print("✅ ICE gathering завершен")

            # Обрабатываем отложенные ICE кандидаты
            print("запускается обработка отложенных ice кандидатов")
            asyncio.create_task(self.process_queued_ice_candidates())

    def on_ice_connection_state_change(self):
        """Обработка изменения состояния ICE соединения"""
        state = self.pc.iceConnectionState
        print(f"🧊 ICE Connection State: {state}")

        if state == "connected":
            print("✅ ICE соединение установлено")
        elif state == "completed":
            print("✅ ICE соединение завершено")
        elif state == "failed":
            print("❌ ICE соединение не удалось - проверьте сетевые настройки")
            print("❌ ICE соединение не удалось")
            print(f"Local description: {self.pc.localDescription}")
            print(f"Remote description: {self.pc.remoteDescription}")
            # Попробуем перезапустить ICE
            asyncio.create_task(self.restart_ice())
        elif state == "disconnected":
            print("📴 ICE соединение разорвано")

    async def restart_ice(self):
        """Перезапуск ICE соединения"""
        try:
            print("🔄 Перезапуск ICE соединения...")
            await self.pc.close()
            self.pc = RTCPeerConnection(configuration=self.config)
            self.pc.on("icecandidate", lambda c: asyncio.create_task(self.on_icecandidate(c)))
            self.pc.on("track", self.on_track)
            self.pc.on("connectionstatechange", self.on_connection_state_change)
            self.pc.on("icegatheringstatechange", self.on_ice_gathering_state_change)
            self.pc.on("iceconnectionstatechange", self.on_ice_connection_state_change)
            print("CallSession экземпляр создан")
            self.pc.addTrack(self.audio_track)
            print("RTCPeerConnection пересоздано")
        except Exception as e:
            print(f"❌ Ошибка при перезапуске ICE: {e}")

    async def create_offer(self):
        """Создание оффера"""
        try:
            print("📤 Создание оффера...")
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            print(f"📤 Оффер создан: type={offer.type}")

            # Ждем немного для сбора ICE кандидатов
            await asyncio.sleep(0.5)

            return offer
        except Exception as e:
            logging.error(f"❌ Ошибка при создании оффера: {e}")
            raise

    async def create_answer(self):
        """Создание ответа"""
        try:
            print("📨 Создание ответа...")
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            print(f"📨 Ответ создан: type={answer.type}")

            # Ждем немного для сбора ICE кандидатов
            await asyncio.sleep(0.5)

            return answer
        except Exception as e:
            logging.error(f"❌ Ошибка при создании ответа: {e}")
            raise

    async def set_remote_description(self, sdp):
        print("вызвалась функция для установки удаленного описания")
        """Установка удаленного описания"""
        try:
            logging.info(f"📥 Установка удаленного описания: type={sdp['type']}")
            print(f"📥 Установка удаленного описания: type={sdp['type']}")
            await self.pc.setRemoteDescription(
                RTCSessionDescription(sdp=sdp['sdp'], type=sdp['type'])
            )
            logging.info("✅ Удаленное описание установлено")
            print("✅ Удаленное описание установлено")

            # После установки удаленного описания обрабатываем отложенные ICE кандидаты
            print("запускается обработка отложенных ice кандидатов")
            await self.process_queued_ice_candidates()

        except Exception as e:
            logging.error(f"❌ Ошибка при установке удаленного описания: {e}")
            raise

    async def add_ice_candidate(self, candidate):
        """Добавление ICE кандидата"""
        print("вызвана функция add_ice_candidate")
        try:
            # Если удаленное описание еще не установлено, добавляем в очередь
            if self.pc.remoteDescription is None:
                print("⏳ Удаленное описание не установлено, добавляем ICE кандидат в очередь")
                self.ice_candidates_queue.append(candidate)
                return

            print(f"🧊 Добавление ICE кандидата: {candidate['candidate'][:50]}...")
            ice_candidate = RTCIceCandidate(
                candidate["candidate"],
                candidate.get("sdpMid"),
                candidate.get("sdpMLineIndex")
            )
            await self.pc.addIceCandidate(ice_candidate)
            print("✅ ICE кандидат добавлен")

        except Exception as e:
            print(f"❌ Ошибка при добавлении ICE кандидата: {e}")
            # Не прерываем выполнение, так как некоторые кандидаты могут быть недоступны

    async def process_queued_ice_candidates(self):
        """Обработка отложенных ICE кандидатов"""
        if not self.ice_candidates_queue:
            print("нету отложенных ice кандидатов")
            return

        print(f"🧊 Обработка {len(self.ice_candidates_queue)} отложенных ICE кандидатов")

        for candidate in self.ice_candidates_queue.copy():
            try:
                await self.add_ice_candidate(candidate)
                self.ice_candidates_queue.remove(candidate)
            except Exception as e:
                print(f"❌ Ошибка при обработке отложенного ICE кандидата: {e}")

        print("✅ Все отложенные ICE кандидаты обработаны")

    async def close(self):
        """Закрытие соединения"""
        try:
            print("🔒 Закрытие WebRTC соединения...")

            # Останавливаем аудио-приемник
            if self.receiver_track:
                await self.receiver_track.stop()
                self.receiver_track = None

            # Останавливаем микрофон
            if hasattr(self, 'audio_track') and self.audio_track:
                self.audio_track.stop()
                self.audio_track = None

            # Очищаем очередь ICE кандидатов
            self.ice_candidates_queue.clear()

            # Закрываем RTCPeerConnection
            if self.pc and self.pc.connectionState != "closed":
                await self.pc.close()

            self.call_active = False
            print("✅ WebRTC соединение закрыто")

        except Exception as e:
            print(f"❌ Ошибка при закрытии соединения: {e}")
        finally:
            self.call_active = False