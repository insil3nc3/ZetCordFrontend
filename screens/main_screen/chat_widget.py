import asyncio
from datetime import datetime, UTC
from PyQt6.QtCore import pyqtSlot, Qt, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QTimer
from PyQt6.QtWidgets import (QWidget, QTextEdit, QLineEdit, QPushButton,
                             QVBoxLayout, QLabel, QHBoxLayout, QScrollArea,
                             QFrame, QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtGui import QColor, QTextCursor, QIcon, QPixmap


class ChatWidget(QWidget):
    def __init__(self, user_id, chat_id, receiver_id, send_via_ws, receiver_name):
        super().__init__()
        self.send_via_ws = send_via_ws
        self.chat_id = chat_id
        self.user_id = user_id
        self.receiver_id = receiver_id
        self.receiver_name = receiver_name

        self.setup_ui()
        self.setup_styles()

        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        self.scroll_bar = self.scroll_area.verticalScrollBar()
        self.scroll_bar.rangeChanged.connect(self.scroll_to_bottom)

    def setup_ui(self):
        # ========== Main Layout ==========
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ========== Chat Header ==========
        self.header = QWidget()
        self.header.setFixedHeight(50)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon.fromTheme("go-previous"))
        self.back_button.setFlat(True)

        self.contact_name = QLabel(self.receiver_name)  # Замените на реальное имя
        self.contact_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.back_button)
        header_layout.addWidget(self.contact_name)
        header_layout.addStretch()

        # ========== Messages Area ==========
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(15, 10, 15, 10)
        self.messages_layout.setSpacing(10)
        self.messages_container.setStyleSheet("background: transparent;")
        self.messages_layout.addStretch()  # Push messages to top
        self.messages_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setWidget(self.messages_container)

        # ========== Input Area ==========
        self.input_container = QWidget()
        self.input_container.setFixedHeight(70)
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(15, 5, 15, 15)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Написать сообщение...")
        self.message_input.setMinimumHeight(40)

        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon.fromTheme("mail-send"))
        self.send_button.setFixedSize(40, 40)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        # ========== Assemble Main Layout ==========
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.input_container)

    def setup_styles(self):
        # ========== Global Styles ==========
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # ========== Header Styles ==========
        self.header.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-bottom: 1px solid #444;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton {
                background: transparent;
                border: none;
                padding: 5px;
            }
        """)

        # ========== Input Area Styles ==========
        self.input_container.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-top: 1px solid #444;
            }
            QLineEdit {
                background-color: #333333;
                border: 1px solid #444;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
                color: white;
            }
            QPushButton {
                background-color: #855685;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #9a68a8;
            }
            QPushButton:pressed {
                background-color: #6a4a6a;
            }
        """)

    def send_message(self):
        message_text = self.message_input.text().strip()
        if not message_text:
            return

        message_data = {
            "type": "chat_message",
            "chat_id": self.chat_id,
            "receiver_id": self.receiver_id,
            "content": message_text,
        }

        try:
            self.send_via_ws(message_data)
            self.add_message(self.user_id, message_text, is_my_message=True)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")

        self.message_input.clear()
        self.smooth_scroll_to_bottom()

    def append_message(self, message_data: dict):
        if not message_data or "message" not in message_data:
            return

        message = message_data["message"]
        sender_id = message.get("sender_id")
        content = message.get("content", "")
        timestamp = message.get("timestamp", datetime.now(UTC).isoformat())

        if not sender_id or not content:
            return

        is_my_message = sender_id == self.user_id
        time_str = datetime.fromisoformat(timestamp).strftime("%H:%M")

        message_widget = MessageWidget(
            text=content,
            is_my_message=is_my_message,
            timestamp=time_str,
            sender_name="Вы" if is_my_message else "Собеседник"
        )

        # Анимация
        self.animate_message(message_widget, is_my_message)

        # Добавляем в layout
        if is_my_message:
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget,
                                              alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget,
                                              alignment=Qt.AlignmentFlag.AlignLeft)

        self.scroll_to_bottom()

    def show_history(self, messages_data: list):
        for message_data in reversed(messages_data):
            sender_id = message_data.get("sender_id")
            content = message_data.get("content")
            self.add_message(sender_id, content, is_my_message=(sender_id == self.user_id))

        # Прокрутка вниз после загрузки истории
        self.scroll_to_bottom()

    def add_message(self, sender_id, content, is_my_message):
        message_widget = MessageWidget(
            text=content,
            is_my_message=is_my_message,
            timestamp=datetime.now(UTC).strftime("%H:%M"),
            sender_name="Вы" if is_my_message else "Собеседник"
        )

        if is_my_message:
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget,
                                              alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget,
                                              alignment=Qt.AlignmentFlag.AlignLeft)

    def scroll_to_bottom(self):
        """Мгновенная прокрутка вниз (используется при инициализации)"""
        self.scroll_bar.setValue(self.scroll_bar.maximum())

    def smooth_scroll_to_bottom(self):
        """Плавная прокрутка вниз (используется при отправке сообщения)"""
        anim = QPropertyAnimation(self.scroll_bar, b"value")
        anim.setDuration(300)  # Длительность анимации в миллисекундах
        anim.setStartValue(self.scroll_bar.value())
        anim.setEndValue(self.scroll_bar.maximum())
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()

    def animate_message(self, message_widget, is_my_message):
        # Сохраняем текущую позицию прокрутки
        scroll_bar = self.scroll_area.verticalScrollBar()
        was_at_bottom = scroll_bar.value() == scroll_bar.maximum()

        # Начальная прозрачность
        opacity_effect = QGraphicsOpacityEffect(message_widget)
        message_widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0)

        # Анимация прозрачности
        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(0)
        opacity_anim.setEndValue(1)

        # Анимация положения
        pos_anim = QPropertyAnimation(message_widget, b"pos")
        pos_anim.setDuration(300)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        if is_my_message:
            pos_anim.setStartValue(QPoint(self.width(), message_widget.y()))
        else:
            pos_anim.setStartValue(QPoint(-message_widget.width(), message_widget.y()))

        pos_anim.setEndValue(message_widget.pos())

        # Группируем анимации
        anim_group = QParallelAnimationGroup()
        anim_group.addAnimation(opacity_anim)
        anim_group.addAnimation(pos_anim)

        # Восстанавливаем прокрутку после анимации, если нужно
        def restore_scroll():
            if was_at_bottom:
                self.scroll_to_bottom()

        anim_group.finished.connect(restore_scroll)
        anim_group.start()


