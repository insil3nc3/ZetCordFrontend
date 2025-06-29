import asyncio

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QCursor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from aiortc import RTCPeerConnection
from more_itertools.recipes import unique

from backend.avatar_path_getter import find_image_path_by_number
from backend.call_session import CallSession

from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.animate_text_button import AnimatedButton
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.screen_style_sheet import load_custom_font
from screens.utils.search_screen_profile_widget import SearchScreenProfileWidget

class CallWidget(QWidget):
    def __init__(self, receiver_id, receiver_name, receiver_avatar_path, cur_user_info, audio, set_calling_status_callback, send_via_ws, is_group=False):
        super().__init__()
        self.call_active = False
        self.receiver_id = receiver_id
        self.receiver_name = receiver_name
        self.receiver_avatar_path = receiver_avatar_path
        self.cur_user_info = cur_user_info
        self.audio = audio
        self.set_calling_status = set_calling_status_callback
        self.send_via_ws = send_via_ws
        self.pc = None
        self.audio_track = None
        self.call_session = None
        self.is_group = is_group
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(10, 10, 0, 0)
        main_layout.setSpacing(15)
        top_container = QWidget()
        top_layout = QVBoxLayout()
        top_container.setLayout(top_layout)

        bottom_container = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_container.setLayout(bottom_layout)
        bottom_container.setFixedHeight(90)

        container_style_sheet = """
            background-color: #1f1b24;
            border-radius: 10px;
        """
        top_container.setStyleSheet(container_style_sheet)
        bottom_container.setStyleSheet(container_style_sheet)

        font = load_custom_font(12)
        if font:
            self.setFont(font)

        call_layout = QVBoxLayout()
        call_layout.addStretch()

        self.avatar = QLabel(self)
        self.avatar.setFixedSize(120, 120)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("background: transparent;")
        call_layout.addWidget(self.avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.nickname = QLabel()
        self.nickname.setFont(QFont("inter", 20, QFont.Weight.Bold))
        self.nickname.setContentsMargins(5, 5, 5, 5)
        self.nickname.setStyleSheet("background-color: #7A4165;")
        call_layout.addWidget(self.nickname, alignment=Qt.AlignmentFlag.AlignCenter)
        call_layout.addStretch()

        self.call_button = QPushButton()
        self.call_button.setFixedSize(90, 90)
        self.call_button.setStyleSheet("background-color: #3ba55d; border-radius: 45;")
        self.call_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.call_button.clicked.connect(self.toggle_call_state)
        self.call_button.setIcon(QIcon("icons/phone-call.svg"))
        self.call_button.setIconSize(QSize(70, 70))
        call_layout.addWidget(self.call_button, alignment=Qt.AlignmentFlag.AlignCenter)
        call_layout.addStretch()

        top_layout.addLayout(call_layout)

        members_container = QWidget()
        members_container.setStyleSheet("background-color: #110f12; border-radius: 15px;")
        call_members_layout = QVBoxLayout()
        call_members_layout.setSpacing(10)
        call_members_layout.setContentsMargins(10, 10, 10, 10)
        self.cur_user = SearchScreenProfileWidget()
        self.receiver = SearchScreenProfileWidget()
        call_members_layout.addWidget(self.cur_user, alignment=Qt.AlignmentFlag.AlignTop)
        call_members_layout.addWidget(self.receiver, alignment=Qt.AlignmentFlag.AlignTop)
        call_members_layout.addStretch()
        members_container.setLayout(call_members_layout)
        top_layout.addWidget(members_container)

        self.set_cur_user_info()
        self.set_receiver_info()
        self.fill_data()
        main_layout.addWidget(top_container)
        main_layout.addWidget(bottom_container)

        self.call_session = None

    def fill_data(self):
        self.set_avatar(self.receiver_avatar_path)
        self.nickname.setText(self.receiver_name)

    def set_avatar(self, receiver_avatar_path):
        pixmap = QPixmap(receiver_avatar_path if receiver_avatar_path else default_ava_path)
        circular_pixmap = create_circular_pixmap(pixmap, 120)
        self.avatar.setPixmap(circular_pixmap)

    async def send_ice_callback(self, data: dict):
        print("был вызван send_ice_callback в call_widget")
        print(data)
        # data["to"] = self.receiver_id
        self.send_via_ws(data)

    async def offer_to_call(self):
        try:
            # Создаем сессию звонка
            print("создаем экземпляр CallSession в call_widget")
            self.call_session = CallSession(
                audio_manager=self.audio,
                send_ice_callback=self.send_ice_callback,
                user_id=self.receiver_id
            )

            print(f"📞 Начало offer_to_call, receiver={self.receiver_name}")
            desc = await self.call_session.create_offer()
            print(f"📤 Оффер готов: type={desc.type}, sdp={desc.sdp[:100]}...")

            data = {
                "type": "offer",
                "to": self.receiver_id,
                "offer": {
                    "type": desc.type,
                    "sdp": desc.sdp
                }
            }
            self.send_via_ws(data)
            self.call_session.call_active = True
            print("📤 Оффер отправлен")
        except Exception as e:
            print(f"❌ Ошибка в offer_to_call: {type(e).__name__}: {e}")
            self.end_call()
            raise

    def end_call(self):
        print(f"🛑 Звонок с {self.receiver_name} завершён")
        self.audio.stop_ringtone()
        self.audio.play_notification("sounds/end_calling.mp3")
        self.set_calling_status(False)

        if self.call_session:
            print("🛑 Закрытие call_session")
            asyncio.create_task(self.call_session.close())
            self.send_via_ws({"type": "end_call", "to": self.receiver_id})

        self.call_session = None

    async def on_ice_candidate_received(self, candidate):
        if self.call_session and self.call_session.pc:
            await self.call_session.add_ice_candidate(candidate)

    def set_cur_user_info(self):
        data = {"nickname": self.cur_user_info["nickname"], "avatar_path": find_image_path_by_number("avatar", 1)}
        self.cur_user.sync_input_data(data)

    def set_receiver_info(self):
        data = {"nickname": self.receiver_name, "avatar_path": self.receiver_avatar_path}
        self.receiver.sync_input_data(data)

    def toggle_call_state(self):
        if not self.call_active:
            self.call_active = True
            self.call_button.setStyleSheet("background-color: #ed4245; border-radius: 45;")
            self.call_button.setIcon(QIcon("icons/phone-disconnect.svg"))
            self.call_user()
        else:
            self.call_active = False
            self.call_button.setStyleSheet("background-color: #3ba55d; border-radius: 45;")
            self.call_button.setIcon(QIcon("icons/phone-call.svg"))
            self.end_call()

    def call_user(self):
        print(f"Начинается звонок пользователю {self.receiver_name}")
        asyncio.create_task(self.offer_to_call())
        self.audio.play_ringtone("sounds/zetcord.mp3")
        self.set_calling_status(True)

    def init_call(self, info):
        print("звонок начался: ", info)

    async def on_answer_received(self, sdp):
        try:
            self.audio.stop_ringtone()
            print(f"📨 Получен ответ (answer): sdp={sdp}")
            if not self.call_session:
                raise RuntimeError("CallSession не инициализирован")

            await self.call_session.set_remote_description(sdp)
            print("✅ Ответ обработан")
        except Exception as e:
            print(f"❌ Ошибка в on_answer_received: {type(e).__name__}: {e}")
            self.end_call()
            raise