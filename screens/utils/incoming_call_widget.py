import asyncio

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QCursor, QIcon, QKeyEvent
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from backend.avatar_path_getter import find_image_path_by_number
from backend.call_session import CallSession

from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.screen_style_sheet import screen_style, load_custom_font


class IncomingCallWidget(QDialog):
    def __init__(self, data, audio, send_via_ws_callback, call_accepted_callback, parent=None):
        super().__init__(parent)
        print("incomming call screen loaded")
        self.setWindowTitle("Найти пользователя")
        self.setModal(False)
        self.setFixedSize(550, 300)
        self.setStyleSheet(screen_style)
        self.calling_user_data = data["from"]
        self.calling_user_offer = data
        self.audio = audio
        self.send_via_ws = send_via_ws_callback
        self.call_session = None
        self.call_accepted_callback = call_accepted_callback
        # ====== загрузка шрифта ======
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # ==========================
        self.ringtone_on("sounds/zetcord.mp3")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addStretch()
        # ========== Label ==========
        label = QLabel("Входящий звонок")
        label.setFont(QFont("Inter", 20, QFont.Weight.ExtraBold))
        main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
        # ===========================

        # ========== Avatar ==========
        avatar = QLabel()
        avatar.setFixedSize(70, 70)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background: transparent;")
        # ============================
        avatar_path = find_image_path_by_number("avatar", self.calling_user_data["id"])
        pixmap = QPixmap(avatar_path if avatar_path else default_ava_path)
        # Преобразуем изображение в круглое
        circular_pixmap = create_circular_pixmap(pixmap, 70)
        avatar.setPixmap(circular_pixmap)
        main_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        # ============================

        nickname = QLabel(self.calling_user_data["nickname"])
        nickname.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        nickname.setStyleSheet("color: white;")
        main_layout.addWidget(nickname, alignment=Qt.AlignmentFlag.AlignCenter)

        unique_name = QLabel(self.calling_user_data["unique_name"])
        unique_name.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        unique_name.setStyleSheet("color: gray;")
        main_layout.addWidget(unique_name, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()

        # ========== Button Layout ==========
        button_layout = QHBoxLayout()

        accept_button = QPushButton()
        accept_button.clicked.connect(lambda: asyncio.create_task(self.call_accepted()))
        accept_button.setFixedSize(70, 70)
        accept_button.setStyleSheet("background-color: #3ba55d; border-radius: 35;")
        accept_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        accept_button.setIcon(QIcon("icons/phone-call.svg"))
        accept_button.setIconSize(QSize(50, 50))

        cancel_button = QPushButton()
        cancel_button.clicked.connect(self.call_rejected)
        cancel_button.setFixedSize(70, 70)
        cancel_button.setStyleSheet("background-color: #ed4245; border-radius: 35;")
        cancel_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_button.setIcon(QIcon("icons/phone-disconnect.svg"))
        cancel_button.setIconSize(QSize(50, 50))

        button_layout.addStretch()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.setSpacing(15)
        main_layout.addLayout(button_layout)
        # ===================================
        main_layout.addStretch()
        main_layout.setContentsMargins(0, 10, 0, 10)

    def ringtone_on(self, path):
        self.audio.play_ringtone(path)

    def ringtone_off(self):
        self.audio.stop_ringtone()

    async def send_ice_callback(self, data: dict):
        """Callback для отправки ICE кандидатов"""
        data["to"] = self.calling_user_data["id"]
        print(f"🧊 Отправка ICE кандидата: {data}")
        self.send_via_ws(data)

    async def handle_ice_candidate(self, candidate_data):
        """Обработка входящих ICE кандидатов"""
        if self.call_session:
            try:
                await self.call_session.add_ice_candidate(candidate_data["candidate"])
                print(f"✅ ICE кандидат обработан: {candidate_data['candidate']['candidate'][:50]}...")
            except Exception as e:
                print(f"❌ Ошибка обработки ICE кандидата: {e}")

    async def call_accepted(self):
        self.ringtone_off()
        print("Звонок принят")

        offer = self.calling_user_offer.get("offer")
        print(f"Данные звонящего пользователя: {self.calling_user_data}")

        if offer:
            try:
                # Создаем call_session с правильным callback
                self.call_session = CallSession(
                    audio_manager=self.audio,
                    send_ice_callback=self.send_ice_callback,
                    user_id=self.calling_user_data["id"]
                )

                print("📥 Устанавливаем удаленное описание...")
                await self.call_session.set_remote_description(offer)

                print("📨 Создаем ответ...")
                answer = await self.call_session.create_answer()

                # Отправляем ответ
                data = {
                    "type": "answer",
                    "to": self.calling_user_data["id"],
                    "answer": {
                        "type": answer.type,
                        "sdp": answer.sdp
                    }
                }
                print(f"📤 Отправляем ответ: {data['type']}")
                self.send_via_ws(data)

                # Уведомляем о принятии звонка
                self.call_accepted_callback()
                print("✅ Звонок принят, ответ отправлен")
                self.call_session.call_active = True

                # Ждем небольшую паузу для обработки ICE кандидатов
                await asyncio.sleep(0.5)

                self.accept()
                self.close()

            except Exception as e:
                print(f"❌ Ошибка при принятии звонка: {e}")
                self.call_rejected()

    def call_rejected(self):
        self.ringtone_off()
        self.audio.play_notification("sounds/end_calling.mp3")
        print("❌ Звонок отклонен")

        # Отправляем уведомление об отклонении
        data = {
            "type": "call_rejected",
            "to": self.calling_user_data["id"]
        }
        self.send_via_ws(data)

        self.reject()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            asyncio.create_task(self.call_accepted())
        elif event.key() == Qt.Key.Key_Escape:
            self.call_rejected()
        else:
            super().keyPressEvent(event)