class MessageWidget(QWidget):
    def __init__(self, text, is_my_message, timestamp, sender_name):
        super().__init__()

        self.is_my_message = is_my_message
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Контейнер для сообщения
        self.message_container = QWidget()
        message_layout = QVBoxLayout(self.message_container)
        message_layout.setContentsMargins(12, 8, 12, 8)

        # Имя отправителя (только для чужих сообщений)
        if not is_my_message:
            self.sender_label = QLabel(sender_name)
            self.sender_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
            message_layout.addWidget(self.sender_label)

        # Текст сообщения
        self.message_label = QLabel(text)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: white;")
        self.message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_layout.addWidget(self.message_label)

        # Время отправки
        self.time_label = QLabel(timestamp)
        self.time_label.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        message_layout.addWidget(self.time_label)

        # Настройка стиля
        bg_color = "#855685" if is_my_message else "#2a2a2a"
        border_radius = "12px; border-bottom-right-radius: 4px;" if is_my_message else "12px; border-bottom-left-radius: 4px;"

        self.message_container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: {border_radius}
            }}
        """)

        # Выравнивание сообщения
        if is_my_message:
            self.layout.addStretch()
            self.layout.addWidget(self.message_container)
        else:
            self.layout.addWidget(self.message_container)
            self.layout.addStretch()

        # Минимальная/максимальная ширина сообщения
        self.setMaximumWidth(int(self.parent().width() * 0.7) if self.parent() else 300)