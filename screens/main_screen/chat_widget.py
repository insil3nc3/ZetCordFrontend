import asyncio
from datetime import datetime, UTC

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QLabel, QHBoxLayout


class ChatWidget(QWidget):
    def __init__(self, user_id, chat_id, receiver_id, send_via_ws):
        super().__init__()
        self.send_via_ws = send_via_ws
        self.chat_id = chat_id
        self.user_id = user_id
        self.receiver_id = receiver_id
        # Настройка интерфейса
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # Добавлен отступ сверху списков
        main_layout.setContentsMargins(5, 10, 0, 0)  # Отступ сверху
        top_chat_part_container = QWidget()
        top_chat_layout = QHBoxLayout()
        top_chat_layout.setContentsMargins(0, 10, 0, 10)
        top_chat_layout.setSpacing(10)
        top_chat_layout.addStretch()
        top_chat_layout.addWidget(QLabel("чат с кем то"))
        top_chat_layout.addStretch()
        top_chat_part_container.setLayout(top_chat_layout)
        top_chat_part_container.setStyleSheet("""
            QWidget {
                background-color: #333333;
                border-radius: 10px;
            }   
        """)
        main_layout.addWidget(top_chat_part_container)

        bottom_chat_part_container = QWidget()
        bottom_layout = QVBoxLayout()
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Отправить")
        bottom_layout.addWidget(QLabel("Чат"))
        bottom_layout.addWidget(self.message_display)
        bottom_layout.addWidget(self.message_input)
        bottom_layout.addWidget(self.send_button)
        bottom_chat_part_container.setLayout(bottom_layout)
        bottom_chat_part_container.setStyleSheet("""
            QWidget {
                background-color: #333333;
                border-radius: 10px;
            }   
        """)
        main_layout.addWidget(bottom_chat_part_container)
        self.setLayout(main_layout)

        self.send_button.clicked.connect(self.send_message)


    def send_message(self):
        message_data = {
            "type": "chat_message",
            "chat_id": self.chat_id,
            "receiver_id": self.receiver_id,
            "content": self.message_input.text(),
        }
        try:
            self.send_via_ws(message_data)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
        self.message_input.clear()


    def append_message(self, message_data: dict):
        sender_id = message_data["message"]["sender_id"]
        content = message_data["message"]["content"]
        self.show_message(sender_id, content)

    def show_message(self, sender_id, content):
        if sender_id == self.user_id:
            sender = "Вы"
        else:
            sender = "Собеседник"
        self.message_display.append(f"{sender}: {content}")

    def show_history(self, messages_data: dict):
        messages_data = messages_data[::-1]
        for message_data in messages_data:
            sender_id = message_data.get("sender_id")
            content = message_data.get("content")
            self.show_message(sender_id, content)