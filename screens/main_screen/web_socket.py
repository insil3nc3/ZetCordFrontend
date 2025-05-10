from PyQt6.QtCore import QObject, QUrl, pyqtSlot, pyqtSignal
from PyQt6.QtWebSockets import QWebSocket, QWebSocketProtocol
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QLineEdit, QPushButton
import json
class WebSocketClient(QObject):
    message_received = pyqtSignal(str)
    connected = pyqtSignal()
    def __init__(self, token, parent=None):
        super().__init__()
        self.token = token
        self.socket = QWebSocket()
        self.socket.connected.connect(self.on_connected)
        self.socket.textMessageReceived.connect(self.on_message_received)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.errorOccurred.connect(self.on_error)

    def connect(self):
        url = QUrl(f"ws://localhost:8000/ws?token={self.token}")
        print()
        self.socket.open(url)

    @pyqtSlot()
    def on_connected(self):
        self.connected.emit()

    @pyqtSlot(str)
    def on_message_received(self, message):
        self.message_received.emit(message)
        data = json.loads(message)
        # print("получено сообщение: ", data)

    @pyqtSlot()
    def send_json(self, data:dict):
        # Формируем JSON-сообщение
        message = json.dumps(data)
        self.socket.sendTextMessage(message)
        print("данные отправлены:", data)

    @pyqtSlot()
    def on_disconnected(self):
        print("отключено")

    def close(self):
        print("ChatClient socket closed")
        if self.socket.isValid():
            self.socket.close()

    @pyqtSlot()
    def on_error(self):
        print(f"Ошибка: {self.socket.errorString()}")