import asyncio
from datetime import datetime, UTC

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QLabel

class ChatWidget(QWidget):
    def __init__(self, user_id, chat_id, receiver_id, send_via_ws):
        super().__init__()
        self.send_via_ws = send_via_ws
        self.chat_id = chat_id
        self.user_id = user_id
        self.receiver_id = receiver_id
        # Настройка интерфейса
        layout = QVBoxLayout()
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Отправить")
        layout.addWidget(QLabel("Чат"))
        layout.addWidget(self.message_display)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        self.setLayout(layout)

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