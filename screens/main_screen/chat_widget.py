import asyncio
from datetime import datetime, UTC

from PyQt6.QtGui import QPixmap, QFont, QIcon, QCursor, QPalette, QColor
from alembic.command import history

from api.profile_actions import get_avatar_path, get_user_info
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.enter_text_edit import EnterTextEdit
from screens.utils.message_widget import MessageWidget
from PyQt6.QtCore import pyqtSlot, Qt, QTime, QTimer, QSize
from PyQt6.QtWidgets import QWidget, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QLabel, QScrollArea, QFrame, \
    QHBoxLayout
import os
from screens.utils.screen_style_sheet import load_custom_font


class ChatWidget(QWidget):
    def __init__(self, user_id, chat_id, receiver_id, username, send_via_ws, update_last_msg_callback, is_group=False):
        super().__init__()
        self.send_via_ws = send_via_ws
        self.chat_id = chat_id
        self.user_id = user_id
        print("user_id - ", self.user_id)
        self.nick_cache = {}
        self.receiver_id = receiver_id
        print("receiver_id - ", self.receiver_id)
        self.username = username
        self.message = None
        self.is_group = is_group
        self.update_last_msg_callback = update_last_msg_callback
        if self.is_group:
            self.user_avatar_path = default_ava_path
            self.receiver_avatar_path = default_ava_path
        else:
            self.user_avatar_path = get_avatar_path(self.user_id)
            self.receiver_avatar_path = get_avatar_path(self.receiver_id)

        # Настройка интерфейса
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 0, 0)
        layout.setSpacing(0)
        self.setMinimumWidth(200)
        # ====== загрузка шрифта ======
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # ==========================
        # ========== Top bar ==========
        bar_container = QWidget()
        bar_layout = QHBoxLayout()
        bar_layout.setContentsMargins(10, 0, 10, 0)
        bar_layout.setSpacing(10)

        # Аватар получателя (сверху)
        self.receiver_bar_avatar = QLabel()
        selected_path = self.receiver_avatar_path if self.receiver_avatar_path else default_ava_path
        pixmap = QPixmap(selected_path)
        circular_pixmap = create_circular_pixmap(pixmap, 50)
        self.receiver_bar_avatar.setPixmap(circular_pixmap)
        self.receiver_bar_avatar.setFixedSize(50, 50)
        self.receiver_bar_avatar.setStyleSheet("background: transparent;")
        bar_layout.addWidget(self.receiver_bar_avatar)
        name_last_seen_layout = QVBoxLayout()
        self.receiver_name = QLabel(self.username)
        self.receiver_name.setStyleSheet("color: #FFFFFF;")
        self.receiver_name.setFont(QFont("Inter", 14, QFont.Weight.Bold))

        if self.is_group:
            self.last_seen = QLabel(f"{len(self.receiver_id)} участник(а)")

        else:
            self.last_seen = QLabel("был(а) недавно")
        self.last_seen.setStyleSheet("color: gray;")
        self.last_seen.setFont(QFont("Inter", 12, QFont.Weight.Normal))
        name_last_seen_layout.setSpacing(0)
        name_last_seen_layout.setContentsMargins(0, 0, 0, 0)
        name_last_seen_layout.addStretch()
        name_last_seen_layout.addWidget(self.receiver_name, alignment=Qt.AlignmentFlag.AlignBottom)
        name_last_seen_layout.addWidget(self.last_seen, alignment=Qt.AlignmentFlag.AlignTop)
        name_last_seen_layout.addStretch()
        bar_layout.addLayout(name_last_seen_layout)
        bar_container.setStyleSheet("""
            background-color: #1f1b24;
            border-top-right-radius: 10px;
            border-top-left-radius: 10px;
        """)
        bar_container.setLayout(bar_layout)
        bar_container.setFixedHeight(60)
        layout.addWidget(bar_container)
        # =============================


        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #272428;")
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)

        self.bottom_container = QWidget()
        self.bottom_container.setStyleSheet("""
            background-color: #1f1b24;
            border-bottom-right-radius: 10px;
            border-bottom-left-radius: 10px;
        """)
        bottom_layout = QHBoxLayout()
        self.text_input = EnterTextEdit()
        self.text_input.setPlaceholderText("Сообщение...")
        self.text_input.setMinimumHeight(35)  # Задаём стартовую высоту
        self.text_input.setFixedHeight(35)
        palette = self.text_input.palette()
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#4a2a3a"))  # Тёмно-бледно-бордовый фон
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))  # Белый текст при выделении
        self.text_input.setPalette(palette)
        self.text_input.height_changed.connect(self.adjust_bottom_height)
        self.text_input.enter_pressed.connect(self.send_message)
        self.text_input.setFont(QFont("Inter", 11, QFont.Weight.Normal))
        self.adjust_bottom_height(self.text_input.height())
        bottom_layout.addWidget(self.text_input)

        send_button = QPushButton()
        icon_path = os.path.join("..", "icons", "send_icon.png")
        send_button.setIcon(QIcon(icon_path))
        send_button.setIconSize(QSize(35, 35))
        send_button.setStyleSheet("""
            QPushButton {
                border: none;
            }
        """)
        send_button.clicked.connect(self.send_message)
        send_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        bottom_layout.addWidget(send_button)
        bottom_layout.setContentsMargins(10, 10, 10, 10)  # сверху и снизу добавлены по 5px
        self.bottom_container.setLayout(bottom_layout)
        layout.addWidget(self.bottom_container)


        # ========== Avatars ==========
        self.user_avatar = QLabel()
        selected_path = self.user_avatar_path if self.user_avatar_path else default_ava_path
        pixmap = QPixmap(selected_path)
        circular_pixmap = create_circular_pixmap(pixmap, 40)
        self.user_avatar.setPixmap(circular_pixmap)
        self.user_avatar.setStyleSheet("background: transparent;")

        self.receiver_avatar = QLabel()
        selected_path = self.receiver_avatar_path if self.receiver_avatar_path else default_ava_path
        pixmap = QPixmap(selected_path)
        circular_pixmap = create_circular_pixmap(pixmap, 40)
        self.receiver_avatar.setPixmap(circular_pixmap)
        self.receiver_avatar.setStyleSheet("background: transparent;")
        # ==============================


        self.setLayout(layout)

    def adjust_bottom_height(self, new_text_height):
        total_height = new_text_height + 20
        self.bottom_container.setFixedHeight(total_height)

    async def add_message(self, data, history=None):
        sender_id = data.get("sender_id")
        msg_sender = "user" if sender_id == self.user_id else "receiver"

        new_sender = True
        if self.message:
            prev_sender_id = self.message.sender_id
            if prev_sender_id == sender_id:
                new_sender = False

        # Обёртка одного сообщения
        message_container = QWidget()
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(5, 10 if new_sender else 2, 5, 0)
        message_layout.setSpacing(2)

        # Групповой чат: ник
        if self.is_group and new_sender:
            nickname = self.nick_cache.get(sender_id)
            if not nickname:
                try:
                    user_info = await get_user_info(sender_id)
                    print("user info - ", user_info)
                    nickname = user_info.get("nickname", f"User {sender_id}")
                    self.nick_cache[sender_id] = nickname
                except Exception as e:
                    print(f"⚠️ Не удалось получить nickname для user {sender_id}: {e}")
                    nickname = f"User {sender_id}"

            nickname_label = QLabel(nickname)
            nickname_label.setStyleSheet("color: gray; padding-left: 45px; font-size: 11px;")
            message_layout.addWidget(nickname_label)

        # Линия с аватаркой и сообщением
        msg_container = QWidget()
        msg_container_layout = QHBoxLayout(msg_container)
        msg_container_layout.setContentsMargins(0, 0, 0, 0)
        msg_container_layout.setSpacing(5)

        if new_sender:
            avatar = QLabel()
            selected_path = self.user_avatar_path if msg_sender == "user" else self.receiver_avatar_path
            pixmap = QPixmap(selected_path if selected_path else default_ava_path)
            circular_pixmap = create_circular_pixmap(pixmap, 40)
            avatar.setPixmap(circular_pixmap)
            avatar.setStyleSheet("background: transparent;")
            msg_container_layout.addWidget(avatar)
        else:
            spacer = QWidget()
            spacer.setFixedWidth(40)
            msg_container_layout.addWidget(spacer)

        self.message = MessageWidget(data, msg_sender)
        self.message.sender_id = sender_id
        msg_container_layout.addWidget(self.message)

        message_layout.addWidget(msg_container)
        self.messages_layout.addWidget(message_container)

        if not history:
            self.update_last_msg_callback(data["content"])
            QTimer.singleShot(1, self.scroll_to_bottom)

    def send_message(self):
        text = self.text_input.toPlainText().strip()

        message_type = "chat_message" if not self.is_group else "group_message"

        data = {
            "type": message_type,
            "chat_id": self.chat_id,
            "receiver_id": self.receiver_id if not self.is_group else None,
            "content": text
        }
        self.send_via_ws(data) if not self.is_group else self.send_group_msg(data)
        self.text_input.clear()

    def send_group_msg(self, data):
        print(data)
        self.send_via_ws(data)


    def show_history(self, messages_data: dict):
        messages_data = messages_data[::-1]
        for message_data in messages_data:
            asyncio.create_task(self.add_message(message_data, history=True))
        self.messages_widget.adjustSize()
        self.messages_widget.updateGeometry()
        QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())